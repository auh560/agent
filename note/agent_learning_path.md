# 后端转 Agent：3 个月学习计划

适合背景：

- 有 C++ / 后端基础
- 还没有系统学过 LLM、RAG、Agent
- 希望 3 个月内做出一个能展示、能写简历、能面试讲清楚的项目

核心策略：

```text
主线：LLM API -> FastAPI -> RAG -> Tool Calling -> Mini Agent -> 项目整合
目标：做出一个本地知识库 RAG Agent 系统
原则：先做应用闭环，再了解框架和底层工程
```

不要一开始就把 Transformer、LangChain、LangGraph、私有化部署、微调、量化、多模态全部塞进主线。它们都可以了解，但不适合作为第一个 Agent 项目的学习主线。

---

## 1. 总体学习路径

推荐顺序：

```text
Python 后端基础
-> LLM API 调用
-> Prompt 与结构化输出
-> FastAPI 服务封装
-> RAG
-> Tool Calling
-> Mini Agent
-> 项目整合
-> 简历和面试表达
```

最终项目：

```text
本地知识库 RAG Agent 系统
```

项目要能做到：

- 导入 txt / md 文档
- 文档切分
- 生成 embedding
- 向量检索
- 基于资料回答问题
- 输出来源引用
- 支持简单工具调用
- 记录请求日志和耗时
- 提供 FastAPI 接口
- 可选做一个简单 Web UI

---

## 2. 第 1 个月：LLM API + Python 后端

目标：

```text
能调用大模型 API，并把模型能力封装成一个后端服务
```

### 2.1 LLM API 基础

需要掌握：

- LLM 是什么
- token 是什么
- prompt 是什么
- system / user / assistant message
- context window 上下文窗口
- temperature / top_p / max_tokens
- streaming 输出
- JSON 结构化输出
- OpenAI-compatible API
- 模型 API 请求和响应格式

实践任务：

- 用 Python 调一次模型 API
- 修改 temperature 看回答差异
- 修改 max_tokens 看输出长度
- 写一个最简单的命令行聊天脚本

产出：

```text
local_chat.py
notes/llm_api_notes.md
```

### 2.2 Prompt 与结构化输出

需要掌握：

- system prompt 的作用
- few-shot 示例
- 让模型输出 JSON
- 如何限制回答范围
- 如何让模型在不知道时说明不知道
- 如何设计面向 RAG 的 prompt

实践任务：

- 写 3 个不同 system prompt 对比效果
- 让模型输出固定 JSON 字段
- 让模型根据给定资料回答，不允许编造

产出：

```text
prompt_examples.md
structured_output.py
```

### 2.3 FastAPI 后端基础

需要掌握：

- Python 虚拟环境
- requests / httpx
- FastAPI
- Pydantic
- JSON
- 路由
- 异常处理
- 日志
- 请求耗时统计

实践任务：

- 写 `/health` 接口
- 写 `/chat` 接口
- 封装模型 API 调用
- 返回模型回答和请求耗时

产出：

```text
app/main.py
app/llm_client.py
```

---

## 3. 第 2 个月：RAG

目标：

```text
实现一个可以查资料再回答的知识库问答系统
```

RAG 一句话理解：

```text
RAG = 先查资料，再让模型基于资料回答
```

### 3.1 RAG 基础概念

需要掌握：

- 文档读取
- chunk 文档切分
- embedding 向量
- 向量相似度
- cosine similarity
- top-k 检索
- 向量数据库
- 检索召回
- 来源引用
- 幻觉控制

RAG 基本流程：

```text
文档
-> 切分成 chunks
-> 生成 embedding
-> 存入向量库
-> 用户提问
-> 检索相关 chunks
-> 拼接 prompt
-> 模型生成回答
```

### 3.2 RAG 实践顺序

第一步：读取文档

```text
读取 txt / md 文件
```

第二步：切分文档

```text
长文档 -> 多个 chunk
```

第三步：生成向量

```text
chunk -> embedding
```

第四步：检索

```text
query -> top-k chunks
```

第五步：生成回答

```text
query + retrieved chunks -> LLM answer
```

实践任务：

- 从 `data/docs` 读取文档
- 实现简单 chunk 切分
- 生成 embedding
- 存入 Chroma 或 FAISS
- 根据用户问题检索 top-k 文档片段
- 调用模型生成答案
- 输出答案和来源

产出：

```text
app/rag.py
scripts/ingest_docs.py
scripts/test_rag.py
notes/rag_notes.md
```

---

## 4. 第 3 个月：Tool Calling + Mini Agent + 项目整合

目标：

```text
让系统不只是问答，而是能根据任务选择工具并执行
```

### 4.1 Tool Calling

Tool Calling 是 Agent 的核心。

模型本身不会真的查文件、算数、访问数据库，它需要调用外部工具。

