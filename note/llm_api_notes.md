# LLM API 学习笔记：第 1 天

日期：2026-07-02

今日目标：

```text
跑通一次最小 LLM API 调用链路
```

最终完成的链路：

```text
用户输入
-> Python 读取环境变量
-> 构造 messages
-> 请求 /chat/completions
-> 解析 choices[0].message.content
-> 打印模型回答
-> 打印 finish_reason 和 usage
```

---

## 1. LLM API 是什么

LLM API 可以先理解成一个远程函数：

```python
answer = ask_model("什么是 Agent？")
```

但它底层不是普通函数调用，而是一次 HTTP 请求：

```text
Python 程序
-> 发送 JSON 请求到模型服务
-> 模型服务生成回答
-> 返回 JSON 响应
-> Python 解析响应并打印结果
```

---

## 2. messages 结构

LLM API 的输入不是单个字符串，而是一组 `messages`。

一条 message 通常由两部分组成：

```text
message = role + content
```

示例：

```json
{
  "role": "user",
  "content": "什么是 Agent？"
}
```

常见 role：

```text
system：系统规则，设定模型身份、风格、边界
user：用户当前输入
assistant：模型之前的回答，用于多轮上下文
```

示例：

```json
[
  {
    "role": "system",
    "content": "你是一个后端工程师视角的学习助手，回答要清晰、具体、偏工程实践。"
  },
  {
    "role": "user",
    "content": "什么是 Agent？"
  }
]
```

总结：

```text
system message / user message / assistant message 本质上都是 message，只是 role 不同。
```

---

## 3. system message 和 user message 的区别

如果希望模型每次都用“后端工程师视角”回答，应该放在 system message：

```json
{
  "role": "system",
  "content": "你是一个后端工程师视角的学习助手。"
}
```

如果只想影响当前这一次问题，也可以放在 user message：

```json
{
  "role": "user",
  "content": "请用后端工程师视角解释：什么是 Agent？"
}
```

区别：

```text
放在 user message：主要影响当前问题
放在 system message：作为持续规则，影响整个对话
```

---

## 4. 请求体 request_body

今天使用的请求体结构：

```python
request_body = {
    "model": model,
    "messages": [
        {
            "role": "system",
            "content": "你是一个后端工程师视角的学习助手，回答要清晰、具体、偏工程实践。",
        },
        {
            "role": "user",
            "content": user_input,
        },
    ],
    "temperature": 0.7,
    "max_tokens": 500,
}
```

字段含义：

```text
model：使用哪个模型
messages：对话内容
temperature：控制回答随机性
max_tokens：控制最大输出长度
```

---

## 5. 响应体 response_body

模型返回的不是单纯文本，而是一个结构化 JSON。

