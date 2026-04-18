import os
from typing import TypedDict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from dotenv import load_dotenv

# LangGraph imports
from langgraph.graph import StateGraph, END

# Import your other files
from sentiment import get_stress_context
from prompts import SYSTEM_GUIDE

load_dotenv()
app = FastAPI()

# CORS configuration for Prachi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- 1. LANGGRAPH STATE DEFINITION ---
class TwinState(TypedDict):
    user_message: str
    emotion_data: dict
    ai_final_reply: str

# --- 2. THE AGENT NODES ---

def triage_agent(state: TwinState):
    """Agent 1: Checks the mood and stress levels."""
    print("--- [A2A] Agent 1: Triage analyzing message ---")
    stress_results = get_stress_context(state["user_message"])
    return {"emotion_data": stress_results}

def clinical_twin_agent(state: TwinState):
    """Agent 2: Reasons using Clinical Guidelines and User Bio."""
    print("--- [A2A] Agent 2: Twin generating response ---")
    
    mock_bio = "22yo Engineering Student, History of high caffeine intake."
    mock_rag = "WHO guidelines suggest limiting caffeine if heart rate exceeds 100bpm."
    
    final_prompt = SYSTEM_GUIDE.format(
        user_context=mock_bio,
        rag_chunks=mock_rag,
        stress_info=state["emotion_data"]
    )
    
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": final_prompt},
            {"role": "user", "content": state["user_message"]}
        ],
        model="llama-3.3-70b-versatile",
    )
    
    return {"ai_final_reply": chat_completion.choices[0].message.content}

def emergency_alert_agent(state: TwinState):
    """Agent 4: Handles critical safety warnings."""
    print("--- [A2A] Agent 4: Emergency Alert Triggered! ---")
    emergency_msg = (
        "⚠️ EMERGENCY DETECTED: Your symptoms or stress levels suggest a critical risk. "
        "Please stop what you are doing, prioritize rest, and seek medical attention if pain persists. "
        "I have flagged this for your clinical record."
    )
    return {"ai_final_reply": emergency_msg}

# --- 3. CONDITIONAL ROUTING LOGIC ---

def route_emergency(state: TwinState):
    """Decider: Routes to Emergency Agent or Clinical Twin."""
    print("--- [A2A] Routing Decision ---")
    data = state.get("emotion_data", {})
    
    # Logic: High stress score OR keywords in message
    is_high_stress = data.get("stress_score", 0) > 0.8
    msg_lower = state["user_message"].lower()
    has_pain_keywords = any(word in msg_lower for word in ["pain", "hurt", "emergency", "dying", "racing"])

    if is_high_stress or has_pain_keywords:
        return "emergency"
    return "normal"

# --- 4. WIRING THE GRAPH ---

workflow = StateGraph(TwinState)

# Define Nodes
workflow.add_node("triage", triage_agent)
workflow.add_node("clinical_twin", clinical_twin_agent)
workflow.add_node("emergency_alert", emergency_alert_agent)

# Define Logic Flow
workflow.set_entry_point("triage")

workflow.add_conditional_edges(
    "triage",
    route_emergency,
    {
        "emergency": "emergency_alert",
        "normal": "clinical_twin"
    }
)

workflow.add_edge("emergency_alert", END)
workflow.add_edge("clinical_twin", END)

# Compile
twin_brain = workflow.compile()

# --- 5. FASTAPI ENDPOINTS ---

@app.get("/")
def home():
    return {"status": "Backend live with LangGraph & Autonomous Routing"}

@app.post("/api/chat")
async def chat(payload: dict):
    print("--- API REQUEST RECEIVED ---")
    try:
        user_msg = payload.get("message")
        initial_input = {"user_message": user_msg}
        final_state = twin_brain.invoke(initial_input)
        
        return {
            "reply": final_state["ai_final_reply"],
            "emotion": final_state["emotion_data"]['emotion']
        }
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        return {"error": "Internal Server Error", "details": str(e)}

# --- 6. MANUAL TEST BLOCK (Commented Out) ---
#if __name__ == "__main__":
    # This only runs if you type 'python main.py'
 #   print("--- RUNNING MANUAL GRAPH TEST ---")
 #   test_state = {"user_message": "i feel tired can you check my sleep data?."}
 #   result = twin_brain.invoke(test_state)
  #  print("Final AI Reply:", result["ai_final_reply"])