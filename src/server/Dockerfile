FROM vllm/vllm-openai:latest

ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}

ENV HF_HOME=/model-cache
RUN --mount=type=secret,id=HF_TOKEN,required=true \
    HF_TOKEN=$(cat /run/secrets/HF_TOKEN) && \
    huggingface-cli login $HF_TOKEN && \
    huggingface-cli download google/gemma-2-2b-it

ENV HF_HUB_OFFLINE=1

ENTRYPOINT ["python3", "-m", "vllm.entrypoints.openai.api_server", \
    "--port", "${PORT:-8000}", \
    "--model", "${MODEL_NAME:-google/gemma-2-2b-it}"]
