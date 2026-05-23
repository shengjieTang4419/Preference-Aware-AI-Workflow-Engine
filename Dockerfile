FROM python:3.13-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY pyproject.toml ./
RUN pip install --no-cache-dir uv && \
    uv pip install --system --no-cache .

# 应用代码
COPY . .

# 创建存储目录
RUN mkdir -p storage/agents storage/tasks storage/crews storage/executions \
    storage/artifacts storage/skills storage/uploads

EXPOSE 8000

CMD ["uvicorn", "crewai_web.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
