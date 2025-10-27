FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# 安装系统依赖
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources && sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources
# System dependencies for psycopg2
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev git \
    && rm -rf /var/lib/apt/lists/*

# 依赖清单，先做依赖安装
COPY requirements.txt .
RUN python -m pip install --upgrade pip -i https://mirrors.ustc.edu.cn/pypi/simple \
 && pip install -r requirements.txt -i https://mirrors.ustc.edu.cn/pypi/simple

# 再复制源码
COPY app ./app
COPY main.py ./

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
