# 心聆 Echo

更新日期：2026-05-28

心聆 Echo 是一个面向大学生心理状态记录、陪伴与自我觉察的 Streamlit 应用。项目把日记式访谈、秘密树洞、角色陪伴、用户画像、多模态输入、主动关怀和安全边界放在同一套本地优先的数据结构里，适合课程项目、比赛演示和本地原型验证。

> 重要说明：Echo 不是医疗诊断系统，也不是应急救援系统。它只提供陪伴、记录、状态提示和资源建议；当出现明显高风险表达时，系统会在前台提示用户联系现实中的可信任人士或专业资源，不会后台报警、上报或替用户联系第三方。

## 当前入口

```powershell
streamlit run main.py
```

启动后进入登录页，可以选择登录/注册，也可以点击“跳过 → 本地使用”。本地模式下，数据保存在项目的 `data/` 目录中。

## 核心功能

### 首页与用户画像

- 首页提供三个主要空间入口：`踩下心情`、`秘密树洞`、`另一世界`。
- `用户画像中枢` 会汇总近期情绪、关注主题、画像标签、综合状态和互动记录。
- 用户可在画像页调整陪伴偏好，例如回复风格、回复长度、建议方式、主动关怀、多模态是否参与画像等。

### 踩下心情

- 以日记/访谈方式记录近期状态。
- 围绕六个维度生成轻量心理状态画像：情绪状态、焦虑与压力、生理状态、行为与动力、社交与支持、认知与意义。
- 支持心情日历、历史记录、继续追问和文字记录下载。
- 可生成雷达图和报告，用于自我觉察与比赛展示。

### 秘密树洞

- 日记本式输入界面，AI 在右页回应用户。
- 支持 DeepSeek API、本地 Qwen LoRA 微调模型和本地规则兜底。
- 支持语音输入、图片上传、千问视觉图片理解、摄像头表情识别。
- 每条 AI 回复可进行五星反馈，后续回复会参考最近评分来调整语气。

### 另一世界

- 微信风格陪伴聊天界面。
- 可创建自定义角色，设置身份、年龄、性格、说话方式和关系资料。
- 保存长期记忆、亲密度、关系阶段、情绪残留和未读状态。
- 支持语音、图片、表情、置顶、清未读、删除聊天和删除角色等交互。

### 主动关怀

- 首页可开启或关闭主动关怀。
- 踩下心情、秘密树洞和另一世界会根据近期上下文，在合适时机生成轻量关怀消息。
- 画像不足时，系统会提示先补充一点近况，避免空泛打扰。

### 安全边界

- `services/safety.py` 会识别明显自伤、轻生、伤害他人或强烈痛苦相关表达。
- 高风险时会触发更谨慎的回复和危机提示弹窗。
- 详细边界见 [SAFETY.md](./SAFETY.md)。

## 技术栈

- 前端与应用框架：Streamlit
- 语言模型：DeepSeek Chat API，本地 Qwen LoRA 微调模型，本地规则兜底
- 多模态：千问视觉、千问 ASR、千问 TTS、OpenCV 摄像头采集、SpeechRecognition、pyttsx3
- 数据与画像：本地 JSON 存储、Supabase 可选云端同步
- 可视化：Matplotlib 雷达图
- RAG/知识库：LangChain、Chroma、FAISS、sentence-transformers
- 微调：Qwen2.5、Transformers、PEFT、QLoRA

## 项目结构

```text
.
├── main.py                         # 当前 Streamlit 入口
├── requirements.txt                # 应用运行依赖
├── .env.example                    # 环境变量模板
├── SAFETY.md                       # 心理安全边界说明
├── setup_guide.md                  # 本地部署与演示补充说明
├── DEMO_SCRIPT.md                  # 3 分钟比赛演示脚本
├── ui/                             # Streamlit 页面与交互
│   ├── home_page.py                # 首页与入口
│   ├── diary_chat_page.py          # 踩下心情
│   ├── treehole_page.py            # 秘密树洞
│   ├── companion_page.py           # 另一世界
│   └── profile_page.py             # 用户画像
├── services/                       # 业务服务层
│   ├── app_storage.py              # 本地数据结构与会话保存
│   ├── ai_service.py               # DeepSeek / 千问 API 封装
│   ├── treehole_ai_service.py      # 树洞模型路由
│   ├── multimodal_service.py       # 语音、TTS、表情识别
│   ├── proactive_engine.py         # 主动关怀
│   ├── user_profile.py             # 用户画像
│   ├── safety.py                   # 高风险文本识别与安全回复
│   ├── storage_auth.py             # 登录/注册
│   └── storage_cloud.py            # Supabase 同步
├── data/                           # 数据准备、微调数据和本地运行数据
├── assets/                         # 页面背景与日记模板素材
├── tests/                          # 单元测试
├── reports/                        # 项目报告文档
├── inducing/                       # 旧版 RAG/知识库脚本
└── tools/                          # 报告与资料处理工具
```

## 快速开始

