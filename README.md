# TestMaster - 工业级API测试平台

<p align="center">
  <strong>一个功能完整、生产可用的API接口测试平台</strong>
</p>

<p align="center">
  <a href="#核心特性">核心特性</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#架构设计">架构设计</a> •
  <a href="#使用指南">使用指南</a> •
  <a href="#部署指南">部署指南</a>
</p>

---

## 📋 核心特性

### 🚀 测试执行引擎
- ✅ 工业级HTTP客户端（连接池、自动重试、超时控制）
- ✅ 多层次断言系统（JSONPath、JSONSchema、正则表达式）
- ✅ 并发执行优化（线程池/进程池）
- ✅ 实时结果反馈

### 🔧 YAML驱动配置
- ✅ 数据库与YAML双向同步
- ✅ 多环境配置管理（test/staging/prod）
- ✅ 变量插值支持
- ✅ 版本控制友好

### 🎯 多触发方式
- ✅ **Web UI触发** - 可视化界面操作
- ✅ **REST API触发** - CI/CD集成
- ✅ **CLI命令行** - 独立脚本执行
- ✅ **定时任务** - Celery Beat周期性执行

### 📊 报告系统
- ✅ HTML报告（可交互式）
- ✅ JUnit XML（Jenkins/GitLab CI）
- ✅ JSON格式（程序化处理）
- ✅ Markdown摘要（PR评论）

### 🔐 企业级特性
- ✅ 权限控制和认证
- ✅ 敏感数据加密
- ✅ 审计日志
- ✅ 监控告警

---

## 🚀 快速开始

### 使用Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd test_master

# 2. 启动所有服务
docker-compose up -d

# 3. 运行数据库迁移
docker-compose exec web python3 manage.py migrate

# 4. 创建超级用户
docker-compose exec web python3 manage.py createsuperuser

# 5. 访问系统
# Web UI: http://localhost
# API: http://localhost/api/
# Admin: http://localhost/admin/
```

### 本地开发环境

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置数据库
export DATABASE_URL="postgresql://user:pass@localhost:5432/testmaster"

# 3. 运行迁移
python3 manage.py migrate

# 4. 启动开发服务器
python3 manage.py runserver

# 5. 启动Celery Worker（另一个终端）
celery -A TestCaseGenerator worker -l info

# 6. 启动Celery Beat（另一个终端）
celery -A TestCaseGenerator beat -l info
```

---

## 🏗️ 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                      触发层                              │
│  Web UI │ REST API │ CLI工具 │ Celery Beat             │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    Django REST API                       │
│  ViewSets │ Serializers │ Permissions │ Authentication  │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                  核心执行引擎（插件化）                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │TestExecutor  │  │AssertionEngine│ │  YAML Plugin  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │HTTP客户端池  │  │ 并发执行器   │  │ 报告生成器    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                      存储层                              │
│  PostgreSQL  │  Redis  │  File Storage                  │
└─────────────────────────────────────────────────────────┘
```

### 技术栈

| 组件 | 技术选型 | 说明 |
|-----|---------|------|
| 后端框架 | Django 4.2 + DRF | 成熟稳定，生态丰富 |
| 数据库 | PostgreSQL 15 | 支持JSON字段，性能优秀 |
| 缓存/队列 | Redis 7 | 高性能，支持多种数据结构 |
| 异步任务 | Celery 5.3 | 分布式任务队列 |
| HTTP客户端 | Requests + urllib3 | 连接池，自动重试 |
| 配置格式 | YAML | 可读性好，版本控制友好 |
| 报告生成 | HTML + JUnit XML | 多格式支持 |
| 容器化 | Docker + docker-compose | 标准化部署 |

---

## 📖 使用指南

### 1. CLI命令行工具

安装CLI工具：

```bash
pip install -e .
```

#### 执行测试用例

```bash
# 从YAML文件执行
testmaster run --yaml ./tests/api_tests.yaml --env test --report ./reports

# 并发执行
testmaster run --yaml ./tests/api_tests.yaml --env test --parallel

# 指定报告格式
testmaster run --yaml ./tests/api_tests.yaml --format junit
```

#### 生成测试用例

```bash
# 为指定接口生成测试用例
testmaster generate 123 --category 1 --category 2
```

#### YAML导入导出

```bash
# 导出YAML
testmaster export --scope interface --ids 1 2 3 --output ./config/interfaces.yaml

