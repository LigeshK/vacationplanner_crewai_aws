# 2. Implementation guide

[← Back to README](../README.md)

How the project was built. It was first built on Amazon Bedrock; the switch to a local LLM is covered in [03 – Local LLM](03-local-llm-ollama.md).

## 1. Environment setup

| Tool | Command | Notes |
|---|---|---|
| Python | `python --version` | The course recommends 3.11.9; this project runs on **3.12.12**. CrewAI supports 3.10–3.13. |
| uv | `pip install uv`, then `uv --version` | Fast package and virtual-env manager used by CrewAI |
| CrewAI CLI | `uv tool install crewai`, then `uv tool list` | Run `uv tool update-shell` if `crewai` is not found |
| AWS CLI (Bedrock only) | `aws configure`, then `aws sts get-caller-identity` | Needs IAM permissions for Bedrock in a region where the model is enabled |

A C++ compiler is only needed if a package install reports a compiler error.

## 2. Create the project

```powershell
crewai create crew vacation_planner
```

The wizard asks for an LLM provider and model. We chose **Amazon Bedrock → Nova Pro**, region **ap-southeast-2** (model id `bedrock/apac.amazon.nova-pro-v1:0`). The course used `us-west-2` to avoid throttling. Choose a region based on model availability, quotas, latency and cost; changing region does not guarantee higher quotas.

## 3. Agents – `config/agents.yaml`

| Agent | Role | Goal |
|---|---|---|
| `vacation_researcher` | Senior Vacation Researcher | Find the best vacation spots related to `{topic}` |
| `itinerary_planner` | Itinerary Planner | Detailed itinerary for `{topic}`: tourist spots, city history, must-try local food |

`{topic}` is filled in at run time from the inputs (see step 7).

## 4. Tasks – `config/tasks.yaml`

| Task | Agent | Expected output |
|---|---|---|
| `research_task` | vacation_researcher | 15 bullet points with the most important facts about `{topic}` |
| `reporting_task` | itinerary_planner | A full Markdown report (no code fences), saved to `report.md` |

## 5. Web search tool – Serper

The researcher needs internet access. We used `SerperDevTool` from `crewai_tools`. The course notes call it "Surfer Dev"; the correct name is **Serper**.

1. Get an API key at [serper.dev](https://serper.dev).
2. Put it in `.env` as `Serper_API_KEY=...` (this project uses this exact casing).
3. In `crew.py`:
   ```python
   serper_dev_tool = SerperDevTool(api_key=os.getenv("Serper_API_KEY"))
   ```
4. Give it only to the researcher: `tools=[serper_dev_tool]`.

The course hardcoded the key in `crew.py` while debugging. Don't do that; keep keys in `.env`.

## 6. Orchestration – `crew.py`

`crew.py` uses CrewAI decorators:

- `@CrewBase` on the class loads both YAML files.
- `@agent` methods build agents from the YAML. **Method names must match the YAML keys.**
- `@task` methods build tasks; `reporting_task` sets `output_file='report.md'`.
- `@crew` returns `Crew(agents, tasks, process=Process.sequential, verbose=True)`.

### Original Bedrock LLM

The LLM is set explicitly on each agent so the wizard's default model isn't picked up by accident:

```python
from crewai import LLM
bedrock_llm = LLM(model="bedrock/apac.amazon.nova-pro-v1:0")
# Agent(..., llm=bedrock_llm)
```

Bedrock also needs `boto3` (`uv add boto3`) and AWS credentials from the normal AWS credential chain. Prefer IAM roles or temporary credentials over access keys.

## 7. Inputs – `main.py`

```python
inputs = {"topic": "London", "current_year": str(datetime.now().year)}
VacationPlanner().crew().kickoff(inputs=inputs)
```

Change `topic` to Paris, Tokyo or another destination; the agents and tasks stay the same.

## 8. Install and run

```powershell
cd vacation_planner      # the folder that contains pyproject.toml
crewai install           # installs dependencies and writes uv.lock
crewai run               # runs the crew and writes report.md
```

With `verbose=True` the console shows each agent's reasoning, the Serper tool calls and the final report.

## 9. Streamlit UI – `streamlitui.py`

A simple front end; in production you would usually build this in React or Next.js.

- A title, a destination input, a **Plan My Dream Vacation** button and quick-pick destinations.
- On submit it calls `VacationPlanner().crew().kickoff(inputs={"topic": destination, ...})`.
- It shows `report.md` and offers a download button.

```powershell
uv add streamlit
uv run streamlit run streamlitui.py
```

## Key learnings

- `crewai create crew` scaffolds the standard structure; there's no need to hand-write it.
- Agents and tasks are configured in YAML; `crew.py` wires them to tools and the LLM.
- Set the LLM explicitly on each agent.
- `{topic}` makes the same crew reusable for any destination.
- uv manages and locks dependencies; `crewai run` starts the workflow.
