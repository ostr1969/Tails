import requests
import json

def embed_ollama(text, model="nomic-embed-text"):
    r = requests.post(
        "http://localhost:11434/api/embeddings",
        json={"model": model, "prompt": text}
    )
    r.raise_for_status()
    return r.json()["embedding"]

if __name__ == "__main__":
    sample_text = "Hello, world!"
    embedding = embed_ollama(sample_text)
    print(f"Embedding for '{sample_text}':\n{json.dumps(embedding, indent=2)}")