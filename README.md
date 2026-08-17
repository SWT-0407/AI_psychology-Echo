<div align="center">

# 心聆 Echo

**面向日常自我觉察的 AI 心理陪伴与状态感知原型**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.57-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/core%20tests-13%20passed-2EA44F)](#测试)

日记与六维状态画像 · 匿名树洞 · 长程 AI 伴侣 · 多模态输入 · 本地/云端可选

</div>

> [!IMPORTANT]
> Echo 是学习与研究用途的心理陪伴原型，不是医疗器械，不提供临床诊断、治疗建议或紧急救援。评分来自规则和模型生成，尚未经过临床效度验证。遇到现实危险或持续心理困扰时，请优先联系当地紧急服务、学校心理中心、专业机构或身边可信任的人。完整边界见 [SAFETY.md](SAFETY.md)。

## 项目概览

Echo 使用 Streamlit 将日记记录、对话、多模态输入、状态评估、长程记忆和可选云同步组织为三个相互独立的心理空间。项目默认支持本地 JSON 存储和规则式回复；配置模型或云服务后，可启用 DeepSeek、Qwen、LoRA 模型和 Supabase。

| 心理空间 | 用户任务 | 已实现能力 |
| --- | --- | --- |
| **踩下心情** | 记录日记并观察状态变化 | 六维评分、雷达图、综合状态、周/月趋势与报告 |
| **秘密树洞** | 低压力地表达情绪 | 文本/语音/表情输入、模型或本地回复、安全提示 |
| **另一个世界** | 与长期 AI 角色持续对话 | 角色创建、聊天记忆、亲密度与关系阶段、主动关怀 |

## 界面预览（v1版本，目前已调整为粉色背景，暂未更新图片）

| 心理日记 | 对话与状态追踪 | 六维画像与报告 |
| --- | --- | --- |
| ![心理日记输入界面](img.png) | ![对话与实时状态追踪](img_1.png) | ![六维状态画像与分析报告](img_2.png) |

截图展示的是项目原型界面与示例数据，不代表医学评估结果。

## 能力与运行模式

| 能力 | 零配置本地模式 | 可选增强 | 数据边界 |
| --- | --- | --- | --- |
| 日记、画像和本地历史 | 可用 | Supabase 同步 | 默认写入 `data/`；云同步需主动配置 |
| 树洞/伴侣回复 | 本地规则兜底 | DeepSeek API 或本地 Qwen + LoRA | 使用云端模型时，输入会发送给相应服务商 |
| 语音、TTS、表情 | 部分本地能力 | Qwen API、麦克风、摄像头 | 设备权限和外部 API 均为可选 |
| RAG 知识检索 | 需本地构建索引 | ChromaDB、FAISS、BGE embeddings | 知识库和向量索引保存在本机 |
| 主动关怀 | 应用内规则调度 | 可调整频率与免打扰时段 | 不会在后台自动联系第三方或救援机构 |

模型回复提供者由 `ECHO_REPLY_PROVIDER` 或 `TREEHOLE_REPLY_PROVIDER` 控制：

- `auto`：检测到本地 LoRA checkpoint 时优先本地模型，否则尝试 DeepSeek，最后使用规则式兜底。
- `deepseek`：只请求 DeepSeek；密钥缺失或调用失败时显示错误/安全兜底。
- `local`：只使用本地 Qwen + LoRA；需要可用 checkpoint 和相应推理依赖。

## 系统结构

```mermaid
flowchart LR
    U["Streamlit UI"] --> D["日记与六维状态"]
    U --> T["树洞与 AI 伴侣"]
    U --> M["语音 / 表情 / TTS"]
    D --> S["本地 JSON 存储"]
    T --> P["回复路由"]
    P --> L["本地规则或 Qwen + LoRA"]
    P --> C["DeepSeek API"]
    T --> R["RAG 检索"]
    M --> Q["Qwen API / 本地设备"]
    S -. 用户主动启用 .-> DB["Supabase"]
    D --> G["安全规则与前台提示"]
    T --> G
```

主要模块：

```text
AI_psychology-Echo/
├── main.py                       # Streamlit 入口与页面路由
├── ui/                           # 首页、日记、树洞、伴侣和个人资料页面
├── services/
│   ├── psych_assessment.py       # 六维状态评估
│   ├── treehole_ai_service.py    # 本地/云端回复路由
│   ├── local_ai.py               # 本地规则和安全兜底
│   ├── local_model_service.py    # Qwen + LoRA 推理
│   ├── multimodal_service.py     # 语音、表情和 TTS
│   ├── rag_service.py            # RAG 检索
│   ├── proactive_engine.py       # 应用内主动关怀
│   ├── storage_local.py          # 本地 JSON 存储
│   ├── storage_cloud.py          # Supabase 同步
│   └── safety.py                 # 风险识别与安全提示
├── inducing/                     # 知识库索引构建
├── data/                         # 本地运行数据和微调数据工具
├── tests/                        # 核心逻辑、存储、多模态与页面测试
├── finetune_qwen.py              # LoRA 微调实验脚本
├── requirements.txt
├── setup_guide.md
└── SAFETY.md
```

## 快速开始

### 1. 环境准备

推荐 Python 3.10-3.12。完整依赖包含 PyTorch、OpenCV、向量检索和音频组件，首次安装时间较长；`PyAudio` 在部分 Windows 环境需要 Conda 或预编译 wheel。

```powershell
git clone https://github.com/SWT-0407/AI_psychology-Echo.git
Set-Location AI_psychology-Echo

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

macOS / Linux 激活命令：

```bash
source .venv/bin/activate
```

### 2. 配置

```powershell
Copy-Item .env.example .env
```

所有外部服务均为可选。零配置体验可以直接跳过登录，以本地模式进入。

```env
# 可选模型服务
DEEPSEEK_API_KEY=
QWEN_API_KEY=

# auto / deepseek / local
ECHO_REPLY_PROVIDER=auto
TREEHOLE_REPLY_PROVIDER=auto
LOCAL_LORA_PATH=./qwen_psychology_finetuned

# 可选云同步
SUPABASE_URL=
SUPABASE_ANON_KEY=
```

不要提交 `.env`、聊天记录、日记、摄像头/语音数据或任何真实用户隐私信息。

### 3. 启动

```powershell
streamlit run main.py
```

浏览器打开 Streamlit 提供的本地地址，登录页选择“跳过 / 本地使用”即可进入零配置模式。完整环境说明见 [setup_guide.md](setup_guide.md)。

## 六维状态画像

系统从日记和对话中维护六个观察维度：情绪状态、焦虑与压力、生理状态、行为与动力、社交与支持、认知与意义。它们用于个人趋势观察，不是标准化心理量表，也不能替代专业评估。

当前基础评分路径是“关键词/规则信号 -> 覆盖度与基线修正 -> 六维汇总 -> 可视化与生成式说明”。规则的优点是离线、透明和易调试；局限是对语境、反讽、个体差异和临床含义理解有限。任何研究或展示都应同时报告这些局限，而不是只展示单个总分。

## 数据与隐私

- 本地模式将会话和画像写入 `data/` 下的 JSON 文件；该目录中的运行数据不应提交。
- Supabase 仅在用户配置项目并选择云端流程后使用。请在自己的 Supabase 项目中配置访问控制，不要使用高权限 service key 作为前端密钥。
- DeepSeek/Qwen 模式会把相应输入发送给模型服务商。不要输入身份证号、医疗记录、联系方式等不必要的敏感信息。
- 摄像头和麦克风能力需要系统权限；不使用时保持关闭。
- 高风险提示仅在前台展示资源建议，不会自动报警、定位或联系任何人。

## 测试

运行完整测试套件：

```powershell
python -m pytest -q
```

只验证不依赖 Streamlit/OpenAI/Supabase 的核心安全、评估和本地回复逻辑：

```powershell
python -m pytest -q tests/test_safety.py tests/test_psych_assessment.py tests/test_local_ai.py
```

2026-08-09 在未安装项目可选依赖的裸 Python 3.14 环境中，核心子集为 `13 passed`；完整套件需要先安装 `requirements.txt`，否则会在导入 Streamlit/OpenAI/Supabase 时停止收集。这个结果说明核心纯 Python 逻辑可执行，不代表完整 UI、多模态或云服务已经在所有平台验证。

## RAG 与微调实验

重建本地知识索引：

```powershell
python inducing/rebuild_all_books.py
```

准备微调数据并启动 LoRA 实验：

```powershell
python data/prepare_finetune_data.py
python finetune_qwen.py
```

微调脚本和仓库内训练数据用于课程/研究实验。使用前应检查数据许可、敏感信息、标签质量、训练/测试泄漏，并记录基座模型、随机种子、硬件、指标和失败案例。

## 当前限制与研究方向

- 六维评分尚无临床验证，当前只能作为自我观察与交互原型。
- 多模态、云模型和 Supabase 流程依赖外部服务、网络和用户配置。
- 本地 LoRA 模型对硬件和模型文件有额外要求，仓库不附带大模型权重。
- RAG、生成回复和主动关怀需要更系统的离线评测，包括基线、消融、鲁棒性、偏差和成本。
- 后续研究优先级是建立匿名评测集、数据治理文档、错误分类、可复现 benchmark 和明确的个人贡献记录。

## 许可与责任

仓库当前没有独立的开源许可证文件。除非另有书面授权，代码与素材仅按仓库声明用于学习和研究，不应推定可用于商业产品、医疗场景或再分发第三方模型/素材。准备公开协作前，应分别确认代码、训练数据、字体、图片、模型权重和音频素材的许可。

---

<div align="center">

**心聆 Echo：让情绪被记录，让变化可回看。**

</div>
