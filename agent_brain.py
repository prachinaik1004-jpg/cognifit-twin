import os
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from groq import Groq
from dotenv import load_dotenv

# Import your actual logic from earlier
from sentiment import get_stress_context
from prompts import SYSTEM_GUIDE

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 1. The State: This is what the agents "pass" to each other
class TwinState(TypedDict):
    user_message: str
    emotion_data: dict
    clinical_context: str
    ai_final_reply: str