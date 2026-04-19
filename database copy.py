import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load your .env credentials
load_dotenv()

# Initialize the persistent Supabase connection
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

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
    Pradnya will use this to ground the agent in medical truth.
    """
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Embed the query
    query_embedding = model.encode(query).tolist()
    
    # Call the SQL RPC function you created earlier
    response = supabase.rpc(
        "match_clinical_facts", 
        {"query_embedding": query_embedding, "match_threshold": 0.5, "match_count": 3}
    ).execute()
    
    return [r['fact_text'] for r in response.data]