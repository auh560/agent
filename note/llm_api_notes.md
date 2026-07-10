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

---

## 59. 结构化输出

今天开始学习结构化输出。

普通模型回答适合人看：
```text
Agent 是一种可以根据目标调用工具完成任务的程序。
```

结构化输出适合程序解析：
```json
{
  "answer": "Agent 是一种可以根据目标调用工具完成任务的程序。",
  "confidence": "high",
  "need_tool": false
}
```

结构化输出的核心目标：
```text
让模型输出固定格式
让 Python 程序可以稳定解析
```

---

## 60. 要求模型只输出 JSON

结构化输出 prompt 里要明确：
```text
只输出 JSON
不要输出 Markdown
不要输出代码块
不要输出额外解释
```

原因：
```text
json.loads() 只能解析合法 JSON
如果模型多输出“当然可以，下面是 JSON”，解析就会失败
```

字段也要写清楚：
```text
answer: string
confidence: "low" | "medium" | "high"
need_tool: boolean
```

prompt 是提前约束模型；Pydantic 是事后验证结果。

---

## 61. structured_output.py

今天新增：
```text
structured_output.py
```

作用：
```text
输入一个问题
-> 让模型只输出 JSON
-> json.loads() 解析
-> Pydantic 校验
-> 打印结构化字段
```

核心链路：
```text
模型输出字符串
-> json.loads()
-> Python dict
-> StructuredOutput.model_validate()
-> StructuredOutput 对象
```

---

## 62. StructuredOutput 模型

结构化输出模型：
```python
class StructuredOutput(BaseModel):
    answer: str = Field(min_length=1)
    confidence: Literal["low", "medium", "high"]
    need_tool: bool
```

含义：
```text
answer：非空字符串
confidence：只能是 low / medium / high
need_tool：布尔值
```

`Literal["low", "medium", "high"]` 表示：
```text
字段只能取固定几个值
```

适合：
```text
分类
状态
动作类型
工具名称
置信度
```

---

## 63. field_validator

为了防止 answer 是纯空格，增加了：
```python
@field_validator("answer")
@classmethod
def answer_must_not_be_blank(cls, value: str) -> str:
    stripped_value = value.strip()
    if not stripped_value:
        raise ValueError("answer must not be blank")
    return stripped_value
```

这句：
```python
if not isinstance(answer, str) or not answer.strip():
```

可以理解为：
```text
如果 answer 不是字符串，或者去掉空格后是空字符串，就不合法
```

---

## 64. model_validate

`model_validate()` 是 Pydantic `BaseModel` 提供的方法。

因为：
```python
class StructuredOutput(BaseModel):
    ...
```

所以可以调用：
```python
StructuredOutput.model_validate(parsed_output)
```

作用：
```text
拿一份外部数据
按照 StructuredOutput 的字段和规则进行校验
校验通过 -> 返回 StructuredOutput 对象
校验失败 -> 抛 ValidationError
```

---

## 65. dict 和 Pydantic 对象

`json.loads()` 得到的是普通 dict：
```python
parsed_output["answer"]
```

`model_validate()` 得到的是 Pydantic 对象：
```python
structured_output.answer
```

区别：
```text
dict 是原始数据，字段和类型不可靠
Pydantic 对象是校验后的数据，字段和类型更可靠
```

结构化输出推荐流程：
```text
模型字符串
-> json.loads()
-> dict
-> model_validate()
-> Pydantic 对象
-> 业务逻辑使用
```

---

## 66. JSONDecodeError 和 ValidationError

结构化输出有两类常见失败：
```text
JSONDecodeError：模型输出不是合法 JSON
ValidationError：JSON 合法，但字段结构不符合要求
```

例子：
```text
模型多输出解释文字 -> JSONDecodeError
confidence 输出 "sure" -> ValidationError
```

这说明：
```text
先检查是不是合法 JSON
再检查是不是符合 schema
```

---

## 67. 结构化输出修复

今天给 `structured_output.py` 增加了一次修复机会。

流程：
```text
第一次调用模型
-> 解析或校验失败
-> 把错误信息和原始输出发回模型
-> 要求模型重新输出合法 JSON
-> 再解析一次
```

修复时保留：
```text
模型刚才的错误输出
解析/校验错误信息
修复要求
```

注意：
```text
只重试有限次数
当前只重试一次
```

---

## 68. Tool Decision

今天新增：
```text
tool_decision.py
```

目标：
```text
让模型不直接回答，而是先输出工具决策
```

模型输出格式：
```json
{
  "action": "calculator",
  "arguments": {
    "expression": "12 * 8 + 3"
  }
}
```

字段含义：
```text
action：动作 / 工具名
arguments：工具参数
```

---

## 69. ToolDecision 模型

工具决策模型：
```python
class ToolDecision(BaseModel):
    action: Literal["final_answer", "search_docs", "calculator"]
    arguments: dict[str, Any]
```

含义：
```text
action 只能是 final_answer / search_docs / calculator
arguments 是工具参数字典
```

`arguments` 中文可以叫：
```text
工具参数
```

