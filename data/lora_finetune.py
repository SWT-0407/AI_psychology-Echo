"""
Qwen2.5 LoRA 微调脚本
运行条件：需要 CUDA GPU + 至少 8GB 显存
安装依赖: pip install peft bitsandbytes transformers accelerate

用法: python lora_finetune.py
"""
import json, os, sys
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    TrainingArguments, Trainer, DataCollatorForSeq2Seq
)
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
from datasets import Dataset
import torch

# ==========================================
# 配置
# ==========================================
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"  # 可换成 ChatGLM, Yi 等
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "distilled_dialogues.jsonl")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lora_output")

def load_data():
    """加载 JSONL 数据"""
    data = []
    with open(DATA_PATH, encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    print(f"加载 {len(data)} 条数据")
    return data

def format_for_qwen(messages):
    """转换为 Qwen 对话格式"""
    text = "<|im_start|>system\n你是一个温暖共情的心理咨询助手Echo。<|im_end|>\n"
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        text += f"<|im_start|>{role}\n{content}<|im_end|>\n"
    text += "<|im_start|>assistant\n"
    return text

def main():
    data = load_data()
    
    # 格式化
    texts = [format_for_qwen(d["messages"]) for d in data]
    
    dataset = Dataset.from_dict({"text": texts})
    
    # 加载模型和分词器
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    
    def tokenize_fn(examples):
        return tokenizer(examples["text"], truncation=True, max_length=1024, padding="max_length")
    
    dataset = dataset.map(tokenize_fn, batched=True)
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        load_in_4bit=True,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True
    )
    model = prepare_model_for_kbit_training(model)
    
    # LoRA 配置
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=8,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.1,
    )
    model = get_peft_model(model, lora_config)
    
    # 训练参数
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        warmup_steps=10,
        logging_steps=10,
        save_steps=50,
        fp16=True,
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=DataCollatorForSeq2Seq(tokenizer, padding=True),
    )
    
    trainer.train()
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"LoRA 模型已保存到 {OUTPUT_DIR}")

if __name__ == "__main__":
    print("需要 GPU 才能运行。安装依赖后取消注释运行。")
    print(f"pip install peft bitsandbytes transformers accelerate datasets")
    # main()
