# Vacation Planner – CrewAI Multi-Agent App

A multi-agent AI app built with [CrewAI](https://docs.crewai.com). You give it a destination; two agents research it on the web and write a Markdown travel itinerary (`report.md`).

It was first built on **Amazon Bedrock (Nova Pro)** and now runs on a **local LLM (Ollama in Docker)**. Bedrock is kept, commented out, for later use.

## How it works

```
User ──> Streamlit UI or `crewai run`
            │  topic = "London"
            ▼
        CrewAI Crew (sequential)
            │
            ├─ 1. Vacation Researcher ──> Serper web search ──> 15 key facts
            │
            └─ 2. Itinerary Planner ──> report.md (history, attractions, food)
```

## Current stack

| Layer | Technology |
|---|---|
| Agent framework | CrewAI 1.15.34 |
| Language | Python 3.12 (3.10–3.13 supported) |
| LLM | Ollama `llama3.2:3b`, running in Docker |
| Web search | Serper (`SerperDevTool`) |
| UI | Streamlit |
| Packages | uv |

## Quick start

Prerequisites: Docker Desktop (running), uv, the CrewAI CLI (`uv tool install crewai`), a [Serper](https://serper.dev) API key.

```powershell
cd vacation_planner

# 1. Start the local LLM server and download the model (first time only)
docker compose up -d
docker exec vacation-ollama ollama pull llama3.2:3b

# 2. Settings: copy the template and put your Serper key in .env
copy .env.example .env

# 3. Run, from the CLI or the web UI
crewai run                               # writes report.md
uv run streamlit run streamlitui.py      # opens the UI in the browser
```

The first run is slow (~2 min) while the model loads into memory; later replies take seconds. See [Troubleshooting](docs/04-troubleshooting.md) if it times out.

## Project structure

```
vacation_planner/
├── src/vacation_planner/
│   ├── config/
│   │   ├── agents.yaml      # agent role, goal, backstory
│   │   └── tasks.yaml       # task description, expected output, agent
│   ├── tools/               # custom tools (template only)
│   ├── crew.py              # wires agents + tasks + LLM + tools
│   └── main.py              # entry point for `crewai run` (inputs: topic)
├── knowledge/               # extra context files for agents
├── streamlitui.py           # Streamlit front end
├── docker-compose.yml       # Ollama container (local LLM)
├── .env / .env.example      # settings and keys (.env is git-ignored)
├── pyproject.toml, uv.lock  # dependencies
└── report.md                # output of the last run
```

## Documentation

1. [CrewAI concepts](docs/01-crewai-concepts.md) – agents, tasks, processes, crew and other capabilities
2. [Implementation guide](docs/02-implementation.md) – how this project was built (original Bedrock version and the Streamlit UI)
3. [Switching to a local LLM](docs/03-local-llm-ollama.md) – Bedrock → Ollama in Docker: what changed in each file, and how to switch back
4. [Troubleshooting](docs/04-troubleshooting.md) – the issues we hit and how each was fixed

## Security

Never commit `.env`: it holds API keys and is listed in `.gitignore`. Share settings through `.env.example`, which contains placeholders only.
