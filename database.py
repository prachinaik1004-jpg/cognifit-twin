import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load your .env credentials
load_dotenv()

# Initialize the persistent Supabase connection
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Cache the embedding model at module level (loads once, not per request)
_embedding_model = None

def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            print("--- Loading SentenceTransformer model (one-time) ---")
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("--- Model loaded ---")
        except Exception as e:
            print(f"Could not load SentenceTransformer: {e}")
            _embedding_model = False  # Mark as unavailable
    return _embedding_model if _embedding_model is not False else None

# --- 1. State Management (For the "Brain") ---

def get_twin_state(user_id: str) -> dict:
    """Fetches twin state, returns empty dict if not initialized."""
    response = supabase.table("twin_state").select("*").eq("user_id", user_id).execute()
    
    # If the list is empty (no row found), return a default state
    if not response.data:
        return {"risk_scores": {}, "confidence_levels": {}, "active_alerts": []}
        
    return response.data[0] # Return the first (only) row

def update_twin_state(user_id: str, data: dict):
    """Updates risk scores or active alerts when your logic detects an anomaly."""
    return supabase.table("twin_state").update(data).eq("user_id", user_id).execute()

# --- 2. Interaction Logging (For the "Memory") ---

def save_conversation_turn(user_id: str, role: str, content: str, source: str = "user"):
    """Logs the conversation turns into the database."""
    return supabase.table("conversation_turns").insert({
        "user_id": user_id,
        "role": role,
        "content": content,
        "source": source
    }).execute()

def get_conversation_history(user_id: str, limit: int = 50, source: str = None):
    """Fetches conversation history for a user. Optionally filter by source."""
    query = supabase.table("conversation_turns") \
        .select("*") \
        .eq("user_id", user_id)
    if source:
        query = query.eq("source", source)
    response = query.order("created_at", desc=True) \
        .limit(limit) \
        .execute()
    return response.data

# --- 3. Behavioral Memory (For the "RAG Context") ---

def add_memory_fact(user_id: str, fact: str, category: str):
    """Saves a new behavioral observation as a vectorized memory fact."""
    return supabase.table("memory_facts").insert({
        "user_id": user_id,
        "fact_text": fact,
        "category": category
    }).execute()

def get_memory_facts(user_id: str, limit: int = 5):
    """Retrieves top behavioral facts for context injection."""
    response = supabase.table("memory_facts").select("fact_text").eq("user_id", user_id).limit(limit).execute()
    return [fact['fact_text'] for fact in response.data]

# database.py - Add these to your existing file

def get_user_history(user_id: str):
    """
    Fetches the user's longitudinal health context from memory_facts and daily_logs.
    Pradnya will use this to ground the agent in the user's reality.
    """
    # Get behavioral insights from our stored memory facts
    facts = supabase.table("memory_facts").select("fact_text") \
        .eq("user_id", user_id).eq("category", "behavioral").execute()
    
    # Get the last 5 logs to understand what the user has been up to
    logs = supabase.table("daily_logs").select("log_entry") \
        .eq("user_id", user_id).order("created_at", desc=True).limit(5).execute()
    
    return {
        "behavioral_facts": [f['fact_text'] for f in facts.data],
        "recent_logs": [l['log_entry'] for l in logs.data]
    }

def get_clinical_rag(query: str):
    """
    Performs vector similarity search on our clinical guidelines (ICMR/ADA/WHO).
    Falls back to keyword-based search if RPC function is not available.
    """
    try:
        # Try vector similarity search via RPC
        model = _get_embedding_model()
        if model is None:
            raise Exception("Embedding model not available")
        query_embedding = model.encode(query).tolist()
        
        response = supabase.rpc(
            "match_clinical_facts", 
            {"query_embedding": query_embedding, "match_threshold": 0.5, "match_count": 3}
        ).execute()
        
        if response.data:
            return [r['fact_text'] for r in response.data]
    except Exception as e:
        print(f"Vector RAG fallback (RPC unavailable): {e}")
    
    # Fallback: keyword-based search on clinical memory_facts
    try:
        keywords = query.lower().split()
        # Fetch recent clinical facts and filter by keyword overlap
        response = supabase.table("memory_facts").select("fact_text") \
            .eq("category", "clinical").limit(20).execute()
        
        if response.data:
            all_facts = [r['fact_text'] for r in response.data]
            # Simple keyword matching
            matched = []
            for fact in all_facts:
                fact_lower = fact.lower()
                if any(kw in fact_lower for kw in keywords):
                    matched.append(fact)
                    if len(matched) >= 3:
                        break
            if matched:
                return matched
            # If no keyword match, return top 3 clinical facts
            return all_facts[:3]
    except Exception as e:
        print(f"Keyword RAG fallback error: {e}")
    
    return []

# --- 4. User Registration ---

