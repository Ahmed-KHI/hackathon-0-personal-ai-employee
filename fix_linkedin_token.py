"""
Quick fix: Add person_id to LinkedIn token
"""
import json
from pathlib import Path

token_file = Path("secrets/linkedin_token.json")

with open(token_file, 'r') as f:
    data = json.load(f)

# Extract person_id from id_token (it's in the 'sub' claim)
import base64
id_token = data['id_token']
parts = id_token.split('.')
payload = parts[1]

# Add padding if needed
padding = 4 - len(payload) % 4
if padding != 4:
    payload += '=' * padding

try:
    decoded = json.loads(base64.b64decode(payload))
    person_id = decoded['sub']  # Hvhj7UPcNv
    
    data['person_id'] = person_id
    
    with open(token_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Added person_id: {person_id}")
except Exception as e:
    print(f"❌ Error: {e}")
    # Manually add from previous session
    data['person_id'] = 'Hvhj7UPcNv'
    with open(token_file, 'w') as f:
        json.dump(data, f, indent=2)
    print("✅ Added person_id manually: Hvhj7UPcNv")