例如：
```json
{
  "arguments": {
    "expression": "12 * 8 + 3"
  }
}
```

表示：
```text
调用工具时传入 expression 参数
```

---

## 70. 工具参数模型

为了让工具参数更严格，给每个工具定义参数模型：
```python
class FinalAnswerArguments(BaseModel):
    answer: str

class CalculatorArguments(BaseModel):
    expression: str

class SearchDocsArguments(BaseModel):
    query: str
```

两层校验：
```text
ToolDecision 校验 action 是否允许
Arguments 模型校验工具参数是否正确
```

例如：
```text
calculator 必须有 expression
search_docs 必须有 query
```

---

## 71. 工具执行

工具本质上是普通 Python 函数。

例如 calculator：
```python
def calculator(expression: str) -> str:
    ...
```

模型不会真的执行工具。

模型负责输出：
```text
action + arguments
```

Python 负责：
```text
校验参数
执行工具函数
返回工具结果
```

Agent 的关键边界：
```text
模型负责决策
程序负责执行
```

---

## 72. calculator 工具

今天实现了学习版计算器：
```python
def calculator(expression: str) -> str:
    allowed_chars = set("0123456789+-*/(). ")
    if any(char not in allowed_chars for char in expression):
        raise ValueError("expression contains unsupported characters")

    result = eval(expression, {"__builtins__": {}}, {})
    return str(result)
```

安全限制：
```text
只允许数字、空格、+ - * / ( ) .
禁用 __builtins__
```

注意：
```text
这是学习版，不是生产级沙箱
```

---

## 73. 工具注册表

最开始可以用 if/else 分发工具。

工具多了以后，更适合工具注册表：
```python
@dataclass(frozen=True)
class Tool:
    function: Any
    arguments_model: type[BaseModel]

TOOLS: dict[str, Tool] = {
    "calculator": Tool(
        function=calculator,
        arguments_model=CalculatorArguments,
    ),
    "search_docs": Tool(
        function=search_docs,
        arguments_model=SearchDocsArguments,
    ),
}
```

含义：
```text
工具名 -> 工具函数 + 参数模型
```

新增工具时：
```text
1. 写 Arguments 模型
2. 写工具函数
3. 注册到 TOOLS
```

---

## 74. arguments 展开

当前工具执行：
```python
args = tool.arguments_model.model_validate(decision.arguments)
return tool.function(**args.model_dump())
```

`args.model_dump()` 会把 Pydantic 对象转成 dict。

例如：
```python
{"expression": "12*8+3"}
```

`**` 表示把字典展开成关键字参数：
```python
calculator(**{"expression": "12*8+3"})
```

等价于：
```python
calculator(expression="12*8+3")
```

区别：
```text
*list：展开列表/元组
**dict：展开字典
```

---

## 75. search_docs 最小实现

今天实现了最小版 `search_docs`：
```python
def search_docs(query: str) -> str:
    note_dir = Path("note")
    ...
```

功能：
```text
搜索 note/*.md
大小写不敏感匹配 query
返回最多 5 条命中
每条包含文件名、行号和命中文本
```

例如：
```text
search_docs("Agent")
```

会返回：
```text
note/agent_learning_path.md:1: ...
note/agent_learning_path.md:6: ...
```

这已经是一个真实工具。

---

## 76. 最小 Agent Loop

当前 `tool_decision.py` 已经形成最小 Agent loop：
```text
用户任务
-> 模型输出工具决策 JSON
-> Pydantic 校验
-> Python 执行工具
-> 得到 tool_result
-> 把工具结果交给模型
-> 模型生成最终回答
```

对应 Agent 概念：
```text
Task
-> Decide
-> Validate
-> Act
-> Observe
-> Answer
```

当前还不是完整 Agent，因为：
```text
只允许一次工具调用
没有多步循环
没有长期记忆
没有 RAG 检索链路
```

但它已经具备 Agent 的基本骨架。

---

## 77. RAG 是什么

RAG 全称是：
```text
Retrieval-Augmented Generation
```

中文可以理解为：
```text
检索增强生成
```

普通 LLM 流程：
```text
用户问题 -> 模型直接回答
```

RAG 流程：
```text
用户问题
-> 检索相关资料
-> 把资料和问题一起交给模型
-> 模型基于资料回答
```

RAG 的核心作用：
```text
让模型先翻资料，再回答问题
```

---

## 78. chunk 是什么

chunk 是文档切分后的一个小片段。

长文档不能全部塞给模型，因为：
```text
上下文有限
token 成本高
无关内容会干扰回答
```

所以要把文档切成多个 chunk：
```text
长文档 -> chunk1, chunk2, chunk3...
```

chunk 的目标：
```text
短，但语义尽量完整
```

当前学习版先按段落切：
```python
for paragraph in text.split("\n\n"):
    chunk = paragraph.strip()
```

---

## 79. 关键词版 RAG

文件：
```text
keyword_rag.py
```

流程：
```text
读取 note/*.md
-> 按段落切 chunk
-> 根据关键词搜索 chunk
-> 拼 RAG prompt
-> 调用 LLM 回答
```

