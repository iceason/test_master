import os
import json
import sys
from unittest.mock import MagicMock

# Add current directory to path
sys.path.append(os.getcwd())

from test_case_generator.field_generators import DatasetGenerator, LLMDataGenerator

# 1. Define a complex schema that benefits from semantic consistency
schema = {
    "type": "object",
    "properties": {
        "user_id": {"type": "integer"},
        "full_name": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "profile": {
            "type": "object",
            "properties": {
                "bio": {"type": "string", "description": "Short biography"},
                "interests": {"type": "array", "items": {"type": "string"}}
            }
        },
        "address": {
            "type": "object",
            "properties": {
                "street": {"type": "string"},
                "city": {"type": "string"},
                "country": {"type": "string"},
                "zip_code": {"type": "string"}
            }
        }
    }
}

def demo_with_mock_llm():
    print("\n🔹 Demo: Using Mock LLM to generate Semantic Seed Data")
    
    # Simulate an LLM response (Semantic Consistency!)
    mock_llm_response = {
        "user_id": 1001,
        "full_name": "Sarah Connor",
        "email": "sarah.connor@skynet-resistance.org",
        "profile": {
            "bio": "Leader of the resistance against the machines. Expert in survival and weapons.",
            "interests": ["Robotics", "Time Travel", "Fitness"]
        },
        "address": {
            "street": "123 Tech Blvd",
            "city": "Los Angeles",
            "country": "USA",
            "zip_code": "90001"
        }
    }
    
    # Mock the LLM Client
    llm_gen = LLMDataGenerator(api_key="mock-key")
    llm_gen.client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(mock_llm_response)
    llm_gen.client.chat.completions.create.return_value.choices = [mock_choice]
    
    # Instantiate DatasetGenerator with LLM
    dataset_gen = DatasetGenerator(llm_generator=llm_gen)
    
    # Generate Record
    record = dataset_gen.generate_record(schema)
    print(json.dumps(record, indent=2))
    
    # Verify semantic consistency (Simulated)
    if record["address"]["city"] == "Los Angeles" and record["address"]["zip_code"] == "90001":
        print("✅ Semantic Consistency Verified: City matches Zip Code (Mocked)")

def demo_fallback_rule_based():
    print("\n🔹 Demo: Fallback to Rule-based Generation (No LLM)")
    
    # Instantiate WITHOUT LLM
    dataset_gen = DatasetGenerator(llm_generator=None)
    
    # Generate Record
    record = dataset_gen.generate_record(schema)
    print(json.dumps(record, indent=2))
    
    # Note: Rule-based usually generates random independent data
    print("ℹ️ Note: Rule-based data is structurally valid but may lack semantic consistency.")

if __name__ == "__main__":
    demo_with_mock_llm()
    demo_fallback_rule_based()
