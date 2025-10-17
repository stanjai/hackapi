import os
from openai import OpenAI
from typing import List, Dict
import json
import re
import sys

# --- Configuration ---
# Your API key remains set as OPENAI_API_KEY
client = OpenAI()

# 1. Dictionary defining the specialized role and custom instruction for each software
SOFTWARE_INSTRUCTIONS = {
    "Senso": "Use the Senso API to send a 'pipeline_start' event with initial parameters.",
    "Airia": "Utilize Airia's service to analyze the Redpanda stream data and store the aggregated results.",
    "OpenAI": "Generate text embeddings for a data payload and use Chat Completions for final summary generation.",
    "TrueFoundry": "Load a deployed TrueFoundry ML model and make a prediction on a clean data sample.",
    "ElevenLabs": "Convert a final text summary (from OpenAI/Airia) into a temporary audio file (e.g., MP3).",
    "Intercom": "Search for a contact based on an identifier and send a personalized message to them.",
    "Snowflake": "Execute a basic SQL SELECT query to retrieve initial configuration data.",
    "Lightfield": "Simulate processing a fetched image file (e.g., cropping or applying a filter) before storage.",
    "Redpanda": "Set up a producer to stream structured data records and a consumer to read them.",
    "Sentry": "Wrap a core business logic function in Sentry's SDK to capture and monitor any exceptions.",
    "StackAI": "Trigger a defined StackAI workflow via its API to process a complex data object.",
    "Apify": "Start an Apify web scraping actor, wait for its completion, and retrieve the final dataset.",
}


def generate_integrated_code_streaming_custom(
    apis_to_use: List[str],
    existing_code_string: str,
    all_instructions: Dict[str, str],
    model_name: str = "gpt-5"
) -> str:
    """
    Generates integrated code using specific instructions for each requested API.
    """
    # 2. Function to build the context for the model
    def build_prompt_context(api_list: List[str], instructions: Dict[str, str]) -> str:
        context = ["Available Software and Required Usage:"]
        for api in api_list:
            instruction = instructions.get(api, f"Implement basic API calls for {api}.")
            context.append(f"- **{api}**: {instruction}")
        return "\n".join(context)

    # Filter instructions to only include the ones the user wants to use
    context_block = build_prompt_context(apis_to_use, all_instructions)
    api_names_str = ", ".join(apis_to_use)

    # 3. Enhanced System Prompt
    system_prompt = (
        "You are a highly verbose Python Software Architect specializing in hackathon workflows. "
        "Your task is to generate one single, complete, production-quality Python script. "
        "**Implement the main function to demonstrate a sequential, integrated workflow** "
        f"that uses ALL of the requested APIs in a logical chain ({api_names_str}). "
        "Use the specific instructions provided below as your implementation guide. "
        "Include robust error handling, detailed docstrings, and placeholder environment variables. "
        f"\n\n{context_block}\n\n"
        "You **MUST** return ONLY the complete Python code as a single string, "
        "wrapped in a single markdown code block (```python...```). Do not include any other text."
    )

    user_prompt = (
        f"The existing base code is: \n\n```python\n{existing_code_string}\n```\n\n"
        "Using this base, generate the final, integrated script."
    )

    full_response_text = ""
    print("\n--- Model is working (output streaming in real-time) ---")
    
    try:
        response_stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=True 
        )
        
        for chunk in response_stream:
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)
                full_response_text += content
        
        print("\n\n--- Streaming complete. Beginning final code extraction... ---")

        code_match = re.search(r"```python\n(.*)```", full_response_text, re.DOTALL)
        
        if code_match:
            return code_match.group(1).strip()
        else:
            return f"ERROR: Could not find or extract the Python code block. Raw output:\n{full_response_text}"

    except Exception as e:
        return f"An API error occurred: {e}"

# --- Example Usage (Using a powerful subset of 6 APIs for a clear workflow) ---
# Scenario: Scrape data -> Stream -> Analyze -> Store in DB -> Notify -> Log errors
apis_to_use_example = ["Apify", "Redpanda", "Airia", "Snowflake", "ElevenLabs", "Sentry"]

initial_python_code = """
import json
import os
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_integrated_pipeline():
    logging.info("Starting integrated data pipeline...")
    # New logic will be added here
    logging.info("Pipeline executed successfully.")

if __name__ == "__main__":
    run_integrated_pipeline()
"""

# Get the code suggestion
suggested_code = generate_integrated_code_streaming_custom(
    apis_to_use_example, 
    initial_python_code,
    SOFTWARE_INSTRUCTIONS
)

print("\n--- Final Extracted Code ---")
print(suggested_code)
print("----------------------------\n")