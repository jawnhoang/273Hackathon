from chromadb import Client
from chromadb.config import Settings
import chromadb
from extractPDF import extract_text_from_pdf
from generateEmbeddings import generate_embeddings
from chunkFile import chunk_text
import uuid

print("initializing chromaDB client\n")
client = chromadb.PersistentClient(path="source/db/")
collection = client.get_or_create_collection("sofi_2023_2024_document")
print("DB for 2023 and 2024 created.\n")


def pdf_to_vectordb(pdf_path):
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    
    text_chunks = chunk_text(pdf_path, text)
    val = len(text_chunks)
    for i,chunk in enumerate(text_chunks):
        # Generate embeddings for the text
        embeddings = generate_embeddings(chunk)
        
        # Prepare metadata (you can customize this as needed)
        metadatas = [{"text": chunk}]
        
        ids = [str(uuid.uuid4())]
        
        # Add embeddings and metadata to the collection
        collection.add(embeddings=embeddings.tolist(), metadatas=metadatas, ids=ids)
        print("processed " + str(i) + "chunks")
    print("vectordb has been created")


pdf_to_vectordb("food_security_docs\SOFI-2023.pdf")
pdf_to_vectordb("food_security_docs\SOFI-2024.pdf")
print("finished loading vectordb!")
