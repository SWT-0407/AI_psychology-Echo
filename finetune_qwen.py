# -*- coding: utf-8 -*-
"""
LoRA 微调脚本：让模型内化心理学书籍思想
基于 Qwen2.5-7B，使用 QLoRA 4-bit 量化
"""
import os
import json
import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    BitsAndBytesConfig
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType
)
from trl import SFTTrainer

# ========== 配置 ==========
BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"  # 或 Qwen/Qwen2.5-3B-Instruct（需要更少显存）
DATA_PATH = "sft_data.jsonl"
OUTPUT_DIR = "./qwen_psychology_finetuned"
USE_4BIT = True  # 启用 4-bit 量化，8GB 显存也能跑 7B 模型
LORA_R = 16      # LoRA 秩
LORA_ALPHA = 32  # LoRA 缩放参数
MAX_LENGTH = 1024  # 最大输入长度
BATCH_SIZE = 1      # 批量大小
GRADIENT_ACCUM = 2  # 梯度累积
EPOCHS = 5          # 训练轮数
LEARNING_RATE = 2e-4

# ========== 1. 准备数据集 ==========
print("[1/5] 加载训练数据...")
def load_dataset(path):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line.strip()))
    print(f"  共 {len(data)} 条训练数据")
    
    # 转换为 Qwen 对话格式
    formatted = []
    for item in data:
        # Qwen2.5 的聊天模板格式
        messages = [
            {"role": "user", "content": item["instruction"]},
            {"role": "assistant", "content": item["output"]}
        ]
        formatted.append({"messages": messages})
    return formatted

dataset = load_dataset(DATA_PATH)

# ========== 2. 加载模型和分词器 ==========
print("[2/5] 加载基座模型...")
quant_config = None
if USE_4BIT:
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4"
    )

model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    quantization_config=quant_config,
    device_map="auto",
    trust_remote_code=True,
    torch_dtype=torch.float16
)
tokenizer = AutoTokenizer.from_pretrained(
    BASE_MODEL,
    trust_remote_code=True,
    padding_side="right"
)

# 设置 padding token（Qwen2.5 可能需要）
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# 为 kbit 训练准备模型
if USE_4BIT:
    model = prepare_model_for_kbit_training(model)

# ========== 3. 配置 LoRA ==========
print("[3/5] 配置 LoRA...")
lora_config = LoraConfig(
    r=LORA_R,
    lora_alpha=LORA_ALPHA,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()  # 显示可训练参数量

# ========== 4. 格式化函数 ==========
def format_chat_template(example):
    """将 messages 格式转为文本"""
    text = tokenizer.apply_chat_template(
        example["messages"],
        tokenize=False,
        add_generation_prompt=False
    )
    return {"text": text}

# 转换为 HuggingFace Dataset
hf_dataset = Dataset.from_list(dataset)
hf_dataset = hf_dataset.map(format_chat_template)

# 分割训练/验证集
split_dataset = hf_dataset.train_test_split(test_size=0.1, seed=42)
train_dataset = split_dataset["train"]
eval_dataset = split_dataset["test"]
print(f"  训练集: {len(train_dataset)} 条, 验证集: {len(eval_dataset)} 条")

# ========== 5. 配置训练参数并开始训练 ==========
print("[4/5] 配置训练参数...")
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRADIENT_ACCUM,
    num_train_epochs=EPOCHS,
    learning_rate=LEARNING_RATE,
    fp16=True,
    save_steps=20,
    logging_steps=5,
    evaluation_strategy="steps",
    eval_steps=20,
    save_total_limit=2,
    load_best_model_at_end=True,
    report_to="none",  # 禁用 wandb 等
    remove_unused_columns=False,
    optim="adamw_torch",
    lr_scheduler_type="cosine",
    warmup_ratio=0.1,
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
    max_seq_length=MAX_LENGTH,
    formatting_func=format_chat_template,
    dataset_text_field="text",  # 不使用 dataset_text_field，使用 formatting_func
)

# ========== 6. 开始训练 ==========
print("[5/5] 开始训练...")
print(f"  基座模型: {BASE_MODEL}")
print(f"  训练轮数: {EPOCHS}")
print(f"  批次大小: {BATCH_SIZE} (有效批次: {BATCH_SIZE * GRADIENT_ACCUM})")
print(f"  LoRA 秩: {LORA_R}")
print("=" * 50)

trainer.train()

# 保存最终模型
trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"\n训练完成！模型已保存至: {OUTPUT_DIR}")
print(f"\n使用方法：")
print(f"  from transformers import AutoModelForCausalLM, AutoTokenizer")
print(f"  from peft import PeftModel")
print(f"  model = AutoModelForCausalLM.from_pretrained('{BASE_MODEL}', device_map='auto')")
print(f"  model = PeftModel.from_pretrained(model, '{OUTPUT_DIR}')")
