import json
import argparse

def generate_jsonl(tests_json_path, output_jsonl_path):
    print(f"Reading test cases from {tests_json_path}...")
    
    with open(tests_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Handle whether flow-tests.json is a list or a dictionary object
    if isinstance(data, list):
        tests = data
        flow_input_node = "Flow input"
    else:
        flow_input_node = data.get("flowInputNode", {}).get("nodeName", "Flow input")
        tests = data.get("tests", [])
    
    print(f"Found {len(tests)} test cases targeting node: '{flow_input_node}'")
    
    with open(output_jsonl_path, 'w', encoding='utf-8') as out_f:
        for test in tests:
            eval_record = {
                "evalDatasetRecordId": test.get("id"),
                "prompt": test.get("prompt"),
                "referenceResponse": test.get("expected")
            }
            out_f.write(json.dumps(eval_record) + '\n')
            
    print(f"Successfully generated evaluation dataset at: {output_jsonl_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate JSONL dataset for Bedrock Flow evaluation.")
    parser.add_argument("--tests-json", default="flow-tests.json", help="Path to the flow-tests.json file")
    parser.add_argument("--output", default="eval-dataset.jsonl", help="Path to output JSONL file")
    
    args = parser.parse_args()
    generate_jsonl(args.tests_json, args.output)