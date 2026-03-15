import requests
import json

def test_embed():
    url = "http://localhost:11434/api/embed"
    data = {
        "model": "bge-m3",
        "input": ["hello world"]
    }
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_embed()
