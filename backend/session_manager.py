## create a session: store session id inside the sessions list as a index
## add message: create session + append new content into the list (role, content, timestamp)
## get_session_history
## clear_session: del 
## session_exists

from datetime import datetime, timezone

sessions = {}

def create_session(session_id: str):
    if session_id not in sessions:
        sessions[session_id] = [];

def add_message(session_id: str, role: str, content: str):
    create_session(session_id)
    if content.strip():
        sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat() 
        })
    return sessions[session_id]

def session_exists(session_id: str):
    return session_id in sessions

def get_session_history(session_id: str):
    if session_exists(session_id):
        return sessions[session_id]
    return [] 

def clear_session(session_id: str):
    if session_exists(session_id):
        del sessions[session_id]
        return True 
    return False
    