常见结构：

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "这里是模型回答"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 50,
    "completion_tokens": 25,
    "total_tokens": 75
  }
}
```

真正给用户看的内容在：

```python
result["choices"][0]["message"]["content"]
```

原因：

```text
choices：模型可能返回多个候选答案
message：模型返回的也是一条 assistant message
content：assistant message 里的正文
finish_reason：模型为什么停止输出
usage：token 消耗统计
```

---

## 6. temperature

`temperature` 控制模型回答的随机性。

经验：

```text
temperature 越低：回答更稳定、更保守
temperature 越高：回答更发散、更有创意，但更不稳定
```

常见设置：

```text
0 或 0.2：代码、分类、结构化输出、工具选择
0.7：普通问答和解释
1.0：创意写作、头脑风暴
```

Agent / RAG 中通常不需要太高随机性：

```text
RAG 问答：0.2 - 0.5
工具选择：0 - 0.3
JSON 结构化输出：0 - 0.2
普通解释：0.5 - 0.7
```

---

## 7. max_tokens

`max_tokens` 控制模型最多生成多少 token。

注意：

```text
max_tokens 控制输出长度，不是输入长度。
```

现象：

```text
max_tokens 小：回答短，可能被截断
max_tokens 大：回答更完整，但更慢、更贵
```

工程经验：

```text
简短问答：200 - 500
普通解释：500 - 1000
长文总结：1000 - 2000
Agent 工具选择：100 - 300
```

---

## 8. finish_reason

`finish_reason` 表示模型为什么停止输出。

常见值：

```text
stop：正常结束
length：达到 max_tokens 限制，被截断
tool_calls：模型想调用工具
content_filter：被安全策略拦截
```

今天把脚本升级为会打印：

```text
finish_reason: ...
```

这样可以判断回答是否完整。

---

## 9. usage

`usage` 表示 token 消耗。

常见字段：

```text
prompt_tokens：输入消耗
completion_tokens：输出消耗
total_tokens：总消耗
```

用途：

```text
成本统计
日志记录
请求分析
性能优化
```

今天脚本已经会打印：

```text
prompt_tokens
completion_tokens
total_tokens
```

---

## 10. 环境变量

环境变量可以理解成：

```text
操作系统提供给程序读取的一组配置项
```

形式：

```text
名字 = 值
```

本项目用到：

```text
OPENAI_API_KEY：API 密钥
OPENAI_BASE_URL：API 服务地址
OPENAI_MODEL：模型名
```

Python 读取方式：

```python
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
```

为什么 API Key 不写死在代码里：

```text
避免提交到 git
避免截图或发送代码时泄露
方便不同环境使用不同配置
方便更换 Key
```

PowerShell 临时设置方式：

```powershell
$env:OPENAI_API_KEY="你的_api_key"
$env:OPENAI_BASE_URL="http://47.85.46.196:8080/v1"
$env:OPENAI_MODEL="gpt-5.5"
```

临时环境变量只在当前 PowerShell 窗口有效，关闭窗口后会消失。

---

## 11. 今天写的文件

### local_chat.py

作用：

```text
读取用户输入
-> 调用 LLM API
-> 打印模型回答
-> 打印 finish_reason 和 usage
```

核心代码：

```python
result = json.loads(response_body)
choice = result["choices"][0]
return {
    "answer": choice["message"]["content"],
    "finish_reason": choice.get("finish_reason"),
    "usage": result.get("usage", {}),
}
```

### mock_chat_response.py

作用：

```text
不联网模拟 request_body 和 response_body
练习 JSON 序列化和响应解析
```

---

## 12. 今天遇到的问题

### 12.1 Python 环境问题

一开始 `python` 指向了：

```text
D:\msys2\ucrt64\bin\python.exe
```

这个 Python 没有 pip：

```text
No module named pip
```

解决：

```text
安装 Windows 官方 Python
创建项目虚拟环境 .venv
使用 .venv 里的 python.exe
```

本项目当前虚拟环境路径比较特殊：

```text
.venv\bin\python.exe
```

运行方式：

```powershell
.\.venv\bin\python.exe .\local_chat.py
```

### 12.2 SSL 证书问题

访问官方 HTTPS API / PyPI 时出现：

```text
CERTIFICATE_VERIFY_FAILED
unable to get local issuer certificate
```

原因可能是：

```text
Python 本地证书链不完整
网络代理或安全软件替换证书
系统根证书问题
```

临时绕开方式之一是使用 HTTP 中转 API：

```text
http://47.85.46.196:8080/v1
```

注意：

```text
HTTP 不加密，学习测试可以，长期使用不建议传输敏感 API Key。
```

### 12.3 API Key 问题

遇到：

```json
{"code":"INVALID_API_KEY","message":"Invalid API key"}
```

排查方向：

```text
是否复制完整 Key，而不是页面缩略显示的 sk-xxx...xxxx
OPENAI_BASE_URL 是否设置为中转服务地址
Key 是否启用
模型名是否在可用渠道中
```

---

## 13. 今日总结

今天完成了第一个 LLM API 最小闭环：

```text
环境变量配置
-> 单轮用户输入
-> 构造 messages
-> 调用模型 API
-> 解析模型回答
-> 输出调试信息
```

最重要的三个结构：

```text
请求看 messages
回答看 choices[0].message.content
消耗看 usage
```

下一步学习方向：

```text
多轮对话：把 assistant 的历史回答追加回 messages
```

---

## 14. 多轮对话

单轮对话是：

```text
用户问一句
-> 模型答一句
-> 程序结束
```

多轮对话需要保存上下文：

```text
用户：我想学习 Agent
助手：可以从 LLM API、RAG、Tool Calling 开始
用户：那第一步怎么学？
```

第二个问题里的“第一步”依赖上一轮助手回答。

所以多轮对话的核心是：

```text
把历史 messages 保存下来，每轮都一起发给模型。
```

核心代码结构：

```python
messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT,
    }
]

while True:
    user_input = input("You: ")

    messages.append({
        "role": "user",
        "content": user_input,
    })

    result = call_llm(messages)
    answer = result["answer"]

    messages.append({
        "role": "assistant",
        "content": answer,
    })
