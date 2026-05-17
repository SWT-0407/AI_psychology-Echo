# AI 心理学 Echo - 部署指南

## 环境配置

1. 创建虚拟环境：
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置环境变量：
   ```bash
   copy .env.example .env
   # 编辑 .env 填入你的 DeepSeek API_KEY
   ```

## 首次运行

### 1. 构建知识库
```bash
python rebuild_all_books.py
```

### 2. 启动应用
```bash
streamlit run main.py
```

## 知识蒸馏（可选）

生成 248 条微调对话数据：
```bash
python data/distill_summary.py
```

生成的 `data/distilled_dialogues.jsonl` 可用于 DeepSeek 微调平台。