例子：

```text
用户：帮我查一下项目目录里有什么文件
Agent：选择 list_files 工具
程序：执行 list_files()
工具：返回文件列表
模型：基于工具结果回答用户
```

先实现这些工具：

```text
search_docs(query)
calculator(expression)
list_files()
get_time()
```

实践任务：

- 定义工具输入和输出格式
- 实现 `search_docs`
- 实现 `calculator`
- 实现 `list_files`
- 实现 `get_time`
- 根据用户输入选择工具
- 把工具结果交给模型总结

产出：

```text
app/tools.py
```

### 4.2 Mini Agent

最小 Agent 流程：

```text
用户目标
-> 判断下一步
-> 调用工具
-> 观察工具结果
-> 生成最终回答
```

两个月内不用一开始就写复杂循环，可以先写简单版本：

```text
用户输入
-> 程序判断使用哪个工具
-> 执行工具
-> 把工具结果交给模型
-> 输出最终回答
```

实践任务：

- 维护一轮对话上下文
- 让 Agent 判断是否需要查文档
- 让 Agent 判断是否需要计算
- 工具失败时返回清楚的错误信息
- 记录工具调用链路

产出：

```text
app/agent.py
app/schemas.py
notes/agent_notes.md
```

### 4.3 项目整合

项目名称：

```text
本地知识库 RAG Agent 系统
```

核心功能：

- 模型问答
- 文档导入
- 文档切分
- 向量检索
- RAG 问答
- 引用来源
- 简单工具调用
- 请求日志
- 耗时统计
- 简单 Web UI 或 API 文档

推荐技术栈：

```text
Python
FastAPI
Chroma / FAISS
Markdown / txt 文档
HTML / Streamlit
```

---

## 5. 最终项目结构建议

```text
rag_agent_project/
  README.md
  requirements.txt
  app/
    main.py
    llm_client.py
    rag.py
    agent.py
    tools.py
    schemas.py
  data/
    docs/
    index/
  scripts/
    ingest_docs.py
    test_rag.py
  web/
    index.html
  notes/
    llm_api_notes.md
    prompt_examples.md
    rag_notes.md
    agent_notes.md
```

---

## 6. 简历表达

项目名称：

```text
本地知识库 RAG Agent 系统
```

项目描述：

```text
基于 FastAPI 实现知识库问答服务，封装模型 API 调用能力，支持文档导入、文本切分、向量检索和 RAG 问答。
实现轻量级 Agent 工具调用流程，支持文档检索、文件查询、计算和时间查询。
记录检索来源、工具调用链路和请求耗时，提升系统可观测性。
```

技术栈：

```text
Python / FastAPI / RAG / Agent / Chroma 或 FAISS / OpenAI-compatible API
```

---

## 7. 面试要能讲清楚的问题

你要能讲清楚：

- LLM API 是怎么调用的
- system / user / assistant message 有什么区别
- temperature 和 max_tokens 分别控制什么
- RAG 是什么
- 为什么要切分文档
- chunk 太大或太小有什么问题
- embedding 是什么
- 向量检索怎么做
- top-k 怎么选
- 检索不到资料怎么办
- 模型胡说怎么办
- Agent 和普通问答有什么区别
- Tool Calling 怎么设计
- 工具调用失败怎么办
- 项目有哪些可优化点

---

## 8. 暂时不要作为主线的内容

这些内容可以了解，但不要放进第一个项目主线：

```text
Transformer 细节
LangChain
LangGraph
CrewAI
AutoGen
私有化部署
微调
量化
vLLM
TensorRT-LLM
Kubernetes
CUDA
复杂多 Agent
多模态
```

更合适的处理方式：

- Transformer：先理解基本概念，后面补原理
- LangChain / LangGraph：先自己写 Mini Agent，再学框架
- 私有化部署 / 微调 / 量化：作为后续 AI Infra 方向扩展
- 多模态：等文本 Agent 项目跑通后再看

---

## 9. 每周安排

### 第 1-2 周：LLM API 和 Prompt

产出：

```text
local_chat.py
structured_output.py
notes/llm_api_notes.md
```

### 第 3-4 周：FastAPI 服务封装

产出：

```text
app/main.py
app/llm_client.py
```

### 第 5-6 周：RAG 检索链路

产出：

```text
scripts/ingest_docs.py
app/rag.py
```

### 第 7-8 周：RAG 问答和来源引用

产出：

```text
scripts/test_rag.py
RAG 问答接口
notes/rag_notes.md
```

### 第 9-10 周：Tool Calling 和 Mini Agent

产出：

```text
app/tools.py
app/agent.py
notes/agent_notes.md
```

### 第 11-12 周：项目整合和面试准备

产出：

```text
README.md
项目架构图
使用步骤
截图
性能测试记录
面试问答
```

