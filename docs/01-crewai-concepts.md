# 1. CrewAI concepts

[← Back to README](../README.md)

## What is CrewAI?

CrewAI is a lightweight, open-source Python framework for building **multiple AI agents that collaborate** on a task.

- **Multi-agent** – specialised agents work towards one objective.
- **Task-oriented** – each agent has a clear responsibility and goal.
- **LLM-agnostic** – OpenAI, Anthropic, Amazon Bedrock, Google, local models (Ollama) and more.
- **Cloud-agnostic** – runs on AWS, Azure, Google Cloud or locally.
- **Independent** – built from scratch; it does not depend on LangChain.

### Agent framework landscape

| Type | Framework | Provider |
|---|---|---|
| Open source | CrewAI | CrewAI |
| Open source | LangChain / LangGraph | LangChain |
| Open source | AutoGen | Microsoft |
| Proprietary | Amazon Bedrock Agents | AWS |
| Proprietary | Vertex AI | Google Cloud |

Open-source frameworks let you choose the LLM and cloud freely, which reduces vendor lock-in. This project shows that in practice: it moved from Bedrock to a local model by changing configuration only.

## Use case: AI vacation planner

A traveller wants a London itinerary covering history, landmarks, attractions and food. Instead of one agent doing everything, two specialists split the work:

1. **Research agent** – searches the internet and collects facts.
2. **Planner (summariser) agent** – turns the research into a structured itinerary.

They run **sequentially**: the research output becomes the planner's input.

## The four core concepts

### 1. Agents

An autonomous worker with a specialised job. An agent can use tools (web search, files, databases), collaborate with other agents and keep memory.

| Attribute | Purpose | Required |
|---|---|---|
| `role` | Its function, e.g. "Senior Vacation Researcher" | Yes |
| `goal` | What it is trying to achieve | Yes |
| `backstory` | Experience and perspective; shapes its behaviour | Yes |
| `llm` | The model it thinks with | No |
| `tools` | External capabilities it can call | No |
| `memory` | Retain relevant interactions | No |
| `verbose` | Print detailed execution logs | No |
| `max_iter` | Limit reasoning iterations | No |

If `llm` is not set, CrewAI falls back to the `MODEL` environment variable. Set it explicitly so the intended model is always used.

### 2. Tasks

A specific piece of work for an agent: what to do, and what the result should look like.

| Attribute | Purpose | Required |
|---|---|---|
| `description` | Instructions for the work | Yes |
| `expected_output` | What a finished result looks like | Yes |
| `agent` | Which agent performs it | No |
| `tools` | Tools available for this task | No |
| `context` | Outputs of earlier tasks to use as input | No |
| `output_file` | Save the result to a file | No |

### 3. Processes

How tasks are ordered and how agents collaborate.

- **Sequential** (default) – tasks run in a fixed order; each output feeds the next. *Research → Planner → itinerary.* Used in this project.
- **Hierarchical** – a manager agent (`manager_llm`) assigns work to other agents. *Manager → Developer, Tester, Reviewer.*
- **Consensual** – mentioned in course material as planned; check the current CrewAI version before relying on it.

### 4. Crew

The orchestrator: the group of agents, their tasks and the process.

| Attribute | Purpose |
|---|---|
| `agents` | Agents in the crew |
| `tasks` | Tasks to run |
| `process` | Sequential or hierarchical |
| `verbose` | Detailed logs |
| `manager_llm` | Manager's model (hierarchical only) |

## Other capabilities

| Capability | What it does |
|---|---|
| **Knowledge** | Gives agents context from text, PDF, CSV and other sources (e.g. internal travel guides). This project has a `knowledge/` folder. |
| **LLMs** | Any supported provider; set per agent with `llm=`. |
| **Tools** | Web search (Serper), file read/write, CSV, code execution, RAG search, databases, S3, Bedrock knowledge bases, or your own custom tools. |
| **Memory** | Short-term (during a run), long-term (across runs, persistent storage) and entity memory (people, places and their relations). |
| **Planning** | `Crew(planning=True)` breaks a goal into steps before execution. |
| **Training** | Improve agent behaviour with feedback (`crewai train`). |
| **Testing, CLI, events** | Evaluate runs (`crewai eval`), manage projects from the CLI, and listen to execution events. |

## Key takeaways

- **Agents** are specialised workers, **tasks** define the work and expected output, **processes** define the order, and the **crew** brings them together.
- **Tools** connect agents to the outside world; **knowledge** and **memory** give them context.
- CrewAI is LLM-agnostic: the same crew ran on Amazon Bedrock and on a local Ollama model.
