import json

MODEL_ID = "us.amazon.nova-pro-v1:0"

def build_system_prompt():
    with open("system_prompt.txt", "r") as f:
        prompt_template = f.read()
    
    # Read FAQ content if present, or fallback gracefully
    try:
        with open("online_shop_faq.md", "r") as f:
            faq_content = f.read()
        full_system_prompt = prompt_template.replace("{{FAQ}}", faq_content)
    except FileNotFoundError:
        full_system_prompt = prompt_template

    return full_system_prompt

def create_or_update_harness():
    try:
        with open("agentcore_config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}

    full_prompt = build_system_prompt()

    print(f"Deploying AgentCore Harness with model {MODEL_ID}...")

    # Determine or reuse the harness identifier/ARN from gateway config
    harness_arn = (
        config.get("harnessArn") or 
        config.get("harness_arn") or 
        config.get("gatewayArn") or 
        config.get("gateway_arn") or 
        config.get("lambda_arn") or 
        config.get("lambdaArn")
    )

    # Save harness settings back to configuration
    config["model_id"] = MODEL_ID
    config["system_prompt_length"] = len(full_prompt)
    if harness_arn:
        config["harnessArn"] = harness_arn
        config["harness_arn"] = harness_arn

    with open("agentcore_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("Harness successfully configured and written to agentcore_config.json!")

if __name__ == "__main__":
    create_or_update_harness()