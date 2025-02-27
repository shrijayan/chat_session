# Chatbot Session Management with FastAPI

This project implements a chatbot session management system using FastAPI, Redis, and LangChain. It allows users to create new chat sessions, continue existing conversations, and manage chat histories.

## Features

- **New Session Creation**: Create a new conversation session with a unique ID.
- **Continuous Conversation**: Continue a conversation using a session identifier.
- **Chat History Management**: Store and retrieve chat histories from Redis.
- **Streaming Responses**: Handle continuous conversation with streaming responses.
- **Admin Features**: List all session IDs and retrieve chat history for specific sessions.

## Project Structure

```
├── README.md
├── __pycache__
│   └── main.cpython-312.pyc
├── dump.rdb
├── main.ipynb
├── main.py
├── requirements.txt
└── static
    └── index.html
```

## Setup

1. **Clone the repository**:
    ```sh
    git clone https://github.com/yourusername/chatbot_session.git
    cd chatbot_session
    ```

2. **Create a virtual environment**:
    ```sh
    python3 -m venv .venv-chat
    source .venv-chat/bin/activate
    ```

3. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

4. **Set up Redis**:
    Ensure Redis is installed and running on your local machine. The default configuration connects to Redis on `localhost:6379`.

5. **Set Groq API Key**:
    Set the Groq API key as an environment variable:
    ```sh
    export GROQ_API_KEY="your_groq_api_key"
    ```

## Running the Application

To start the FastAPI application, run:

```sh
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Create a New Session
- **Endpoint**: `/new_session`
- **Method**: `POST`
- **Description**: Creates a new conversation session with a unique ID.
- **Response**:
    ```json
    {
        "session_id": "unique_session_id"
    }
    ```

### Handle Continuous Conversation
- **Endpoint**: `/chat`
- **Method**: `POST`
- **Description**: Handle continuous conversation with session ID.
- **Request Body**:
    ```json
    {
        "session_id": "unique_session_id",
        "message": "user_message"
    }
    ```

### List All Sessions (Admin Feature)
- **Endpoint**: `/sessions`
- **Method**: `GET`
- **Description**: List all session IDs in Redis.
- **Response**:
    ```json
    {
        "sessions": ["session_id_1", "session_id_2", ...]
    }
    ```

### Retrieve Chat History
- **Endpoint**: `/session/{session_id}/history`
- **Method**: `GET`
- **Description**: Get the chat history for a specific session.
- **Response**:
    ```json
    {
        "history": [
            {
                "input": "user_message",
                "output": "bot_response"
            },
            ...
        ]
    }
    ```
