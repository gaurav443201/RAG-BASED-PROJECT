import json
import re

file_path = "jsons/06_SEO and Core Web Vitals in HTML.mp3.json"

with open(file_path, encoding="utf-8") as f:
    content = json.load(f)

for chunk in content["chunks"]:
    chunk["text"] = re.sub(r"[,.\?']", "", chunk["text"])

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(content, f, indent=4)

print("Done. Symbols removed from file 06.")