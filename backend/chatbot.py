from flask import Flask, request, jsonify
import chromadb
from sentence_transformers import SentenceTransformer
import pandas as pd
from sqlalchemy import create_engine, text
import json
from groq import Groq
import logging
import os
from dotenv import load_dotenv

app = Flask(__name__)

# --- Load environment variables ---
load_dotenv()
print("Loading environment variables...")

# --- Setup logging ---
logging.basicConfig(level=logging.INFO, filename='chatbot.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# --- DATABASE CONFIGURATION ---
DB_USER = 'postgres'
DB_PASSWORD = 'anushka'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'floatchat_db'
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- Initialize Chroma and embedding model ---
try:
    print("Initializing ChromaDB...")
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection("argo_profiles")
    print("Initializing embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Initializing database engine...")
    engine = create_engine(DATABASE_URL)
except Exception as e:
    logger.error(f"Initialization error: {e}")
    print(f"Initialization failed: {e}")
    raise

# --- Groq API Configuration ---
print("Initializing Groq client...")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY not found in environment variables")
    print("Error: GROQ_API_KEY not found")
    raise ValueError("GROQ_API_KEY environment variable is not set")
groq_client = Groq(api_key=GROQ_API_KEY)

# --- Load database context ---
def load_context():
    print("Loading database context...")
    try:
        with open("db_context.txt", "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading context: {e}")
        print(f"Error loading db_context.txt: {e}")
        return "Database schema unavailable."

# --- Parse query with LLaMA-3.3-70B via Groq ---
def parse_query_with_llm(user_query):
    context = load_context()
    prompt = f"""
    {context}

    User query: {user_query}

    You are an AI assistant for FloatChat, a system for querying ARGO float data stored in the argo_profiles table. Your task is to interpret the user's natural language query and generate a JSON object containing a valid PostgreSQL query and corresponding filters to query the argo_profiles table. The table uses TEXT columns (temperature_values, pressure_levels, salinity_values) that store JSON arrays, requiring explicit casting to JSON with ::json for queries using json_array_elements. The profile_date column is TEXT (format: 'YYYY-MM-DDTHH:MM:SSZ'), not TIMESTAMP. Current date: 2025-09-11.

    Guidelines:
    - Semantically analyze the query to identify conditions for columns: float_id (integer), profile_date (text, e.g., '2025-01-09T19:43:57Z'), latitude (float), longitude (float), temperature_values (text, JSON array), pressure_levels (text, JSON array), salinity_values (text, JSON array).
    - For locations, interpret named regions (e.g., 'Indian Ocean': latitude -30 to 30, longitude 20 to 120; 'Pacific Ocean': latitude -60 to 60, longitude 120 to 270) or coordinates (e.g., near 0°N, 0°E → latitude BETWEEN -5 AND 5, longitude BETWEEN -5 AND 5).
    - For time periods, interpret absolute dates (e.g., '2025': profile_date LIKE :year || '%'; 'January 2025': profile_date LIKE :month || '%') or relative periods (e.g., 'last 6 months': profile_date::timestamp >= CURRENT_DATE - INTERVAL '6 months').
    - For parameters (temperature, salinity, pressure), use json_array_elements(column::json) with conditions (e.g., for 'temperature above 25C': EXISTS (SELECT 1 FROM json_array_elements(temperature_values::json) t WHERE (t->>'value')::float > :temp); for 'pressure above 100 dbar': EXISTS (SELECT 1 FROM json_array_elements(pressure_levels::json) p WHERE (p->>'value')::float > :pressure)).
    - Use reasonable thresholds (e.g., salinity > 34 PSU, temperature > 15C, pressure > 100 dbar) to maximize results.
    - For non-empty arrays, use json_array_length(column::json) > 0 (e.g., for salinity: json_array_length(salinity_values::json) > 0). Never use != '[]'::json.
    - For comparison queries (e.g., 'compare salinity and temperature'), select both temperature_values and salinity_values with json_array_length(column::json) > 0.
    - For gradient queries (e.g., 'temperature gradient across depths'), select temperature_values and pressure_levels, order by (p->>'value')::float ASC.
    - For unsupported parameters (e.g., 'oxygen levels'), return an empty SQL query with an error message.
    - Ensure SQL is valid PostgreSQL, uses parameterized queries (e.g., :lat_min, :temp) for safety, and avoids SQL injection.
    - Avoid DATE_PART or DATE_TRUNC unless profile_date is cast to timestamp.
    - If ambiguous, generate a broad SQL query (e.g., select all fields with float_id = ANY(:ids)).
    - If no profiles are expected (e.g., due to sparse data), include a warning: 'No profiles found, possibly due to sparse data or restrictive filters.'
    - Return valid JSON, ensuring all special characters (e.g., quotes, backslashes) are properly escaped.

    Output format:
    ```json
    {{
        "sql": "SELECT ... FROM argo_profiles WHERE ...;",
        "filters": {{...}},
        "error": null,
        "warning": null
    }}
    ```
    If the query cannot be processed:
    ```json
    {{
        "sql": "",
        "filters": {{}},
        "error": "Reason for failure",
        "warning": null
    }}
    ```

    Return only the JSON object, wrapped in ```json\\n...\\n```.
    """
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        json_str = response.choices[0].message.content.split("```json\n")[1].split("\n```")[0]
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"LLM parsing error: {e}")
        print(f"LLM parsing error: {e}")
        return {
            "sql": "",
            "filters": {},
            "error": f"Failed to parse query: {str(e)}",
            "warning": None
        }

