# 测试用例/数据集生成工具使用说明
## 工具简介
该工具基于 YAML 格式的字段schema配置，自动生成标准化的接口测试用例（包含正向、负向、边界、安全四类）或结构化数据集，最终输出 JSON 格式文件，并提供测试用例覆盖率分析功能。

核心特性：
- 支持生成四类测试用例：Positive（正向）、Negative（负向）、Boundary（边界）、Security（安全）
- 支持生成指定数量的结构化数据集
- 自动输出测试用例覆盖率分析（字段覆盖、类别覆盖）
- 支持字符串、整数、枚举等常见字段类型，适配正则、长度限制、保留字等约束

## 环境准备
### 依赖安装
确保已安装 Python 3.7+，并安装以下依赖包：
```bash
pip install pyyaml faker hypothesis
```

### 文件结构
工具包含两个核心文件：
- `test_case_generator.py`：主程序入口，处理命令行参数、文件读写、覆盖率分析
- `field_generators.py`：测试用例/数据集生成核心逻辑，实现各类场景的用例生成

## 快速开始
### 1. 编写 YAML Schema 文件
创建字段配置文件（如 `schema.yaml`），示例如下：
```yaml
username:
  type: string
  required: true
  min_length: 6
  max_length: 20
  regex: ^[a-zA-Z0-9_]+$
  reserved_words: ["admin", "root", "guest"]
email:
  type: string
  required: true
  format: email
  regex: ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
age:
  type: integer
  required: false
  minimum: 18
  maximum: 100
gender:
  type: string
  enum: ["male", "female", "other"]
password:
  type: string
  required: true
  min_length: 8
  max_length: 32
  regex: ^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{8,32}$
```

### 2. 生成测试用例
执行以下命令生成测试用例（默认模式）：
```bash
python test_case_generator.py \
  -i schema.yaml \
  -o test_cases.json \
  --api-name USER_REGISTER
```

### 3. 生成数据集
执行以下命令生成指定数量的结构化数据集：
```bash
python test_case_generator.py \
  -i schema.yaml \
  -o dataset.json \
  --api-name USER_REGISTER \
  --mode dataset \
  --count 20
```

## 命令行参数说明
| 参数         | 简写 | 必选 | 说明                                                                 |
|--------------|------|------|----------------------------------------------------------------------|
| `--input`    | `-i` | 是   | 输入的 YAML schema 文件路径                                          |
| `--output`   | `-o` | 是   | 输出的 JSON 文件路径（测试用例/数据集）                              |
| `--api-name` | 无   | 是   | API 名称前缀（用于生成测试用例ID，如 `USER_CREATE`）                 |
| `--mode`     | 无   | 否   | 生成模式，可选值：`test_cases`（默认）、`dataset`                   |
| `--count`    | 无   | 否   | 仅 `dataset` 模式生效，指定生成的数据集记录数，默认值：10            |

## YAML Schema 配置规范
| 字段         | 类型    | 说明                                                                 |
|--------------|---------|----------------------------------------------------------------------|
| `type`       | string  | 字段类型，支持：`string`、`integer`、`number`（必填）                |
| `required`   | boolean | 是否为必填字段，默认：`false`                                        |
| `min_length` | integer | 仅字符串类型生效，最小长度                                           |
| `max_length` | integer | 仅字符串类型生效，最大长度（超过1000时会跳过超长字符串生成）           |
| `minimum`    | integer | 仅数值类型生效，最小值                                               |
| `maximum`    | integer | 仅数值类型生效，最大值                                               |
| `enum`       | list    | 枚举值列表，工具会为每个枚举值生成正向用例                           |
| `regex`      | string  | 字段格式正则表达式，工具会生成匹配/不匹配的用例                     |
| `format`     | string  | 字段语义格式，目前仅支持 `email`（用于生成语义非法的负向用例）       |
| `reserved_words` | list | 保留字列表，工具会为每个保留字（含大小写变体）生成负向用例          |

## 输出文件说明
### 测试用例输出（test_cases.json）
单个测试用例结构：
```json
{
  "ID": "USER_REGISTER_USERNAME_POSITIVE_SUCCESS_1234",
  "Field": "username",
  "Input payload": "user_123456",
  "POS/NEG": "Positive",
  "Expected": "Success",
  "Reason": "Valid value (Basic)"
}
```
字段说明：
- `ID`：唯一测试用例ID（API名称+字段+类别+预期结果+随机数）
- `Field`：测试的字段名
- `Input payload`：测试输入值
- `POS/NEG`：用例类别（Positive/Negative/Boundary/Security）
- `Expected`：预期结果（Success/Failure）
- `Reason`：用例设计原因

### 数据集输出（dataset.json）
数据集为JSON数组，每个元素是符合schema的结构化数据：
```json
[
  {
    "username": "user_87987",
    "email": "user_87987@example.com",
    "age": 25,
    "gender": "male",
    "password": "A1b!987654"
  },
  ...
]
```

## 覆盖率分析
生成测试用例后，工具会自动输出覆盖率分析日志，包含以下内容：
1. **总用例数**：生成的测试用例总数
2. **按类别统计**：各类型用例（Positive/Negative/Boundary/Security）的数量及占比，缺失类别会触发警告
3. **按字段统计**：每个字段生成的用例数，无可用例的字段会触发警告

示例输出：
```
📊 === Test Case Coverage Analysis ===
Total Cases: 86

--- By Category ---
  - Positive: 24 (27.9%)
  - Negative: 32 (37.2%)
  - Boundary: 18 (20.9%)
  - Security: 12 (14.0%)

--- By Field ---
  - username: 18
  - email: 20
  - age: 12
  - gender: 16
  - password: 20

=======================================
```

## 注意事项
1. 正则表达式需符合 Python `re` 模块语法，特殊字符（如 `\d`）需转义或使用单引号包裹
2. 字符串最大长度建议不超过1000，避免生成超大字符串影响性能
3. 安全用例仅对字符串类型字段生效，包含SQL注入、XSS、命令注入等常见攻击载荷
4. 数据集生成逻辑基于 `Faker` 库，会生成符合字段约束的真实语义数据（如邮箱、用户名）
5. 若YAML schema中某个字段未生成用例，需检查字段配置是否完整（如`type`是否指定）