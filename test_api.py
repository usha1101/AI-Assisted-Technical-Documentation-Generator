import requests
import json

# The code we want to document
code_to_document = """
def process_user_data(user_list):
    valid_users = []
    for user in user_list:
        if user.get("is_active"):
            valid_users.append(user["name"])
    return valid_users
"""

payload = {"source_code": code_to_document}

print("Sending code to AI...")
try:
    response = requests.post("http://127.0.0.1:8000/generate-docs", json=payload)

    if response.status_code == 200:
        data = response.json()
        print("\n--- AI SUCCESS ---")
        for item in data["results"]:
            print(f"Function: {item['entity_name']}")
            print(f"Generated Docstring: {item['generated_docstring']}")
            print("-" * 30)
    else:
        print("Error:", response.text)
except Exception as e:
    print("Connection refused. Is the server running? Error:", e)
