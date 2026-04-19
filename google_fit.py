import os
import hashlib
import base64
import secrets
import urllib.parse
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
import requests as http_requests
from database import supabase

load_dotenv()

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# Google Fit Scopes
SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/fitness.body.read',
    'https://www.googleapis.com/auth/fitness.heart_rate.read',
    'https://www.googleapis.com/auth/fitness.sleep.read',
]

# In-memory PKCE storage
_pkce_store = {}

def _generate_pkce():
    """Generate PKCE code_verifier and code_challenge."""
    code_verifier = secrets.token_urlsafe(32)
    code_challenge_raw = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge_raw).rstrip(b'=').decode('utf-8')
    return code_verifier, code_challenge

def get_auth_url(user_id: str) -> str:
    """Generate Google OAuth authorization URL with PKCE."""
    print(f"Generating auth URL for user: {user_id}")
    
    # Generate PKCE pair
    code_verifier, code_challenge = _generate_pkce()
    _pkce_store[user_id] = code_verifier
    print(f"PKCE: code_verifier stored for user {user_id}")
    
    # Build authorization URL with proper encoding
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'access_type': 'offline',
        'include_granted_scopes': 'true',
        'prompt': 'consent',
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/auth?{urllib.parse.urlencode(params)}"
    print(f"Generated auth URL: {auth_url[:80]}...")
    return auth_url

def exchange_code_for_tokens(code: str, user_id: str) -> dict:
    """Exchange authorization code for access and refresh tokens using direct HTTP request."""
    print(f"Exchanging code for tokens - user: {user_id}")
    
    # Get stored code verifier
    code_verifier = _pkce_store.pop(user_id, None)
    if code_verifier:
        print(f"Found PKCE code_verifier for user {user_id}")
    else:
        print("WARNING: No code_verifier found - trying without PKCE")
    
    try:
        # Direct HTTP request to Google's token endpoint
        token_data = {
            'code': code,
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'redirect_uri': GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code',
        }
        
        if code_verifier:
            token_data['code_verifier'] = code_verifier
        
        response = http_requests.post(
            'https://oauth2.googleapis.com/token',
            data=token_data
        )
        
        print(f"Token response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Token error response: {response.text}")
            return {"success": False, "error": f"Token exchange failed: {response.text}"}
        
        token_json = response.json()
        access_token = token_json.get('access_token')
        refresh_token = token_json.get('refresh_token')
        expires_in = token_json.get('expires_in', 3600)
        
        print(f"Got tokens - access: {access_token[:20]}..., refresh: {refresh_token[:20] if refresh_token else 'None'}...")
        
        # Save tokens to database
        db_token_data = {
            "user_id": user_id,
            "provider": "google_fit",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat(),
        }
        
        # Check if token exists, update or insert
        existing = supabase.table("wearable_tokens").select("*").eq("user_id", user_id).execute()
        if existing.data:
            supabase.table("wearable_tokens").update(db_token_data).eq("user_id", user_id).execute()
            print("Updated existing token in DB")
        else:
            supabase.table("wearable_tokens").insert(db_token_data).execute()
            print("Inserted new token in DB")
        
        return {"success": True, "message": "Tokens saved successfully"}
    except Exception as e:
        print(f"Token exchange error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def get_wearable_token(user_id: str) -> dict:
    """Get wearable token from database."""
    response = supabase.table("wearable_tokens").select("*").eq("user_id", user_id).execute()
    if not response.data:
        return None
    return response.data[0]

def refresh_access_token(user_id: str) -> str:
    """Refresh access token using refresh token."""
    token_data = get_wearable_token(user_id)
    if not token_data:
        raise Exception("No token found for user")
    
    # Use Google's token endpoint to refresh
    response = http_requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": token_data["refresh_token"],
            "grant_type": "refresh_token",
        }
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to refresh token: {response.text}")
    
    new_token_data = response.json()
    
    # Update database
    supabase.table("wearable_tokens").update({
        "access_token": new_token_data["access_token"],
        "expires_at": (datetime.utcnow() + timedelta(seconds=new_token_data["expires_in"])).isoformat(),
    }).eq("user_id", user_id).execute()
    
    return new_token_data["access_token"]

