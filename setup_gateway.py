import json
import time
import boto3

REGION = 'us-east-1'

def get_cfn_outputs(stack_name='bug-report-tool-stack'):
    cfn = boto3.client('cloudformation', region_name=REGION)
    res = cfn.describe_stacks(StackName=stack_name)
    outputs = res['Stacks'][0]['Outputs']
    return {o['OutputKey']: o['OutputValue'] for o in outputs}

def setup_agentcore_gateway():
    outputs = get_cfn_outputs()
    lambda_arn = outputs['LambdaFunctionArn']
    gateway_role_arn = outputs['GatewayRoleArn']
    harness_role_arn = outputs['HarnessRoleArn']
    table_name = outputs['TableName']

    bedrock_agentcore = boto3.client('bedrock-agentcore', region_name=REGION)

    gateway_name = "CustomerSupportGateway"
    print(f"Creating AgentCore Gateway: {gateway_name}...")
    
    try:
        gw_res = bedrock_agentcore.create_gateway(
            name=gateway_name,
            roleArn=gateway_role_arn,
            description="AgentCore Gateway routing tools to Lambda execution endpoints"
        )
        gateway_arn = gw_res['gatewayArn']
        gateway_id = gw_res['gatewayId']
    except bedrock_agentcore.exceptions.ResourceAlreadyExistsException:
        print("Gateway exists. Fetching Gateway details...")
        gateways = bedrock_agentcore.list_gateways()['gateways']
        gw = next(g for g in gateways if g['name'] == gateway_name)
        gateway_arn = gw['gatewayArn']
        gateway_id = gw['gatewayId']

    print(f"Gateway ARN: {gateway_arn}")

    target_name = "bugreports"
    tool_schema = {
        "name": "create_bug_report",
        "description": "Files a bug report ticket into the engineering database once all details are collected.",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Clear summary of the bug or error experienced by the customer."
                },
                "stepsToReproduce": {
                    "type": "string",
                    "description": "Sequential actions or steps leading up to the unexpected behavior."
                },
                "environment": {
                    "type": "string",
                    "description": "Customer environment details, including browser, OS, device, or app version."
                }
            },
            "required": ["description", "stepsToReproduce", "environment"]
        }
    }

    print(f"Registering target {target_name} on Gateway...")
    
    target_arn = None
    for attempt in range(5):
        try:
            target_res = bedrock_agentcore.create_gateway_target(
                gatewayId=gateway_id,
                name=target_name,
                targetType="LAMBDA",
                targetConfiguration={
                    "lambda": {
                        "functionArn": lambda_arn,
                        "toolSchema": json.dumps(tool_schema)
                    }
                }
            )
            target_arn = target_res['targetArn']
            break
        except Exception as err:
            print(f"Attempt {attempt + 1} failed due to IAM propagation delay ({err}). Retrying in 15 seconds...")
            time.sleep(15)

    if not target_arn:
        targets = bedrock_agentcore.list_gateway_targets(gatewayId=gateway_id)['targets']
        target_arn = next(t['targetArn'] for t in targets if t['name'] == target_name)

    config = {
        "gatewayArn": gateway_arn,
        "gatewayId": gateway_id,
        "targetArn": target_arn,
        "targetName": target_name,
        "fullToolName": f"{target_name}___create_bug_report",
        "lambdaArn": lambda_arn,
        "gatewayRoleArn": gateway_role_arn,
        "harnessRoleArn": harness_role_arn,
        "tableName": table_name,
        "region": REGION
    }

    with open("agentcore_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("AgentCore Gateway setup completed successfully. Configuration stored in agentcore_config.json.")

if __name__ == "__main__":
    setup_agentcore_gateway()