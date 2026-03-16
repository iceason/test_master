# 快速开始指南

本文档帮助您在5分钟内启动TestMaster系统。

---

## 前置条件

- Docker 20.0+
- Docker Compose 2.0+
- Python 3.11+（仅CLI模式需要）

---

## 方式1：Docker Compose（推荐）

### 第一步：启动服务

```bash
# 克隆或进入项目目录
cd test_master

# 启动所有服务（数据库、Redis、Web、Celery）
docker-compose up -d

# 查看启动日志
docker-compose logs -f
```

### 第二步：初始化数据库

```bash
# 运行数据库迁移
docker-compose exec web python3 manage.py migrate

# 创建超级管理员账号
docker-compose exec web python3 manage.py createsuperuser
# 按提示输入用户名、邮箱和密码
```

### 第三步：创建测试环境

```bash
# 进入Django Shell
docker-compose exec web python3 manage.py shell

# 执行以下Python代码
from api.models import Environment
Environment.objects.create(
    name='测试环境',
    code='test',
    base_url='http://httpbin.org',
    description='使用httpbin.org作为测试服务器',
    is_active=True
)
exit()
```

### 第四步：访问系统

- **Web UI**: http://localhost
- **API文档**: http://localhost/api/schema/swagger-ui/
- **Admin后台**: http://localhost/admin/
- **Prometheus指标**: http://localhost/api/metrics/

### 第五步：执行测试

1. 登录系统（使用刚创建的超级管理员账号）
2. 进入"接口管理"，创建一个接口
3. 进入"测试用例"，生成测试用例
4. 进入"测试执行"，选择用例并执行

---

## 方式2：本地开发环境

### 第一步：安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 第二步：配置数据库

```bash
# 使用SQLite（开发环境）
export DATABASE_URL="sqlite:///db.sqlite3"

# 或使用PostgreSQL（推荐）
export DATABASE_URL="postgresql://user:pass@localhost:5432/testmaster"
```

### 第三步：运行迁移

```bash
python3 manage.py migrate
python3 manage.py createsuperuser
```

### 第四步：启动服务

```bash
# 终端1：Django开发服务器
python3 manage.py runserver

# 终端2：Celery Worker
celery -A TestCaseGenerator worker -l info

# 终端3：Celery Beat（可选）
celery -A TestCaseGenerator beat -l info
```

### 第五步：访问系统

- **开发服务器**: http://127.0.0.1:8000
- **API文档**: http://127.0.0.1:8000/api/schema/swagger-ui/

---

## 方式3：CLI独立模式

无需启动Web服务，直接执行YAML测试用例。

### 第一步：安装CLI

```bash
pip install -e .
```

### 第二步：准备YAML配置

```bash
# 使用示例配置
cp examples/configs/api_tests.yaml ./my_tests.yaml

# 编辑配置（修改base_url等）
vim my_tests.yaml
```

### 第三步：执行测试

```bash
# 执行测试
testmaster run --yaml ./my_tests.yaml --env test --report ./reports

# 查看报告
open ./reports/test_report_*.html
```

---

## 快速验证

使用httpbin.org验证系统功能：

```yaml
# quick_test.yaml
version: '1.0'
type: 'testcases'
testcases:
  - name: GET请求测试
    interface:
      method: GET
      path: /get
    request_data:
      param1: value1
    expected_value:
      status_code: 200
      assertions:
        - type: jsonpath
          actual_path: $.args.param1
          expected: value1
          
  - name: POST请求测试
    interface:
      method: POST
      path: /post
    request_data:
      key: value
    expected_value:
      status_code: 200
      assertions:
        - type: jsonpath
          actual_path: $.json.key
          expected: value
```

执行：

```bash
# CLI模式
testmaster run --yaml quick_test.yaml --env test --report ./reports

# 查看结果
cat ./reports/test_report_*.json
```

---

## 下一步

- 📖 阅读[完整文档](README.md)
- 🏗️ 了解[架构设计](ARCHITECTURE.md)
- 💻 查看[使用示例](examples/)
- 🔧 配置[CI/CD集成](.gitlab-ci.yml)

---

## 常见问题

### Q1: 端口被占用怎么办？

修改docker-compose.yml中的端口映射：

```yaml
services:
  web:
    ports:
      - "8001:8000"  # 改为8001
```

### Q2: 如何停止服务？

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据
docker-compose down -v
```

### Q3: 如何查看日志？

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs web
docker-compose logs celery

# 实时跟踪日志
docker-compose logs -f web
```

### Q4: 如何重置数据库？

```bash
# 停止服务
docker-compose down

# 删除数据卷
docker volume rm test_master_postgres_data

# 重新启动
docker-compose up -d
docker-compose exec web python3 manage.py migrate
```

---

## 需要帮助？

- 📧 Email: support@testmaster.example.com
- 💬 Issues: GitHub Issues
- 📚 文档: [完整文档](README.md)