核心函数：
```python
load_markdown_files()
split_into_chunks()
build_chunks()
search_chunks()
build_rag_prompt()
```

关键词版 RAG 优点：
```text
简单
不用 embedding
不消耗 embedding token
```

缺点：
```text
主要依赖字面匹配
不太懂语义
中文拆词能力弱
```

---

## 80. RAG Prompt

当前 RAG prompt 写在：
```text
keyword_rag.py
```

函数：
```python
def build_rag_prompt(query: str, results: list[dict]) -> str:
```

它会把检索结果和用户问题拼成：
```text
Context:
检索到的资料

Question:
用户问题
```

并要求模型：
```text
只基于资料回答
资料不足就说明信息不足
合并重复信息，不要重复同一个观点
```

虽然 `vector_rag.py` 和 `hybrid_rag.py` 是向量/混合检索，但它们也复用了这个 prompt。

---

## 81. embedding 是什么

embedding 是把文本转换成向量：
```text
"BaseModel 是什么" -> [0.12, -0.45, 0.88, ...]
```

向量是一串数字。

有了向量以后，程序可以比较两段文本的语义相似度。

RAG 中 embedding 的用途：
```text
chunk -> embedding
用户问题 -> embedding
比较问题向量和 chunk 向量
找到最相关的 chunk
```

---

## 82. embedding_client.py

文件：
```text
embedding_client.py
```

作用：
```text
调用 embedding API，把文本转成向量
```

核心函数：
```python
def get_embedding(text: str) -> EmbeddingResult:
```

输入：
```text
hello
```

输出：
```text
1536 维向量
usage
elapsed_seconds
```

它和 `llm_client.py` 的区别：
```text
llm_client.py: 文本/消息 -> 模型回答
embedding_client.py: 文本 -> 向量
```

---

## 83. 聊天模型和 embedding 模型分开配置

当前 `config.py` 中已经拆分：
```text
聊天模型配置：
OPENAI_BASE_URL
OPENAI_API_KEY
OPENAI_MODEL

embedding 模型配置：
OPENAI_EMBEDDING_BASE_URL
OPENAI_EMBEDDING_API_KEY
OPENAI_EMBEDDING_MODEL
```

这样可以做到：
```text
聊天继续用原来的 OpenAI 兼容中转
embedding 单独用阿里云百炼
```

示例：
```powershell
$env:OPENAI_EMBEDDING_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:OPENAI_EMBEDDING_API_KEY="你的阿里云百炼 API Key"
$env:OPENAI_EMBEDDING_MODEL="text-embedding-v1"
```

---

## 84. 构建向量索引

文件：
```text
build_vector_index.py
```

作用：
```text
提前给所有 chunk 生成 embedding，并保存到 vector_index.json
```

流程：
```text
读取文档
-> 切 chunk
-> 对每个 chunk 调用 get_embedding()
-> 保存 source、chunk_id、text、embedding
```

生成文件：
```text
vector_index.json
```

测试时可以限制数量：
```powershell
python .\build_vector_index.py --limit 50
```

不加 `--limit` 会处理全部 chunk，会消耗更多 embedding token。

---

## 85. vector_index.json 不提交 Git

`vector_index.json` 是生成文件，不是源码。

原因：
```text
文件可能很大
里面是大量向量数字
会随着文档和模型变化重新生成
不适合人工阅读
```

所以加入 `.gitignore`：
```gitignore
vector_index.json
vector_index/
```

原则：
```text
代码进 Git
向量索引不进 Git
```

---

## 86. 向量版 RAG

文件：
```text
vector_rag.py
```

流程：
```text
读取 vector_index.json
-> 给用户问题生成 embedding
-> 和每个 chunk embedding 计算相似度
-> 取 top_k 个最相关 chunk
-> 拼 RAG prompt
-> 调用 LLM 回答
```

核心函数：
```python
load_vector_index()
cosine_similarity()
search_similar_chunks()
```

向量版 RAG 相比关键词版：
```text
关键词版：按字面匹配
向量版：按语义相似度匹配
```

---

## 87. 余弦相似度

余弦相似度用于判断两个向量是否相似。

代码大概是：
```python
dot_product / (vector_a_length * vector_b_length)
```

含义：
```text
两个向量方向越接近，语义越相似
```

在 RAG 中：
```text
用户问题向量
vs
chunk 向量
```

相似度越高，越可能被检索出来。

---

## 88. top_k

`top_k` 表示取相似度最高的前 k 个 chunk。

例如：
```python
top_k = 5
```

表示取最相关的 5 条资料。

影响：
```text
top_k 太小：可能漏掉重要信息
top_k 太大：可能引入重复或无关资料，token 更多
```

学习阶段常用：
```text
top_k = 3 或 5
```

---

## 89. Hybrid Search

Hybrid Search 是混合检索：
```text
关键词检索 + 向量检索
```

文件：
```text
hybrid_rag.py
```

流程：
```text
向量检索 top 5
-> 关键词检索 top 5
-> 用 (source, chunk_id) 去重
-> 合并结果
-> 拼 prompt
-> LLM 回答
```

