from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from generateEmbeddings import generate_embeddings
import json
import pika
import redis
import asyncio
import hashlib
import uuid
import time
from datetime import datetime
app = FastAPI()

PROMPT_Q = "prompt_queue"
RES_Q = "result_queue"
# Initialize Redis client
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

# RabbitMQ connection parameters
credentials = pika.PlainCredentials('guest', 'guest')
rabbitmq_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost',credentials=credentials))
channel = rabbitmq_connection.channel()
channel.queue_declare(queue=PROMPT_Q)
channel.queue_declare(queue=RES_Q)
# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    content: str
    user: str

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Remaining connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()


def hash_prompt(prompt_text):
    return hashlib.sha256(prompt_text.encode()).hexdigest()


# Function to send a message and await the response
def send_prompt_and_wait(prompt_text):
    prompt_id = str(uuid.uuid4())
    prompt_key = hash_prompt(prompt_text)

    # Send the prompt to RabbitMQ
    channel.basic_publish(exchange='', routing_key=PROMPT_Q, body=json.dumps({'prompt': prompt_text, 'prompt_id': prompt_id}))

    # Wait for the result from the results queue
    while True:
        _, _, body = channel.basic_get(queue=RES_Q, auto_ack=True)
        if body:
            result_data = json.loads(body)
            if result_data['prompt_id'] == prompt_id:
                # Cache the result in Redis with a 30-minute TTL
                
                redis_client.setex(prompt_key, 1800, result_data['response'])
                return result_data['response']
        time.sleep(0.1)  


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/send_message")
async def send_message(message: Message):
    prompt_key = hash_prompt(message.content)
    cached_response = redis_client.get(prompt_key)

    user_message = {
        "content": message.content,
        "user": message.user,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # You can add timestamp here if needed
    }
    if cached_response:
        ai_response = cached_response
        print(f"Cache hit in redis for prompt: {message.content}")
    else:
        ai_response =  send_prompt_and_wait(message.content)
    ai_message = {
            "content": ai_response,
            "user": "AI Assistant",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    print(ai_message)
    # return {"status": "success", "response": ai_message}
    await manager.broadcast(user_message)
    await manager.broadcast(ai_message)
    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)