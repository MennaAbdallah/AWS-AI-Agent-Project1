import json
import boto3

REGION = "us-east-1"

def cleanup():
    try:
        with open("agentcore_config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("agentcore_config.json not found. Nothing to clean up.")
        return

    bedrock_agentcore = boto3.client("bedrock-agentcore", region_name=REGION)

    harness_arn = config.get("harnessArn")
    gateway_id = config.get("gatewayId")
    target_arn = config.get("targetArn")

    if harness_arn:
        print(f"Deleting AgentCore Harness: {harness_arn}...")
        try:
            bedrock_agentcore.delete_harness(harnessArn=harness_arn)
            print("Harness deleted.")
        except Exception as e:
            print(f"Error deleting harness: {e}")

    if gateway_id and target_arn:
        target_name = config.get("targetName", "bugreports")
        print(f"Deleting Gateway Target: {target_name}...")
        try:
            bedrock_agentcore.delete_gateway_target(gatewayId=gateway_id, name=target_name)
            print("Gateway Target deleted.")
        except Exception as e:
            print(f"Error deleting target: {e}")

    if gateway_id:
        print(f"Deleting AgentCore Gateway: {gateway_id}...")
        try:
            bedrock_agentcore.delete_gateway(gatewayId=gateway_id)
            print("Gateway deleted.")
        except Exception as e:
            print(f"Error deleting gateway: {e}")

    print("Cleanup completed.")

if __name__ == "__main__":
    cleanup()