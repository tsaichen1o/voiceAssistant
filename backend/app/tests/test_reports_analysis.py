"""Analyse test_reports.jsonl to calculate the accuracy rate of the model"""

import json

def count_assessments_from_jsonl(file_path: str) -> None:
    """Reads a JSONL file and counts how many assessments are True vs False."""

    true_count = 0
    false_count = 0
    total = 0

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("assessment") is True:
                        true_count += 1
                    elif entry.get("assessment") is False:
                        false_count += 1
                    total += 1
                except json.JSONDecodeError:
                    print(f"⚠️ Skipped malformed line: {line.strip()}")
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"✅ Correct (True): {true_count}")
    print(f"❌ Incorrect (False): {false_count}")
    print(f"📊 Total: {total}")

    accuracy = true_count / total
    print(f"📈 Accuracy rate: {accuracy}%")

if __name__ == "__main__":
    count_assessments_from_jsonl(r"./app/tests/test_results/test_reports.jsonl")
