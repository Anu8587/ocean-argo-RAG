from sqlalchemy import create_engine, inspect

# --- DATABASE CONFIGURATION ---
# IMPORTANT: Replace 'YOUR_PASSWORD' with your PostgreSQL password.
DB_USER = 'postgres'
DB_PASSWORD = 'anushka' 
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'floatchat_db'

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

def get_db_schema_and_context():
    """
    Connects to the database and generates a text description of the
    argo_profiles table's schema and purpose.
    """
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns('argo_profiles')
        
        context = "This database contains ARGO float data in a table named 'argo_profiles'.\n"
        context += "Each row represents a unique measurement profile from a specific float at a specific time.\n\n"
        context += "The table has the following columns:\n"
        
        for column in columns:
            column_name = column['name']
            description = ""
            if column_name == 'float_id':
                description = "The unique identifier for each ARGO float."
            elif column_name == 'profile_date':
                description = "The timestamp (UTC) when the profile was taken. Format is YYYY-MM-DD HH:MM:SS."
            elif column_name == 'latitude':
                description = "The latitude of the float in degrees north."
            elif column_name == 'longitude':
                description = "The longitude of the float in degrees east."
            elif column_name == 'pressure_levels':
                description = "A JSON array of pressure levels (depths) in decibars."
            elif column_name == 'temperature_values':
                description = "A JSON array of temperature readings in Celsius, corresponding to the pressure_levels."
            elif column_name == 'salinity_values':
                description = "A JSON array of salinity readings (PSU), corresponding to the pressure_levels."
            
            context += f"- {column_name}: {description}\n"
            
        return context

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# --- To run this script ---
if __name__ == '__main__':
    schema_context = get_db_schema_and_context()
    
    if schema_context:
        print("--- Generated Database Context (AI Cheat Sheet) ---")
        print(schema_context)
        
        # Save this context to a file for our AI to use later
        with open("db_context.txt", "w") as f:
            f.write(schema_context)
        print("\nContext has been saved to 'db_context.txt'")