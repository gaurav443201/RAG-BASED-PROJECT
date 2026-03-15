import requests
import os
import json
import pandas as pd

OLLAMA_URL = "http://localhost:11434/api/embed"
MODEL = "bge-m3"


def create_embedding(text):

    r = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "input": text
        }
    )

    print("Status Code:", r.status_code)

    try:
        data = r.json()
    except:
        print("❌ Could not decode JSON")
        print(r.text)
        return None

    if r.status_code != 200:
        print("❌ API error:", data)
        return None

    if "embedding" in data:
        return data["embedding"]

    if "embeddings" in data:
        return data["embeddings"][0]

    print("❌ Unexpected response:", data)
    return None


print("Starting embedding check...\n")

json_folder = "jsons"

files = os.listdir(json_folder)

print("JSON files found:", files)

my_dicts = []
chunk_id = 0


for json_file in files:

    print("\nOpening file:", json_file)

    with open(f"{json_folder}/{json_file}", encoding="utf-8") as f:
        content = json.load(f)

    if "chunks" not in content:
        print("❌ 'chunks' key not found")
        continue

    chunks = content["chunks"]

    print("Number of chunks:", len(chunks))

    for i, chunk in enumerate(chunks):

        text = chunk.get("text")

        if text is None:
            print(f"⚠️ Chunk {i} has None text, skipping")
            continue

        text = str(text).strip()

        if text == "":
            print(f"⚠️ Chunk {i} empty text, skipping")
            continue

        print(f"\nCreating embedding for chunk {i+1}/{len(chunks)}")

        embedding = create_embedding(text)

        if embedding is None:
            print("❌ Embedding failed at chunk:", i)
            print("Text:", text)
            break

        chunk["chunk_id"] = chunk_id
        chunk["embedding"] = embedding

        print("Embedding length:", len(embedding))

        chunk_id += 1
        my_dicts.append(chunk)

    # only test first file like your original script
    break


print("\nCreating DataFrame...")

df = pd.DataFrame.from_records(my_dicts)

print("\nDataFrame preview:")
print(df.head())

print("\nTotal embeddings created:", len(df))

print("\n🎉 Program finished")