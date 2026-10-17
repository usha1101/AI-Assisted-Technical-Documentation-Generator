import requests
import json
import os
from datetime import datetime

# 1. SETUP: Define the output directory and filename logic
RESULTS_DIR = "results"
SCRIPT_NAME = os.path.basename(__file__).replace(".py", "") # Gets 'run_complex_test'

# Ensure the results folder exists
os.makedirs(RESULTS_DIR, exist_ok=True)

# Generate timestamped filename
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
output_filename = f"{SCRIPT_NAME}_results_{timestamp}.txt"
output_path = os.path.join(RESULTS_DIR, output_filename)

# The complex code to test
complex_code = """
import time
import functools
from typing import List, Dict

def timer_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        res = func(*args, **kwargs)
        print(f"Time: {time.time() - start}")
        return res
    return wrapper

class FinancialAnalyzer:
    def __init__(self, market_data: Dict):
        self.market_data = market_data

    @timer_decorator
    def calculate_risk_index(self, threshold: float) -> str:
        risk_score = 0
        for asset, value in self.market_data.items():
            if value < 0:
                risk_score += (value ** 2)
            else:
                risk_score -= (value * 0.5)

        if risk_score > threshold:
            return "HIGH_RISK"
        elif risk_score > 0:
            return "MODERATE_RISK"
        else:
            return "SAFE"
"""

print(f"Sending code to AI... (Results will be saved to {output_path})")

try:
    response = requests.post(
        "http://127.0.0.1:8000/generate-docs", 
        json={"source_code": complex_code}
    )

    output_buffer = []

    if response.status_code == 200:
        data = response.json()
        
        # Build the output string
        output_buffer.append("="*50)
        output_buffer.append(f"AI DOCUMENTATION RESULTS - {timestamp}")
        output_buffer.append("="*50 + "\n")

        for item in data["results"]:
            output_buffer.append(f"[ Entity: {item['entity_name']} ({item['entity_type']}) ]")
            output_buffer.append("-" * 30)
            output_buffer.append(f"AI Explanation:\n{item['generated_docstring']}")
            output_buffer.append("-" * 30 + "\n")

        # Join everything into a single string
        final_output = "\n".join(output_buffer)

        # 2. OUTPUT: Print to Console AND Write to File
        print(final_output) 
        
        with open(output_path, "w") as f:
            f.write(final_output)
            
        print(f"\n[SUCCESS] Log file generated: {output_path}")

    else:
        print("Error:", response.text)

except Exception as e:
    print(f"Connection failed: {e}")
