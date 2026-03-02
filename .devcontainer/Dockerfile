
FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

# System deps for PySide6 / Qt (headless-friendly)
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    libgl1 \
    libegl1 \
    libxkbcommon0 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libopengl0 \
    && rm -rf /var/lib/apt/lists/*

# Python tooling
RUN pip install --no-cache-dir -U pip uv ruff mypy pytest

WORKDIR /workspaces/res
