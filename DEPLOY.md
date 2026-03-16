# 部署文档 (Deployment Guide)

本系统基于 **Python Django** 框架开发，支持 **SQLite** (默认/开发环境) 和 **PostgreSQL** (生产环境) 数据库。

## 1. 环境要求
*   **操作系统**: Linux (Ubuntu/CentOS), macOS, Windows
*   **Python**: 3.10 或更高版本
*   **Git**: 用于代码拉取

## 2. 安装步骤

### 2.1 获取代码
```bash
git clone <repository_url>
cd TestCaseGenerator
```

### 2.2 创建虚拟环境
建议使用虚拟环境隔离项目依赖。
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
```

### 2.3 安装依赖
```bash
pip install -r requirements.txt
```

## 3. 数据库配置

### 模式 A: 使用默认 SQLite (开发/轻量级部署)
无需任何配置，系统默认使用项目根目录下的 `db.sqlite3` 文件。

### 模式 B: 使用 PostgreSQL (生产环境)
通过设置环境变量 `DATABASE_URL` 来切换至 PostgreSQL。
```bash
# 格式: postgres://USER:PASSWORD@HOST:PORT/NAME
export DATABASE_URL=postgres://myuser:mypassword@localhost:5432/mydatabase
```

## 4. 初始化系统
无论使用哪种数据库，首次部署或更新代码后均需执行数据库迁移。

1.  **应用数据库迁移** (生成数据库表结构)
    ```bash
    python3 manage.py migrate
    ```

2.  **创建管理员账号** (可选，用于进入 Django Admin 后台)
    ```bash
    python3 manage.py createsuperuser
    ```

3.  **收集静态文件** (生产环境)
    ```bash
    python3 manage.py collectstatic
    ```

## 5. 启动服务

### 5.1 开发模式运行
```bash
python3 manage.py runserver 0.0.0.0:8000
```
访问: `http://localhost:8000`

### 5.2 生产环境运行 (推荐使用 Gunicorn)
安装 Gunicorn:
```bash
pip install gunicorn
```

启动服务:
```bash
gunicorn TestCaseGenerator.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

---

## 常见问题
*   **Q: 启动时提示 `WARNING: No DATABASE_URL environment variable set`**
    *   A: 这是正常提示，表示未检测到外部数据库配置，系统将自动回退到默认的 SQLite 数据库。
*   **Q: 数据库文件在哪里？**
    *   A: 默认情况下，`db.sqlite3` 文件位于项目根目录下。
