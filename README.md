# 🚀 PatentAI - Topic-Aware Patent Chatbot with Parsing & LLM

PatentAI is a FastAPI-based backend that allows users to register/login, parse patents for a topic, and chat with them using powerful LLMs like Mistral. It automatically scrapes patent data from [FreePatentsOnline](https://www.freepatentsonline.com), stores them in MongoDB, and embeds content into ChromaDB for fast vector search.

---

## 📦 Features

* ✅ User Authentication (Register/Login)
* 📚 Topic-Based Patent Parsing
* 🤖 Chat with Patents using LLM (e.g. Mistral)
* 🔍 ChromaDB for Semantic Search
* 🌐 FastAPI + MongoDB + Redis + LangChain
* 🐳 Docker + Docker Compose ready

---

## 🐳 Running with Docker Compose

This is the recommended setup. It builds the app and runs MongoDB and Redis containers automatically.

1. **Add your HuggingFace token to `.env`**

   ```bash
   HF_TOKEN=your_huggingface_token
   ```

2. **Start the services**

   ```bash
   docker-compose up --build
   ```

This will:

* Build and run the app on `localhost:8000`
* Start MongoDB and Redis services
* Automatically mount volume folders for parsed patents and vector DB

---

## 📂 Project Structure

```
patentai/
├── app/
│   ├── routes/
│   ├── utils/
│   ├── chroma_db_patents/     # Created at runtime
│   ├── parsed_patents/        # Created at runtime
│   └── __init__.py
├── main.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
└── .dockerignore
```

---

## 🔌 API Endpoints

### 🔐 Auth

#### `POST /api/register`

* **Input:** `{ "email": "user@example.com", "password": "yourpassword" }`
* **Output:** `{ "message": "User registered successfully" }`

#### `POST /api/login`

* **Input:** `{ "email": "user@example.com", "password": "yourpassword" }`
* **Output:** `{ "message": "Login successful", "session_id": "uuid-string" }`

---

### 🧠 Chat

#### `POST /api/chat`

* **Headers:** `session_id: <your-session-id>`
* **Input:** `{ "message": "What is the patent about X?" }`
* **Output:** `{ "answer": "LLM-generated answer", "citations": ["pid1","pid2"], "user": "user@example.com" }`

---

### 📚 Patent Parsing

#### `POST /api/topic/initiate`

* **Headers:** `session_id: <your-session-id>`
* **Input:** `{ "topic": "machine learning" }`
* **Output:**

  ```json
  {
    "status": "success",
    "message": "Inserted 50 patents for 'machine_learning' into ChromaDB.",
    "user": "user@example.com"
  }
  ```

---

## 🤭 Future Roadmap

* ✅ Add API-based patent ingestion (USPTO, EPO)
* ⛓️ Add cross-topic citation tracking
* 🧠 Improve long-context memory with RAG
* 🧪 Add full test suite (PyTest + coverage)
* 🎨 Add web frontend (React / Svelte)

---

## 🛡️ License

MIT License. Use and contribute freely.

---

## 🤝 Contributing

Pull requests and issues welcome! Please file bugs, suggestions, or docs improvements in the [GitHub Issues](https://github.com/your-org/PatentBot/issues) tab.