```

关键点：

```text
每一轮不是只发当前 user_input
而是发完整 messages 历史
```

---

## 15. 为什么 assistant message 也要保存

多轮上下文不仅包括用户说过什么，也包括模型之前回答过什么。

比如：

```text
用户：我想学习 Agent
助手：可以从 LLM API 开始
用户：那第一步怎么学？
```

如果不保存 assistant message，模型不知道“第一步”指的是 LLM API。

所以完整历史应该是：

```json
[
  {"role": "system", "content": "..."},
  {"role": "user", "content": "我想学习 Agent"},
  {"role": "assistant", "content": "可以从 LLM API 开始"},
  {"role": "user", "content": "那第一步怎么学？"}
]
```

总结：

```text
user message 记录用户说过什么
assistant message 记录模型说过什么
两者一起构成完整对话上下文
```

在 Agent 中，assistant message 还可能记录：

```text
计划
中间观察
工具调用后的总结
下一步动作
```

---

## 16. messages 增长问题

如果每一轮都追加：

```text
system
-> user
-> assistant
-> user
-> assistant
...
```

messages 会越来越长。

后果：

```text
prompt_tokens 越来越多
请求越来越慢
成本越来越高
可能超过模型上下文窗口
```

今天在 `multi_turn_chat.py` 中打印了：

```text
messages_count
prompt_tokens
completion_tokens
total_tokens
```

用来观察上下文增长。

---

## 17. 最近 N 轮历史截断

最简单的上下文控制方式：

```text
system message 永远保留
只保留最近 N 轮 user / assistant
更早的历史丢掉
```

今天实现：

```python
MAX_HISTORY_ROUNDS = 3

def trim_messages(
    messages: list[dict[str, str]],
    max_rounds: int,
) -> list[dict[str, str]]:
    fixed_messages = messages[:2]
    recent_messages = messages[2:][-max_rounds * 2:]
    return fixed_messages + recent_messages
```

解释：

```python
messages[:2]
```

保留前 2 条固定消息。

```python
messages[2:]
```

取普通对话历史。

```python
[-max_rounds * 2:]
```

保留最近 N 轮。

为什么乘以 2：

```text
一轮对话通常包含 1 条 user + 1 条 assistant
```

如果 `MAX_HISTORY_ROUNDS = 3`，就保留：

```text
3 * 2 = 6 条普通历史消息
```

---

## 18. 历史截断的代价

历史截断可以控制 token，但会丢掉早期重要信息。

比如早期用户说：

```text
我有 C++ / 后端基础，目标是 3 个月做出 Agent 项目。
```

如果对话很长，这句话可能被截断。

所以：

```text
截断解决上下文太长
但会带来遗忘问题
```

真实系统里常见方案：

```text
方案 1：只保留最近 N 轮
方案 2：历史摘要
方案 3：外部记忆 / 数据库
```

---

## 19. Session Summary

为了解决截断导致的遗忘，可以在上下文里放一条摘要。

今天加入：

```python
SESSION_SUMMARY = (
    "会话摘要：用户有 C++ / 后端基础，正在学习 Agent。"
    "当前阶段是 LLM API 基础，已经完成单轮调用、多轮对话和最近 N 轮历史截断。"
)
```

初始化 messages：

```python
messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT,
    },
    {
        "role": "system",
        "content": SESSION_SUMMARY,
    }
]
```

现在上下文结构是：

```text
system prompt：模型行为规则
session summary：长期摘要
recent messages：最近几轮对话
```

对应理解：

```text
我应该怎么回答
我需要长期知道什么
刚才我们聊到哪了
```

---

## 20. 手写摘要和自动摘要

今天的 `SESSION_SUMMARY` 是手写的。

优点：

```text
简单
直观
适合学习阶段
```

缺点：

```text
需要人工维护
对话变化后不会自动更新
容易漏掉新信息
```

自动摘要的思路：

```text
对话历史太长
-> 取旧历史
-> 让模型总结成一段 summary
-> 用新 summary 替换旧 summary
-> 保留最近几轮对话
```

摘要里应该保留：

```text
用户长期目标
用户背景
已经完成的学习阶段
当前任务状态
重要决策
用户偏好
未完成事项
```

不一定保留：

```text
闲聊
重复解释
临时错误
已经解决的小问题
无关细节
```

---

## 21. 配置常量

今天把脚本顶部配置整理成常量：

```python
DEFAULT_BASE_URL = "http://47.85.46.196:8080/v1"
DEFAULT_MODEL = "gpt-5.5"

SYSTEM_PROMPT = "你是一个后端工程师视角的学习助手，回答要清晰、具体、偏工程实践。"
SESSION_SUMMARY = (...)