核心函数：
```python
merge_results()
hybrid_search()
```

为什么要 Hybrid：
```text
关键词检索适合精确词：BaseModel、model_validate、HTTPException
向量检索适合语义问题：某个概念有什么作用
```

---

## 90. Rerank

Rerank 中文叫重排序。

常见流程：
```text
向量检索先召回 top 20
-> rerank 模型重新判断相关性
-> 选出最好的 top 3 到 top 5
-> 给 LLM 回答
```

理解：
```text
向量检索：粗筛
rerank：精排
```

优点：
```text
减少无关 chunk
减少重复资料
提高回答准确性
```

缺点：
```text
多一次模型调用
更慢
多一点成本
```

---

## 91. Metadata Filter

metadata 是 chunk 的附加信息。

例如：
```json
{
  "source": "note/agent_learning_path.md",
  "chunk_id": 19
}
```

`source` 和 `chunk_id` 就是 metadata。

Metadata Filter 是根据元数据过滤检索范围：
```text
只查某个文件
只查某个标签
只查某个时间范围
```

作用：
```text
缩小检索范围，让 RAG 更准
```

---

## 92. Query Rewrite

Query Rewrite 是查询改写。

作用：
```text
把用户口语化的问题改写成更适合检索的问题
```

例如：
```text
用户问题：BaseModel 那个东西是干嘛的？
改写后：Pydantic BaseModel 的作用是什么？
```

流程：
```text
用户原始问题
-> LLM 改写检索 query
-> 用改写后的 query 检索
-> 用检索结果回答原始问题
```

---

## 93. Multi-query Retrieval

Multi-query Retrieval 是多查询检索。

作用：
```text
把一个用户问题扩展成多个不同角度的检索问题
```

例如：
```text
RAG 怎么学？
```

可以扩展成：
```text
RAG 学习路线是什么？
检索增强生成的学习步骤是什么？
embedding 和向量检索怎么学习？
本地知识库 RAG Agent 项目怎么做？
```

好处：
```text
覆盖更全
不容易漏掉相关 chunk
```

缺点：
```text
检索次数更多
可能引入重复内容
```

---

## 94. Parent-Child Chunk

Parent-Child Chunk 的核心：
```text
小 chunk 检索
大 chunk 回答
```

原因：
```text
小 chunk 检索更准，但上下文少
大 chunk 上下文完整，但检索不够精准
```

做法：
```text
用 child chunk 做检索
找到相关 child 后
返回它对应的 parent chunk 给模型
```

---

## 95. Agentic RAG

普通 RAG：
```text
固定检索一次，然后回答
```

Agentic RAG：
```text
Agent 自己判断要不要检索、检索什么、检索几次、结果够不够
```

它更像：
```text
Tool Calling + RAG 检索工具
```

当前代码还不是 Agentic RAG。

当前代码：
```text
vector_rag.py: 固定做一次向量检索
hybrid_rag.py: 固定做一次混合检索
```

未来可以把 RAG 检索封装成工具：
```text
search_vector_index(query)
```

再接入 Agent 决策。

---

## 96. Graph RAG

Graph RAG 是基于知识图谱的 RAG。

普通 RAG 检索文本 chunk。

Graph RAG 更关注：
```text
实体
关系
结构
```

例如：
```text
小明 -> 负责 -> RAG 项目
RAG 项目 -> 使用 -> FastAPI
FastAPI 服务 -> 调用 -> 向量数据库
```

适合：
```text
人物关系
公司组织
项目依赖
知识体系
事件关系
代码模块关系
```

它比普通 RAG 复杂，需要实体抽取、关系抽取、图数据库和图查询。

---

## 97. RAG 工程常见问题

1. chunk 太大或太小

```text
太大：检索不精准，token 消耗高
太小：上下文不完整
```

2. 索引更新问题

文档变了，`vector_index.json` 不会自动更新。

需要重新运行：
```powershell
python .\build_vector_index.py
```

3. 重复 chunk 问题

解决方式：
```text
prompt 要求合并重复信息
检索结果去重
减少 top_k
后面加 rerank
```

4. 来源引用问题

真实 RAG 最好告诉用户答案来自哪里：
```text
note/agent_learning_path.md#19
```

5. 检索不到不等于没有答案

可能原因：
```text
query 不好
chunk 切分不好
embedding 模型不适合
top_k 太小
```

调试 RAG 时要先看：
```text
Retrieved chunks
```

---

## 98. 当前 RAG 文件分工

当前文件：
```text
keyword_rag.py          关键词版 RAG
embedding_client.py     调用 embedding API
build_vector_index.py   构建 vector_index.json
vector_rag.py           向量版 RAG 查询
hybrid_rag.py           混合检索 RAG
```

运行顺序：
```text
1. 先构建索引
python .\build_vector_index.py --limit 50

2. 向量 RAG 问答
python .\vector_rag.py

3. 混合检索 RAG 问答
python .\hybrid_rag.py
```

注意：
```text
build_vector_index.py 不要频繁跑，会消耗 embedding token
vector_rag.py / hybrid_rag.py 平时问答使用
```

