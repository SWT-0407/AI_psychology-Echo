"""
Prepare a deduplicated SFT dataset for Echo/Qwen LoRA fine-tuning.

Inputs are kept untouched. Outputs are written to data/finetune_ready/.
"""
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_DIR = DATA_DIR / "finetune_ready"

SOURCES = [
    ROOT / "data" / "distilled_dialogues.jsonl",
    ROOT / "sft_data.jsonl",
    ROOT / "training_dataset.json",
    ROOT / "training_data_full.json",
]

SOURCE_PRIORITY = {
    "distilled_dialogues.jsonl": 0,
    "sft_data.jsonl": 1,
    "training_data_full.json": 2,
    "training_dataset.json": 3,
}

SYSTEM_PROMPT = "你是心语 Echo，一个温暖、具体、不过度诊断的心理陪伴助手。"
RANDOM_SEED = 42
EVAL_RATIO = 0.08
MIN_USER_CHARS = 2
MIN_ASSISTANT_CHARS = 8


def normalize_text(text: Any) -> str:
    text = str(text or "")
    text = text.replace("\ufeff", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def dedupe_key(user: str, assistant: str) -> str:
    compact = re.sub(r"\s+", "", f"{user}\n---\n{assistant}")
    return hashlib.sha256(compact.encode("utf-8")).hexdigest()


def user_key(user: str) -> str:
    return re.sub(r"\s+", "", user)


def source_rank(record: Dict[str, Any]) -> int:
    source = str(record.get("meta", {}).get("source", "")).split(":", 1)[0]
    return SOURCE_PRIORITY.get(source, 99)


def make_record(user: Any, assistant: Any, source: str) -> Optional[Dict[str, Any]]:
    user_text = normalize_text(user)
    assistant_text = normalize_text(assistant)
    if len(user_text) < MIN_USER_CHARS or len(assistant_text) < MIN_ASSISTANT_CHARS:
        return None
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant_text},
        ],
        "meta": {"source": source},
    }


def load_jsonl(path: Path) -> Iterable[Tuple[Any, str]]:
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            yield json.loads(line), f"{path.name}:{line_no}"


def record_from_messages(item: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
    messages = item.get("messages")
    if not isinstance(messages, list):
        return None
    user_text = ""
    assistant_text = ""
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        content = msg.get("content")
        if role == "user" and not user_text:
            user_text = content
        elif role == "assistant" and not assistant_text:
            assistant_text = content
        if user_text and assistant_text:
            break
    return make_record(user_text, assistant_text, source)


def record_from_instruction(item: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
    instruction = normalize_text(item.get("instruction", ""))
    input_text = normalize_text(item.get("input", ""))
    user_text = instruction if not input_text else f"{instruction}\n\n{input_text}"
    return make_record(user_text, item.get("output", ""), source)


def load_source(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if not path.exists():
        return records

    if path.name == "distilled_dialogues.jsonl":
        for item, source in load_jsonl(path):
            record = record_from_messages(item, source) if isinstance(item, dict) else None
            if record:
                records.append(record)
        return records

    if path.name == "sft_data.jsonl":
        for item, source in load_jsonl(path):
            record = record_from_instruction(item, source) if isinstance(item, dict) else None
            if record:
                records.append(record)
        return records

    data = json.loads(path.read_text(encoding="utf-8"))

    if path.name == "training_dataset.json" and isinstance(data, list):
        for idx, item in enumerate(data, 1):
            if isinstance(item, dict):
                record = record_from_instruction(item, f"{path.name}:{idx}")
                if record:
                    records.append(record)
        return records

    if path.name == "training_data_full.json" and isinstance(data, dict):
        # Keep only supervised instruction/answer data. The pretrain raw chunks are
        # useful for RAG or continued pretraining, but not for chat SFT.
        for idx, item in enumerate(data.get("sft", []), 1):
            if isinstance(item, dict):
                record = record_from_instruction(item, f"{path.name}:sft:{idx}")
                if record:
                    records.append(record)
        return records

    return records


def strip_meta(record: Dict[str, Any]) -> Dict[str, Any]:
    return {"messages": record["messages"]}


def write_jsonl(path: Path, records: List[Dict[str, Any]], include_meta: bool = False) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for record in records:
            payload = record if include_meta else strip_meta(record)
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def build_report(stats: Dict[str, Any], train_count: int, eval_count: int) -> str:
    lines = [
        "# Echo SFT Data Preparation Report",
        "",
        "## Sources",
    ]
    for source, count in stats["source_counts"].items():
        lines.append(f"- {source}: {count} usable records")
    lines.extend([
        "",
        "## Deduplication",
        f"- Raw usable records: {stats['raw_count']}",
        f"- Unique records: {stats['unique_count']}",
        f"- Removed duplicates: {stats['duplicate_count']}",
        f"- Exact duplicate records removed: {stats['exact_duplicate_count']}",
        f"- Same-user duplicate records removed: {stats['same_user_duplicate_count']}",
        "",
        "## Output",
        f"- Train records: {train_count}",
        f"- Eval records: {eval_count}",
        f"- All records: {stats['unique_count']}",
        "",
        "## Files",
        "- data/finetune_ready/echo_sft_all.jsonl",
        "- data/finetune_ready/echo_sft_train.jsonl",
        "- data/finetune_ready/echo_sft_eval.jsonl",
        "- data/finetune_ready/echo_sft_all_with_meta.jsonl",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_records: List[Dict[str, Any]] = []
    source_counts: Dict[str, int] = {}
    for source in SOURCES:
        records = load_source(source)
        source_counts[source.name] = len(records)
        raw_records.extend(records)

    exact_unique: List[Dict[str, Any]] = []
    seen = set()
    exact_duplicates = 0
    for record in raw_records:
        user = record["messages"][1]["content"]
        assistant = record["messages"][2]["content"]
        key = dedupe_key(user, assistant)
        if key in seen:
            exact_duplicates += 1
            continue
        seen.add(key)
        exact_unique.append(record)

    by_user: Dict[str, Dict[str, Any]] = {}
    same_user_duplicates = 0
    for record in exact_unique:
        key = user_key(record["messages"][1]["content"])
        existing = by_user.get(key)
        if existing is None:
            by_user[key] = record
            continue
        same_user_duplicates += 1
        if source_rank(record) < source_rank(existing):
            by_user[key] = record

    unique = list(by_user.values())

    random.Random(RANDOM_SEED).shuffle(unique)
    eval_count = max(1, round(len(unique) * EVAL_RATIO)) if unique else 0
    eval_records = unique[:eval_count]
    train_records = unique[eval_count:]
    all_records = sorted(unique, key=lambda item: item["meta"]["source"])

    write_jsonl(OUT_DIR / "echo_sft_all.jsonl", all_records)
    write_jsonl(OUT_DIR / "echo_sft_train.jsonl", train_records)
    write_jsonl(OUT_DIR / "echo_sft_eval.jsonl", eval_records)
    write_jsonl(OUT_DIR / "echo_sft_all_with_meta.jsonl", all_records, include_meta=True)

    stats = {
        "source_counts": source_counts,
        "raw_count": len(raw_records),
        "unique_count": len(unique),
        "duplicate_count": exact_duplicates + same_user_duplicates,
        "exact_duplicate_count": exact_duplicates,
        "same_user_duplicate_count": same_user_duplicates,
    }
    (OUT_DIR / "prepare_report.md").write_text(
        build_report(stats, len(train_records), len(eval_records)),
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(stats | {"train_count": len(train_records), "eval_count": len(eval_records)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