# 导入YAML
testmaster import-yaml ./config/interfaces.yaml --mode merge

# 同步到YAML（版本控制）
testmaster sync-export --output-dir ./config

# 从YAML同步到数据库（部署初始化）
testmaster sync-import ./config --mode merge
```

#### 查询环境

```bash
# 列出所有环境
testmaster list-environments

# 执行单个用例
testmaster execute --case-id 123 --env 1
```

### 2. REST API调用

#### 批量执行测试用例

```bash
curl -X POST http://localhost/api/execution-batches/execute_cases/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nightly Test Run",
    "case_ids": [1, 2, 3],
    "environment": 1,
    "parallel": false
  }'
```

#### 查询执行状态

```bash
curl http://localhost/api/execution-batches/{batch_id}/status/ \
  -H "Authorization: Token YOUR_TOKEN"
```

#### 导出YAML

```bash
curl -X POST http://localhost/api/yaml/export/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scope": "interface",
    "ids": [1, 2, 3]
  }' \
  --output interfaces.yaml
```

### 3. Web UI操作

1. 访问 http://localhost
2. 登录系统
3. 进入"测试执行"页面
4. 选择环境和测试用例
5. 点击"执行测试"
6. 实时查看执行结果
7. 下载测试报告

---

## 🚢 部署指南

### Docker Compose部署（生产环境）

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  web:
    image: your-registry/testmaster:latest
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/testmaster
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
      - ALLOWED_HOSTS=your-domain.com
    ports:
      - "8000:8000"
    volumes:
      - ./reports:/app/reports
      - ./yaml_configs:/app/yaml_configs
    restart: always

  celery:
    image: your-registry/testmaster:latest
    command: celery -A TestCaseGenerator worker -l info -c 4
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/testmaster
    restart: always

  celery-beat:
    image: your-registry/testmaster:latest
    command: celery -A TestCaseGenerator beat -l info
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/testmaster
    restart: always

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=testmaster
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./reports:/usr/share/nginx/html/reports:ro
    depends_on:
      - web
    restart: always

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes部署

参见 `k8s/` 目录中的配置文件。

### 环境变量配置

创建 `.env` 文件：

```bash
# Django配置
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/testmaster

# Celery配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# 其他配置
PAGE_SIZE=20
```

---

## 🔧 配置说明

### 环境配置（YAML格式）

```yaml
# config/environments.yaml
version: '1.0'
type: 'environments'
environments:
  test:
    name: 测试环境
    base_url: http://test-api.example.com
    description: 用于日常测试
    config:
      timeout: 30
      max_retries: 3
      verify_ssl: false
      
  staging:
    name: 预发布环境
    base_url: http://staging-api.example.com
    description: 上线前验证
    config:
      timeout: 30
      max_retries: 2
      verify_ssl: true
      
  prod:
    name: 生产环境
    base_url: https://api.example.com
    description: 生产环境（谨慎操作）
    config:
      timeout: 60
      max_retries: 3
      verify_ssl: true
```

### 接口配置（YAML格式）

```yaml
# config/interfaces.yaml
version: '1.0'
type: 'interfaces'
interfaces:
  - name: 用户注册
    method: POST
    path: /api/users/register
    schema:
      properties:
        username:
          type: string
          required: true
        email:
          type: string
          format: email
          required: true
        password:
          type: string
          minLength: 8
          required: true
    testcases:
      - name: 正向-注册成功
        description: 使用有效数据注册新用户
        request_data:
          username: testuser
          email: test@example.com
          password: Test@123456
        expected_value:
          status_code: 201
          assertions:
            - type: jsonpath
              actual_path: $.data.user_id
              expected: null
              description: 返回用户ID
```

---

## 📊 监控和告警

### Prometheus指标

系统暴露以下Prometheus指标：

```python
# 测试执行总数
test_executions_total{environment="test", status="passed"}

# 测试执行耗时
test_duration_seconds{test_case="user_login"}

# 当前活跃的测试执行
active_test_executions
```

### 配置Prometheus

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'testmaster'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/metrics'
```

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

本项目基于以下优秀的开源项目：

- Django & Django REST Framework
- Celery
- Requests
- Redis
- PostgreSQL

---

<p align="center">
  Made with ❤️ by TestMaster Team
</p>
