"""
Model-backed reply service for the AI treehole page.

The treehole used to call services.local_ai.generate_reply directly, which is a
rule-based demo fallback. This module keeps that fallback separate from real
model calls so the UI can report which path produced a reply.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from Multimodal.config import DEEPSEEK_API_KEY
from services.message_format import normalize_messages


class TreeholeModelError(RuntimeError):
    """Raised when the configured treehole model provider cannot produce a reply."""


TREEHOLE_SYSTEM_PROMPT = """
你是“心语 Echo”的 AI 树洞，不是规则模板。
你的任务是像一个温柔、自然、具体的日记回应者一样接住用户的话。

要求：
1. 只回复给用户看的自然中文，不要输出 JSON、评分或系统说明。
2. 不要过度解读。用户只说“你好”时，就自然打招呼，邀请 TA 慢慢写，不要假装 TA 已经讲清楚一件事。
3. 用户说了具体经历时，先回应具体内容，再轻轻追问一个问题。
4. 语气真诚、短一些、像真实聊天，不要套话。
5. 如果多模态补充或历史评分反馈出现，只把它当作语气参考，不要直接暴露给用户。
""".strip()


def _provider() -> str:
    return os.getenv("TREEHOLE_REPLY_PROVIDER", "auto").strip().lower() or "auto"


def _default_lora_path() -> Path:
    return Path(__file__).resolve().parents[1] / "qwen_psychology_finetuned"


def _configured_lora_path() -> Path:
    raw = os.getenv("LOCAL_LORA_PATH") or os.getenv("QWEN_LORA_PATH") or ""
    if not raw.strip():
        return _default_lora_path()
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    return path


def has_local_finetuned_model() -> bool:
    path = _configured_lora_path()
    return path.exists() and path.is_dir()


def _messages_for_model(
    user_text: str,
    messages: List[Dict[str, Any]],
    scores: Dict[str, Any],
) -> List[Dict[str, str]]:
    recent = []
    for msg in normalize_messages(messages)[-10:]:
        role = msg.get("role")
        content = str(msg.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            recent.append({"role": role, "content": content})

    if recent and recent[-1]["role"] == "user":
        recent[-1]["content"] = user_text
    else:
        recent.append({"role": "user", "content": user_text})

    score_hint = ""
    if scores:
        score_hint = "\n\n当前轻量状态分数，仅供调整语气，不要直接告诉用户：" + str(scores)

    return [{"role": "system", "content": TREEHOLE_SYSTEM_PROMPT + score_hint}, *recent]


def _reply_with_deepseek(model_messages: List[Dict[str, str]]) -> str:
    if not DEEPSEEK_API_KEY:
        raise TreeholeModelError("DeepSeek API Key 未配置。")
    from services.ai_service import chat_with_ai

    reply = chat_with_ai(model_messages, temperature=0.78)
    reply = str(reply or "").strip()
    if not reply:
        raise TreeholeModelError("DeepSeek 返回为空。")
    return reply


def _reply_with_local_model(model_messages: List[Dict[str, str]]) -> str:
    lora_path = _configured_lora_path()
    if not lora_path.exists():
        raise TreeholeModelError(f"本地微调模型目录不存在：{lora_path}")

    os.environ["LOCAL_LORA_PATH"] = str(lora_path)
    try:
        from services.local_model_service import chat
    except Exception as exc:
        raise TreeholeModelError(f"本地模型依赖加载失败：{exc}") from exc

    reply = chat(model_messages, max_new_tokens=512, temperature=0.75)
    reply = str(reply or "").strip()
    if not reply:
        raise TreeholeModelError("本地微调模型返回为空。")
    return reply


def generate_treehole_model_reply(
    user_text: str,
    messages: List[Dict[str, Any]],
    scores: Dict[str, Any],
) -> Tuple[str, str]:
    """
    Generate a treehole reply with a real model.

    Returns:
        (reply_text, source), where source is "deepseek" or "local_finetuned".
    """
    provider = _provider()
    model_messages = _messages_for_model(user_text, messages, scores)
    errors: List[str] = []

    if provider in {"auto", "deepseek"}:
        try:
            return _reply_with_deepseek(model_messages), "deepseek"
        except Exception as exc:
            errors.append(f"DeepSeek 调用失败：{exc}")
            if provider == "deepseek":
                raise TreeholeModelError("; ".join(errors)) from exc

    if provider in {"auto", "local", "local_finetuned", "qwen", "qwen_lora"}:
        try:
            return _reply_with_local_model(model_messages), "local_finetuned"
        except Exception as exc:
            errors.append(f"本地微调模型调用失败：{exc}")
            if provider != "auto":
                raise TreeholeModelError("; ".join(errors)) from exc

    raise TreeholeModelError("; ".join(errors) or f"未知树洞回复模型配置：{provider}")


def model_source_label(source: str) -> str:
    labels = {
        "deepseek": "DeepSeek API",
        "local_finetuned": "本地微调模型",
        "local_template": "本地规则兜底",
    }
    return labels.get(source, source or "未知来源")
