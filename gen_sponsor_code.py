import os
from openai import OpenAI
from typing import List
import json
import re # We'll use this to safely extract the code block

# --- Configuration ---
# Your API key remains the same (set as OPENAI_API_KEY)
# We assume the key has access to the standard chat completions endpoint.

client = OpenAI()

def generate_multi_api_code_suggestion_fallback(
    api_list: List[str],
    existing_code_string: str,
    # **SWITCHING to a model that works with the standard Chat Completions endpoint**
    model_name: str = "gpt-5" # Fallback to standard GPT-5 or use "gpt-4o"
) -> str:
    """
    FALLBACK: Uses the standard Chat Completions API, which is more likely to be 
    enabled on a restricted API key, to achieve the same result.
    """
    if not api_list:
        return "Error: API list cannot be empty."

    api_names = ", ".join(f"'{api}'" for api in api_list)
    
    # SYSTEM Message - Note the emphasis on returning ONLY the code
    system_prompt = (
        "You are an expert Python developer specialized in API integration. "
        "Your task is to analyze the provided Python code and generate a complete, "
        "updated version of that code that demonstrates an integrated use case for "
        f"the following APIs: {api_names}. "
        "You **MUST** return only the complete Python code as a single string "
        "inside a single markdown code block. Do not include any preamble, "
        "explanation, or text outside of the code block."
    )

    user_prompt = (
        f"The existing code is: \n\n```python\n{existing_code_string}\n```\n\n"
        f"Using the existing code as a base, generate a new, complete Python script "
        f"that successfully integrates all of the following APIs: {api_names}. "
        "Ensure the generated code is syntactically correct and includes mock API keys "
        "or placeholders for environment variables."
    )

    try:
        # 1. Call the Chat Completions API (Legacy/Standard Endpoint)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            # Note: The reasoning_effort parameter is not supported here.
            # We rely on the model's inherent ability for complex tasks.
        )

        raw_output = response.choices[0].message.content
        
        # 2. Extract the code block safely using regex
        # This handles the model wrapping the code in ```python ... ```
        code_match = re.search(r"```python\n(.*)```", raw_output, re.DOTALL)
        
        if code_match:
            return code_match.group(1).strip()
        else:
            # If the model failed to wrap the code, return the raw output for review
            return raw_output

    except Exception as e:
        return f"An API error occurred on the FALLBACK endpoint: {e}"

# --- Example Usage (from your previous prompt) ---
apis_to_integrate = ["StackAI", "Twilio", "Google Sheets API"]
initial_python_code = """
import json
import requests

def run_workflow():
    print("Starting integration workflow...")
    # This is where the new API logic should be integrated
    return {"status": "success", "message": "Base code ran."}

if __name__ == "__main__":
    result = run_workflow()
    print(json.dumps(result, indent=4))
"""

# Try the fallback function
suggested_code = generate_multi_api_code_suggestion_fallback(apis_to_integrate, initial_python_code)

print("\n--- GPT-5/GPT-4o Code Suggestion (FALLBACK ENDPOINT) ---")
print(suggested_code)
print("----------------------------------------------------------\n")