---

## 99. RAG 工具化

昨天的 RAG 文件可以单独运行：
```powershell
python .\vector_rag.py
python .\hybrid_rag.py
```

这种形式是：
```text
独立 RAG 问答程序
```

今天开始把 RAG 变成 Agent 可以调用的工具：
```python
def search_knowledge_base(query: str) -> str:
    ...
```

工具化后的职责：
```text
只负责检索资料
返回相关 chunk
不直接生成最终回答
```

最终回答仍然由 Agent 统一生成。

---

## 100. search_knowledge_base

文件：
```text
hybrid_rag.py
```

新增函数：
```python
def format_search_results(results: list[dict]) -> str:
    ...

def search_knowledge_base(query: str) -> str:
    results = hybrid_search(query)
    return format_search_results(results)
```

`hybrid_search()` 返回的是 chunk 列表。

Agent 工具更适合返回字符串，所以要格式化成：
```text
[1] source: note/agent_learning_path.md, chunk_id: 19
chunk 内容...

[2] source: note/llm_api_notes.md, chunk_id: 83
chunk 内容...
```

一句话：
```text
search_knowledge_base 是给 Agent 调用的 RAG 检索工具
```

---

## 101. tool_decision.py 接入 RAG 工具

今天在 `tool_decision.py` 中新增了一个 action：
```python
"search_knowledge_base"
```

`ToolDecision` 从：
```python
Literal["final_answer", "search_docs", "calculator"]
```

变成：
```python
Literal[
    "final_answer",
    "search_docs",
    "search_knowledge_base",
    "calculator",
]
```

新增参数模型：
```python
class SearchKnowledgeBaseArguments(BaseModel):
    query: str
```

注册工具：
```python
"search_knowledge_base": Tool(
    function=search_knowledge_base,
    arguments_model=SearchKnowledgeBaseArguments,
)
```

这样模型可以输出：
```json
{
  "action": "search_knowledge_base",
  "arguments": {
    "query": "LLM 学习计划"
  }
}
```

---

## 102. 最小 RAG Agent

现在 `tool_decision.py` 已经是一个最小 RAG Agent。

流程：
```text
用户问题
-> 模型输出工具决策 JSON
-> Python 解析并校验
-> 如果 action 是 search_knowledge_base
-> 调用 RAG 工具检索知识库
-> 得到 tool_result
-> 再把用户问题和 tool_result 交给模型
-> 模型生成最终回答
```

它已经具备：
```text
Agent 决策
RAG 工具
最终回答生成
```

但它还是最小版，因为：
```text
只支持一次工具调用
不会判断检索结果够不够
不会自动换 query 再查
没有多步工具循环
```

---

## 103. traceback 是什么

traceback 是 Python 的错误调用栈。

当程序异常没有被捕获时，Python 会打印：
```text
Traceback (most recent call last):
  File ...
  File ...
```

它表示错误从哪个函数一路传出来。

今天遇到过：
```text
tool_decision.py
-> execute_tool_decision()
-> search_knowledge_base()
-> hybrid_search()
-> search_similar_chunks()
-> get_embedding()
-> urllib 请求阿里云 embedding API
-> HTTP 401
```

因为当时只捕获了 `ValueError`，没有捕获 `LLMAPIError`，所以异常一路冒泡，最终触发 traceback。

---

## 104. 分层异常处理

Agent 中错误可能发生在不同层：
```text
模型决策层
工具执行层
最终回答层
```

模型决策层：
```python
decision = parse_tool_decision(result.answer)
```

可能错误：
```text
模型没有输出合法 JSON
action 不符合 Literal
arguments 格式不对
```

捕获：
```python
except (json.JSONDecodeError, ValidationError, ValueError)
```

工具执行层：
```python
tool_result = execute_tool_decision(decision)
```

可能错误：
```text
工具参数错误
embedding API key 错
embedding 服务失败
vector_index.json 不存在
```

捕获：
```python
except (ValueError, ConfigError, LLMAPIError, LLMResponseError)
```

最终回答层：
```python
final_result = call_llm(final_messages)
```

可能错误：
```text
聊天模型 API 失败
模型响应格式不对
```

捕获：
```python
except (ConfigError, LLMAPIError, LLMResponseError)
```

分层处理的好处：
```text
更容易知道是哪个阶段失败
输出更友好
避免直接 traceback
```

---

## 105. 单步 Agent 和多步 Agent

当前 `tool_decision.py` 是单步 Agent：
```text
决策一次
-> 执行一次工具
-> 最终回答
```

多步 Agent 是：
```text
决策
-> 工具
-> 观察结果
-> 再决策
-> 再工具
-> 直到 final_answer
```

多步 Agent 的核心是循环：
```python
for step in range(max_steps):
    decision = ask_model(...)
    if decision.action == "final_answer":
        return answer

    tool_result = execute_tool(...)
    scratchpad.append(...)
```

---

## 106. scratchpad

scratchpad 是 Agent 本次任务的临时工作记录。

