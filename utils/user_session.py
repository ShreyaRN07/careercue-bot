user_sessions = {}
_shown_instructions = set()

def start_session(user_id):
    user_sessions[user_id] = {"json_file": None, "job_type": None, "location": None}

def update_session(user_id, key, value):
    if user_id in user_sessions:
        user_sessions[user_id][key] = value

def get_session(user_id):
    return user_sessions.get(user_id)

def clear_session(user_id):
    if user_id in user_sessions:
        del user_sessions[user_id]

# Instruction UI helpers
def mark_instructions_shown(user_id):
    _shown_instructions.add(user_id)

def has_shown_instructions(user_id):
    return user_id in _shown_instructions
