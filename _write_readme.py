# 临时脚本，用于写入 README.md
content = """# 🌱 AI_psychology — 大学生心理状态全周期评估系统

> 面向大学生的心理健康辅助工具，通过日记 + 多轮对话进行六维心理状态评估，并生成深度解析报告。

---

## 📋 项目简介

本项目通过**日记撰写**与**AI 多轮对话**相结合的方式，从六个核心维度对用户的心理状态进行动态评估，最终生成综合评分与深度解析报告。

| 维度 | 说明 |
|:---:|:---:|
| x1 情绪状态 | 0（严重抑郁/负面）↔ 10（积极/平稳） |
| x2 焦虑与压力 | 0（极度焦虑/崩溃）↔ 10（放松/无压） |
| x3 生理状态 | 0（严重失眠/躯体化）↔ 10（睡眠饮食正常） |
| x4 行为与动力 | 0（摆烂/逃避/丧失动力）↔ 10（积极/有动力） |
| x5 社交与支持 | 0（严重孤立/缺乏支持）↔ 10（社交良好/有人倾诉） |
| x6 认知与意义 | 0（绝望/认知扭曲）↔ 10（充满希望/目标清晰） |

---

## 🏗️ 项目架构

```
AI_psychology/
├── main.py                  # 入口文件 — 路由分发
├── config.py                # 配置管理（API、维度、权重等）
├── .env                     # [需自行创建] 环境变量（API Key）
│
├── models/
│   └── eval_net.py          # ScientificEvalNet — 科学评估网络
│
├── services/
│   ├── ai_service.py        # DeepSeek API 调用与响应解析
│   ├── storage_local.py     # 本地文件存储（对话/评分历史）
│   └── storage_cloud.py     # [预留] Supabase 云端存储
│
├── ui/
│   ├── sidebar.py           # 侧边栏（状态监控、评分追踪、重置）
│   ├── diary_page.py        # 日记模式页面（首轮采集）
│   ├── chat_page.py         # 对话采集页面（多轮交互）
│   └── report_page.py       # 深度解析报告页面（雷达图 + 趋势 + AI 分析）
│
├── utils/
│   ├── session_manager.py   # Streamlit session_state 管理
│   ├── prompts.py           # AI System Prompt 管理
│   ├── visualization.py     # 雷达图可视化
│   └── status_assets.py     # 状态资源（Emoji、评级、颜色）
│
├── data/                    # 本地存储数据
│   ├── history/             # 对话历史记录
│   └── scores/              # 评分与趋势数据
│
├── diary_backup.py          # [旧版] 单文件版项目备份
├── modelrating.py           # [开发中] 模型训练代码
├── trainingW.py             # [开发中] 权重训练代码
└── input.py                 # [旧版] 测试代码
```

### 数据流向

```
用户日记/对话
     │
     ▼
DeepSeek API ──→ 解析 JSON 响应 ──→ 更新六维评分
     │                                      │
     │                                      ▼
     └── 自然语言回复 ──→ 继续多轮对话      │
                                           ▼
                               所有维度已评估？
                              ┌─────┬─────┐
                              │     │     │
                              ▼     ▼     ▼
                        ScientificEvalNet  继续对话
                        （固定专家权重）
                              │
                              ▼
                    生成报告页面
                  （雷达图 + 趋势图 + AI 分析）
```

---

## 🚀 运行方法

### 前置要求

- Python 3.9+
- 安装依赖：`pip install streamlit openai requests python-dotenv torch matplotlib pandas numpy`

### 步骤

```bash
# 1. 克隆仓库
git clone https://github.com/SWT-0407/AI_psychology-Echo.git
cd AI_psychology

# 2. 创建 .env 文件（同目录下）
# 文件内容：api_key="你的 DeepSeek API Key"

# 3. 运行
streamlit run main.py
```

> ⚠️ **注意**：本项目依赖 DeepSeek API，需在 `.env` 文件中配置 `api_key` 才能正常运行。API Key 可前往 [DeepSeek 开放平台](https://platform.deepseek.com/) 获取。

---

## 🧪 运行流程

| 阶段 | 页面 | 说明 |
|:---:|:---:|:---|
| **第一阶段** | 📓 日记模式 | 用户撰写今日心情随笔，触发 AI 初步六维评分 |
| **第二阶段** | 💬 对话采集 | AI 根据已评分维度，针对性提问尚未覆盖的维度，实现多轮动态微调 |
| **第三阶段** | 🧠 深度报告 | 雷达图 + 综合评分 + 历史趋势图 + AI 深度解析报告 |

---

## 📸 运行截图

![主界面](img.png)

![对话交互](img_1.png)

![深度报告](img_2.png)

---

## 🧠 模型训练（开发中）

- 已收集 **150+ 份心理问卷数据**，持续扩大中
- 数据经过人工筛选以保证质量
- 训练目标：从线性加权 → 非线性神经网络模型
- 相关代码：`modelrating.py`、`trainingW.py`

---

## 🔮 未来优化方向

1. **云端部署与持久化存储** — 支持多日历史记录查询与跨日趋势折线图
2. **非线性模型训练** — 利用问卷数据集训练更精准的评分模型
3. **Prompt 工程与微调** — 加入心理专业知识，提升对话专业性
4. **虚拟伴侣功能** — 用户可自定义 AI 角色（家人/朋友/伴侣等）
   > ⚖️ 严格遵守法规：服务对象限定为大学生及以上年龄群体
5. **AI 自适应个性化** — AI 通过多轮对话自动学习用户偏好，选择最合适的交流风格
6. **UI 界面优化** — 提升交互体验与视觉设计

---

## 📄 许可证

本项目仅供学习研究使用。
"""

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(content)

print('README.md 写入成功！')
