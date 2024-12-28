FROM vllm/vllm-openai:latest

ENV HF_HOME=/model-cache
ARG HF_TOKEN
RUN --mount=type=secret,id=HF_TOKEN \
    if [ -z "$(cat /run/secrets/HF_TOKEN)" ]; then echo "Error: HF_TOKEN secret is empty" && exit 1; fi && \
    HF_TOKEN=$(cat /run/secrets/HF_TOKEN) && \
    echo "Logging into Hugging Face..." && \
    huggingface-cli login $HF_TOKEN && \
    echo "Downloading model..." && \
    huggingface-cli download google/gemma-2-2b-it

ENV HF_HUB_OFFLINE=1

ENTRYPOINT python3 -m vllm.entrypoints.openai.api_server \
    --port ${PORT:-8000} \
    --model ${MODEL_NAME:-google/gemma-2-2b-it} \
    ${MAX_MODEL_LEN:+--max-model-len "$MAX_MODEL_LEN"}