def create_user(user_data: dict):
    """
    Creates a new user with their health profile in the database.
    Returns the created user data with user_id.
    """
    import uuid
    
    # Generate a new UUID for the user
    user_id = str(uuid.uuid4())
    
    # Calculate BMI
    height = float(user_data.get('height', 170))
    weight = float(user_data.get('weight', 70))
    
    # Check if height is in meters (less than 3) or cm (greater than 100)
    if height < 3:
        # Height is already in meters
        height_m = height
    else:
        # Height is in cm, convert to meters
        height_m = height / 100
    
    bmi = round(weight / (height_m ** 2), 1)
    
    # Validate BMI is in reasonable range (15-50)
    if bmi < 15 or bmi > 50:
        print(f"Warning: Calculated BMI {bmi} is outside normal range. Height: {height}, Weight: {weight}")
        # Recalculate with default values if BMI is unreasonable
        bmi = round(weight / ((1.7) ** 2), 1)
    
    # Map activity level to boolean
    activity_level = user_data.get('activityLevel', 'sedentary')
    is_active = activity_level in ['moderately', 'very']
    
    # Map smoking to boolean
    smoking = user_data.get('smoking', 'No') in ['Yes', 'Occasionally']
    
    # Map family history (default to False for now)
    family_hx_diabetes = False
    hypertension = False
    
    # Insert into twin_state table
    twin_state_data = {
        "user_id": user_id,
        "name": user_data.get('name', ''),
        "age": int(user_data.get('age', 22)),
        "gender": user_data.get('sex', 'male'),
        "height": int(user_data.get('height', 170)),
        "weight": int(user_data.get('weight', 70)),
        "bmi": bmi,
        "smoker": smoking,
        "physically_active": is_active,
        "on_bp_meds": False,
        "total_chol": 180,  # Default, should be updated with real data
        "hdl": 45,          # Default, should be updated with real data
        "sbp": 130,         # Default, should be updated with real data
        "family_hx_diabetes": family_hx_diabetes,
        "hypertension": hypertension,
        "risk_scores": {},
        "confidence_levels": {},
        "active_alerts": []
    }
    
    response = supabase.table("twin_state").insert(twin_state_data).execute()
    
    # Add initial behavioral memory facts
    behavioral_facts = [
        f"User is {activity_level} active",
        f"User smoking status: {user_data.get('smoking', 'No')}",
        f"User drinking status: {user_data.get('drinking', 'No')}",
    ]
    
    for fact in behavioral_facts:
        add_memory_fact(user_id, fact, "behavioral")
    
    return {"user_id": user_id, **twin_state_data}

def log_daily_activity(user_id: str, log_entry: str, log_type: str = "general", metadata: dict = None):
    """
    Logs a daily activity entry (meals, exercise, etc.) to the daily_logs table.
    """
    insert_data = {
        "user_id": user_id,
        "log_entry": log_entry,
        "log_type": log_type,
    }
    if metadata:
        insert_data["metadata"] = metadata
    return supabase.table("daily_logs").insert(insert_data).execute()


# --- 5. Wearable Data Management ---

def get_wearable_data(user_id: str, data_type: str = None, days: int = 7) -> list:
    """Fetch wearable data from database.
    
    Args:
        user_id: User UUID
        data_type: Filter by type ('steps', 'heart_rate', 'sleep', etc.) or None for all
        days: Number of days to look back (default 7)
    """
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = supabase.table("wearable_data").select("*").eq("user_id", user_id)
    
    if data_type:
        query = query.eq("data_type", data_type)
    
    query = query.gte("timestamp", cutoff_date).order("timestamp", desc=True)
    
    response = query.execute()
    return response.data if response.data else []

def get_latest_wearable_data(user_id: str, data_type: str) -> dict:
    """Get the most recent wearable data point for a specific type."""
    response = supabase.table("wearable_data").select("*") \
        .eq("user_id", user_id) \
        .eq("data_type", data_type) \
        .order("timestamp", desc=True) \
        .limit(1) \
        .execute()
    
    if response.data:
        return response.data[0]
    return None

def get_wearable_connection_status(user_id: str) -> dict:
    """Check if user has connected Google Fit."""
    response = supabase.table("wearable_tokens").select("*").eq("user_id", user_id).execute()
    
    if not response.data:
        return {"connected": False, "provider": None}
    
    token_data = response.data[0]
    return {
        "connected": True,
        "provider": token_data.get("provider"),
        "last_sync": token_data.get("updated_at")
    }

def save_manual_health_data(user_id: str, data_type: str, value: dict):
    """Save manually logged health data (from chat) to wearable_data table."""
    from datetime import datetime
    
    entry = {
        "user_id": user_id,
        "data_type": data_type,
        "value": value,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    response = supabase.table("wearable_data").insert(entry).execute()
    return response.data[0] if response.data else None