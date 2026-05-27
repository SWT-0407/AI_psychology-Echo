# -*- coding: utf-8 -*-
"""
本地模型推理服务
在 LoRA 微调完成后，用此模块替换 ai_service.py 中的 DeepSeek API 调用
"""
import os
import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer
from peft import PeftModel

# 配置
BASE_MODEL = os.getenv("LOCAL_BASE_MODEL") or os.getenv("QWEN_BASE_MODEL") or "Qwen/Qwen2.5-7B-Instruct"
_DEFAULT_LORA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "qwen_psychology_finetuned")
LORA_PATH = os.getenv("LOCAL_LORA_PATH") or os.getenv("QWEN_LORA_PATH") or _DEFAULT_LORA_PATH
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# 全局单例
_model = None
_tokenizer = None


def _load_model():
    """加载微调后的模型（单例懒加载）"""
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer

    print(f"[本地模型] 加载基座模型: {BASE_MODEL}")
    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL,
        trust_remote_code=True,
        padding_side="right"
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 先用 4-bit 加载基座模型
    from transformers import BitsAndBytesConfig
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4"
    )

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=quant_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16
    )

    # 加载 LoRA 权重
    print(f"[本地模型] 加载 LoRA 权重: {LORA_PATH}")
    if os.path.exists(LORA_PATH):
        model = PeftModel.from_pretrained(base_model, LORA_PATH)
    else:
        print(f"[本地模型] 未找到微调权重，使用基座模型")
        model = base_model

    model.eval()
    _model = model
    _tokenizer = tokenizer
    return model, tokenizer


def chat(messages, max_new_tokens=1024, temperature=0.7):
    """
    与本地模型对话
    替代 ai_service.py 中的 chat_with_ai()

    Args:
        messages: list, 消息列表 [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        max_new_tokens: int, 最大生成 token 数
        temperature: float, 生成温度

    Returns:
        str: 模型回复文本
    """
    model, tokenizer = _load_model()

    # 将 system prompt 合并到 user 消息中（Qwen2.5 格式）
    formatted_messages = []
    system_content = None
    for msg in messages:
        if msg["role"] == "system":
            system_content = msg["content"]
        else:
            formatted_messages.append(msg)

    # 如果有 system prompt，添加到第一个 user 消息前
    if system_content and formatted_messages:
        formatted_messages[0]["content"] = f"{system_content}\n\n{formatted_messages[0]['content']}"

    # 应用聊天模板
    text = tokenizer.apply_chat_template(
        formatted_messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # 编码
    inputs = tokenizer(text, return_tensors="pt").to(DEVICE)

    # 生成
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id
        )

    # 解码（只取新生成的部分）
    input_length = inputs["input_ids"].shape[1]
    response = tokenizer.decode(
        outputs[0][input_length:],
        skip_special_tokens=True
    )

    return response.strip()


def test_inference():
    """测试推理效果"""
    test_cases = [
        "我最近总是莫名想哭，觉得自己很没用。",
        "什么是人生坐标？",
        "我总是害怕和别人发生冲突。"
    ]
    
    print("=" * 50)
    print("本地模型推理测试")
    print("=" * 50)
    
    for query in test_cases:
        messages = [
            {"role": "user", "content": query}
        ]
        print(f"\n[用户] {query}")
        response = chat(messages, max_new_tokens=512)
        print(f"[模型] {response}")
        print("-" * 30)


if __name__ == "__main__":
    test_inference()
