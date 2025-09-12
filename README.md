# 🌊 Floatchat – ARGO Float Data + LLM Chatbot  

Floatchat is a full-stack project that integrates **PostgreSQL**, **ChromaDB**, and **Large Language Models (LLMs)** to query **ARGO float oceanographic data** through a chatbot interface.  

It loads ARGO float measurement profiles into PostgreSQL, indexes them with embeddings in ChromaDB, and allows you to interact with the data via a conversational UI.  

---

## 🚀 Features
- Load large ARGO float datasets (CSV → PostgreSQL)  
- Store structured profiles (temperature, salinity, pressure levels)  
- Index with embeddings (`sentence-transformers`) into **ChromaDB**  
- Query with **Groq/OpenAI LLMs** through a Flask API  
- Frontend UI for chatting with your dataset  

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/floatchat.git
cd floatchat

2. Create a virtual environment
python -m venv venv
# Activate
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

3. Install dependencies
pip install -r requirements.txt

🗄️ Database Setup (PostgreSQL)

Install PostgreSQL (16/17 recommended).

Create a database:

createdb floatchat_db


Update DB credentials in:

backend/context.py

backend/load_data.py

backend/setup_chroma.py

backend/chatbot.py

👉 Or place them in a .env file if using python-dotenv.

Load ARGO CSV data into PostgreSQL:

python backend/load_data.py


This script:

Reads the CSV in chunks

Creates the argo_profiles table if not exists

Inserts profiles (with JSON arrays for pressure, temperature, salinity)

Builds indexes for performance

🔎 ChromaDB Setup

After DB is populated, index profiles with embeddings:

python backend/setup_chroma.py


This will:

Pull profiles from PostgreSQL

Encode them with all-MiniLM-L6-v2

Store vectors + metadata in ChromaDB

🤖 Run the Chatbot Backend

Start the Flask chatbot service:

python backend/chatbot.py


By default, it runs at:
👉 http://127.0.0.1:5000

You can test with:

curl -X POST http://127.0.0.1:5000/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Show me temperature profiles near 10N 70E"}'

🎨 Frontend Setup

The frontend folder contains the UI (React/Flask HTML).

Run with React:
cd frontend
npm install
npm start


It will open at 👉 http://localhost:3000

The frontend connects to the Flask backend at http://127.0.0.1:5000.

📂 Project Structure
floatchat/
 ├── backend/
 │    ├── chatbot.py        # Flask API + Groq LLM integration
 │    ├── setup_chroma.py   # Populate ChromaDB with embeddings
 │    ├── context.py        # Database schema + config
 │    ├── load_data.py      # CSV → PostgreSQL ingestion
 │    ├── db_context.txt    # Schema description (auto-generated)
 │    └── ...
 ├── frontend/
 │    ├── src/
 │    │   ├── App.js        # Chat UI
 │    │   └── ...
 │    ├── package.json
 │    └── ...
 ├── requirements.txt
 └── README.md

⚙️ Requirements

Here’s the full requirements.txt:

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

pip install -r requirements.txt

⚡ Usage Workflow

Prepare DB

python backend/load_data.py


Index with Chroma

python backend/setup_chroma.py


Run Chatbot API

python backend/chatbot.py


Start Frontend

cd frontend
npm start


Open UI
Go to 👉 http://localhost:3000 and start chatting!

🔑 API Keys

If using Groq/OpenAI LLMs, set your API key:

Linux/Mac

export GROQ_API_KEY="your_api_key_here"


Windows (PowerShell)

setx GROQ_API_KEY "your_api_key_here"
```bash
git clone [https://github.com/your-username/floatchat.git](https://github.com/your-username/floatchat.git)
cd floatchat
