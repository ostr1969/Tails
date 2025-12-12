import tiktoken

enc = tiktoken.get_encoding("cl100k_base")  # general-purpose BPE

def chunk_by_tokens(text, chunk_size=300, overlap=50):
    tokens = enc.encode(text)
    chunks = []

    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
        start = end - overlap
    return chunks

if __name__ == "__main__":
    sample_text = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
        "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi "
        "ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit "
        "in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur "
        "sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt "
        "mollit anim id est laborum."
    )
    chunks = chunk_by_tokens(sample_text, chunk_size=20, overlap=5)
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}:\n{chunk}\n")