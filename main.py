from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
import redis
import json
import uuid
import os
from typing import List, Dict, Any, Optional

# Set Groq API key as environment variable
os.environ["GROQ_API_KEY"] = "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"

# Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0)

app = FastAPI()

# Mount the static directory for serving the UI
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the index.html at the root
@app.get("/")
async def get_index():
    return FileResponse('static/index.html')

class ChatRequest(BaseModel):
    session_id: str
    message: str

class RedisMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id: str):
        self.session_id = session_id

    @property
    def messages(self) -> List[BaseMessage]:
        """Retrieve all messages from Redis"""
        raw_history = redis_client.hget(self.session_id, "messages")
        if raw_history:
            history = json.loads(raw_history)
            return [
                HumanMessage(content=msg["content"]) if msg["type"] == "human"
                else AIMessage(content=msg["content"])
                for msg in history
            ]
        return []

    def add_message(self, message: BaseMessage) -> None:
        """Add a message to Redis"""
        history = self.messages
        if isinstance(message, HumanMessage):
            history.append({"type": "human", "content": message.content})
        elif isinstance(message, AIMessage):
            history.append({"type": "ai", "content": message.content})
        redis_client.hset(self.session_id, "messages", json.dumps(history))

    async def aadd_message(self, message: BaseMessage) -> None:
        self.add_message(message)

    def clear(self) -> None:
        """Clear all messages from Redis"""
        redis_client.hset(self.session_id, "messages", json.dumps([]))

def get_message_history(session_id: str) -> RedisMessageHistory:
    return RedisMessageHistory(session_id=session_id)

@app.post("/new_session")
async def create_session():
    """Create new conversation session with unique ID"""
    session_id = str(uuid.uuid4())
    redis_client.hset(session_id, "messages", json.dumps([]))
    return {"session_id": session_id}

async def generate_response(session_id: str, message: str):
    """Streaming response generator with session context"""
    if not redis_client.exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Initialize LLM with streaming
    llm = ChatGroq(
        streaming=True,
        temperature=0.7,
        model_name="llama3-8b-8192"
    )
    
    # Create prompt template with history
    prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])
    
    # Create the chain
    chain = prompt | llm
    
    # Create runnable with message history
    runnable = RunnableWithMessageHistory(
        chain,
        get_message_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    
    # Setup streaming
    full_response = []
    async for chunk in runnable.astream(
        {"input": message},
        config={"configurable": {"session_id": session_id}}
    ):
        content = chunk.content
        full_response.append(content)
        yield content

@app.post("/chat")
async def chat_stream(request: ChatRequest):
    """Handle continuous conversation with session ID"""
    return StreamingResponse(
        generate_response(request.session_id, request.message),
        media_type="text/event-stream"
    )

# Add optional endpoint to list all sessions (for admin purposes)
@app.get("/sessions")
async def list_sessions():
    """List all session IDs in Redis (admin feature)"""
    keys = [key.decode() for key in redis_client.keys()]
    return {"sessions": keys}

# Add endpoint to retrieve chat history
@app.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """Get the chat history for a specific session"""
    if not redis_client.exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    message_history = get_message_history(session_id)
    messages = message_history._get_history()  # Using the internal method to get raw history
    
    # Format messages into input/output pairs for UI compatibility
    formatted_history = []
    for i in range(0, len(messages), 2):
        if i+1 < len(messages):
            formatted_history.append({
                "input": messages[i]["content"],
                "output": messages[i+1]["content"]
            })
    
    return {"history": formatted_history}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)