TEMPERATURE = 0.7
MAX_TOKENS = 200
MAX_HISTORY_ROUNDS = 3
```

Python 习惯：

```text
全大写变量名通常表示配置常量
```

好处：

```text
配置集中
容易修改
函数内部更干净
代码更像项目结构
```

请求体里使用：

```python
request_body = {
    "model": model,
    "messages": messages,
    "temperature": TEMPERATURE,
    "max_tokens": MAX_TOKENS,
}
```

---

## 22. 今日新增文件

### multi_turn_chat.py

作用：

```text
支持多轮聊天
保存 messages 历史
追加 user / assistant message
打印 usage 和 messages_count
保留 session summary
只保留最近 N 轮对话
```

运行：

```powershell
python .\multi_turn_chat.py
```

退出：

```text
exit
quit
```

---

## 23. 今日最终总结

今天从单轮 LLM API 调用推进到了最小多轮上下文管理。

已经掌握：

```text
LLM API 单轮调用
messages 结构
system / user / assistant
temperature / max_tokens
finish_reason / usage
多轮对话
assistant message 回写
最近 N 轮历史截断
session summary
配置常量
```

今天可以收尾。继续往下会进入更工程化的封装，例如：

```text
llm_client.py
配置文件
自动摘要
FastAPI 封装
```

---

## 24. 工程化拆分：llm_client.py

今天把模型调用逻辑从 `multi_turn_chat.py` 中拆出来，形成单独模块：

```text
llm_client.py
```

拆分前：

```text
multi_turn_chat.py 同时负责：
读取环境变量
构造 HTTP 请求
调用模型 API
解析响应
维护多轮 messages
处理命令行输入
打印调试信息
```

拆分后：

```text
llm_client.py：负责模型 API 调用
multi_turn_chat.py：负责命令行多轮聊天流程
```

调用关系：

```text
multi_turn_chat.py
-> import call_llm
-> llm_client.py
-> /chat/completions
```

代码：

```python
from llm_client import call_llm

result = call_llm(messages)
```

这一步的核心思想：

```text
函数职责单一
模块职责单一
调用方不关心底层 HTTP 细节
```

---

## 25. dataclass：定义清晰的数据结构

之前 `call_llm` 返回普通 dict：

```python
return {
    "answer": "...",
    "finish_reason": "stop",
    "usage": {},
}
```

问题：

```text
字段名靠字符串
写错 key 运行时才报错
结构不够明确
IDE 不容易提示
```

今天改成 `dataclass`：

```python
from dataclasses import dataclass


@dataclass
class LLMResult:
    answer: str
    finish_reason: str | None
    usage: dict[str, Any]
    elapsed_seconds: float
```

现在访问：

```python
result.answer
result.finish_reason
result.usage
result.elapsed_seconds
```

理解：

```text
dataclass 适合定义只承载数据的小类
它会自动生成 __init__ 等基础方法
```

---

## 26. ChatMessage：把 message 从 dict 变成对象

之前的 message：

```python
{
    "role": "user",
    "content": user_input,
}
```

今天改成：

```python
@dataclass
class ChatMessage:
    role: Role
    content: str
```

创建消息：

```python
ChatMessage(role=Role.USER, content=user_input)
```

因为模型 API 最终需要 dict，所以加了：

```python
def to_dict(self) -> dict[str, str]:
    return {
        "role": self.role.value,
        "content": self.content,
    }
```

请求前转换：

```python
"messages": [message.to_dict() for message in messages]
```

这句是列表推导式，等价于：

```python
message_dicts = []
for message in messages:
    message_dicts.append(message.to_dict())
```

---

## 27. Enum：固定 role 的合法值

之前：

```python
role: str
```

问题：

```text
任何字符串都能传入
比如 "usr" 也不会立刻报错
```

今天改成枚举：

```python
from enum import Enum


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
```

使用：

```python
ChatMessage(role=Role.SYSTEM, content=SYSTEM_PROMPT)
ChatMessage(role=Role.USER, content=user_input)
ChatMessage(role=Role.ASSISTANT, content=answer)
```

`to_dict()` 中用：

```python
self.role.value
```

把枚举值转成 API 需要的字符串：

```text
system / user / assistant
```

还加了运行时校验：

```python
def __post_init__(self) -> None:
    if not isinstance(self.role, Role):
        raise ValueError(f"Invalid role: {self.role}")
```

理解：

```text
Enum 适合表示固定选项
后面 Agent 的动作类型、工具状态、结果类型都可以用 Enum
```

---

## 28. logging：正式记录运行信息

`print` 适合给用户看，`logging` 适合记录程序运行状态。

今天引入：

```python
import logging
```

初始化：

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
```