它记录：
```text
原始用户任务
每一步模型决策
每一步工具参数
每一步工具返回结果
```

例如：
```text
Step 1:
Action: search_knowledge_base
Arguments: {"query": "当前学习进度"}
Observation:
检索到了 RAG 和 Agent 学习内容

Step 2:
Action: calculator
Arguments: {"expression": "4 / 2"}
Observation:
2
```

scratchpad 不是长期记忆。

它只在当前任务中存在，程序结束后就没了。

---

## 107. 多步 Agent 的停止条件

多步 Agent 必须有停止条件，否则可能无限循环。

常见停止条件：
```text
1. 模型输出 final_answer
2. 达到 max_steps
```

正常停止：
```json
{
  "action": "final_answer",
  "arguments": {
    "answer": "..."
  }
}
```

安全停止：
```python
max_steps = 5
```

如果 5 步后还没有最终答案，就返回：
```text
Agent stopped because max_steps was reached.
```

---

## 108. multi_step_agent.py

文件：
```text
multi_step_agent.py
```

作用：
```text
把 tool_decision.py 的单步 Agent 扩展成多步 Agent
```

核心函数：
```python
format_scratchpad()
build_agent_messages()
run_agent()
```

`format_scratchpad()`：
```text
把历史步骤列表拼成文本
```

`build_agent_messages()`：
```text
把用户任务、scratchpad、工具说明一起发给模型
```

`run_agent()`：
```text
负责多步循环
```

基本流程：
```text
初始化 scratchpad
-> 最多循环 max_steps 次
-> 每轮让模型输出 action
-> 如果 final_answer 就结束
-> 否则执行工具
-> 把 observation 写入 scratchpad
-> 进入下一轮
```

一句话：
```text
multi_step_agent.py 是在 tool_decision.py 外面套了一层循环和 scratchpad
```

---

## 109. Agent 为什么需要工程化控制

Agent 不是普通函数。

普通函数一般是：

```text
输入 -> 固定逻辑 -> 输出
```

Agent 更像是：

```text
输入 -> 模型判断下一步 -> 调用工具 -> 观察结果 -> 再判断 -> 最终回答
```

因为中间的决策由 LLM 参与，所以它可能出现：

```text
1. 重复调用同一个工具
2. 调错工具
3. 工具结果已经足够，但仍然继续搜索
4. 达到最大步数仍然没有 final_answer
```

所以工程化 Agent 不能只依赖 prompt，还需要用代码加边界。

常见控制方式：

```text
max_steps：限制最多执行几步
tool_calls：记录工具调用，防止重复
errors：记录失败原因
steps：记录执行轨迹
```

一句话：

```text
模型负责决策，代码负责兜底。
```

---

## 110. 防重复工具调用

今天给 `multi_step_agent.py` 加了一个简单的防重复机制。

核心思想：

```text
如果 action 和 arguments 都完全一样，就认为是重复工具调用。
```

例如允许：

```json
{"action": "search_knowledge_base", "arguments": {"query": "RAG"}}
{"action": "search_knowledge_base", "arguments": {"query": "Agentic RAG"}}
```

因为 query 不同。

但会拦住：

```json
{"action": "search_knowledge_base", "arguments": {"query": "RAG"}}
{"action": "search_knowledge_base", "arguments": {"query": "RAG"}}
```

代码中的记录结构：

```python
current_call = {
    "action": decision.action,
    "arguments": decision.arguments,
}
```

如果 `current_call` 已经在 `tool_calls` 里，就停止：

```python
if current_call in state.tool_calls:
    ...
```

注意：

```text
final_answer 不算工具调用，不参与重复检查。
```

---

## 111. Agent State

Agent State 表示 Agent 当前运行过程中的状态。

之前只有：

```python
scratchpad: list[str] = []
```

后来整理成：

```python
state = {
    "scratchpad": [],
    "tool_calls": [],
    "steps": [],
    "errors": [],
}
```

它们的作用：

```text
scratchpad：给模型看的历史记录
tool_calls：给程序判断重复工具调用
steps：记录每一步执行轨迹
errors：记录错误和停止原因
```

重点区别：

```text
scratchpad 是给 LLM 看的文本历史
state 是给程序看的结构化状态
```

---

## 112. Pydantic 版 AgentResult

为了让 Agent 返回结果更规范，今天把普通 dict 升级成了 Pydantic 模型。

主要结构：

```python
class AgentStep(BaseModel):
    step: int
    action: str
    arguments: dict[str, Any]
    observation: str


class AgentError(BaseModel):
    step: int
    error: str
    action: str | None = None
    arguments: dict[str, Any] | None = None


class AgentState(BaseModel):
    scratchpad: list[str] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    steps: list[AgentStep] = Field(default_factory=list)
    errors: list[AgentError] = Field(default_factory=list)


class AgentResult(BaseModel):
    answer: str
    state: AgentState
```

含义：

```text
AgentStep：记录一步执行
AgentError：记录一个错误
AgentState：记录整个运行过程
AgentResult：记录最终答案 + 完整状态
```

为什么用 `Field(default_factory=list)`：

