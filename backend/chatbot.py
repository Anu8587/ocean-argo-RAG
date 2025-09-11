from flask import Flask, request, jsonify
import chromadb
from sentence_transformers import SentenceTransformer
import pandas as pd
from sqlalchemy import create_engine, text
import json
import re

app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
DB_USER = 'postgres'
DB_PASSWORD = 'anushka'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'floatchat_db'
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- Initialize Chroma and embedding model ---
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("argo_profiles")
model = SentenceTransformer('all-MiniLM-L6-v2')
engine = create_engine(DATABASE_URL)

# --- Parse simple queries ---
def parse_query(query):
    filters = {}
    if "equator" in query.lower():
        filters['latitude'] = (-5, 5)
    if "2025" in query.lower():
        filters['date'] = ("2025-01-01", "2025-12-31")
    if "warm" in query.lower() or re.search(r"temp[^\d]*>[\s]*25", query.lower()):
        filters['temperature'] = 25.0
    return filters

# --- Query function ---
def query_profiles(user_query):
    try:
        # Get embedding and query Chroma
        query_embedding = model.encode(user_query).tolist()
        results = collection.query(query_embeddings=[query_embedding], n_results=50)
        profile_ids = [int(m['float_id']) for m in results['metadatas'][0]]  # Use float_id from metadata
        print("DEBUG: Chroma returned float_ids:", profile_ids)

        if not profile_ids:
            return []

        # Parse filters
        filters = parse_query(user_query)

        # Build SQL query
        sql = """
        SELECT float_id, profile_date, latitude, longitude, 
               temperature_values, pressure_levels, salinity_values
        FROM argo_profiles
        WHERE float_id = ANY(:ids)
          AND json_array_length(temperature_values::json) > 0
        """
        params = {'ids': profile_ids}

        if 'latitude' in filters:
            sql += " AND latitude BETWEEN :lat_min AND :lat_max"
            params['lat_min'], params['lat_max'] = filters['latitude']

        if 'date' in filters:
            sql += " AND profile_date BETWEEN :date_start AND :date_end"
            params['date_start'], params['date_end'] = filters['date']

        if 'temperature' in filters:
            sql += """
            AND EXISTS (
                SELECT 1 FROM json_array_elements(temperature_values::json) t
                WHERE (t->>'value')::float > :temp
            )
            """
            params['temp'] = filters['temperature']

        # Execute SQL safely
        with engine.connect() as conn:
            profiles = pd.read_sql(text(sql), conn, params=params)

        # Format results
        formatted = []
        for _, row in profiles.iterrows():
            formatted.append({
                'float_id': row['float_id'],
                'date': row['profile_date'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'temperature_count': len(json.loads(row['temperature_values'])),
                'pressure_count': len(json.loads(row['pressure_levels'])),
                'salinity_count': len(json.loads(row['salinity_values']))
            })

        return formatted
    except Exception as e:
        return {'error': str(e)}

# --- Flask endpoint ---
@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing query'}), 400

    user_query = data['query']
    results = query_profiles(user_query)

    if isinstance(results, dict) and 'error' in results:
        return jsonify({'error': results['error']}), 500

    return jsonify({
        'query': user_query,
        'results': results,
        'count': len(results)
    })

# --- Run app ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
