"""VacationPlanner crew: researcher (web search) -> itinerary planner (report.md)."""

import os

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from crewai import LLM, Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from vacation_planner.tools.custom_tool import SerperSearchTool
#AgentCore Gateway imports

#utilising tool decorator to define the tool
from crewai.tools import tool
import requests #to make HTTP requests to the AgentCore Gateway

app = BedrockAgentCoreApp()

# Local model: Ollama on the host (.env), or llama.cpp server inside the Docker image
# (MODEL=openai/qwen2.5-0.5b, LLM_BASE_URL=http://127.0.0.1:8081/v1).
llm = LLM(
    model=os.getenv("MODEL", "ollama/qwen2.5:0.5b"),
    base_url=os.getenv("LLM_BASE_URL") or os.getenv("OLLAMA_API_BASE", "http://localhost:11434"),
    temperature=0.3,
)

# Bedrock (disabled, kept for later): uncomment, add boto3, set MODEL/AWS_DEFAULT_REGION in .env.
# llm = LLM(model=os.getenv("MODEL", "bedrock/apac.amazon.nova-pro-v1:0"))

#AgentCore Gateway code
CLIENT_ID = "48bo6mupddn9lbjc17ueibi9d4"
CLIENT_SECRET = "1t2fhf6dc7bvm2igqkkli1c7nq9suckok0tolm2b7tes54npgebu"
TOKEN_URL = "https://ap-southeast-2czkmt0kb9.auth.ap-southeast-2.amazoncognito.com/oauth2/token"

def fetch_access_token(client_id, client_secret, token_url):
  response = requests.post(
    token_url,
    data="grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}".format(client_id=client_id, client_secret=client_secret),
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  print("Access Token Response:", response.json()['access_token'])
  return response.json()['access_token']

def call_tool(gateway_url, access_token, tool_name, arguments):
  headers = {
      "Content-Type": "application/json",
      "Accept": "application/json, text/event-stream",
      "Authorization": f"Bearer {access_token}",
      "MCP-Protocol-Version": MCP_PROTOCOL_VERSION
  }

  payload = {
      "jsonrpc": "2.0",
      "id": "call-tool-request",
      "method": "tools/call",
      "params": {
          "tool_name": tool_name, # The name of the tool to call
          "arguments": arguments # The arguments to pass to the tool
      }
  }

  response_tool = requests.post(gateway_url, headers=headers, json=payload)
  print("This is Travel Packages detail response:", response_tool.json())
  return response_tool.json()

#Agentcore GW - wrap your exisitng functions as a CwewAI tool
@tool("Get Travel Packages")
def get_travel_packages(city: str) -> str:
    """Get travel packages for a given city using the AgentCore Gateway."""
    gateway_url = "https://gateway-vacation-planner-lknfwclwfa.gateway.bedrock-agentcore.ap-southeast-2.amazonaws.com/mcp"
    access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
    return call_tool(gateway_url, access_token, "target-travel-agent-tool__get_travel_packages", {"city": city})

@CrewBase
class VacationPlanner():
    """VacationPlanner crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def vacation_researcher(self) -> Agent:
        return Agent(config=self.agents_config['vacation_researcher'],  # type: ignore[index]
                     llm=llm, tools=[SerperSearchTool, get_travel_packages], verbose=True)

    @agent
    def itinerary_planner(self) -> Agent:
        return Agent(config=self.agents_config['itinerary_planner'],  # type: ignore[index]
                     llm=llm, verbose=True)

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config['research_task'])  # type: ignore[index]

    @task
    def reporting_task(self) -> Task:
        return Task(config=self.tasks_config['reporting_task'], output_file='report.md')  # type: ignore[index]

    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential, verbose=True)


@app.entrypoint
def agent_invocation(payload, context):
    """AgentCore entrypoint: {"topic": "..."} -> {"result": "..."}"""
    try:
        topic = payload.get("topic", "Tokyo, Japan")
        result = VacationPlanner().crew().kickoff(inputs={"topic": topic})
        return {"result": result.raw}
    except Exception as e:
        return {"error": f"Error during agent invocation: {e}"}


if __name__ == "__main__":
    app.run()  # AgentCore HTTP server on port 8080
