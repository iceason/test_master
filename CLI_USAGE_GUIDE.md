# TestMaster CLI使用指南

## 安装

```bash
# 进入项目目录
cd test_master

# 安装CLI工具
pip install -e .

# 验证安装
testmaster --version
```

## 命令说明

### 1. run - 执行测试

从YAML文件执行测试用例

```bash
# 基础用法
testmaster run --yaml ./examples/configs/api_tests.yaml --env test

# 并发执行
testmaster run --yaml ./tests/smoke.yaml --env test --parallel

# 生成报告
testmaster run --yaml ./tests/full.yaml --env test --report ./reports --format html

# 指定环境
testmaster run --yaml ./tests/api.yaml --env staging --report ./reports
```

**参数说明：**
- `--yaml, -y`: YAML配置文件路径（必填）
- `--env, -e`: 运行环境（test/staging/prod，默认test）
- `--parallel, -p`: 并发执行标志
- `--report, -r`: 报告输出目录
- `--format, -f`: 报告格式（html/json/junit，默认html）

### 2. generate - 生成测试用例

为指定接口生成测试用例

```bash
# 生成所有类型用例
testmaster generate 123

# 指定用例分类
testmaster generate 123 --category 1 --category 2

# 多个分类
testmaster generate 456 -c 1 -c 2 -c 3
```

**参数说明：**
- `interface_id`: 接口ID（必填）
- `--category, -c`: 用例分类ID（可多次指定）

### 3. export - 导出YAML

导出数据库配置到YAML文件

```bash
# 导出测试用例
testmaster export --scope testcase --ids 1 2 3 --output ./config/testcases.yaml

# 导出接口
testmaster export --scope interface --ids 10 11 12 --output ./config/interfaces.yaml

# 导出环境配置
testmaster export --scope environment --ids 1 2 --output ./config/environments.yaml
```

**参数说明：**
- `--scope, -s`: 导出范围（testcase/interface/environment）
- `--ids, -i`: ID列表（可多次指定）
- `--output, -o`: 输出文件路径

### 4. import-yaml - 导入YAML

从YAML文件导入到数据库

```bash
# 合并模式（默认）
testmaster import-yaml ./config/interfaces.yaml

# 替换模式
testmaster import-yaml ./config/testcases.yaml --mode replace

# 导入多个文件
testmaster import-yaml ./config/env.yaml --mode merge
testmaster import-yaml ./config/api.yaml --mode merge
```

**参数说明：**
- `yaml_file`: YAML文件路径（必填）
- `--mode, -m`: 导入模式（merge/replace，默认merge）

### 5. execute - 执行单个用例

执行指定的单个测试用例

```bash
# 执行用例
testmaster execute --case-id 123 --env 1

# 指定环境
testmaster execute -c 456 -e 2
```

**参数说明：**
- `--case-id, -c`: 测试用例ID
- `--env, -e`: 环境ID

### 6. list-environments - 列出环境

显示所有可用的测试环境

```bash
testmaster list-environments
```

### 7. sync-export - 同步导出

将数据库完整同步到YAML文件（用于版本控制）

```bash
# 导出所有配置到指定目录
testmaster sync-export --output-dir ./yaml_configs

# 导出结果：
# yaml_configs/
# ├── environments.yaml
# └── interfaces.yaml
```

### 8. sync-import - 同步导入

从YAML目录批量导入到数据库（用于部署初始化）

```bash
# 从目录导入所有YAML
testmaster sync-import ./yaml_configs --mode merge

# 替换模式
testmaster sync-import ./yaml_configs --mode replace
```

---

## 使用场景

### 场景1：本地开发测试

```bash
# 1. 查看可用环境
testmaster list-environments

# 2. 执行本地测试
testmaster run --yaml ./tests/local.yaml --env test --report ./reports

# 3. 查看HTML报告
open ./reports/test_report_*.html
```

### 场景2：CI/CD集成

```bash
# Jenkins/GitLab CI脚本中使用
testmaster run --yaml ./tests/ci_suite.yaml --env ci --parallel --report ./reports --format junit

# 检查退出码
echo $?  # 0=成功，1=失败
```

### 场景3：版本控制

```bash
# 1. 导出当前配置
testmaster sync-export --output-dir ./configs

# 2. 提交到Git
git add configs/
git commit -m "Update test configurations"
git push

# 3. 在新环境恢复配置
testmaster sync-import ./configs --mode merge
```

### 场景4：独立脚本执行

```bash
# 不依赖Web UI，纯命令行执行
testmaster run --yaml ./standalone_tests.yaml --env prod --report ./prod_reports
```

---

## 最佳实践

### 1. 环境隔离

为不同环境创建独立的YAML配置：

```
configs/
├── environments.yaml      # 所有环境定义
├── test_api_tests.yaml   # 测试环境用例
├── staging_api_tests.yaml # 预发环境用例
└── prod_smoke_tests.yaml  # 生产冒烟用例
```

### 2. CI/CD集成

在CI脚本中使用：

```yaml
# .gitlab-ci.yml
test:
  script:
    - pip install -e .
    - testmaster run --yaml ./tests/ci.yaml --env ci --parallel --report ./reports --format junit
  artifacts:
    reports:
      junit: ./reports/junit_report_*.xml
```

### 3. 定期导出

定期导出配置到版本控制：

```bash
# 添加到crontab
0 2 * * * cd /opt/testmaster && testmaster sync-export --output-dir ./backup/$(date +\%Y\%m\%d)
```

### 4. 报告归档

保留历史报告：

```bash
# 归档脚本
DATE=$(date +%Y%m%d)
testmaster run --yaml ./tests/daily.yaml --env test --report ./reports/$DATE
```

---

## 常见问题

### Q1: 如何设置环境变量？

在YAML中使用 `${ENV_VAR_NAME}` 格式：

```yaml
environments:
  test:
    base_url: ${TEST_API_URL}
    config:
      api_key: ${TEST_API_KEY}
```

### Q2: 如何处理认证？

在环境配置中设置认证头：

```yaml
environments:
  test:
    config:
      default_headers:
        Authorization: Bearer ${API_TOKEN}
```

### Q3: 执行失败如何调试？

查看详细日志和报告：

```bash
# 1. 查看HTML报告中的请求/响应详情
open ./reports/test_report_*.html

# 2. 查看JSON报告中的完整数据
cat ./reports/test_report_*.json | jq .

# 3. 检查系统日志
docker-compose logs celery
```

---

## 更多帮助

```bash
# 查看命令帮助
testmaster --help

# 查看子命令帮助
testmaster run --help
testmaster export --help
```
