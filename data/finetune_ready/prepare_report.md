# Echo SFT Data Preparation Report

## Sources
- distilled_dialogues.jsonl: 1006 usable records
- sft_data.jsonl: 29 usable records
- training_dataset.json: 26 usable records
- training_data_full.json: 12 usable records

## Deduplication
- Raw usable records: 1073
- Unique records: 1068
- Removed duplicates: 5
- Exact duplicate records removed: 3
- Same-user duplicate records removed: 2

## Output
- Train records: 983
- Eval records: 85
- All records: 1068

## Files
- data/finetune_ready/echo_sft_all.jsonl
- data/finetune_ready/echo_sft_train.jsonl
- data/finetune_ready/echo_sft_eval.jsonl
- data/finetune_ready/echo_sft_all_with_meta.jsonl