建议使用 Python 3.10 或更高版本。

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
streamlit run main.py
```

如果 `PyAudio` 在非 Windows 环境安装失败，可以先移除该依赖；应用仍可使用 Streamlit 上传录音能力，只有本机麦克风兜底输入会受影响。

## 环境变量

`.env.example` 已提供模板：

| 变量 | 用途 | 可否留空 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 语言对话与真实模型回复 | 可以，留空后使用本地规则兜底 |
| `QWEN_API_KEY` | 语音识别、图片理解、表情分析、TTS | 可以，但多模态能力会受限 |
| `ECHO_REPLY_PROVIDER` | 通用回复来源，支持 `auto`、`deepseek`、`local` | 可以，默认 `auto` |
| `TREEHOLE_REPLY_PROVIDER` | 树洞回复来源，支持 `auto`、`deepseek`、`local` | 可以，默认 `auto` |
| `LOCAL_LORA_PATH` | 本地 LoRA 微调模型目录 | 可以，默认 `./qwen_psychology_finetuned` |
| `SUPABASE_URL` | Supabase 项目地址 | 可以，留空则只用本地存储 |
| `SUPABASE_ANON_KEY` | Supabase 匿名密钥 | 可以，留空则只用本地存储 |
| `ECHO_CRISIS_RESOURCE_TEXT` | 高风险对话中的前台资源提示文案 | 可以，系统有默认值 |

## 模型回复策略

树洞和评测对话优先通过 `services/treehole_ai_service.py` 路由：

1. `auto`：优先检查可用的本地 LoRA 模型，否则尝试 DeepSeek。
2. `deepseek`：只使用 DeepSeek API。
3. `local`：只使用本地 Qwen LoRA 微调模型。
4. 如果真实模型不可用，页面会提示原因，并回退到本地规则回复。

本地 LoRA 目录需要包含 `adapter_config.json` 和 `adapter_model.safetensors`。如果 `LOCAL_LORA_PATH` 指向父目录，系统会自动选择最新的 `checkpoint-*`。

## 数据存储

本地数据主要写入：

- `data/history/`：踩下心情、树洞、角色聊天的完整历史记录。
- `data/treehole/messages.json`：秘密树洞当前消息。
- `data/companion/`：角色列表和角色聊天记录。
- `data/diary_ui/profile.json`：手帐基础资料。
- `data/diary_ui/moods.json`：心情日历。

云端同步是可选能力。配置 Supabase 后，应用会使用 `users` 和 `chat_history` 表；只有登录并授权后才会上传。关闭“上传完整聊天内容”时，云端只保存摘要、评分和分析结果。

## 测试

```powershell
python -m unittest discover tests
```

当前测试覆盖了安全识别、本地 AI 规则、心理评估、云/本地存储轻量逻辑、多模态情绪映射和部分角色聊天输入行为。

## 微调数据与本地模型

准备去重后的 SFT 数据：

```powershell
python data\prepare_finetune_data.py
```

输出目录：

- `data/finetune_ready/echo_sft_all.jsonl`
- `data/finetune_ready/echo_sft_train.jsonl`
- `data/finetune_ready/echo_sft_eval.jsonl`
- `data/finetune_ready/prepare_report.md`

进行 QLoRA 微调：

```powershell
python finetune_qwen.py
```

微调默认使用 `Qwen/Qwen2.5-3B-Instruct`，输出到 `qwen_psychology_finetuned/`。该步骤需要 CUDA GPU，并需要额外安装 `transformers`、`datasets`、`peft`、`accelerate`、`bitsandbytes` 等训练依赖。

常用训练环境变量：

- `BASE_MODEL`：基础模型，默认 `Qwen/Qwen2.5-3B-Instruct`
- `SFT_TRAIN_PATH`：训练集路径
- `SFT_EVAL_PATH`：验证集路径
- `LORA_OUTPUT_DIR`：LoRA 输出目录
- `MAX_STEPS`、`EPOCHS`、`BATCH_SIZE`、`GRADIENT_ACCUM`、`LEARNING_RATE`：训练参数
- `RESUME_FROM_CHECKPOINT`：断点恢复路径

## RAG 与资料脚本

旧版知识库脚本位于 `inducing/`，需要时可重建：

```powershell
python inducing\rebuild_all_books.py
```

项目报告与文档处理脚本位于 `tools/`，生成的 Word 报告保存在 `reports/`。

## 演示建议

完整演示词见 [DEMO_SCRIPT.md](./DEMO_SCRIPT.md)。推荐流程：

1. 首页展示三个空间和用户画像中枢。
2. 进入“踩下心情”，输入近况，展示六维状态、雷达图和报告。
3. 进入“秘密树洞”，展示日记式回应、语音/图片/表情输入和五星反馈。
4. 进入“另一世界”，展示角色、长期记忆、亲密度和主动关怀。
5. 输入模拟高压语句，说明安全边界：只做前台建议，不后台上报，不替用户做强制处置。

## 常见问题

### 没有配置 API Key 还能演示吗？

可以。应用会使用本地规则兜底回复，核心页面、记录、画像、报告和安全边界仍可演示。语音、视觉和真实模型回复需要对应 API Key。

### 本地微调模型没有加载成功怎么办？

确认 `LOCAL_LORA_PATH` 指向包含 LoRA adapter 的目录，且目录中存在 `adapter_config.json` 和 `adapter_model.safetensors`。如果暂时不可用，可将 `TREEHOLE_REPLY_PROVIDER=deepseek` 或保持 `auto` 让系统尝试 DeepSeek / 本地规则兜底。

### Supabase 必须配置吗？

不是。默认可以完全本地运行。只有需要账号登录、跨设备同步或云端恢复历史时，才需要配置 `SUPABASE_URL` 和 `SUPABASE_ANON_KEY`。

### 这是心理诊断工具吗？

不是。Echo 的分数、标签、表情识别和报告都只能作为自我觉察辅助，不能替代心理咨询、医学诊断或紧急救援。

