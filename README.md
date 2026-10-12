# Persistent Memory Agent

一个与具体模型和 AI 平台解耦的长期记忆 Agent。它把“记忆管理”和“模型调用”拆成两个独立层，使同一套记忆数据可以在 OpenAI、Anthropic、兼容网关、本地模型服务或其他 Agent 框架之间复用。

当前仓库提供一个轻量、可审计、可迁移的 MVP：

- 使用 SQLite 保存长期记忆
- 使用确定性的词法检索召回相关记忆
- 通过 Provider 接口适配不同模型服务
- 提供命令行工具和 Python API
- 提供可复用的长期记忆 Skill 规范

> 当前版本不会自动把每轮对话都写入记忆库。只有通过 `remember` 命令或 `MemoryAgent.remember()` 显式保存的内容才会进入长期记忆。这种默认行为可以避免把临时对话、错误信息或敏感数据无意中永久保存。

## 工作原理

```text
用户请求
   |
   v
MemoryAgent
   |-- 从 MemoryStore 检索相关记忆
   |-- 将记忆作为上下文交给 Provider
   `-- 返回模型响应

MemoryStore  <---->  SQLite / 未来的 PostgreSQL、向量数据库
Provider     <---->  OpenAI-compatible、Anthropic、本地模型或自定义服务
```

记忆记录目前包含以下字段：

| 字段 | 说明 |
| --- | --- |
| `content` | 记忆内容 |
| `kind` | 类型，例如 `fact`、`preference`、`project` |
| `importance` | 重要程度，范围为 1 到 5 |
| `source` | 来源，例如 `user` 或 `agent` |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

## 环境要求

- Python 3.10 或更高版本
- 一个可调用的模型服务

MVP 使用 Python 标准库实现，安装项目本身不需要额外的运行时依赖。

## 安装

### Windows PowerShell

```powershell
git clone https://github.com/dbnody/persistent-memory-agent.git
cd persistent-memory-agent

python -m venv .venv
.\.venv\Scripts\Activate.ps1

Copy-Item .env.example .env
```

### macOS / Linux

```bash
git clone https://github.com/dbnody/persistent-memory-agent.git
cd persistent-memory-agent

python3 -m venv .venv
source .venv/bin/activate

cp .env.example .env
```

也可以以可编辑模式安装命令行入口：

```bash
pip install -e .
```

如果不安装项目，直接在仓库根目录执行 `python -m memory_agent.cli ...` 即可。

## 配置模型服务

复制 `.env.example` 后，根据模型服务修改以下环境变量：

```dotenv
MEMORY_AGENT_PROVIDER=openai-compatible
MEMORY_AGENT_API_KEY=replace-me
MEMORY_AGENT_MODEL=gpt-4o-mini
MEMORY_AGENT_BASE_URL=https://api.openai.com/v1
MEMORY_AGENT_DB=data/memory.db
```

### OpenAI 或 OpenAI-compatible 服务

适用于 OpenAI、兼容网关，以及许多本地模型服务器：

```powershell
$env:MEMORY_AGENT_PROVIDER = "openai-compatible"
$env:MEMORY_AGENT_API_KEY = "your-api-key"
$env:MEMORY_AGENT_MODEL = "gpt-4o-mini"
$env:MEMORY_AGENT_BASE_URL = "https://api.openai.com/v1"
```

如果使用本地兼容服务，只需替换地址和模型名。例如：

```powershell
$env:MEMORY_AGENT_API_KEY = "local"
$env:MEMORY_AGENT_MODEL = "your-local-model"
$env:MEMORY_AGENT_BASE_URL = "http://localhost:1234/v1"
```

### Anthropic

```powershell
$env:MEMORY_AGENT_PROVIDER = "anthropic"
$env:MEMORY_AGENT_API_KEY = "your-anthropic-key"
$env:MEMORY_AGENT_MODEL = "claude-3-5-sonnet-latest"
$env:MEMORY_AGENT_BASE_URL = "https://api.anthropic.com/v1"
```

项目当前不会自动加载 `.env` 文件，因此在 PowerShell、CI 或部署环境中请显式注入变量，或接入你自己的 dotenv 配置方式。

## 命令行使用

### 保存记忆

```powershell
python -m memory_agent.cli remember "用户偏好使用中文回答"
```

默认会保存为 `kind=fact`、`importance=3`。记忆保存成功后会输出记忆 ID。

### 检索记忆

```powershell
python -m memory_agent.cli recall "中文"
```

检索结果按相关程度和重要程度排序。

### 使用记忆进行对话

```powershell
python -m memory_agent.cli chat "请根据我的偏好回答这个问题"
```

Agent 会先检索与请求相关的记忆，然后把检索结果放入系统上下文，再调用配置好的 Provider。

### 指定数据库位置

```powershell
python -m memory_agent.cli remember "项目使用 Python" --db data/project.db
python -m memory_agent.cli recall "项目" --db data/project.db
```

### 导出记忆

```powershell
python -m memory_agent.cli export data/memory-export.json
```

导出前建议人工检查文件内容，确认没有包含不应迁移或公开的敏感数据。

## Python API

```python
from memory_agent.agent import MemoryAgent, provider_from_env
from memory_agent.storage import MemoryStore

store = MemoryStore("data/memory.db")
agent = MemoryAgent(provider_from_env(), store)

# 显式保存长期记忆
agent.remember(
    "用户偏好使用中文回答",
    kind="preference",
    importance=5,
)

# 检索记忆
for memory in agent.recall("用户语言偏好"):
    print(memory.content)

# 让 Agent 使用相关记忆回答
answer = agent.chat("请用我偏好的语言回答")
print(answer)
```

## 接入其他 AI 工具

只要实现以下 Provider 接口，就可以接入其他模型、企业内部网关或本地推理服务：

```python
class Provider:
    def complete(self, messages: list[dict[str, str]]) -> str:
        ...
```

示例：

```python
class MyProvider:
    def complete(self, messages):
        # 在这里调用你的模型或 Agent 平台
        return "模型响应"


agent = MemoryAgent(MyProvider(), MemoryStore("data/memory.db"))
```

这样更换模型时不需要迁移记忆库，也不需要修改 `MemoryStore` 或 Skill 规则。

## 目录结构

```text
.
├── memory_agent/
│   ├── agent.py       # Agent 编排和 Provider 环境配置
│   ├── cli.py         # 命令行入口
│   ├── models.py      # Memory 数据结构
│   ├── providers.py   # 模型服务适配器
│   └── storage.py     # SQLite 持久化和检索
├── skill/
│   └── long-term-memory/
│       └── SKILL.md   # 长期记忆行为规范
├── tests/
├── data/
├── .env.example
├── pyproject.toml
└── LICENSE
```

## 测试

```powershell
python -m unittest discover -s tests
python -m compileall -q memory_agent
```

测试不需要 API Key，也不会调用外部模型服务。


## 从 MVP 升级到生产环境

当前版本适合个人使用、原型验证和本地部署。生产环境通常还需要：

1. 用 PostgreSQL/pgvector 或其他向量数据库替换 SQLite。
2. 增加 embedding 检索和混合检索，而不是只使用词法匹配。
3. 增加自动会话摘要、记忆去重、冲突更新和过期策略。
4. 为不同用户或租户增加隔离、认证和权限控制。
5. 对敏感字段进行脱敏、加密和审计。
6. 增加模型调用重试、超时、限流、成本统计和可观测性。
7. 为记忆召回质量和错误记忆建立评测集。

## 许可证

本项目使用 [MIT License](LICENSE)。