def get_valid_token(user_id: str) -> str:
    """Get valid access token, refresh if needed."""
    token_data = get_wearable_token(user_id)
    if not token_data:
        raise Exception("No token found for user")
    
    # Check if token is expired
    expires_at = token_data["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    # Make both offset-aware for comparison
    from datetime import timezone
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now >= expires_at:
        return refresh_access_token(user_id)
    
    return token_data["access_token"]

def fetch_steps(user_id: str, days: int = 7) -> list:
    """Fetch step count data from Google Fit."""
    access_token = get_valid_token(user_id)
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    service = build('fitness', 'v1', credentials=Credentials(token=access_token))
    
    try:
        response = service.users().dataset().aggregate(
            userId='me',
            body={
                "aggregateBy": [{"dataTypeName": "com.google.step_count.delta"}],
                "bucketByTime": {"durationMillis": 86400000},
                "startTimeMillis": int(start_time.timestamp() * 1000),
                "endTimeMillis": int(end_time.timestamp() * 1000)
            }
        ).execute()
        
        print(f"Steps API response buckets: {len(response.get('bucket', []))}")
        
        steps_data = []
        for bucket in response.get('bucket', []):
            start = datetime.fromtimestamp(bucket['startTimeMillis'] / 1000)
            steps = 0
            for dataset in bucket.get('dataset', []):
                for point in dataset.get('point', []):
                    for value in point.get('value', []):
                        steps += value.get('intVal', 0)
            
            if steps > 0:
                steps_data.append({
                    "date": start.strftime('%Y-%m-%d'),
                    "steps": steps
                })
        
        print(f"Steps data parsed: {steps_data}")
        return steps_data
    except Exception as e:
        print(f"Error fetching steps: {e}")
        import traceback
        traceback.print_exc()
        return []

def fetch_heart_rate(user_id: str, days: int = 7) -> list:
    """Fetch heart rate data from Google Fit."""
    access_token = get_valid_token(user_id)
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    service = build('fitness', 'v1', credentials=Credentials(token=access_token))
    
    try:
        response = service.users().dataset().aggregate(
            userId='me',
            body={
                "aggregateBy": [{"dataTypeName": "com.google.heart_rate.bpm"}],
                "bucketByTime": {"durationMillis": 86400000},
                "startTimeMillis": int(start_time.timestamp() * 1000),
                "endTimeMillis": int(end_time.timestamp() * 1000)
            }
        ).execute()
        
        print(f"Heart rate API response buckets: {len(response.get('bucket', []))}")
        
        hr_data = []
        for bucket in response.get('bucket', []):
            start = datetime.fromtimestamp(bucket['startTimeMillis'] / 1000)
            avg_hr = 0
            count = 0
            for dataset in bucket.get('dataset', []):
                for point in dataset.get('point', []):
                    for value in point.get('value', []):
                        avg_hr += value.get('fpVal', 0)
                        count += 1
            
            if count > 0:
                hr_data.append({
                    "date": start.strftime('%Y-%m-%d'),
                    "bpm": round(avg_hr / count)
                })
        
        print(f"Heart rate data parsed: {hr_data}")
        return hr_data
    except Exception as e:
        print(f"Error fetching heart rate: {e}")
        import traceback
        traceback.print_exc()
        return []

def fetch_sleep(user_id: str, days: int = 7) -> list:
    """Fetch sleep data from Google Fit."""
    access_token = get_valid_token(user_id)
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    service = build('fitness', 'v1', credentials=Credentials(token=access_token))
    
    try:
        response = service.users().dataset().aggregate(
            userId='me',
            body={
                "aggregateBy": [{"dataTypeName": "com.google.sleep.segment"}],
                "bucketByTime": {"durationMillis": 86400000},
                "startTimeMillis": int(start_time.timestamp() * 1000),
                "endTimeMillis": int(end_time.timestamp() * 1000)
            }
        ).execute()
        
        print(f"Sleep API response buckets: {len(response.get('bucket', []))}")
        
        sleep_data = []
        for bucket in response.get('bucket', []):
            start = datetime.fromtimestamp(bucket['startTimeMillis'] / 1000)
            sleep_duration = 0
            for dataset in bucket.get('dataset', []):
                for point in dataset.get('point', []):
                    start_nanos = point.get('startTimeNanos', 0)
                    end_nanos = point.get('endTimeNanos', 0)
                    duration_seconds = (end_nanos - start_nanos) / 1e9
                    sleep_duration += duration_seconds / 3600
            
            if sleep_duration > 0:
                sleep_data.append({
                    "date": start.strftime('%Y-%m-%d'),
                    "hours": round(sleep_duration, 2)
                })
        
        print(f"Sleep data parsed: {sleep_data}")
        return sleep_data
    except Exception as e:
        print(f"Error fetching sleep: {e}")
        import traceback
        traceback.print_exc()
        return []

def save_wearable_data(user_id: str, data_type: str, data: list):
    """Save wearable data to database."""
    for item in data:
        # Convert date string to timestamp
        date_str = item.get("date")
        if date_str:
            timestamp = datetime.strptime(date_str, "%Y-%m-%d").isoformat()
        else:
            timestamp = datetime.utcnow().isoformat()
        
        supabase.table("wearable_data").insert({
            "user_id": user_id,
            "data_type": data_type,
            "value": item,
            "timestamp": timestamp
        }).execute()

def sync_all_data(user_id: str) -> dict:
    """Sync all wearable data from Google Fit."""
    print(f"--- SYNCING DATA FOR USER: {user_id} ---")
    try:
        print("Fetching steps...")
        steps = fetch_steps(user_id)
        print(f"Steps data: {steps}")
        
        print("Fetching heart rate...")
        heart_rate = fetch_heart_rate(user_id)
        print(f"Heart rate data: {heart_rate}")
        
        print("Fetching sleep...")
        sleep = fetch_sleep(user_id)
        print(f"Sleep data: {sleep}")
        
        print("Saving to database...")
        save_wearable_data(user_id, "steps", steps)
        save_wearable_data(user_id, "heart_rate", heart_rate)
        save_wearable_data(user_id, "sleep", sleep)
        
        print(f"Sync complete: {len(steps)} steps, {len(heart_rate)} heart rate, {len(sleep)} sleep records")
        
        return {
            "success": True,
            "steps": len(steps),
            "heart_rate": len(heart_rate),
            "sleep": len(sleep)
        }
    except Exception as e:
        print(f"Error syncing data: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

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

