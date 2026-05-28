# Echo 本地部署与比赛演示指南

本项目当前入口是 `main.py`，包含三个空间：踩下心情、秘密树洞、另一世界。旧版 README 中的流程可能与当前代码不完全一致，比赛演示以本文件为准。

## 1. 环境准备

建议使用 Python 3.10+。

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

如果 `PyAudio` 在非 Windows 环境安装失败，可以先移除该依赖；应用仍可使用 Streamlit 的录音上传能力，只有本机麦克风兜底输入会受影响。

## 2. 配置环境变量

```powershell
copy .env.example .env
```

按需填写：

- `DEEPSEEK_API_KEY`：语言模型能力，可留空使用本地规则演示。
- `QWEN_API_KEY`：语音识别、视觉表情分析、TTS 等多模态能力。
- `TREEHOLE_REPLY_PROVIDER`：树洞回复来源，`auto` 会优先调用 DeepSeek；可设为 `local` 使用本地微调模型。
- `LOCAL_LORA_PATH`：本地 LoRA 微调模型目录，默认 `./qwen_psychology_finetuned`。
- `SUPABASE_URL` / `SUPABASE_ANON_KEY`：云端同步，可留空使用本地模式。
- `ECHO_CRISIS_RESOURCE_TEXT`：高风险对话中的前台建议文案；系统不会后台联系任何机构或个人。

## 3. 启动应用

```powershell
streamlit run main.py
```

进入登录页后，可以选择“跳过 → 本地使用”，这样所有数据只保存在本地 `data/` 目录。

## 4. 可选能力

### 云端同步

需要在 Supabase 创建 `users` 和 `chat_history` 表，并配置 `.env`。用户授权后才会上传；关闭“上传完整聊天内容”时，只保存摘要和评分。

### 多模态

- 语音输入：依赖 `QWEN_API_KEY` 或本机麦克风环境。
- 表情识别：依赖摄像头、OpenCV 和 `QWEN_API_KEY`。
- 表情信号只作为共情参考，不作为医学诊断依据。

### 知识库/RAG

如需使用旧版 RAG 脚本，可运行：

```powershell
python inducing\rebuild_all_books.py
```

## 5. 比赛演示建议

1. 首页展示三个空间：踩下心情、秘密树洞、另一世界。
2. 在踩下心情中输入一段日记，展示六维状态和报告。
3. 在秘密树洞中展示语音输入或表情识别。
4. 在另一世界中展示长期记忆、亲密度、关系阶段。
5. 用一条模拟高压语句展示安全边界：系统只给前台建议，不后台上报或强制联系心理中心。

## 6. 隐私与安全边界

详见 `SAFETY.md`。Echo 是心理陪伴和状态感知工具，不是医疗诊断或应急系统。
