# 智扫通机器人智能客服 / Smart Robot Customer Service Agent / スマートロボット カスタマーサービス エージェント

> 基于 **LangGraph ReAct Agent** + **RAG** + **动态提示词切换** 的扫地/扫拖一体机器人智能客服 Demo
>
> A demo of a sweeping/mopping robot customer-service agent built on **LangGraph ReAct Agent**, **RAG**, and **dynamic prompt switching**.
>
> **LangGraph ReAct Agent** + **RAG** + **動的プロンプト切替** をベースにした、お掃除ロボット向けスマートカスタマーサービスのデモ。

[中文](#中文) · [English](#english) · [日本語](#日本語)

---

## 中文

### 概述

本项目是一个**面向扫地机器人/扫拖一体机器人售后场景**的智能客服 Agent，演示了如何用 LangGraph 构建生产级 ReAct Agent，并配合 RAG、工具调用、中间件、持久化对话等能力解决真实业务问题。

### 核心特性

| 能力 | 实现 |
|---|---|
| ReAct 推理 | LangChain `create_agent`（基于 LangGraph） |
| 知识检索（RAG） | ChromaDB + DashScope Embedding（`text-embedding-v4`） |
| 大模型 | 通义千问 `qwen-max`（DashScope API） |
| 对话持久化 | LangGraph `SqliteSaver` Checkpointer |
| 多场景提示词 | `@dynamic_prompt` 中间件按上下文切换系统提示词 |
| 工具调用监控 | `@wrap_tool_call` 中间件统一日志/状态注入 |
| 前端 UI | Streamlit，支持多会话 `thread_id` 路由 |

### 架构图

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit UI (app.py)                 │
│              ┌─────────────────────────────┐            │
│              │   thread_id（多会话隔离）      │            │
│              └─────────────────────────────┘            │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              ReactAgent (agent/react_agent.py)          │
│   ┌──────────────────────────────────────────────────┐  │
│   │  middleware = [                                  │  │
│   │    monitor_tool          (@wrap_tool_call)       │  │
│   │    log_before_model      (@before_model)         │  │
│   │    report_prompt_switch  (@dynamic_prompt)       │  │
│   │  ]                                               │  │
│   │                                                  │  │
│   │  tools = [                                       │  │
│   │    rag_summarize, get_weather, get_user_id,      │  │
│   │    get_user_location, get_current_month,         │  │
│   │    fetch_external_data, fill_context_for_report, │  │
│   │  ]                                               │  │
│   │                                                  │  │
│   │  checkpointer = SqliteSaver(agent_history.db)    │  │
│   └──────────────────────────────────────────────────┘  │
└──────┬─────────────────────────┬────────────────────────┘
       │                         │
       ▼                         ▼
┌──────────────┐        ┌──────────────────────────┐
│  RAG Service │        │  External Data (CSV)     │
│  ┌────────┐  │        │  data/external/records.csv │
│  │ Chroma │  │        └──────────────────────────┘
│  └────────┘  │
│  data/*.txt  │
│  data/*.pdf  │
└──────────────┘
```

### 项目结构

```
agent_project/
├── app.py                      # Streamlit 入口
├── agent/
│   ├── react_agent.py          # ReAct Agent 封装
│   └── tools/
│       ├── agent_tools.py      # 7 个业务工具
│       └── middleware.py       # 3 个中间件
├── rag/
│   ├── vector_store.py         # Chroma 向量库 + 文档切分入库
│   └── rag_service.py          # 检索 + 生成链
├── model/
│   └── factory.py              # 大模型/Embedding 工厂
├── prompts/
│   ├── main_prompt.txt         # 默认系统提示词（客服人格）
│   ├── report_prompt.txt       # 报告生成场景提示词
│   └── rag_summarize.txt       # RAG 摘要提示词
├── config/
│   ├── rag.yml                 # 模型/API key 配置
│   ├── chroma.yml              # 向量库配置
│   ├── agent.yml               # Agent 配置
│   └── prompts.yml             # 提示词路径配置
├── data/                       # 知识库原始文档（.txt/.pdf）
│   └── external/records.csv    # 用户使用记录（用于报告生成）
├── utils/                      # 工具函数（配置/日志/文件/路径）
└── chroma_db/                  # 向量库持久化目录（运行后生成）
```

### 关键设计

#### 1. 动态提示词切换（双人格 Agent）

通过工具调用驱动 system prompt 在运行时切换：

```
用户问"生成报告"
  ↓
LLM 调 fill_context_for_report 工具
  ↓
monitor_tool 中间件检测到 → 在 runtime.context 写 report=True
  ↓
下一轮调模型时 report_prompt_switch 读取标记 → 切换到 report_prompt.txt
  ↓
LLM 以"报告写手"人格继续工作
```

**好处**：避免单一 prompt 过长导致模型注意力分散，把状态切换交给确定性代码而非模型自身判断。

#### 2. LangGraph Checkpointer（对话持久化）

使用 `SqliteSaver` 把每轮的完整 graph state 写入 `agent_history.db`，支持：

- 跨会话恢复（前端通过 `?thread=xxx` URL 参数切换会话）
- 中间状态回溯（`agent.get_state_history(config)`）
- 工具调用全过程留痕

相比传统 `RunnableWithMessageHistory`，能力是超集。

#### 3. RAG 增量入库

`vector_store.load_document()` 遍历 `data/` 目录，对每个文件计算 MD5 → 写入 `md5.text`，已处理过的文件自动跳过，支持持续追加知识。

### 快速开始

#### 1. 环境要求

- Python ≥ 3.10
- DashScope（阿里云百炼）API Key

#### 2. 安装依赖

```bash
pip install streamlit \
            langchain \
            langgraph \
            langchain-chroma \
            langchain-community \
            langchain-text-splitters \
            chromadb \
            dashscope \
            pypdf \
            pyyaml \
            requests
```

#### 3. 配置 API Key

编辑 `config/rag.yml`：

```yaml
chat_model_name: qwen-max
embedding_model: text-embedding-v4
api_key: sk-xxxxxxxxxxxxxxxxxxxxxxxx   # 替换为你的 DashScope API Key
```

#### 4. 构建知识库（首次运行）

```python
from rag.vector_store import VectorStoreService
VectorStoreService().load_document()
```

或者直接运行：

```bash
cd agent_project
python -c "from rag.vector_store import VectorStoreService; VectorStoreService().load_document()"
```

#### 5. 启动应用

```bash
cd agent_project
streamlit run app.py
```

浏览器打开 `http://localhost:8501`。

### 工具一览

| 工具 | 入参 | 用途 |
|---|---|---|
| `rag_summarize` | `query: str` | 从向量库检索扫地机相关知识 |
| `get_weather` | `city: str` | 获取城市天气（demo 写死） |
| `get_user_location` | 无 | 获取用户所在城市（demo 随机） |
| `get_user_id` | 无 | 获取当前登录用户 ID（demo 从白名单随机） |
| `get_current_month` | 无 | 获取当前月份 `YYYY-MM` |
| `fetch_external_data` | `user_id, month` | 查询用户某月使用记录 |
| `fill_context_for_report` | 无 | **报告场景开关**，触发 prompt 切换 |

### 示例问题

- "扫地机器人和扫拖一体机器人有什么区别？" → 走 RAG
- "今天上海适合用扫地机吗？" → 调 `get_weather` + RAG
- "**帮我生成本月使用报告**" → 触发报告流程：`get_user_id` → `get_current_month` → `fill_context_for_report` → `fetch_external_data` → 切换 prompt → 生成 Markdown 报告

### 常见问题

<details>
<summary><b>1. 启动报错 <code>InvalidApiKey</code> 或 <code>401 Unauthorized</code></b></summary>

`config/rag.yml` 里的 `api_key` 没填或写错。打开 [DashScope 控制台](https://dashscope.console.aliyun.com/) 拿到 `sk-` 开头的 Key 填进去。

</details>

<details>
<summary><b>2. 提问后模型一直转圈 / 没有任何回复</b></summary>

通常是网络或额度问题：

- DashScope API 可能需要在中国大陆网络环境下访问
- 检查账户是否开通 `qwen-max` 与 `text-embedding-v4` 的调用权限
- 查看 `logs/app_YYYYMMDD.log` 里有没有异常堆栈

</details>

<details>
<summary><b>3. RAG 回答 "无相关资料" / 检索结果为空</b></summary>

向量库还没构建。确认 `chroma_db/` 目录非空，没有的话执行：

```bash
python -c "from rag.vector_store import VectorStoreService; VectorStoreService().load_document()"
```

每次往 `data/` 加文档后都要重跑这条命令（已通过 MD5 去重，不会重复入库）。

</details>

<details>
<summary><b>4. 报告生成失败：<code>FileNotFoundError: 外部数据文件不存在</code></b></summary>

确认 `config/agent.yml` 里的 `external_data_path` 与 `data/external/` 下实际文件名一致（默认是 `records.csv`）。

</details>

<details>
<summary><b>5. 想清空对话历史 / 测试新会话</b></summary>

- 临时方案：点击侧边栏 "新建对话" 按钮，会生成新的 `thread_id`
- 彻底清空：停掉服务后删除 `agent_history.db` 系列文件（`.db / .db-shm / .db-wal`）

</details>

<details>
<summary><b>6. 想用别的模型（不是通义千问）</b></summary>

改 `model/factory.py`：把 `ChatTongyi` / `DashScopeEmbeddings` 换成 `ChatOpenAI` / `OpenAIEmbeddings` 等任意 LangChain 支持的模型，并相应调整 `config/rag.yml` 字段。

</details>

---

## English

### Overview

A production-grade **ReAct Agent** demo for sweeping/mopping robot after-sales support. Showcases how to build a real-world agent with **LangGraph**, **RAG**, **tool calling**, **middleware**, and **persistent conversations**.

### Key Features

| Capability | Implementation |
|---|---|
| ReAct reasoning | LangChain `create_agent` (LangGraph-based) |
| Knowledge retrieval (RAG) | ChromaDB + DashScope embeddings (`text-embedding-v4`) |
| LLM | Qwen-max via DashScope API |
| Conversation persistence | LangGraph `SqliteSaver` checkpointer |
| Multi-persona prompts | `@dynamic_prompt` middleware swaps system prompt at runtime |
| Tool-call observability | `@wrap_tool_call` middleware for unified logging / state injection |
| Frontend | Streamlit with multi-session `thread_id` routing |

### Project Structure

```
agent_project/
├── app.py                      # Streamlit entry point
├── agent/
│   ├── react_agent.py          # ReAct Agent wrapper
│   └── tools/
│       ├── agent_tools.py      # 7 business tools
│       └── middleware.py       # 3 middlewares
├── rag/
│   ├── vector_store.py         # Chroma vector store + doc ingestion
│   └── rag_service.py          # Retrieval + generation chain
├── model/factory.py            # LLM / Embedding factory
├── prompts/                    # System / report / RAG prompts
├── config/                     # YAML configs
├── data/                       # Knowledge base files (.txt/.pdf) + CSV
└── utils/                      # Helpers (config, logging, paths)
```

### Highlight: Dynamic Prompt Switching

The agent has two "personas" controlled by middleware, not by the model itself:

```
User: "Generate my monthly report"
  ↓
LLM calls fill_context_for_report tool
  ↓
monitor_tool middleware detects → writes report=True into runtime.context
  ↓
Next model invocation: report_prompt_switch reads the flag
  → returns report_prompt.txt as system prompt
  ↓
LLM continues as "report writer" persona
```

**Why?** Splitting prompts keeps each one focused and short, and uses deterministic code (not the model) to manage state transitions—much more reliable.

### Highlight: LangGraph Checkpointer (vs `RunnableWithMessageHistory`)

`SqliteSaver` stores the **full graph state** (messages + tool calls + custom state) per `thread_id`, enabling:

- Cross-session resumption (frontend uses `?thread=xxx` URL param)
- Time travel via `agent.get_state_history(config)`
- Full tool-call audit trail

Strictly more powerful than `RunnableWithMessageHistory`, which only stores `BaseMessage` lists and is now considered legacy.

### Quick Start

#### 1. Prerequisites

- Python ≥ 3.10
- DashScope (Alibaba Cloud Bailian) API key

#### 2. Install dependencies

```bash
pip install streamlit \
            langchain \
            langgraph \
            langchain-chroma \
            langchain-community \
            langchain-text-splitters \
            chromadb \
            dashscope \
            pypdf \
            pyyaml \
            requests
```

#### 3. Configure API key

Edit `config/rag.yml`:

```yaml
chat_model_name: qwen-max
embedding_model: text-embedding-v4
api_key: sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

#### 4. Ingest the knowledge base (first run only)

```bash
cd agent_project
python -c "from rag.vector_store import VectorStoreService; VectorStoreService().load_document()"
```

#### 5. Launch the app

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### Tools

| Tool | Args | Purpose |
|---|---|---|
| `rag_summarize` | `query: str` | Retrieve robot-related knowledge from the vector store |
| `get_weather` | `city: str` | Get city weather (mocked) |
| `get_user_location` | — | Get user's city (mocked, random) |
| `get_user_id` | — | Get current user ID (mocked, from whitelist) |
| `get_current_month` | — | Get current month as `YYYY-MM` |
| `fetch_external_data` | `user_id, month` | Look up a user's monthly usage records |
| `fill_context_for_report` | — | **Report-mode toggle**; triggers prompt switching |

### Example Queries

- *"What's the difference between a sweeper and a sweeper-mopper?"* → triggers RAG
- *"Is today good weather for using a vacuum in Shanghai?"* → calls `get_weather` + RAG
- *"Generate my monthly usage report"* → triggers full report pipeline: `get_user_id` → `get_current_month` → `fill_context_for_report` → `fetch_external_data` → prompt switch → Markdown report

### Troubleshooting

<details>
<summary><b>1. <code>InvalidApiKey</code> / <code>401 Unauthorized</code> on startup</b></summary>

Your `api_key` in `config/rag.yml` is missing or wrong. Grab one from the [DashScope console](https://dashscope.console.aliyun.com/) (starts with `sk-`).

</details>

<details>
<summary><b>2. The model hangs forever after a question</b></summary>

Usually a network or quota issue:

- DashScope APIs may require access from a Chinese mainland network
- Verify your account has access to `qwen-max` and `text-embedding-v4`
- Check `logs/app_YYYYMMDD.log` for stack traces

</details>

<details>
<summary><b>3. RAG returns "无相关资料" / empty retrieval</b></summary>

The vector store hasn't been built. Ensure `chroma_db/` is not empty, otherwise run:

```bash
python -c "from rag.vector_store import VectorStoreService; VectorStoreService().load_document()"
```

Re-run after adding docs to `data/` (deduped by MD5, safe to call repeatedly).

</details>

<details>
<summary><b>4. Report fails with <code>FileNotFoundError: 外部数据文件不存在</code></b></summary>

Make sure `external_data_path` in `config/agent.yml` matches an actual file under `data/external/` (default: `records.csv`).

</details>

<details>
<summary><b>5. How do I reset history / start a fresh session?</b></summary>

- Quick: click "新建对话" in the sidebar to mint a new `thread_id`
- Full reset: stop the app and delete `agent_history.db*` files (`.db / .db-shm / .db-wal`)

</details>

<details>
<summary><b>6. Can I use a different LLM (not Qwen)?</b></summary>

Edit `model/factory.py`: swap `ChatTongyi` / `DashScopeEmbeddings` for `ChatOpenAI` / `OpenAIEmbeddings` (or any LangChain-supported provider) and update `config/rag.yml` accordingly.

</details>

---

## 日本語

### 概要

本プロジェクトは、お掃除ロボット／水拭き一体型ロボットのアフターサービス向けに構築された **ReAct エージェント** のデモです。**LangGraph**、**RAG**、**ツール呼び出し**、**ミドルウェア**、**会話の永続化** といった本番運用レベルの機能を組み合わせ、実業務シナリオを再現しています。

### 主な機能

| 機能 | 実装 |
|---|---|
| ReAct 推論 | LangChain `create_agent`（LangGraph ベース） |
| 知識検索（RAG） | ChromaDB + DashScope Embedding（`text-embedding-v4`） |
| LLM | 通義千問 `qwen-max`（DashScope API） |
| 会話の永続化 | LangGraph `SqliteSaver` チェックポインタ |
| 動的プロンプト切替 | `@dynamic_prompt` ミドルウェアでシステムプロンプトを実行時に切り替え |
| ツール呼び出しの可観測性 | `@wrap_tool_call` ミドルウェアでログ／状態注入を一元化 |
| フロントエンド | Streamlit、`thread_id` によるマルチセッション対応 |

### プロジェクト構成

```
agent_project/
├── app.py                      # Streamlit エントリポイント
├── agent/
│   ├── react_agent.py          # ReAct Agent ラッパー
│   └── tools/
│       ├── agent_tools.py      # 業務ツール 7 種
│       └── middleware.py       # ミドルウェア 3 種
├── rag/
│   ├── vector_store.py         # Chroma ベクトルストア + ドキュメント取込
│   └── rag_service.py          # 検索 + 生成チェーン
├── model/factory.py            # LLM / Embedding ファクトリ
├── prompts/                    # システム／レポート／RAG 用プロンプト
├── config/                     # YAML 設定ファイル
├── data/                       # ナレッジベース（.txt/.pdf）+ CSV
└── utils/                      # ヘルパ（設定／ログ／パス）
```

### 注目ポイント：動的プロンプト切替

このエージェントには 2 つの「人格」があり、モデル自身ではなく **ミドルウェアが制御** しています。

```
ユーザー：「月次レポートを生成して」
  ↓
LLM が fill_context_for_report ツールを呼び出す
  ↓
monitor_tool ミドルウェアが検知 → runtime.context に report=True を書き込み
  ↓
次回のモデル呼び出し時、report_prompt_switch がフラグを読み取り
  → report_prompt.txt をシステムプロンプトとして返す
  ↓
LLM が「レポートライター」人格として続行
```

**なぜこの設計か**：プロンプトを場面ごとに分けることで各プロンプトを短く焦点を絞れ、状態遷移をモデルではなく決定論的なコードに委ねることで信頼性が大幅に向上します。

### 注目ポイント：LangGraph チェックポインタ（`RunnableWithMessageHistory` 比）

`SqliteSaver` は `thread_id` ごとに **グラフ状態の完全なスナップショット**（メッセージ・ツール呼び出し・カスタム状態）を保存し、以下を実現します。

- セッション復元（フロントエンドで `?thread=xxx` URL パラメータを指定）
- `agent.get_state_history(config)` による任意ステップへの遡及
- ツール呼び出しの完全な監査ログ

`RunnableWithMessageHistory` の上位互換であり、後者は現在レガシー扱いとなっています。

### クイックスタート

#### 1. 動作要件

- Python ≥ 3.10
- DashScope（阿里云百炼）の API キー

#### 2. 依存ライブラリのインストール

```bash
pip install streamlit \
            langchain \
            langgraph \
            langchain-chroma \
            langchain-community \
            langchain-text-splitters \
            chromadb \
            dashscope \
            pypdf \
            pyyaml \
            requests
```

#### 3. API キーの設定

`config/rag.yml` を編集します。

```yaml
chat_model_name: qwen-max
embedding_model: text-embedding-v4
api_key: sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

#### 4. ナレッジベースの構築（初回のみ）

```bash
cd agent_project
python -c "from rag.vector_store import VectorStoreService; VectorStoreService().load_document()"
```

#### 5. アプリ起動

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` を開きます。

### ツール一覧

| ツール | 引数 | 用途 |
|---|---|---|
| `rag_summarize` | `query: str` | ベクトルストアからロボット関連知識を検索 |
| `get_weather` | `city: str` | 都市の天気を取得（demo はモック） |
| `get_user_location` | なし | ユーザー都市を取得（demo はランダム） |
| `get_user_id` | なし | 現在のユーザー ID を取得（demo はホワイトリストからランダム） |
| `get_current_month` | なし | 現在の月を `YYYY-MM` 形式で取得 |
| `fetch_external_data` | `user_id, month` | ユーザーの月次使用記録を検索 |
| `fill_context_for_report` | なし | **レポートモード切替スイッチ**、プロンプト切替を発火 |

### サンプル質問

- 「お掃除ロボットと水拭き一体型ロボットの違いは？」 → RAG が動く
- 「今日の上海はロボット掃除機の使用に向いていますか？」 → `get_weather` + RAG
- 「**今月の使用レポートを生成して**」 → レポート全パイプライン：`get_user_id` → `get_current_month` → `fill_context_for_report` → `fetch_external_data` → プロンプト切替 → Markdown レポート出力

### トラブルシューティング

<details>
<summary><b>1. 起動時に <code>InvalidApiKey</code> または <code>401 Unauthorized</code> が出る</b></summary>

`config/rag.yml` の `api_key` が未設定または誤りです。[DashScope コンソール](https://dashscope.console.aliyun.com/) で `sk-` から始まるキーを取得して設定してください。

</details>

<details>
<summary><b>2. 質問してもモデルが応答しない／ロード中のままになる</b></summary>

ネットワークまたは利用枠の問題が多いです。

- DashScope API は中国本土ネットワークからのアクセスが必要な場合があります
- アカウントで `qwen-max` と `text-embedding-v4` の利用権限が有効か確認
- `logs/app_YYYYMMDD.log` にスタックトレースが出ていないか確認

</details>

<details>
<summary><b>3. RAG が「无相关资料」を返す／検索結果が空</b></summary>

ベクトルストアが未構築です。`chroma_db/` ディレクトリが空でないことを確認し、空なら以下を実行：

```bash
python -c "from rag.vector_store import VectorStoreService; VectorStoreService().load_document()"
```

`data/` にドキュメントを追加した後はこのコマンドを再実行してください（MD5 で重複排除済み、何度実行しても安全）。

</details>

<details>
<summary><b>4. レポート生成時に <code>FileNotFoundError: 外部数据文件不存在</code> が出る</b></summary>

`config/agent.yml` の `external_data_path` が `data/external/` 配下の実ファイル名（デフォルト `records.csv`）と一致しているか確認してください。

</details>

<details>
<summary><b>5. 履歴をリセットしたい／新しいセッションを試したい</b></summary>

- 簡易版：サイドバーの「新建对话」ボタンで新しい `thread_id` を発行
- 完全リセット：サービスを停止し `agent_history.db` 系列ファイル（`.db / .db-shm / .db-wal`）を削除

</details>

<details>
<summary><b>6. 通義千問以外のモデルを使いたい</b></summary>

`model/factory.py` を編集します。`ChatTongyi` / `DashScopeEmbeddings` を `ChatOpenAI` / `OpenAIEmbeddings` など LangChain がサポートする任意のプロバイダに差し替え、`config/rag.yml` のフィールドを合わせて調整してください。

</details>

---

## License

MIT (demo 项目仅供学习参考 / for educational purposes / 学習目的のみ)
