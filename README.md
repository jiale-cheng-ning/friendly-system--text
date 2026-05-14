# 全渠道电商客服工单智能处理 Agent

基于 Claude API 的多 Agent 协作系统，实现电商客服工单的**自动接收 → 智能分类 → 自动回复闭环 → 复杂问题转人工**全链路处理。

## 痛点解决

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 人均日处理工单 | < 80 单 | 300+ 单 |
| 客户平均等待时间 | 15 分钟 | < 2 分钟（自动回复） |
| 人工分类错误率 | 高 | LLM 分类准确率 > 90% |

## 架构

```
淘宝/JD/抖音 webhook
        │
        ▼
  [Reception Agent]  ── 标准化 + 去重 + 信息补全
        │
        ▼
  [Classifier Agent] ── 12大类 → 36小类 + 紧急度
        │
        ├── 自动回复类(C01-C06) ──→ [Auto Reply Agent]
        │                                    │
        │                              ┌── 闭环 → 工单关闭
        │                              └── 未解决 ──┐
        │                                           │
        ├── 半自动类(C07,C09,C10) ──→ [Auto Reply]  │
        │    │                       或 [转人工]     │
        │    └──────────────────────────────────────┤
        │                                           ▼
        └── 转人工类(C08,C11,C12) ──→ [Handoff Agent]
                                              │
                                              ▼
                                        人工坐席工作台
```

## 快速开始

### 1. 环境准备

```bash
# Python 3.11+
python --version

# 克隆项目
git clone <repo-url>
cd ecommerce-ticket-agent

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入你的 ANTHROPIC_API_KEY
```

### 3. 启动服务

```bash
python main.py
```

访问:
- **API 文档**: http://localhost:8000/docs
- **管理看板**: http://localhost:8000/web

### 4. 运行测试

```bash
pytest tests/ -v
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/tickets` | 创建工单（渠道 webhook） |
| GET | `/api/tickets` | 工单列表（筛选/分页） |
| GET | `/api/tickets/{id}` | 工单详情 + 对话记录 |
| POST | `/api/tickets/{id}/classify` | 触发分类 |
| POST | `/api/tickets/{id}/reply` | 自动回复（CoT 推理） |
| POST | `/api/tickets/{id}/handoff` | 转人工（生成交接包） |
| GET | `/api/dashboard` | 仪表盘数据 |
| GET | `/api/knowledge/search?q=` | FAQ 知识库检索 |

## 12 大分类体系

| 编号 | 大类 | 路由 | 优先级 |
|------|------|------|--------|
| C01 | 物流查询 | auto | P2 |
| C02 | 退换货 | auto | P1 |
| C03 | 订单问题 | auto | P2 |
| C04 | 支付问题 | auto | P1 |
| C05 | 商品咨询 | auto | P3 |
| C06 | 促销活动 | auto | P3 |
| C07 | 账户问题 | semi | P2 |
| C08 | 投诉建议 | human | P1 |
| C09 | 发票问题 | semi | P2 |
| C10 | 售后维修 | semi | P1 |
| C11 | 敏感事件 | human | P0 |
| C12 | 其他 | human | P3 |

## 项目结构

```
ecommerce-ticket-agent/
├── agents/                # 4 个核心 Agent
│   ├── reception.py       # 工单接收（多渠道归一化）
│   ├── classifier.py      # 分类路由（意图识别）
│   ├── auto_reply.py      # 自动回复（CoT 长链推理）
│   └── handoff.py         # 转人工（上下文整理）
├── channels/              # 渠道适配器（淘宝/JD/抖音）
├── core/                  # LLM 封装、记忆、配置、数据库
├── models/                # ORM 数据模型
├── services/              # 工单服务、意图服务、知识库
├── api/                   # FastAPI 路由 + Pydantic schemas
├── prompts/               # Prompt 模板
├── data/                  # 分类体系 + FAQ 知识库
├── web/                   # 管理看板
├── tests/                 # 单元测试
├── main.py                # 启动入口
└── requirements.txt
```

## 扩展指南

### 添加新渠道

```python
# channels/pinduoduo.py
from channels.base import ChannelAdapter, ChannelMessage

class PinduoduoAdapter(ChannelAdapter):
    def normalize(self, raw_message: dict) -> ChannelMessage:
        return ChannelMessage(...)
```

然后在 `channels/__init__.py` 中注册即可。

### 添加新分类

编辑 `data/categories.json`，在 categories 数组中添加新类别。

### 添加 FAQ 知识

编辑 `data/faq_samples.json`，按格式添加问答对，服务会自动热加载。
