# 🌊 Floatchat – ARGO Float Data + LLM Chatbot

Floatchat is a full-stack project that integrates PostgreSQL, ChromaDB, and Large Language Models (LLMs) to query ARGO float oceanographic data through a chatbot interface.  

It loads ARGO float measurement profiles into PostgreSQL, indexes them with embeddings in ChromaDB, and allows you to interact with the data via a conversational UI.

---

## 🚀 Features
- Load large ARGO float datasets (CSV → PostgreSQL)  
- Store structured profiles (temperature, salinity, pressure levels)  
- Index with embeddings (sentence-transformers) into ChromaDB  
- Query with Groq/OpenAI LLMs through a Flask API  
- Frontend UI for chatting with your dataset  

---

## 📦 Installation

1. Clone the repository:  
   `git clone https://github.com/your-username/floatchat.git && cd floatchat`

2. Create a virtual environment:  
   `python -m venv venv`  

   Activate it:  
   - Mac/Linux → `source venv/bin/activate`  
   - Windows → `venv\Scripts\activate`

3. Install dependencies:  
   `pip install -r requirements.txt`

---

## 🗄️ Database Setup (PostgreSQL)

1. Install PostgreSQL (16/17 recommended).  
2. Create a database:  
   `createdb floatchat_db`  
3. Update DB credentials inside:  
   - backend/context.py  
   - backend/load_data.py  
   - backend/setup_chroma.py  
   - backend/chatbot.py  
   (or use a `.env` file with `python-dotenv`)  

4. Load ARGO CSV data into PostgreSQL:  
   `python backend/load_data.py`  

This script reads the CSV in chunks, creates the `argo_profiles` table if not exists, inserts profiles with JSON arrays (pressure, temperature, salinity), and builds indexes for performance.

---

## 🔎 ChromaDB Setup

After DB is populated, index profiles with embeddings:  
`python backend/setup_chroma.py`

This will pull profiles from PostgreSQL, encode them with `all-MiniLM-L6-v2`, and store vectors + metadata in ChromaDB.

---

## 🤖 Run the Chatbot Backend

Start the Flask chatbot service:  
`python backend/chatbot.py`

By default, it runs at `http://127.0.0.1:5000`.  

You can test with:  
`curl -X POST http://127.0.0.1:5000/chat -H "Content-Type: application/json" -d '{"message": "Show me temperature profiles near 10N 70E"}'`

---

## 🎨 Frontend Setup

Navigate to the frontend folder:  
`cd frontend`

Install dependencies:  
`npm install`

Start the dev server:  
`npm start`

It will open at `http://localhost:3000`, which connects to the Flask backend at `http://127.0.0.1:5000`.

---


---

## ⚙️ Requirements

Full `requirements.txt`:
flask
sqlalchemy
psycopg2-binary
pandas
numpy
chromadb
sentence-transformers
torch
transformers
groq
python-dotenv


Install with:  
`pip install -r requirements.txt`

---

## ⚡ Usage Workflow

1. Prepare DB → `python backend/load_data.py`  
2. Index with Chroma → `python backend/setup_chroma.py`  
3. Run Chatbot API → `python backend/chatbot.py`  
4. Start Frontend → `cd frontend && npm start`  
5. Open UI → Go to `http://localhost:3000` and start chatting!  

---

## 🔑 API Keys

If using Groq/OpenAI LLMs, set your API key before running:  

Linux/Mac → `export GROQ_API_KEY="your_api_key_here"`  
Windows PowerShell → `setx GROQ_API_KEY "your_api_key_here"`


