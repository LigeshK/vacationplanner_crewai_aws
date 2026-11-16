"""VacationPlanner crew: researcher (web search) -> itinerary planner (report.md)."""

import os

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from crewai import LLM, Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from vacation_planner.tools.custom_tool import SerperSearchTool

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


@CrewBase
class VacationPlanner():
    """VacationPlanner crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def vacation_researcher(self) -> Agent:
        return Agent(config=self.agents_config['vacation_researcher'],  # type: ignore[index]
                     llm=llm, tools=[SerperSearchTool()], verbose=True)

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