常见日志级别：

```text
DEBUG：调试细节
INFO：正常运行信息
WARNING：警告，程序还能继续
ERROR：错误
```

今天的分工：

```text
print：输出 Assistant 回答给用户看
logging：记录调试信息、错误信息、token 用量、messages_count
```

示例：

```python
logging.info("finish_reason: %s", result.finish_reason)
logging.info("messages_count: %s", len(messages))
logging.error("Error: %s", exc)
```

为什么用 `%s`：

```text
把模板和值交给 logging
由 logging 决定什么时候格式化
更适合项目日志
```

---

## 29. 日志写入文件

今天新增日志目录和日志文件：

```python
from pathlib import Path

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "app.log"
```

创建目录：

```python
LOG_DIR.mkdir(exist_ok=True)
```

含义：

```text
如果 logs 不存在，就创建
如果已经存在，不报错
```

两个 handler：

```python
logging.StreamHandler()
logging.FileHandler(LOG_FILE, encoding="utf-8")
```

作用：

```text
StreamHandler：输出到终端
FileHandler：写入 logs/app.log
```

日志文件可以用于排查：

```text
某次请求为什么失败
模型调用花了多久
token 消耗是多少
messages_count 有没有增长
```

---

## 30. 模型调用耗时统计

今天在 `llm_client.py` 里加入：

```python
import time
```

调用前记录开始时间：

```python
start_time = time.perf_counter()
```

HTTP 请求完成后计算耗时：

```python
elapsed_seconds = time.perf_counter() - start_time
```

放入结果：

```python
return LLMResult(
    answer=choice["message"]["content"],
    finish_reason=choice.get("finish_reason"),
    usage=result.get("usage", {}),
    elapsed_seconds=elapsed_seconds,
)
```

日志输出：

```python
logging.info("elapsed_seconds: %.2f", result.elapsed_seconds)
```

`%.2f` 表示保留两位小数。

意义：

```text
知道一次模型调用花了多久
后续可以分析慢在模型、网络还是工具调用
这是后端可观测性的基础
```

---

## 31. 今日学习总结

今天从“能跑脚本”推进到“更像项目代码”。

完成内容：

```text
llm_client.py 模块拆分
自定义模块 import
LLMResult dataclass
ChatMessage dataclass
Role Enum
logging 基础
日志输出到终端和文件
time.perf_counter 耗时统计
```

当前代码结构：

```text
llm_client.py
  ChatMessage
  Role
  LLMResult
  call_llm

multi_turn_chat.py
  多轮聊天
  session summary
  最近 N 轮历史截断
  logging
```

今天可以收尾。继续往下会进入新主题：

```text
FastAPI 封装
配置文件
自定义异常类型
自动摘要
RAG 前置知识
```

---

## 32. FastAPI 服务封装

今天开始把 LLM 调用能力封装成 HTTP API。

当前文件：
```text
api_server.py
```

核心结构：
```python
from fastapi import FastAPI

app = FastAPI()
```

可以理解为：
```text
FastAPI = 后端服务框架
app = 当前这个后端应用
```

接口函数通过装饰器挂到 `app` 上：
```python
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

含义：
```text
当用户用 GET 请求访问 /health
FastAPI 就执行 health() 函数
并把返回的 dict 自动转成 JSON
```

---

## 33. GET 和 POST

今天先记住：
```text
GET：主要用于获取信息，一般没有请求体
POST：主要用于提交数据，一般有请求体
```

所以：
```text
GET /health
```

适合做健康检查。

而：
```text
POST /chat
```

适合接收用户输入，再调用模型。

---

## 34. Pydantic 请求模型

`ChatRequest` 用来定义 `/chat` 接口需要什么请求体：
```python
class ChatRequest(BaseModel):
    message: str
```

表示客户端应该发送：
```json
{
  "message": "什么是 Agent？"
}
```

FastAPI 会自动检查：
```text
是否有 message 字段
message 是否是字符串
```

如果请求体不符合要求，FastAPI 会自动返回 422。

---

## 35. Pydantic 响应模型

`ChatResponse` 用来定义 `/chat` 正常返回的数据结构：
```python
class ChatResponse(BaseModel):
    answer: str
    finish_reason: str | None
    usage: dict
    elapsed_seconds: float
