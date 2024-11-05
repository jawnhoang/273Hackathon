
def chunk_text(pdf_path, text, max_tokens=1000):
    # Split the text into chunks of specified token size
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        # Estimate the token count (1 token is roughly 4 characters, adjust as needed)
        if len(current_chunk) >= max_tokens:  
            chunks.append(" ".join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(" ".join(current_chunk))  # Add the last chunk if any
    print(f"{pdf_path} chunk size: ", len(chunks))
    return chunks


