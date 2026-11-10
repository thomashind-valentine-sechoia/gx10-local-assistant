FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

ARG CUDA=130

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    sox \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch with CUDA support before app deps so pip does not replace it.
RUN pip install --no-cache-dir \
    "torch==2.11.0" "torchaudio==2.11.0" --index-url https://download.pytorch.org/whl/cu${CUDA}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV HF_HOME=/data/huggingface \
    PYTHONUNBUFFERED=1

COPY server.py design_voices.py synth_client.py ./

EXPOSE 10200

ENTRYPOINT ["python", "server.py"]
