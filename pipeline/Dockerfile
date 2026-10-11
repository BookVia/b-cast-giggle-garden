FROM python:3.13-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libegl1 libx11-6 libxrender1 libxi6 libxxf86vm1 libxfixes3 libxkbcommon0 libsm6 libice6 fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir bpy==5.2.2
WORKDIR /project
CMD ["python", "pipeline/ci_check.py"]
