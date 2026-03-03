FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

# Remove Yarn repo if it exists (breaks apt-get update when key is missing)
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && rm -f /usr/share/keyrings/yarnkey.gpg \
    && rm -f /etc/apt/keyrings/yarn.gpg \
    && find /etc/apt/sources.list.d -maxdepth 1 -type f -name "*.list" -print -exec sed -i '/dl\.yarnpkg\.com/d' {} \; \
    && sed -i '/dl\.yarnpkg\.com/d' /etc/apt/sources.list \
    || true

# System deps for PySide6 / Qt
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    libgl1 \
    libegl1 \
    libopengl0 \
    libxkbcommon0 \
    libdbus-1-3 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxcb-util1 \
    libxcb1 \
    libx11-6 \
    libx11-xcb1 \
    libxext6 \
    libxrender1 \
    libxi6 \
    libxrandr2 \
    libxfixes3 \
    libxcursor1 \
    libxkbcommon-x11-0 \
    libfontconfig1 \
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -U pip uv ruff mypy pytest

WORKDIR /workspaces/res