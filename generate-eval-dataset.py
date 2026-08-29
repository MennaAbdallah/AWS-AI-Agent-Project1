import argparse
import json
import boto3

REGION = "us-east-1"
DEFAULT_MODEL_IDENTIFIER = "my-support-chatbot"

def generate_dataset(tests_json_path, output_jsonl_path):
    with open("agentcore_config.json", "r") as f:
        config = json.load(f)

    harness_arn = config["harnessArn"]
    runtime_client = boto3.client("bedrock-agentcore-runtime", region_name=REGION)

    with open(tests_json_path, "r") as f:
        test_suite = json.load(f)

    eval_records = []
    print(f"Running evaluation dataset generation against harness {harness_arn}...")

    for test in test_suite.get("tests", []):
        test_id = test["id"]
        prompt_text = test["prompt"]
        expected_text = test["expected"]
        
        session_id = f"eval-session-{test_id}"
        print(f"Executing Test ID: {test_id}...")

        try:
            res = runtime_client.invoke_harness(
                harnessArn=harness_arn,
                runtimeSessionId=session_id,
                inputText=prompt_text
            )
            actual_response = res.get("outputText", "").strip()
        except Exception as err:
            print(f"Error executing test {test_id}: {err}")
            actual_response = f"[HARNESS_ERROR] Failed to invoke harness: {str(err)}"

        record = {
            "prompt": prompt_text,
            "referenceResponse": expected_text,
            "modelResponses": [
                {
                    "response": actual_response,
                    "modelIdentifier": DEFAULT_MODEL_IDENTIFIER
                }
            ]
        }
        eval_records.append(record)
        print(f"wrote eval line for {test_id}")

    with open(output_jsonl_path, "w") as f:
        for rec in eval_records:
            f.write(json.dumps(rec) + "\n")

    print(f"\nDataset generation complete. Written {len(eval_records)} records to {output_jsonl_path}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Bedrock Evaluations Dataset")
    parser.add_argument("--tests-json", default="harness-tests.json", help="Path to input test suite JSON")
    parser.add_argument("--output-jsonl", default="output_eval_dataset.jsonl", help="Path to output JSONL file")
    args = parser.parse_args()

    generate_dataset(args.tests_json, args.output_jsonl)