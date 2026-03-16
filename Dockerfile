FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p /app/reports /app/yaml_configs /app/static

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=TestCaseGenerator.settings

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "TestCaseGenerator.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
