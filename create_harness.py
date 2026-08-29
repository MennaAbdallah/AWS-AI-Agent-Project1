import json
import boto3

REGION = "us-east-1"
MODEL_ID = "us.amazon.nova-pro-v1:0"

def build_system_prompt():
    with open("system_prompt.txt", "r") as f:
        prompt_template = f.read()
    with open("online_shop_faq.md", "r") as f:
        faq_content = f.read()

    full_system_prompt = prompt_template.replace("{{FAQ}}", faq_content)
    return full_system_prompt

def create_or_update_harness():
    with open("agentcore_config.json", "r") as f:
        config = json.load(f)

    full_prompt = build_system_prompt()
    bedrock_agentcore = boto3.client("bedrock-agentcore", region_name=REGION)

    harness_name = "CustomerSupportHarness"
    print(f"Deploying AgentCore Harness with model {MODEL_ID}...")

    target_arn = config["targetArn"]
    harness_role_arn = config["harnessRoleArn"]

    existing_harness_arn = config.get("harnessArn")

    if existing_harness_arn:
        print(f"Updating existing harness ARN: {existing_harness_arn}...")
        res = bedrock_agentcore.update_harness(
            harnessArn=existing_harness_arn,
            description="Stateful customer support chatbot harness",
            modelId=MODEL_ID,
            roleArn=harness_role_arn,
            instruction=full_prompt,
            gatewayTargets=[{"targetArn": target_arn}]
        )
        harness_arn = res["harnessArn"]
        harness_id = res["harnessId"]
    else:
        try:
            res = bedrock_agentcore.create_harness(
                name=harness_name,
                description="Stateful customer support chatbot harness",
                modelId=MODEL_ID,
                roleArn=harness_role_arn,
                instruction=full_prompt,
                gatewayTargets=[{"targetArn": target_arn}]
            )
            harness_arn = res["harnessArn"]
            harness_id = res["harnessId"]
        except bedrock_agentcore.exceptions.ResourceAlreadyExistsException:
            harnesses = bedrock_agentcore.list_harnesses()["harnesses"]
            h = next(item for item in harnesses if item["name"] == harness_name)
            harness_arn = h["harnessArn"]
            harness_id = h["harnessId"]
            
            res = bedrock_agentcore.update_harness(
                harnessArn=harness_arn,
                description="Stateful customer support chatbot harness",
                modelId=MODEL_ID,
                roleArn=harness_role_arn,
                instruction=full_prompt,
                gatewayTargets=[{"targetArn": target_arn}]
            )

    config["harnessArn"] = harness_arn
    config["harnessId"] = harness_id
    config["modelId"] = MODEL_ID

    with open("agentcore_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print(f"Harness successfully configured. Harness ARN: {harness_arn}")

if __name__ == "__main__":
    create_or_update_harness()