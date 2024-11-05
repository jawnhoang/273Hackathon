from sentence_transformers import SentenceTransformer

# Load a pre-trained model for generating embeddings
model = SentenceTransformer('all-MiniLM-L6-v2') 

def generate_embeddings(text):
    return model.encode(text, convert_to_tensor=True)