# -*- coding: utf-8 -*-
"""
QLoRA fine-tuning entrypoint for Echo.

Default data:
  data/finetune_ready/echo_sft_train.jsonl
  data/finetune_ready/echo_sft_eval.jsonl

Default output:
  qwen_psychology_finetuned
"""
import json
import os
from pathlib import Path
from typing import Dict, List

import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForSeq2Seq,
    Trainer,
    TrainingArguments,
)


ROOT = Path(__file__).resolve().parent

BASE_MODEL = os.getenv("BASE_MODEL", "Qwen/Qwen2.5-3B-Instruct")
TRAIN_PATH = Path(os.getenv("SFT_TRAIN_PATH", ROOT / "data" / "finetune_ready" / "echo_sft_train.jsonl"))
EVAL_PATH = Path(os.getenv("SFT_EVAL_PATH", ROOT / "data" / "finetune_ready" / "echo_sft_eval.jsonl"))
OUTPUT_DIR = Path(os.getenv("LORA_OUTPUT_DIR", ROOT / "qwen_psychology_finetuned"))

MAX_LENGTH = int(os.getenv("MAX_LENGTH", "768"))
EPOCHS = float(os.getenv("EPOCHS", "3"))
MAX_STEPS = int(os.getenv("MAX_STEPS", "-1"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1"))
GRADIENT_ACCUM = int(os.getenv("GRADIENT_ACCUM", "8"))
LEARNING_RATE = float(os.getenv("LEARNING_RATE", "2e-4"))
EVAL_STEPS = int(os.getenv("EVAL_STEPS", "50"))
LORA_R = int(os.getenv("LORA_R", "16"))
LORA_ALPHA = int(os.getenv("LORA_ALPHA", "32"))
LORA_DROPOUT = float(os.getenv("LORA_DROPOUT", "0.05"))
SAVE_STRATEGY = os.getenv("SAVE_STRATEGY", "steps")
SAVE_STEPS = int(os.getenv("SAVE_STEPS", "50"))
SAVE_TOTAL_LIMIT = int(os.getenv("SAVE_TOTAL_LIMIT", "2"))
RESUME_FROM_CHECKPOINT = os.getenv("RESUME_FROM_CHECKPOINT") or None


def load_jsonl(path: Path) -> List[Dict]:
    rows: List[Dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def normalize_messages(item: Dict) -> List[Dict[str, str]]:
    if "messages" in item:
        return [
            {"role": str(msg["role"]), "content": str(msg["content"])}
            for msg in item["messages"]
            if msg.get("role") in {"system", "user", "assistant"} and msg.get("content")
        ]

    instruction = str(item.get("instruction", "")).strip()
    input_text = str(item.get("input", "")).strip()
    user_text = instruction if not input_text else f"{instruction}\n\n{input_text}"
    return [
        {"role": "system", "content": "你是心语 Echo，一个温暖、具体、不过度诊断的心理陪伴助手。"},
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": str(item.get("output", "")).strip()},
    ]


def build_tokenizer():
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    return tokenizer


def preprocess_dataset(rows: List[Dict], tokenizer) -> Dataset:
    def encode(item: Dict) -> Dict:
        messages = normalize_messages(item)
        assistant_index = next(
            (idx for idx in range(len(messages) - 1, -1, -1) if messages[idx]["role"] == "assistant"),
            len(messages) - 1,
        )
        prompt_messages = messages[:assistant_index]
        full_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        prompt_text = tokenizer.apply_chat_template(prompt_messages, tokenize=False, add_generation_prompt=True)

        full = tokenizer(full_text, truncation=True, max_length=MAX_LENGTH, add_special_tokens=False)
        prompt = tokenizer(prompt_text, truncation=True, max_length=MAX_LENGTH, add_special_tokens=False)

        input_ids = full["input_ids"]
        attention_mask = full["attention_mask"]
        labels = input_ids.copy()
        prompt_len = min(len(prompt["input_ids"]), len(labels))
        labels[:prompt_len] = [-100] * prompt_len
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
        }

    return Dataset.from_list(rows).map(encode, remove_columns=list(rows[0].keys()))


def build_model():
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA 不可用。请先安装 CUDA 版 PyTorch，或改用云端 GPU。")

    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=quant_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16,
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    return model


def main() -> None:
    print("=" * 60)
    print("Echo QLoRA fine-tuning")
    print(f"Base model: {BASE_MODEL}")
    print(f"Train data: {TRAIN_PATH}")
    print(f"Eval data:  {EVAL_PATH}")
    print(f"Output dir: {OUTPUT_DIR}")
    if RESUME_FROM_CHECKPOINT:
        print(f"Resume from: {RESUME_FROM_CHECKPOINT}")
    print(f"CUDA: {torch.cuda.is_available()} | {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none'}")
    print("=" * 60)

    train_rows = load_jsonl(TRAIN_PATH)
    eval_rows = load_jsonl(EVAL_PATH)
    print(f"Loaded train={len(train_rows)}, eval={len(eval_rows)}")

    tokenizer = build_tokenizer()
    train_dataset = preprocess_dataset(train_rows, tokenizer)
    eval_dataset = preprocess_dataset(eval_rows, tokenizer)
    model = build_model()

    args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=GRADIENT_ACCUM,
        num_train_epochs=EPOCHS,
        max_steps=MAX_STEPS,
        learning_rate=LEARNING_RATE,
        fp16=True,
        gradient_checkpointing=True,
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=EVAL_STEPS,
        save_strategy=SAVE_STRATEGY,
        save_steps=SAVE_STEPS,
        save_total_limit=SAVE_TOTAL_LIMIT,
        report_to="none",
        optim="paged_adamw_8bit",
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        remove_unused_columns=False,
        dataloader_num_workers=0,
    )

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        padding=True,
        pad_to_multiple_of=8,
        label_pad_token_id=-100,
        return_tensors="pt",
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
        data_collator=data_collator,
    )

    trainer.train(resume_from_checkpoint=RESUME_FROM_CHECKPOINT)
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    (OUTPUT_DIR / "echo_training_config.json").write_text(
        json.dumps(
            {
                "base_model": BASE_MODEL,
                "train_path": str(TRAIN_PATH),
                "eval_path": str(EVAL_PATH),
                "max_length": MAX_LENGTH,
                "epochs": EPOCHS,
                "batch_size": BATCH_SIZE,
                "gradient_accumulation": GRADIENT_ACCUM,
                "learning_rate": LEARNING_RATE,
                "eval_steps": EVAL_STEPS,
                "save_strategy": SAVE_STRATEGY,
                "save_steps": SAVE_STEPS,
                "save_total_limit": SAVE_TOTAL_LIMIT,
                "resumed_from_checkpoint": RESUME_FROM_CHECKPOINT,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"训练完成，LoRA 已保存至: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
