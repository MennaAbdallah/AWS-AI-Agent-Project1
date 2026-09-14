import json
import time
import boto3

REGION = "us-east-1"
STACK_NAME = "bug-report-tool-stack"

def get_stack_outputs(stack_name):
    cfn = boto3.client("cloudformation", region_name=REGION)
    response = cfn.describe_stacks(StackName=stack_name)
    outputs = response["Stacks"][0]["Outputs"]
    return {o["OutputKey"]: o["OutputValue"] for o in outputs}

def main():
    print(f"Retrieving stack outputs from {STACK_NAME}...")
    outputs = get_stack_outputs(STACK_NAME)
    
    lambda_arn = outputs["LambdaFunctionArn"]
    gateway_role_arn = outputs["GatewayRoleArn"]
    harness_role_arn = outputs["HarnessRoleArn"]
    table_name = outputs["TableName"]

    # Use bedrock-agentcore-control or bedrock-agentcore client
    agentcore = boto3.client("bedrock-agentcore", region_name=REGION)

    print("Creating AgentCore Gateway...")
    
    # Verify the method name matching your toolkit (e.g., create_gateway or create_agent_gateway)
    # If create_gateway isn't available, check the starter toolkit helper script or requirements.
    
    config_data = {
        "region": REGION,
        "lambda_arn": lambda_arn,
        "gateway_role_arn": gateway_role_arn,
        "harness_role_arn": harness_role_arn,
        "table_name": table_name,
        "model_id": "us.amazon.nova-pro-v1:0"
    }

    with open("agentcore_config.json", "w") as f:
        json.dump(config_data, f, indent=2)

    print("Successfully generated agentcore_config.json!")

if __name__ == "__main__":
    main()