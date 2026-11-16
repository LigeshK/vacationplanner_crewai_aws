# Vacation Planner: CrewAI + llama.cpp server (Qwen2.5-0.5B-Instruct GGUF, CPU) on Bedrock AgentCore Runtime,
# with ADOT observability. llama-server exposes an OpenAI-compatible API on localhost:8081.
#
# Local test:
#   docker buildx build --platform linux/amd64 -t vacation-planner --load .
#   docker run --rm -p 8080:8080 -e Serper_API_KEY=<key> -e OTEL_SDK_DISABLED=true vacation-planner
#   curl -X POST http://localhost:8080/invocations -H "Content-Type: application/json" -d '{"topic":"Tokyo, Japan"}'
#
# Push to ECR (AgentCore needs arm64):
#   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
#   docker buildx build --platform linux/arm64 -t <account>.dkr.ecr.<region>.amazonaws.com/vacation-planner:latest --push .
#
# Bedrock instead of llama.cpp (later):
#   crew.py: use the commented Bedrock `llm` line. Here: base the runtime stage on debian:bookworm-slim,
#   delete the model COPY, the LLAMA_ARG_* / LLM_BASE_URL env vars and `/app/llama-server &` in CMD.
#   Run with -e MODEL=bedrock/apac.amazon.nova-pro-v1:0 -e AWS_DEFAULT_REGION=ap-southeast-2
#   (on AgentCore, grant the runtime role bedrock:InvokeModel).

# Stage 1: Python deps (crewai, bedrock-agentcore, ADOT) on uv's standalone CPython 3.11.
# Standalone Python is portable across glibc versions, so it runs on the llama.cpp (Ubuntu) base below.
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS deps
ENV UV_PYTHON_INSTALL_DIR=/opt/python UV_PYTHON_PREFERENCE=only-managed
COPY requirements-docker.txt .
RUN uv python install 3.11 && \
    uv venv --python 3.11 /opt/venv && \
    VIRTUAL_ENV=/opt/venv uv pip install --no-cache -r requirements-docker.txt && \
    rm -f /opt/venv/bin/uv /opt/venv/bin/uvx

# Stage 2: runtime = official llama.cpp CPU server image (~300 MB, amd64 + arm64; no GPU libs)
FROM ghcr.io/ggml-org/llama.cpp:server-b12407

# Model weights (~400 MB), baked into the image from the local models/ folder (gitignored).
# Get the file once (see README / below):
#   curl -L -o models/qwen2.5-0.5b-instruct-q4_k_m.gguf https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf
COPY models/qwen2.5-0.5b-instruct-q4_k_m.gguf /models/model.gguf

COPY --from=deps /opt/python /opt/python
COPY --from=deps /opt/venv /opt/venv
WORKDIR /app
RUN chown ubuntu:ubuntu /app   # crew writes report.md here
COPY src/ /app/src/

# uid 1000 already exists in the Ubuntu base as "ubuntu"
USER ubuntu

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    LLAMA_ARG_MODEL=/models/model.gguf \
    LLAMA_ARG_ALIAS=qwen2.5-0.5b \
    LLAMA_ARG_HOST=127.0.0.1 \
    LLAMA_ARG_PORT=8081 \
    LLAMA_ARG_CTX_SIZE=8192 \
    LLAMA_ARG_N_PREDICT=1024 \
    MODEL=openai/qwen2.5-0.5b \
    LLM_BASE_URL=http://127.0.0.1:8081/v1 \
    OPENAI_API_KEY=not-needed \
    OTEL_PYTHON_DISTRO=aws_distro \
    OTEL_PYTHON_CONFIGURATOR=aws_configurator \
    OTEL_SERVICE_NAME=vacation-planner \
    OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=aws_crewai
# aws_crewai is off: ADOT 0.22's CrewAI instrumentor reads event fields that crewai 0.193 lacks
# and crashes every kickoff. HTTP/boto/OpenAI-call tracing stays on. Re-enable after upgrading crewai.

EXPOSE 8080
# The base image's ENTRYPOINT is llama-server; reset it so CMD starts both processes.
ENTRYPOINT []
CMD ["sh", "-c", "/app/llama-server & exec opentelemetry-instrument python -m vacation_planner.crew"]
