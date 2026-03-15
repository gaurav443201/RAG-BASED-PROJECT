import json
import os
import re

jsons_dir = "jsons"

for filename in os.listdir(jsons_dir):
    if not filename.endswith(".json"):
        continue

    filepath = os.path.join(jsons_dir, filename)

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    for chunk in data.get("chunks", []):
        if "text" in chunk:
            chunk["text"] = re.sub(r"[,.\?']", "", chunk["text"])

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Processed: {filename}")

print("Done.")
