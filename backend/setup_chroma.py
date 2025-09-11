import chromadb
from sentence_transformers import SentenceTransformer
import pandas as pd
from sqlalchemy import create_engine
import json

# Database configuration
DB_USER = 'postgres'
DB_PASSWORD = 'anushka'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'floatchat_db'
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Initialize Chroma and embedding model
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("argo_profiles")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load profiles from DB
engine = create_engine(DATABASE_URL)
profiles = pd.read_sql("SELECT * FROM argo_profiles", engine)

# Generate embeddings
print("Generating embeddings for profiles...")
for idx, row in profiles.iterrows():
    # Create text representation
    temp = json.loads(row['temperature_values'])
    pres = json.loads(row['pressure_levels'])
    psal = json.loads(row['salinity_values'])
    text = (f"Float {row['float_id']}, date {row['profile_date']}, "
            f"latitude {row['latitude']}, longitude {row['longitude']}, "
            f"temperature {temp[:5] if temp else 'none'}, "
            f"pressure {pres[:5] if pres else 'none'}, "
            f"salinity {psal[:5] if psal else 'none'}")
    embedding = model.encode(text).tolist()
    
    # Add to Chroma
    collection.add(
        ids=[str(idx)],
        embeddings=[embedding],
        metadatas=[{
            'float_id': str(row['float_id']),
            'profile_date': row['profile_date'],
            'latitude': float(row['latitude']),
            'longitude': float(row['longitude']),
            'temp_count': len(temp),
            'pres_count': len(pres),
            'psal_count': len(psal)
        }]
    )

print(f"Populated Chroma with {collection.count()} profiles!")