```

含义：
```text
answer：模型回答正文
finish_reason：模型为什么停止输出
usage：token 消耗信息
elapsed_seconds：模型调用耗时
```

---

## 36. /chat 接口链路

当前 `/chat` 的调用链路：
```text
用户发送 POST /chat
-> FastAPI 解析 JSON 请求体
-> 创建 ChatRequest 对象
-> 构造 messages
-> 调用 call_llm(messages)
-> 得到 LLMResult
-> 包装成 ChatResponse
-> 返回 JSON
```

职责分工：
```text
api_server.py：负责 HTTP 接口
llm_client.py：负责模型 API 调用
```

---

## 37. HTTPException

今天给 `/chat` 增加了异常处理：
```python
try:
    result = call_llm(messages)
except Exception as exc:
    raise HTTPException(
        status_code=500,
        detail="Model API request failed.",
    ) from exc
```

含义：
```text
模型调用成功：返回 ChatResponse
模型调用失败：返回 HTTP 500 和 detail 错误信息
```

---

## 38. HTTP 状态码

今天重点理解了三个状态码：
```text
200：请求成功
422：请求体格式或字段校验失败
500：服务端处理失败
```

简单判断：
```text
请求没问题，处理成功 -> 200
客户端参数有问题 -> 422
服务端处理出错 -> 500
```

---

## 39. FastAPI 自动文档

服务启动后访问：
```text
http://127.0.0.1:8000/docs
```

FastAPI 会根据代码自动生成接口文档。

启动服务命令：
```powershell
.\venv\Scripts\python.exe -m uvicorn api_server:app --host 127.0.0.1 --port 8000
```

命令含义：
```text
uvicorn：运行 FastAPI 的 ASGI 服务器
api_server:app：加载 api_server.py 里的 app 对象
127.0.0.1：只允许本机访问
8000：服务端口
```

---

## 40. FastAPI 文档元信息

今天给 FastAPI 应用增加了文档元信息：
```python
app = FastAPI(
    title="LLM Chat API",
    description="A small FastAPI service that wraps an OpenAI-compatible chat model.",
    version="0.1.0",
)
```

作用：
```text
title：显示在 /docs 页面顶部
description：说明这个服务做什么
version：API 当前版本
```

---

## 41. Pydantic 字段校验

今天给 `message` 增加了字段校验：
```python
message: str = Field(
    min_length=1,
    max_length=2000,
    description="User message sent to the chat model.",
)
```

为了拦截纯空格输入，又增加了自定义校验：
```python
@field_validator("message")
@classmethod
def message_must_not_be_blank(cls, value: str) -> str:
    stripped_value = value.strip()
    if not stripped_value:
        raise ValueError("message must not be blank")
    return stripped_value
```

调用时机：
```text
FastAPI 收到请求
-> Pydantic 创建 ChatRequest 对象
-> 自动调用 message_must_not_be_blank()
-> 校验通过才进入 chat() 函数
-> 校验失败直接返回 422
```

---

## 42. 接口层日志

今天在 `api_server.py` 中增加了 logger：
```python
import logging

logger = logging.getLogger(__name__)
```

含义：
```text
获取当前模块对应的 logger
在 api_server.py 中，__name__ 通常是 "api_server"
```

`logging.getLogger(__name__)` 只是获取 logger，不负责日志初始化。

---

## 43. logger.exception 和 logger.error

`logger.exception()` 通常写在 `except` 代码块里：
```python
try:
    result = call_llm(messages)
except Exception:
    logger.exception("Model API request failed")
```

它会记录：
```text
错误信息
完整 traceback
```

普通的：
```python
logger.error("Model API request failed")
```

默认只记录错误信息，不自动记录 traceback。

---

## 44. 日志中的 %s 写法

今天的日志写法：
```python
logger.info(
    "Model API request completed: finish_reason=%s elapsed_seconds=%.2f total_tokens=%s",
    result.finish_reason,
    result.elapsed_seconds,
    result.usage.get("total_tokens"),
)
```

这里：
```text
%s：字符串占位
%.2f：浮点数保留两位小数
```

推荐在 logging 中这样写，而不是直接用 f-string。

原因：
```text
logger.info("xxx=%s", value)
会把模板和值交给 logging
logging 判断这条日志需要输出时，再做格式化
```

这叫懒格式化。

---

## 45. 今日 FastAPI 小结

今天完成的内容：
```text
理解 FastAPI app
理解 GET / POST
理解请求模型 ChatRequest
理解响应模型 ChatResponse
理解 /chat 接口链路
增加 HTTPException 异常处理
理解 200 / 422 / 500
学习 /docs 自动接口文档
给 FastAPI 增加 title / description / version
给 message 增加字段校验
理解 field_validator 的调用时机
增加 api_server.py 日志
理解 logger.exception
理解 logging 中的 %s 写法
```

当前 FastAPI 阶段可以认为已经从：
```text
能跑的接口
```

推进到：
```text
有请求校验、有错误处理、有日志、有文档信息的后端接口
```

---

## 46. 配置管理：config.py

今天把模型调用相关配置从 `llm_client.py` 中拆出来，放到单独的：
```text
config.py
```

配置管理的目标：
```text
把程序运行参数集中放到一个地方
让业务代码只使用配置，不到处读取环境变量
```

当前配置对象：
```python
@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_base_url: str
    openai_model: str
    temperature: float
    max_tokens: int
