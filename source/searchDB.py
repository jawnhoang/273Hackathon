from generateEmbeddings import generate_embeddings
from vectorDB import collection
import openai

def query_vectordb(question, n_results=5):
    # Generate embeddings for the question
    question_embedding = generate_embeddings(question)

    # Query the collection for similar embeddings
    results = collection.query(query_embeddings=question_embedding.tolist(), n_results=n_results)
    
    return results  



def prepare_context(results):
    if 'metadatas' in results and isinstance(results['metadatas'], list):
        # Extract the texts from the metadatas list
        context = "\n".join([metadata['text'] for metadata in results['metadatas'] if 'text' in metadata])
        return f"Use the following context to answer the question:\n\nContext:\n{context}\n\nPlease provide an answer strictly based on this context."
    else:
        return "No valid metadata found."


openai.api_key = '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'

def chatgpt_prompt(question, context):
    prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Specify the model you want to use
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response['choices'][0]['message']['content']



def answer_question(question):
    # Query the Vector Database for relevant context
    results = query_vectordb(question)
    
    # Ensure results is as expected
    if isinstance(results, dict):
        # Prepare the context from the query results
        context = prepare_context(results)
        
        # Ask ChatGPT for an answer based on the context
        answer = chatgpt_prompt(question, context)
        return answer
    else:
        return "Error: Unexpected results format from the database."

# query = "Compare list of Food insecurity reason in 2023 and 2024."

# response = answer_question(query)


while(True):
    user_query = input("Ask LLM about SOFI 2023/2024 data:\n")
    response = answer_question(user_query)
    print("chatgpt response: \n", response)