# --- Query function ---
def query_profiles(user_query):
    try:
        print(f"Processing query: {user_query}")
        logger.info(f"Processing query: {user_query}")
        
        # Get embedding and query Chroma
        query_embedding = model.encode(user_query).tolist()
        results = collection.query(query_embeddings=[query_embedding], n_results=50)
        profile_ids = [int(m['float_id']) for m in results['metadatas'][0]]
        logger.info(f"Chroma returned float_ids: {profile_ids}")
        print(f"Chroma returned {len(profile_ids)} profile IDs")

        # Get LLM-generated query parameters
        query_info = parse_query_with_llm(user_query)
        if query_info.get("error"):
            logger.warning(f"Query failed: {query_info['error']}")
            print(f"Query error: {query_info['error']}")
            return {'error': query_info['error']}

        sql = query_info.get('sql')
        params = {'ids': profile_ids}
        params.update(query_info.get('filters', {}))

        # Fallback SQL if LLM fails or returns empty/invalid SQL
        if not sql or not query_info.get('filters'):
            logger.info("Using fallback SQL query")
            print("Using fallback SQL query")
            sql = """
            SELECT float_id, profile_date, latitude, longitude, 
                   temperature_values, pressure_levels, salinity_values
            FROM argo_profiles
            WHERE float_id = ANY(:ids)
            AND json_array_length(temperature_values::json) > 0
            """
            if "salinity" in user_query.lower():
                sql += " AND json_array_length(salinity_values::json) > 0"
                params['warning'] = "Salinity data is sparse (~50% of profiles lack salinity measurements)."
            if "pressure" in user_query.lower():
                sql += " AND EXISTS (SELECT 1 FROM json_array_elements(pressure_levels::json) p WHERE (p->>'value')::float > :pressure)"
                params['pressure'] = 100

            if "last" in user_query.lower() and ("month" in user_query.lower() or "year" in user_query.lower()):
                sql += " AND profile_date::timestamp >= CURRENT_DATE - INTERVAL :interval"
                params['interval'] = '6 months' if "month" in user_query.lower() else '1 year'    
            if "temperature" in user_query.lower() and "gradient" not in user_query.lower():
                sql += " AND EXISTS (SELECT 1 FROM json_array_elements(temperature_values::json) t WHERE (t->>'value')::float > :temp)"
                params['temp'] = 15

                

        print(f"Executing SQL: {sql} with params: {params}")
        logger.info(f"Executing SQL: {sql} with params: {params}")

        # Execute SQL safely
        with engine.connect() as conn:
            profiles = pd.read_sql(text(sql), conn, params=params)

        # Format results
        formatted = []
        for _, row in profiles.iterrows():
            formatted.append({
                'float_id': row['float_id'],
                'date': str(row['profile_date']),
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude']),
                'temperature_count': len(json.loads(row['temperature_values'])),
                'pressure_count': len(json.loads(row['pressure_levels'])),
                'salinity_count': len(json.loads(row['salinity_values']))
            })

        # Handle zero results
        if not formatted:
            warning = query_info.get('warning', 'No profiles found, possibly due to sparse data or restrictive filters.')
            formatted.append({'warning': warning})
            logger.warning(warning)
            print(warning)

        # Add warning from params if present
        if 'warning' in params:
            formatted.append({'warning': params['warning']})

        logger.info(f"Query returned {len([r for r in formatted if 'warning' not in r])} profiles for: {user_query}")
        print(f"Query returned {len([r for r in formatted if 'warning' not in r])} profiles")
        return formatted
    except Exception as e:
        logger.error(f"Query error: {e}")
        print(f"Query error: {e}")
        return {'error': str(e)}


# --- Stats endpoint for Page 1 ---
@app.route('/stats', methods=['GET'])
def stats():
    try:
        sql = """
        SELECT float_id, profile_date, latitude, longitude,
               json_array_length(temperature_values::json) as temperature_count,
               json_array_length(salinity_values::json) as salinity_count
        FROM argo_profiles
        WHERE latitude BETWEEN -30 AND 30 AND longitude BETWEEN 20 AND 120
        AND profile_date::timestamp >= CURRENT_DATE - INTERVAL '6 months'
        """
        with engine.connect() as conn:
            profiles = pd.read_sql(text(sql), conn).to_dict(orient="records")
        return jsonify({
            "results": profiles,
            "count": len(profiles),
            "latest_date": max(p["profile_date"] for p in profiles) if profiles else "N/A",
            "salinity_count": sum(1 for p in profiles if p["salinity_count"] > 0)
        })
    except Exception as e:
        logger.error(f"Stats error: {e}")
        print(f"Stats error: {e}")
        return jsonify({"error": str(e)}), 400


# --- Flask endpoint ---
@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    if not data or 'query' not in data:
        logger.error("Missing or invalid query in request")
        print("Error: Missing or invalid query")
        return jsonify({'error': 'Missing query'}), 400

    user_query = data['query']
    results = query_profiles(user_query)

    if isinstance(results, dict) and 'error' in results:
        return jsonify({'error': results['error']}), 500

    return jsonify({
        'query': user_query,
        'results': results,
        'count': len([r for r in results if 'warning' not in r])
    })

# --- Run app ---
if __name__ == '__main__':
    print("Server starting on http://0.0.0.0:5000...")
    app.run(debug=True, host='0.0.0.0', port=5000)