```

含义：
```text
openai_api_key：模型 API Key，可能不存在，所以是 str | None
openai_base_url：OpenAI-compatible API 地址
openai_model：模型名
temperature：模型输出随机性
max_tokens：最大输出 token 数
```

`frozen=True` 表示：
```text
Settings 对象创建后不允许修改
```

配置通常应该是：
```text
启动时读取
运行中只读
```

---

## 47. get_settings 和 @lru_cache

配置通过 `get_settings()` 获取：
```python
@lru_cache
def get_settings() -> Settings:
    return Settings(...)
```

`get_settings()` 负责：
```text
读取环境变量
应用默认值
创建 Settings 对象
```

`@lru_cache` 的作用：
```text
第一次调用 get_settings() 时真正读取配置
后续调用直接返回第一次创建好的 Settings 对象
```

注意：
```text
这个缓存只在当前 Python 进程中有效
服务停止后，缓存消失
重新启动服务后，又会重新读取环境变量
```

所以如果修改了环境变量：
```text
需要重启服务，新的配置才会生效
```

---

## 48. 配置读取和配置校验

当前设计中：
```text
config.py 负责读取配置
llm_client.py 在真正使用配置时校验配置
```

例如：
```python
settings = get_settings()

if not settings.openai_api_key:
    raise ConfigError("Missing OPENAI_API_KEY environment variable.")
```

这样设计的好处：
```text
服务可以先启动
/health 不依赖 API Key
只有调用 /chat 时才要求 OPENAI_API_KEY
```

配置校验有两种策略：
```text
启动时校验：服务启动时就检查，缺配置直接启动失败
使用时校验：真正用到配置时再检查
```

当前学习项目适合：
```text
使用时校验
```

---

## 49. 自定义异常类型

之前缺少 API Key 时使用：
```python
raise RuntimeError("Missing OPENAI_API_KEY environment variable.")
```

后来改成自定义异常：
```python
class ConfigError(Exception):
    pass
```

然后：
```python
raise ConfigError("Missing OPENAI_API_KEY environment variable.")
```

`pass` 的意思：
```text
什么也不做，只是占位
```

这里虽然类体为空，但 `ConfigError` 继承了 `Exception`，所以它可以：
```text
被 raise 抛出
被 except 捕获
接收错误信息
通过 str(exc) 查看错误信息
```

自定义异常的核心价值：
```text
异常类型 = 错误分类
```

不要通过字符串判断错误：
```python
if "OPENAI_API_KEY" in str(exc):
    ...
```

更好的方式是：
```python
except ConfigError:
    ...
```

---

## 50. 当前 LLM 错误分类

当前定义了三类 LLM 相关错误：
```text
ConfigError
LLMAPIError
LLMResponseError
```

含义：
```text
ConfigError：服务端配置错误，例如 OPENAI_API_KEY 未设置
LLMAPIError：调用上游模型 API 失败，例如 HTTPError / URLError
LLMResponseError：模型 API 返回了响应，但响应格式不符合预期
```

边界：
```text
没拿到正常 HTTP 响应 -> LLMAPIError
拿到了响应，但解析结构失败 -> LLMResponseError
```

---

## 51. LLMAPIError

模型 HTTP 请求失败时，抛出：
```python
class LLMAPIError(Exception):
    pass
```

对应代码：
```python
except urllib.error.HTTPError as exc:
    error_body = exc.read().decode("utf-8", errors="replace")
    raise LLMAPIError(f"API request failed: HTTP {exc.code}\n{error_body}") from exc

except urllib.error.URLError as exc:
    raise LLMAPIError(f"API request failed: {exc.reason}") from exc
