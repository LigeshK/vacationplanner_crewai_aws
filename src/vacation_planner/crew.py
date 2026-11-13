"""
VacationPlanner crew.

Two agents work one after the other:
  1. vacation_researcher - searches the web (Serper) for destination info.
  2. itinerary_planner   - turns that research into a day-by-day plan (report.md).

Agent roles/goals live in config/agents.yaml, task descriptions in
config/tasks.yaml. This file wires them together with an LLM and tools.
"""

import os

from crewai import LLM, Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from crewai import LLM

#Agent core changes
#Add AgentCore - imports
from bedrock_agentcore.runtime import BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

# Google search via serper.dev. The API key is read from .env (Serper_API_KEY).
serper_dev_tool = SerperDevTool(api_key=os.getenv("Serper_API_KEY"))
llm=LLM(model=os.getenv("MODEL", "ollama/llama3.2:3b"), base_url=os.getenv("OLLAMA_API_BASE", "http://localhost:11434"), temperature=0.3)

# ---------------------------------------------------------------------------
# LLM (the "brain" every agent uses)
# ---------------------------------------------------------------------------

# Active: local model served by Ollama running in Docker (see docker-compose.yml).
#   model       - "<provider>/<model name>", read from MODEL in .env.
#   base_url    - where the Ollama server listens, read from OLLAMA_API_BASE.
#   temperature - 0 = predictable, 1 = creative. Kept low so the small local
#                 model stays focused and calls tools reliably.
# The second argument of os.getenv() is the fallback used when .env lacks the key.
local_llm = LLM(
    model=os.getenv("MODEL", "ollama/llama3.2:3b"),
    base_url=os.getenv("OLLAMA_API_BASE", "http://localhost:11434"),
    temperature=0.3,
)

# Disabled: AWS Bedrock, kept for later use.
# To switch back:
#   1. Uncomment the line below and comment out the Ollama LLM above.
#   2. In .env, enable the Bedrock lines and disable the Ollama lines.
#   3. In pyproject.toml, uncomment boto3, then run `uv sync`.
#   4. Make sure AWS credentials are configured (e.g. `aws configure`).
# local_llm = LLM(model=os.getenv("MODEL", "bedrock/apac.amazon.nova-pro-v1:0"))


# ---------------------------------------------------------------------------
# Crew definition
# ---------------------------------------------------------------------------

@CrewBase
class VacationPlanner():
    """VacationPlanner crew"""

    # @CrewBase fills these lists automatically from the @agent and @task
    # methods below, in the order they are defined.
    agents: list[BaseAgent]
    tasks: list[Task]

    # --- Agents -------------------------------------------------------------
    # Each method name must match a key in config/agents.yaml.

    @agent
    def vacation_researcher(self) -> Agent:
        """Researches destinations, attractions and travel info on the web."""
        return Agent(
            config=self.agents_config['vacation_researcher'],  # type: ignore[index]
            verbose=True,              # print the agent's reasoning to the console
            #llm=local_llm,             # which model this agent thinks with
            tools=[serper_dev_tool],   # only this agent can search the web
            llm=llm
        )

    @agent
    def itinerary_planner(self) -> Agent:
        """Builds the final itinerary from the researcher's findings."""
        return Agent(
            config=self.agents_config['itinerary_planner'],  # type: ignore[index]
            verbose=True,
            #llm=local_llm,             # no tools: works only from the research it receives
            llm=llm
        )

    # --- Tasks --------------------------------------------------------------
    # Each method name must match a key in config/tasks.yaml.
    # The YAML assigns each task to an agent.

    @task
    def research_task(self) -> Task:
        """Step 1: gather information about the destination."""
        return Task(
            config=self.tasks_config['research_task'],  # type: ignore[index]
        )

    @task
    def reporting_task(self) -> Task:
        """Step 2: write the itinerary. Receives step 1's output automatically."""
        return Task(
            config=self.tasks_config['reporting_task'],  # type: ignore[index]
            output_file='report.md',   # final result is saved here (project root)
        )

    # --- Crew ---------------------------------------------------------------

    @crew
    def crew(self) -> Crew:
        """Creates the VacationPlanner crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # run tasks in order; each sees the previous output
            verbose=True,
        )
# @agentcore.entrypoint decorator is used to mark the entry point of the BedrockAgentCoreApp. It specifies which crew class to run when the application starts.
@app.entrypoint
def agent_invocation(payload,context):
    """Handle the agent invocation. """
    print("Agent invocation received with payload:", payload)
    try:
        #extract user input from payload
        user_input = payload.get("topic","Tokyo, Japan")  # Default to "Tokyo, Japan" if not provided
        print(f"User input extracted: {user_input}")

        #Crew execution - Creates an instance of the Vacation Planner class and run crew method with user input as argument
        research_crew_instance = VacationPlanner()
        crew = research_crew_instance.crew()

        #starts the sequential agent workflow
        result = crew.kickoff(inputs={"topic": user_input})
        print("Context:\n-----\n", context)
        print("Result Raw:\n-----\n", result.raw)

        #Safely access json_dict if it exists
        if hasattr(result, 'json_dict'):
            print("Result JSON:\n-----\n", result.json_dict)
        else:
            print("No JSON output available.")
        return {"result":result.raw}
    except Exception as e:
        print(f"Error during agent invocation: {e}")
        return{"error":f"Error during agent invocation: {e}"}

#Local test function
def test_local():
    """Test the crew locally without BedrockAgentCoreApp."""
    try:
        crew_instance = VacationPlanner()
        crew = crew_instance.crew()
        result = crew.kickoff(inputs={"topic": "Plan a vacation to Germany"})
        print("Result Raw:\n-----\n", result.raw)
        if hasattr(result, 'json_dict'):
            print("Result JSON:\n-----\n", result.json_dict)
        else:
            print("No JSON output available.")
        return result
    except Exception as e:
        print(f"Error during local test: {e}")
        return {"error": f"Error during local test: {e}"}
if __name__ == "__main__":

    # Run AgentCore server - HTTP server on port 8080
    app.run()