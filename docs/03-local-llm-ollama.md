# 3. Switching to a local LLM (Ollama in Docker)

[← Back to README](../README.md)

## Why

1. **Bedrock** had token issues (quota and limit errors), so we moved to a model running locally.
2. Ollama was first installed natively, then **moved to Docker** so it runs as a self-contained service.
3. The machine has **8 GB RAM**, so the model went from `llama3.1:8b` (~6–8 GB) to **`llama3.2:3b`** (~2.5 GB).

Removed code was **commented out, not deleted**, so Bedrock can be restored later.

## What changed in each file

### `.env` and `.env.example`

```ini
# MODEL=bedrock/apac.amazon.nova-pro-v1:0       # Bedrock (disabled)
# AWS_DEFAULT_REGION=ap-southeast-2
MODEL=ollama/llama3.2:3b                         # <provider>/<model>
OLLAMA_API_BASE=http://localhost:11434           # where Ollama listens
Serper_API_KEY=...
```

- `MODEL` sets the provider and model. CrewAI reads it when an agent has no explicit `llm`.
- `.env.example` is the same file with placeholder values; it is safe to commit.

### `src/vacation_planner/crew.py`

```python
llm = LLM(
    model=os.getenv("MODEL", "ollama/llama3.2:3b"),
    base_url=os.getenv("OLLAMA_API_BASE", "http://localhost:11434"),
    temperature=0.3,
)
# both agents: Agent(..., llm=llm)
```

- An explicit LLM makes the model choice visible in code. The values still come from `.env`.
- `os.getenv(key, default)` uses the default when the key is missing from `.env`.
- `temperature=0.3` keeps a small model focused and better at calling tools (0 = predictable, 1 = creative).
- CrewAI uses Ollama's OpenAI-compatible endpoint and **adds `/v1` to the base URL automatically**.
- The Bedrock LLM line is kept as a comment.

### `pyproject.toml`

- `boto3` (the AWS SDK, needed only for Bedrock) is commented out. `uv sync` then uninstalls it.
- The `litellm` extra was added later for a Groq attempt. Ollama doesn't need it (see [Troubleshooting #9](04-troubleshooting.md)).

### `docker-compose.yml` (new)

```yaml
services:
  ollama:
    image: ollama/ollama:0.40.13      # pinned version
    container_name: vacation-ollama   # "ollama" is used by another project
    ports: ["11434:11434"]            # host port : container port
    volumes: [ollama:/root/.ollama]   # models survive container rebuilds
    restart: unless-stopped           # starts again with Docker Desktop
```

- The port mapping keeps the address at `localhost:11434`, so the crew needed no changes.
- A GPU block is included but commented out (this machine has no NVIDIA GPU, so it runs on CPU).

## How the pieces connect

```
crew.py ──reads──> .env (MODEL, OLLAMA_API_BASE)
   │
   └──prompts──> localhost:11434 ──> vacation-ollama container ──> llama3.2:3b
```

## Everyday commands

```powershell
docker compose up -d                       # start Ollama
docker compose down                        # stop it (models are kept)
docker exec vacation-ollama ollama list    # installed models
docker exec vacation-ollama ollama ps      # model loaded in RAM?
docker exec vacation-ollama ollama pull <model>
```

To change model: pull it, then update `MODEL` in `.env`. Nothing else changes.

## Switching back to Bedrock

1. `.env`: uncomment the Bedrock lines, and comment out `MODEL=ollama/...` and `OLLAMA_API_BASE`.
2. `crew.py`: uncomment the Bedrock `LLM(...)` line and comment out the Ollama one.
3. `pyproject.toml`: uncomment `boto3`, then run `uv sync`.
4. Check AWS credentials: `aws sts get-caller-identity`.
