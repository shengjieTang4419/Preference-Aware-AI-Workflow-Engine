FROM mcr.microsoft.com/devcontainers/python:1-3.13-bookworm

# 安装 uv 包管理器（可选，但推荐）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 配置清华镜像源（加速下载）
ENV UV_DEFAULT_INDEX=https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/
ENV PIP_INDEX_URL=https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/

# 更新 apt 源为清华镜像
RUN rm -f /etc/apt/sources.list.d/yarn.list && \
    sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update

# 设置时区为上海
ENV TZ=Asia/Shanghai
RUN apt-get install -y ca-certificates tzdata && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /workspace

# 预安装常用工具 + Node.js
RUN apt-get update && \
    apt-get install -y git curl wget vim nano && \
    # 安装 Node.js 18.x (LTS)
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    # 配置 npm 淘宝镜像（国内加速）
    npm config set registry https://registry.npmmirror.com && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 验证安装
RUN node --version && npm --version
