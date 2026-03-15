import requests
import os
import json
import pandas as pd

OLLAMA_URL = "http://localhost:11434/api/embed"
MODEL_NAME  = "bge-m3"

# ---------------------------------------------------------------------------
def create_embedding(text_list, source_file="?"):
    print(f"  [DEBUG] Sending {len(text_list)} chunk(s) to Ollama  (file: '{source_file}')")

    # 1. Network / connection
    try:
        r = requests.post(OLLAMA_URL, json={"model": MODEL_NAME, "input": text_list}, timeout=60)
    except requests.exceptions.ConnectionError:
        print(f"  [ERROR] Cannot reach Ollama at {OLLAMA_URL} — is Ollama running?")
        return None
    except requests.exceptions.Timeout:
        print(f"  [ERROR] Request timed out for '{source_file}'")
        return None

    # 2. HTTP status
    print(f"  [DEBUG] HTTP status: {r.status_code}")
    if r.status_code != 200:
        print(f"  [WARN]  Batch failed (HTTP {r.status_code}): {r.text[:200]}")
        print(f"  [INFO]  Retrying {len(text_list)} chunk(s) one-by-one to isolate bad chunk(s)...")
        results = []
        bad = 0
        for idx, text in enumerate(text_list):
            # Keep progress visible for large files so the run does not look stuck.
            if idx % 25 == 0:
                print(f"  [PROGRESS] Retrying chunk {idx + 1}/{len(text_list)}...")

            try:
                r2 = requests.post(
                    OLLAMA_URL,
                    json={"model": MODEL_NAME, "input": [text]},
                    timeout=20
                )
                if r2.status_code == 200:
                    resp2 = r2.json()
                    emb = resp2.get("embeddings") or resp2.get("embedding")
                    results.append(emb[0] if emb else None)
                else:
                    print(f"  [SKIP]  Chunk {idx} failed: {r2.text[:100]}")
                    results.append(None)
                    bad += 1
            except requests.exceptions.Timeout:
                print(f"  [SKIP]  Chunk {idx} timed out during retry")
                results.append(None)
                bad += 1
            except Exception as e:
                print(f"  [SKIP]  Chunk {idx} retry error: {e}")
                results.append(None)
                bad += 1
        good = len(text_list) - bad
        print(f"  [OK]    Per-chunk retry done — {good} good, {bad} skipped.")
        return results

    # 3. JSON decode
    try:
        response = r.json()
    except Exception as e:
        print(f"  [ERROR] Could not parse JSON response: {e}")
        print(f"  [DEBUG] Raw text: {r.text[:300]}")
        return None

    print(f"  [DEBUG] Response keys: {list(response.keys())}")

    # 4. Embedding key (old = 'embeddings', new = 'embedding')
    embeddings = response.get("embeddings") or response.get("embedding")
    if embeddings is None:
        print(f"  [ERROR] Neither 'embeddings' nor 'embedding' found in response.")
        print(f"  [DEBUG] Full response:\n{json.dumps(response, indent=2)[:500]}")
        return None

    # 5. Type check
    if not isinstance(embeddings, list):
        print(f"  [ERROR] Expected list, got {type(embeddings).__name__}")
        return None

    # 6. Single flat vector — wrap in a list
    if embeddings and isinstance(embeddings[0], (int, float)):
        print(f"  [DEBUG] Single flat embedding detected — wrapping in list")
        embeddings = [embeddings]

    # 7. Count mismatch
    if len(embeddings) != len(text_list):
        print(
            f"  [ERROR] Count mismatch: {len(embeddings)} vector(s) "
            f"for {len(text_list)} chunk(s) in '{source_file}'"
        )
        return None

    print(f"  [OK]    {len(embeddings)} embedding(s), dim={len(embeddings[0])}")
    return embeddings


# ---------------------------------------------------------------------------
jsons = os.listdir("jsons")
print(f"[INFO] Found {len(jsons)} JSON file(s): {jsons}\n")

my_dicts  = []
chunk_id  = 0
skipped   = []

for json_file in jsons:
    print(f"[FILE] {json_file}")

    # 8. File read / JSON parse
    json_path = os.path.join("jsons", json_file)
    try:
        with open(json_path, encoding="utf-8") as f:
            content = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  [ERROR] Invalid JSON: {e}")
        skipped.append((json_file, "invalid JSON"))
        continue
    except Exception as e:
        print(f"  [ERROR] Could not open file: {e}")
        skipped.append((json_file, str(e)))
        continue

    # 9. Expected structure
    if "chunks" not in content:
        print(f"  [ERROR] 'chunks' key missing. Keys found: {list(content.keys())}")
        skipped.append((json_file, "missing 'chunks' key"))
        continue

    chunks = content["chunks"]
    print(f"  [DEBUG] Chunk count: {len(chunks)}")

    if len(chunks) == 0:
        print(f"  [WARN]  No chunks — skipping.")
        skipped.append((json_file, "0 chunks"))
        continue

    # 10. Get embeddings
    embeddings = create_embedding([c["text"] for c in chunks], source_file=json_file)
    if embeddings is None:
        skipped.append((json_file, "embedding failed — see errors above"))
        continue

    bad_chunks = 0
    for i, chunk in enumerate(chunks):
        if embeddings[i] is None:
            print(f"  [SKIP]  Chunk {i} has no embedding — skipping.")
            bad_chunks += 1
            continue
        chunk["chunk_id"] = chunk_id
        chunk["embedding"] = embeddings[i]
        chunk_id += 1
        my_dicts.append(chunk)

    good_chunks = len(chunks) - bad_chunks
    print(f"  [OK]    {good_chunks}/{len(chunks)} chunk(s) added (skipped {bad_chunks} bad).\n")

# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
if skipped:
    print(f"[SUMMARY] Skipped {len(skipped)} file(s):")
    for fname, reason in skipped:
        print(f"  - {fname}: {reason}")
else:
    print("[SUMMARY] All files processed successfully.")

print(f"[SUMMARY] Total chunks embedded: {chunk_id}")
print("=" * 60 + "\n")

df = pd.DataFrame.from_records(my_dicts)
print(df)
