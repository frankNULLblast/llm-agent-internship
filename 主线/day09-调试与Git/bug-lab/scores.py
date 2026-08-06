import json
from pathlib import Path


def average(values):
    if not values:
        return None
    return sum(values) / len(values)


def load_scores(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [row["score"] for row in data]


def grade(score):
    if score >= 60:
        return "pass"
    return "fail"