```

含义：
```text
HTTPError：上游模型服务返回了非 2xx 状态码
URLError：网络连接、DNS、超时等请求层错误
```

API 层把它转换成：
```text
HTTP 502 Upstream model service failed.
```

因为当前服务调用的是上游模型服务，上游失败通常可以用 502 表示。

---

## 52. LLMResponseError

模型响应格式异常时，抛出：
```python
class LLMResponseError(Exception):
    pass
```

当前解析逻辑：
```python
try:
    result = json.loads(response_body)
    choice = result["choices"][0]
    answer = choice["message"]["content"]
except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
    raise LLMResponseError("Invalid model response format.") from exc
```

这些异常含义：
```text
json.JSONDecodeError：返回体不是合法 JSON
KeyError：缺少 choices / message / content 等字段
IndexError：choices 是空列表
TypeError：字段类型不是预期类型
```

这些底层异常被统一转换成：
```text
LLMResponseError
```

这叫异常归一化：
```text
底层保留具体错误
上层看到业务含义明确的错误
```

API 层把它转换成：
```text
HTTP 500 Invalid model response.
```

---

## 53. 异常捕获顺序

当前 API 层捕获顺序：
```python
except ConfigError as exc:
    ...
except LLMAPIError as exc:
    ...
except LLMResponseError as exc:
    ...
except Exception as exc:
    ...
```

原则：
```text
越具体的异常写前面
越通用的异常写后面
Exception 通常放最后兜底
```

因为：
```python
class ConfigError(Exception):
    pass
```

`ConfigError` 也是一种 `Exception`。

如果把：
```python
except Exception:
```

放在最前面，后面的 `except ConfigError` 就没有机会执行。

---

## 54. raise ... from exc

当前代码常见写法：
```python
raise LLMResponseError("Invalid model response format.") from exc
```

含义：
```text
抛出一个新的上层异常
同时保留原始底层异常作为原因
```

例如：
```text
底层是 KeyError: 'choices'
上层转换成 LLMResponseError
```

`from exc` 可以保留异常链，方便日志和 traceback 排查。

---

## 55. HTTPException 和错误响应

FastAPI 中正常响应使用：
```python
return ChatResponse(...)
```

错误响应使用：
```python
raise HTTPException(
    status_code=500,
    detail="Server configuration error.",
)
```

原因：
```text
return 表示正常处理完成
raise HTTPException 表示当前请求失败，需要立即返回 HTTP 错误
```

不要用 200 返回错误信息。

例如不要这样：
```python
return {"detail": "Server configuration error."}
```

因为默认状态码会是 200，状态码说成功，但内容说失败，这会让客户端很难判断。

---

## 56. 当前 /chat 完整错误映射

当前 `/chat` 错误映射：
```text
请求参数不合法
-> FastAPI / Pydantic 自动返回 422

API Key 缺失
-> ConfigError
-> HTTP 500 Server configuration error.

模型 HTTP 请求失败
-> LLMAPIError
-> HTTP 502 Upstream model service failed.

模型响应格式异常
-> LLMResponseError
-> HTTP 500 Invalid model response.

其他未知错误
-> Exception
-> HTTP 500 Model API request failed.
```

---

## 57. 当前三层结构

现在核心结构：
```text
config.py
-> llm_client.py
-> api_server.py
```

职责：
```text
config.py：读取配置，返回 Settings
llm_client.py：使用 Settings 调用模型，并把模型相关错误分类
api_server.py：处理 HTTP 请求，把底层异常转换成 HTTP 响应
```

一次成功的 `/chat` 链路：
```text
用户 POST /chat
-> FastAPI 校验 ChatRequest
-> api_server.py 构造 messages
-> llm_client.py 调用 get_settings()
-> config.py 返回 Settings
-> llm_client.py 调用模型 API
-> llm_client.py 解析 response_body
-> 返回 LLMResult
-> api_server.py 包装 ChatResponse
-> 用户收到 200 JSON
```

这一套结构后面可以复用到：
```text
RAG
Tool Calling
Agent
```

---

## 58. 是否拆 exceptions.py

当前异常类放在：
```text
llm_client.py
```

现在还可以接受，因为这些异常主要由模型调用层抛出。

未来如果异常越来越多，例如：
```text
DocumentNotFoundError
RAGIndexError
ToolExecutionError
AgentStepLimitError
```

可以考虑拆出：
```text
exceptions.py
```

判断标准：
```text
某个异常只被一个模块使用 -> 可以先放在那个模块里
多个模块都要抛出或捕获 -> 考虑放到 exceptions.py
异常类型越来越多 -> 考虑放到 exceptions.py
```

当前建议：
```text
先不拆
等进入 RAG / Tool Calling 后再自然拆分
```