```text
表示每次创建对象时，都生成一个新的空列表。
```

这样比直接写 `=[]` 更安全，也更符合 Pydantic 的推荐写法。

---

## 113. run_agent 的返回值

之前：

```python
def run_agent(...) -> str:
```

只返回最终答案字符串。

现在：

```python
def run_agent(...) -> AgentResult:
```

返回结构化结果。

这样可以同时拿到：

```python
result.answer
result.state.steps
result.state.errors
result.state.tool_calls
result.state.scratchpad
```

这一步的意义：

```text
run_agent 不再只是命令行 demo，而是可以被 FastAPI、日志系统、测试代码复用的工程函数。
```

---

## 114. FastAPI 接入 Agent

今天在 `api_server.py` 中新增了：

```text
POST /agent/chat
```

请求模型：

```python
class AgentChatRequest(BaseModel):
    message: str
    max_steps: int = 5
```

调用流程：

```text
用户请求 /agent/chat
-> FastAPI 校验 message 和 max_steps
-> 调用 run_agent()
-> 得到 AgentResult
-> 保存日志
-> 返回对外响应
```

测试请求示例：

```json
{
  "message": "根据我的学习笔记，说一下 RAG 是什么",
  "max_steps": 5
}
```

---

## 115. 内部状态和对外响应分离

`run_agent()` 内部返回完整的：

```python
AgentResult
```

里面有：

```text
answer
state.scratchpad
state.tool_calls
state.steps
state.errors
```

但是 `/agent/chat` 对外不直接暴露完整 state。

对外响应模型：

```python
class AgentPublicStep(BaseModel):
    step: int
    action: str
    arguments: dict


class AgentChatResponse(BaseModel):
    answer: str
    steps: list[AgentPublicStep]
    errors: list[AgentError]
```

为什么不把完整 state 都返回给用户：

```text
1. scratchpad 可能很长
2. observation 可能很长
3. 内部执行细节不一定适合暴露
4. 对外接口应该稳定、简洁
```

一句话：

```text
内部数据结构不等于对外 API 结构。
```

---

## 116. Agent 日志 jsonl

为了方便排查 Agent 的运行过程，今天新增了日志保存。

日志文件：

```text
logs/agent_runs.jsonl
```

`.jsonl` 的意思是：

```text
JSON Lines
一行就是一个完整 JSON
```

它适合日志，因为可以不断追加：

```json
{"created_at":"...","user_message":"...","result":{...}}
{"created_at":"...","user_message":"...","result":{...}}
```

保存函数：

```python
def save_agent_run(user_message: str, result) -> None:
```

记录内容：

```text
created_at：运行时间
user_message：用户输入
result：完整 AgentResult
```

查看日志：

```powershell
Get-Content .\logs\agent_runs.jsonl -Tail 5
```

---

## 117. view_agent_logs.py

今天新增了：

```text
view_agent_logs.py
```

作用：

```text
读取 logs/agent_runs.jsonl
打印每次 Agent 运行摘要
```

运行：

```powershell
python .\view_agent_logs.py
```

输出类似：

```text
Run #1
created_at: ...
user_message: ...
answer: ...
steps: 2
errors: 0
```

如果有错误，会打印：

```text
error_details:
- step=2 error=repeated tool call
```

这个脚本属于工程里的辅助排查工具。

---

## 118. 今天 Agent 工程化小结

今天的核心不是让 Agent 更聪明，而是让 Agent 更可控、更可观察。

目前链路：

```text
用户请求
-> FastAPI /agent/chat
-> run_agent()
-> LLM 决策
-> 工具调用
-> AgentResult
-> 保存完整 jsonl 日志
-> 返回简化 API 响应
```

今天形成的工程能力：

```text
1. 有状态：AgentState
2. 有结构：AgentResult
3. 有边界：max_steps + 防重复调用
4. 有接口：/agent/chat
5. 有日志：agent_runs.jsonl
6. 有查看工具：view_agent_logs.py
```

一句话总结：

```text
Agent 工程化的第一步，是把每一步做了什么记录清楚，并用代码限制它不要乱跑。
```

---

## 119. 接口工程化：run_id

今天开始做 Agent 的接口工程化。

第一步是给每次 Agent 运行增加：

```text
run_id
```

`run_id` 的作用：

```text
给每一次 Agent 调用一个唯一编号。
```

为什么需要：

```text
1. /agent/chat 返回 run_id
2. 日志里保存 run_id
3. 后面可以根据 run_id 查询这次运行详情
4. 用户反馈某次回答有问题时，可以精确定位
```

生成方式：

```python
def generate_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = uuid4().hex[:8]
    return f"run_{timestamp}_{suffix}"
```

示例：

```text
run_20260710123456_ab12cd34
```

其中：

```text
20260710123456：时间
ab12cd34：随机短 ID
```

这样既方便人看，也能降低重复概率。

---

## 120. agent_run_store.py

为了避免 `api_server.py` 越来越乱，今天新增了：

```text
agent_run_store.py
```

它专门负责 Agent 运行记录的存储和读取。

目前包含：

