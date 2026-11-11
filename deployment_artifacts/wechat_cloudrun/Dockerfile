FROM python:3.10-slim-bookworm
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 CERAMIC_DEVICE=cpu CERAMIC_ROOT=/app \
    CERAMIC_CHECKPOINT=/app/weights/checkpoint-step114750.pt \
    CERAMIC_CHECKPOINT_SHA256=6dd2b1e14f79f0ce3c02c1eafb48e1da8bfe2cfcd664564ecd39c69678275674
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch==2.3.1+cpu torchvision==0.18.1+cpu \
       --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
COPY . .
RUN python verify_package.py
EXPOSE 8080
CMD ["python", "serve.py"]
