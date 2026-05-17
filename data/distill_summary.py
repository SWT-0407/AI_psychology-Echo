"""
知识蒸馏总入口：从 RAG 知识库生成微调数据
包含 3 种使用方式：
1. 查看生成的对话数据
2. 用对话数据微调本地模型（需 GPU）
3. 将对话数据注入 System Prompt 作为 Few-shot 示例（立即可用）
"""
import json, os, random

SRC = r"E:\Users\醨\PycharmProjects\PythonProject6"
DATA_DIR = os.path.join(SRC, "data")

# ==========================================
# 1. 加载对话数据
# ==========================================
def load_dialogues():
    path = os.path.join(DATA_DIR, "distilled_dialogues.json")
    if not os.path.exists(path):
        print(f"数据文件不存在: {path}")
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("dialogues", [])

dialogues = load_dialogues()
print(f"📚 共加载 {len(dialogues)} 条蒸馏对话数据\n")

# ==========================================
# 2. 构建 Few-shot 示例（用于注入 System Prompt）
# ==========================================
def get_few_shot_examples(n=5):
    """随机抽取 n 条对话作为 Few-shot 示例"""
    if not dialogues:
        return ""
    samples = random.sample(dialogues, min(n, len(dialogues)))
    parts = []
    for i, d in enumerate(samples):
        parts.append(f"【示例 {i+1}】\n用户：{d['user']}\nEcho：{d['echo']}")
    return "\n\n".join(parts)

examples = get_few_shot_examples(3)
print("=== Few-shot 示例（前3条）===")
print(examples)

# ==========================================
# 3. 统计信息
# ==========================================
print("\n=== 数据统计 ===")
print(f"总对话数: {len(dialogues)}")
avg_user_len = sum(len(d["user"]) for d in dialogues) / len(dialogues)
avg_echo_len = sum(len(d["echo"]) for d in dialogues) / len(dialogues)
print(f"平均用户输入长度: {avg_user_len:.0f} 字")
print(f"平均 Echo 回复长度: {avg_echo_len:.0f} 字")

# 话题分析
topics_count = {}
all_text = " ".join([d["user"] + d["echo"] for d in dialogues])
for t in ["焦虑","抑郁","失眠","社交","学习","情感","家庭","自信","拖延",
           "压力","孤独","意义","恐惧","愤怒","悲伤","快乐","成长","接纳"]:
    count = all_text.count(t)
    if count > 0:
        topics_count[t] = count

print(f"\n话题关键词出现频次（前10）:")
sorted_topics = sorted(topics_count.items(), key=lambda x: -x[1])
for t, c in sorted_topics[:10]:
    print(f"  {t}: {c} 次")

print(f"\n✅ 数据目录: {DATA_DIR}")
print(f"   - distilled_dialogues.json  (完整数据)")
print(f"   - distilled_dialogues.jsonl (微调格式)")
