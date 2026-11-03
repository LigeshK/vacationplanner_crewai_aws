# 4. Troubleshooting

[← Back to README](../README.md)

The issues we hit while moving from Bedrock to a local LLM, in the order they happened.

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | Bedrock calls fail with token / limit errors | Bedrock token quota and limits on the account | Switched to a local LLM (Ollama). Bedrock config kept as comments. |
| 2 | `ollama : The term 'ollama' is not recognized` | Ollama not installed, or not on PATH in an already-open terminal | Install it, then open a new terminal. Later uninstalled in favour of Docker (see the uninstall note below). |
| 3 | `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine` | Docker Desktop not running | Start Docker Desktop and wait until `docker info` responds. |
| 4 | Image download stopped partway | Download killed because the PC was critically low on RAM. The `ollama/ollama` image is **~8.5 GB** (includes CUDA libraries). | Close apps and retry with `docker compose pull --quiet`; it resumes from cached layers. |
| 5 | `Conflict. The container name "/ollama" is already in use` | A stopped container from another project (`E:\AI\Ecommerce.AI`) already has that name | Renamed ours `container_name: vacation-ollama`. The other project was left untouched. |
| 6 | Port 11434 already allocated | Both projects' Ollama containers publish 11434 | Run only one at a time (`docker stop <name>`), or map ours to `11435:11434` and update `OLLAMA_API_BASE`. |
| 7 | Test prompt hangs; log shows `Load failed … timed out waiting for llama-server to start` | Not enough free RAM: 7.8 GB total, ~0.6 GB free; the Docker VM is capped at ~3.7 GB, so Windows pages it to disk | Close Chrome and other heavy apps and retry. After the model loaded, the **first prompt took ~134 s and the next ~7 s**. |
| 8 | `llama3.1:8b` too heavy for this PC | 8B model needs ~6–8 GB RAM on CPU | Switched to `llama3.2:3b` (~2.5 GB). Even smaller: `llama3.2:1b`, but it's weaker at tool calls. |
| 9 | Groq not usable as `groq/...` | Groq is not a native CrewAI provider; it needs LiteLLM | `uv add "crewai[tools,litellm]"`, then `MODEL=groq/<model>` and `GROQ_API_KEY` in `.env`. The attempt was stopped: `pyproject.toml` lists the extra but litellm isn't installed yet. |
| 10 | Researcher answers without searching | Small local models sometimes skip tool calls | Check the verbose log for the Serper call. Keep `temperature` low, or try `qwen2.5:7b` if RAM allows. |
| 11 | `README.md` contained `<<<<<<< HEAD … >>>>>>>` | Unresolved git merge conflict | Resolved by rewriting the README. |

## Tips

- **The model unloads after 5 idle minutes**, so the next run pays the slow load again. To keep it loaded longer, add `environment: [OLLAMA_KEEP_ALIVE=30m]` to the service in `docker-compose.yml` and run `docker compose up -d`.
- **Memory check before a run:**
  ```powershell
  $os = Get-CimInstance Win32_OperatingSystem
  "{0:N1} GB free" -f ($os.FreePhysicalMemory/1MB)
  ```
- **Is the server up?** `curl http://localhost:11434/api/version`
- **What is it doing?** `docker logs vacation-ollama --tail 30`
- **Quick model test (PowerShell):**
  ```powershell
  $b = '{"model":"llama3.2:3b","messages":[{"role":"user","content":"Reply with just: OK"}],"stream":false}'
  (Invoke-RestMethod http://localhost:11434/api/chat -Method Post -Body $b -ContentType 'application/json').message.content
  ```

## Uninstalling native Ollama (Windows)

1. Quit Ollama from the system tray (or `Stop-Process -Name "ollama*" -Force`).
2. Settings → Apps → Installed apps → Ollama → Uninstall (or run `unins000.exe /VERYSILENT` in `%LOCALAPPDATA%\Programs\Ollama`).
3. Delete leftover data: `Remove-Item -Recurse -Force "$env:USERPROFILE\.ollama"`. The uninstaller keeps your models.

## If none of this helps: other options

| Option | Pros | Cons |
|---|---|---|
| Native Ollama (no Docker) | No Docker VM overhead; most reliable on 8 GB RAM | Another install on Windows |
| Hosted API (Groq, OpenRouter) | No local RAM needed; fast | Not local; needs an API key |
| Back to Bedrock | Strong model (Nova Pro) | The original token and limit issues |
