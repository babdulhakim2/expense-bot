FROM vllm/vllm-openai:latest

ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}

ENV HF_HOME=/model-cache
RUN --mount=type=secret,id=HF_TOKEN,required=true \
    if [ -z "$(cat /run/secrets/HF_TOKEN)" ]; then \
        echo "Error: HF_TOKEN secret is empty" && exit 1; \
    fi && \
    HF_TOKEN=$(cat /run/secrets/HF_TOKEN) && \
    echo "Logging into Hugging Face..." && \
    huggingface-cli login $HF_TOKEN && \
    echo "Downloading model..." && \
    huggingface-cli download google/gemma-2-2b-it

ENV HF_HUB_OFFLINE=1

ENTRYPOINT ["python3", "-m", "vllm.entrypoints.openai.api_server", \
    "--port", "${PORT:-8000}", \
    "--model", "${MODEL_NAME:-google/gemma-2-2b-it}"]
