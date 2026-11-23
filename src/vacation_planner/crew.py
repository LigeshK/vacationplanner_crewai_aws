"""VacationPlanner crew hosted on Bedrock AgentCore.

Request flow:
    1. AgentCore calls `agent_invocation` with {"topic": "<destination>"}.
    2. Previous conversations for the session are loaded from AgentCore Memory.
    3. Crew runs sequentially:
         vacation_researcher -> web search (Serper) + travel packages (AgentCore Gateway)
         itinerary_planner   -> writes the final itinerary to report.md
    4. The user/assistant exchange is saved back to AgentCore Memory.
    5. {"result": "<itinerary>"} is returned to the caller.
"""

# --- Imports -------------------------------------------------------------------
import os
import uuid
from datetime import datetime, timezone

import boto3
import requests
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from crewai import LLM, Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import tool

from vacation_planner.tools.custom_tool import SerperSearchTool

# --- Configuration -------------------------------------------------------------
# All values come from the environment: .env locally (loaded by crewai on import),
# runtime environment variables when deployed to AgentCore.
AWS_REGION = os.getenv("AWS_REGION")

# AgentCore Memory: stores past conversations per session.
MEMORY_ID = os.getenv("AGENTCORE_MEMORY_ID")
MEMORY_ACTOR_ID = "user"

# AgentCore Gateway (MCP) secured by Cognito client-credentials OAuth.
CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")
TOKEN_URL = os.getenv("COGNITO_TOKEN_URL")
GATEWAY_URL = os.getenv("GATEWAY_URL")
GATEWAY_TOOL_NAME = os.getenv("GATEWAY_TOOL_NAME")
MCP_PROTOCOL_VERSION = os.getenv("MCP_PROTOCOL_VERSION")

# --- Clients -------------------------------------------------------------------
app = BedrockAgentCoreApp()

# Local model: Ollama on the host (.env), or llama.cpp server inside the Docker image
# (MODEL=openai/qwen2.5-0.5b, LLM_BASE_URL=http://127.0.0.1:8081/v1).
llm = LLM(
    model=os.getenv("MODEL", "ollama/qwen2.5:0.5b"),
    base_url=os.getenv("LLM_BASE_URL") or os.getenv("OLLAMA_API_BASE", "http://localhost:11434"),
    temperature=0.3,
)
# Bedrock (disabled, kept for later): set MODEL/AWS_DEFAULT_REGION in .env and uncomment.
# llm = LLM(model=os.getenv("MODEL", "bedrock/apac.amazon.nova-pro-v1:0"))

memory_client = boto3.client("bedrock-agentcore", region_name=AWS_REGION)


# --- AgentCore Gateway helpers -------------------------------------------------
def fetch_access_token(client_id: str, client_secret: str, token_url: str) -> str:
    """Get an OAuth access token from Cognito using the client-credentials grant."""
    response = requests.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()
    return response.json()["access_token"]


def call_tool(gateway_url: str, access_token: str, tool_name: str, arguments: dict) -> dict:
    """Invoke a tool on the AgentCore Gateway via an MCP JSON-RPC `tools/call` request."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {access_token}",
        "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
    }
    payload = {
        "jsonrpc": "2.0",
        "id": "call-tool-request",
        "method": "tools/call",
        "params": {"tool_name": tool_name, "arguments": arguments},
    }
    response = requests.post(gateway_url, headers=headers, json=payload)
    print("Travel packages response:", response.json())
    return response.json()


@tool("Get Travel Packages")
def get_travel_packages(city: str) -> str:
    """Get travel packages for a given city using the AgentCore Gateway."""
    access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
    return call_tool(GATEWAY_URL, access_token, GATEWAY_TOOL_NAME, {"city": city})


# --- AgentCore Memory helpers --------------------------------------------------
def load_previous_conversations(session_id: str, max_results: int = 3) -> list[dict]:
    """Fetch recent memory events for the session, with datetimes made JSON-friendly."""
    response = memory_client.list_events(
        memoryId=MEMORY_ID,
        actorId=MEMORY_ACTOR_ID,
        sessionId=session_id,
        maxResults=max_results,
    )
    return [
        {k: v.isoformat() if isinstance(v, datetime) else v for k, v in event.items()}
        for event in response.get("events", [])
    ]


def save_conversation(session_id: str, user_text: str, assistant_text: str) -> None:
    """Store one user/assistant exchange as a memory event."""
    memory_client.create_event(
        memoryId=MEMORY_ID,
        actorId=MEMORY_ACTOR_ID,
        sessionId=session_id,
        eventTimestamp=datetime.now(timezone.utc),
        payload=[
            {"conversational": {"content": {"text": user_text}, "role": "USER"}},
            {"conversational": {"content": {"text": assistant_text}, "role": "ASSISTANT"}},
        ],
        clientToken=str(uuid.uuid4()),
    )


# --- Crew ----------------------------------------------------------------------
@CrewBase
class VacationPlanner:
    """Two-agent sequential crew: research the destination, then plan the itinerary."""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def vacation_researcher(self) -> Agent:
        """Step 1 agent: gathers destination info and travel packages."""
        return Agent(
            config=self.agents_config["vacation_researcher"],  # type: ignore[index]
            llm=llm,
            tools=[SerperSearchTool(), get_travel_packages],
            verbose=True,
        )

    @agent
    def itinerary_planner(self) -> Agent:
        """Step 2 agent: turns the research into a day-by-day itinerary."""
        return Agent(
            config=self.agents_config["itinerary_planner"],  # type: ignore[index]
            llm=llm,
            verbose=True,
        )

    @task
    def research_task(self) -> Task:
        """Task 1: research the destination (runs first)."""
        return Task(config=self.tasks_config["research_task"])  # type: ignore[index]

    @task
    def reporting_task(self) -> Task:
        """Task 2: write the itinerary report to report.md (runs second)."""
        return Task(config=self.tasks_config["reporting_task"], output_file="report.md")  # type: ignore[index]

    @crew
    def crew(self) -> Crew:
        """Run tasks in the order they are defined above."""
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential, verbose=True)


# --- AgentCore entrypoint ------------------------------------------------------
@app.entrypoint
def agent_invocation(payload, context):
    """AgentCore entrypoint: {"topic": "..."} -> {"result": "..."} or {"error": "..."}."""
    print(f"Payload: {payload}")
    try:
        # 1. Read input and session
        topic = payload.get("topic", "Tokyo, Japan")
        session_id = getattr(context, "sessionId", "default_session")
        print(f"Processing vacation destination: {topic}")

        # 2. Load past conversations from memory
        previous_conversations = load_previous_conversations(session_id)

        # 3. Run the crew with the topic and memory context
        result = VacationPlanner().crew().kickoff(
            inputs={"topic": topic, "previous_conversations": previous_conversations}
        )

        # 4. Save this exchange to memory
        save_conversation(session_id, topic, result.raw)

        print("Context:\n-------\n", context)
        print("Result Raw:\n*******\n", result.raw)
        if getattr(result, "json_dict", None):
            print("Result JSON:\n*******\n", result.json_dict)

        # 5. Return the result
        return {"result": result.raw}

    except Exception as e:
        print(f"Exception occurred: {e}")
        return {"error": f"An error occurred: {e}"}


if __name__ == "__main__":
    app.run()  # AgentCore HTTP server on port 8080
