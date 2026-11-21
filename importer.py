import json
from collections import Counter

def parse_export(path):
    with open(path, encoding="utf-8") as file:
        data = json.load(file)

    messages = data["messages"]
    authors = {}
    names = {}

    for m in messages:
        if m.get("type") != "message":
            continue
        from_id = m.get("from_id", "")
        if not from_id.startswith("user"):
            continue
        user_id = int(from_id[4:])
        authors[m["id"]] = user_id
        names[user_id] = m.get("from") or "Unknown"

    counts = Counter()
    for m in messages:
        target = m.get("reply_to_message_id")
        if target is None or m["id"] not in authors:
            continue
        i = authors[m["id"]]
        j = authors.get(target)
        if j is None or i == j:
            continue
        counts[(i, j)] += 1

    return counts, names