```python
generate_run_id()
save_agent_run()
load_agent_runs()
find_agent_run()
```

职责划分：

```text
api_server.py：负责接口
agent_run_store.py：负责日志存储和查询
view_agent_logs.py：负责命令行查看日志
```

这样做的好处：

```text
1. api_server.py 更干净
2. 读写 jsonl 的逻辑只有一份
3. 后面从 jsonl 换成 SQLite 时，主要改 agent_run_store.py
4. 多个地方都可以复用日志读取函数
```

一句话：

```text
agent_run_store.py 是 Agent 运行记录的存储层。
```

---

## 121. save_agent_run

`save_agent_run()` 负责把一次 Agent 运行保存到 jsonl 文件。

函数大概结构：

```python
def save_agent_run(run_id: str, user_message: str, result: Any) -> None:
    ...
```

保存内容：

```text
run_id：本次运行 ID
created_at：创建时间
user_message：用户输入
result：完整 AgentResult
```

写入文件：

```text
logs/agent_runs.jsonl
```

每次保存是一行 JSON：

```json
{"run_id":"...","created_at":"...","user_message":"...","result":{...}}
```

`result.model_dump()` 的作用：

```text
把 Pydantic 模型转换成普通 dict，方便 json.dumps 保存。
```

---

## 122. load_agent_runs 和 find_agent_run

`load_agent_runs()` 负责读取所有 Agent 运行记录。

基本逻辑：

```text
1. 如果日志文件不存在，返回空列表
2. 逐行读取 agent_runs.jsonl
3. 每一行用 json.loads 转成 dict
4. 返回 records 列表
```

`find_agent_run(run_id)` 负责按 run_id 查找某一次运行。

基本逻辑：

```python
for record in load_agent_runs():
    if record.get("run_id") == run_id:
        return record

return None
```

如果找到，返回完整记录。

如果没找到，返回：

```python
None
```

这个函数后面用于：

```text
GET /agent/runs/{run_id}
```

---

## 123. GET /agent/runs

今天新增了历史运行摘要接口：

```http
GET /agent/runs
```

作用：

```text
查看最近的 Agent 运行记录摘要。
```

返回内容：

```python
class AgentRunSummary(BaseModel):
    run_id: str | None
    created_at: str | None
    user_message: str | None
    answer: str | None
    steps_count: int
    errors_count: int
```

示例返回：

```json
[
  {
    "run_id": "run_20260710123456_ab12cd34",
    "created_at": "2026-07-10T...",
    "user_message": "根据我的学习笔记说一下 RAG",
    "answer": "...",
    "steps_count": 2,
    "errors_count": 0
  }
]
```

注意：

```text
这个接口只返回摘要，不返回完整 scratchpad、tool_calls、observation。
```

因为列表接口应该轻量。

---

## 124. GET /agent/runs/{run_id}

今天新增了运行详情接口：

```http
GET /agent/runs/{run_id}
```

作用：

```text
根据 run_id 查看某一次 Agent 的完整运行记录。
```

核心逻辑：

```python
record = find_agent_run(run_id)
if record is None:
    raise HTTPException(status_code=404, detail="Agent run not found.")
return record
```

如果找到，返回完整记录：

```json
{
  "run_id": "...",
  "created_at": "...",
  "user_message": "...",
  "result": {
    "answer": "...",
    "state": {
      "scratchpad": [],
      "tool_calls": [],
      "steps": [],
      "errors": []
    }
  }
}
```

如果没找到，返回：

```json
{
  "detail": "Agent run not found."
}
```

状态码：

```text
404
```

---

## 125. view_agent_logs.py 复用存储模块

之前 `view_agent_logs.py` 自己读取 jsonl。

现在改成复用：

```python
from agent_run_store import load_agent_runs
```

这样：

```text
读取日志的逻辑只在 agent_run_store.py 里维护。
```

`view_agent_logs.py` 只负责展示：

```text
run_id
created_at
user_message
answer
steps 数量
errors 数量
```

这体现了一个工程习惯：

```text
同一份逻辑不要在多个文件里重复写。
```

---

## 126. 接口工程化阶段小结

这轮接口工程化完成后，目前后端接口有：

```text
GET  /health
POST /chat
POST /agent/chat
GET  /agent/runs
GET  /agent/runs/{run_id}
```

整体链路：

```text
用户调用 /agent/chat
-> 生成 run_id
-> run_agent() 执行多步 Agent
-> 保存完整运行记录到 agent_runs.jsonl
-> 返回 answer、steps、errors、run_id
```

历史查询链路：

```text
GET /agent/runs
-> 返回运行摘要列表

GET /agent/runs/{run_id}
-> 返回某次完整运行详情
```

目前形成的工程能力：

```text
1. 每次运行可追踪：run_id
2. 运行记录可持久化：jsonl
3. 历史记录可查询：/agent/runs
4. 单次详情可查看：/agent/runs/{run_id}
5. 存储逻辑独立：agent_run_store.py
```

一句话总结：

```text
接口工程化的核心，是让一次 Agent 调用不仅能返回答案，还能被记录、查询和追踪。
```
