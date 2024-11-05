import pika
import redis
import json
from pydantic import BaseModel
from typing import List
from generateEmbeddings import generate_embeddings
from vectorDB import collection
import openai


openai.api_key = "your OPEN API Key"
# Initialize Redis client
PROMPT_Q = "prompt_queue"
RES_Q = "result_queue"
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

# RabbitMQ connection parameters
credentials = pika.PlainCredentials('guest', 'guest')
rabbitmq_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost',credentials=credentials))
channel = rabbitmq_connection.channel()
channel.queue_declare(queue=PROMPT_Q)
channel.queue_declare(queue=RES_Q)

# Simulated AI response function (to be replaced with actual processing logic)
def query_vectordb(question, n_results=5):
    # Generate embeddings for the question
    question_embedding = generate_embeddings(question)

    # Query the collection for similar embeddings
    # results = collection.query(query_embeddings=question_embedding.tolist(), n_results=n_results)
    
    return {"hello":"there"}  

def prepare_context(results):
    if 'metadatas' in results and isinstance(results['metadatas'], list):
        # Extract the texts from the metadatas list
        context = "\n".join([metadata['text'] for metadata in results['metadatas'] if 'text' in metadata])
        return f"Use the following context to answer the question:\n\nContext:\n{context}\n\nPlease provide an answer strictly based on this context."
    else:
        return "No valid metadata found."

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

# Callback function to process incoming prompts
def on_request(ch, method, properties, body):
    prompt_data = json.loads(body)
    prompt_text = prompt_data['prompt']
    prompt_id = prompt_data['prompt_id']
    
    # Generate response (simulate AI processing)
    response = answer_question(prompt_text)
    print(f"Processed prompt {prompt_text} with response {response}, now putting into result Queue.")

    # Send response back to the results queue with the same prompt_id
    response_message = json.dumps({
        'prompt_id': prompt_id,
        'response': response
    })
    channel.basic_publish(exchange='', routing_key=RES_Q, body=response_message)

# Set up consumer to listen to the prompts_queue
print("Strting consuming prompts.")
channel.basic_consume(queue=PROMPT_Q, on_message_callback=on_request, auto_ack=True)
channel.start_consuming()

