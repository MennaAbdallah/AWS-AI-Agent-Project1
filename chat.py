import json
import uuid
import boto3

REGION = "us-east-1"
MODEL_ID = "us.amazon.nova-pro-v1:0"

def load_system_prompt():
    with open("system_prompt.txt", "r") as f:
        prompt_template = f.read()
    try:
        with open("online_shop_faq.md", "r") as f:
            faq_content = f.read()
        return prompt_template.replace("{{FAQ}}", faq_content)
    except FileNotFoundError:
        return prompt_template

def run_chat_session():
    try:
        with open("agentcore_config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: agentcore_config.json not found. Run setup_gateway.py first.")
        return

    lambda_arn = config.get("lambda_arn") or config.get("lambdaArn")
    
    # Initialize Bedrock Runtime client
    bedrock_runtime = boto3.client("bedrock-runtime", region_name=REGION)
    lambda_client = boto3.client("lambda", region_name=REGION)

    system_prompt = load_system_prompt()
    messages = []
    
    session_id = str(uuid.uuid4())

    print("\n=======================================================")
    print("      Customer Support Chatbot (Bedrock Nova Pro)      ")
    print(f"Session ID: {session_id}")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("=======================================================\n")

    # Define the tool schema for the model
    tool_config = {
        "tools": [
            {
                "toolSpec": {
                    "name": "bugreports___create_bug_report",
                    "description": "Records software bug reports into the support system database.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string", "description": "Detailed summary of the bug."},
                                "stepsToReproduce": {"type": "string", "description": "Steps taken prior to the bug."},
                                "environment": {"type": "string", "description": "Device, OS, browser, or app version."}
                            },
                            "required": ["description", "stepsToReproduce", "environment"]
                        }
                    }
                }
            }
        ]
    }

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("Ending session. Goodbye!")
                break

            # Append user message to conversation history
            messages.append({
                "role": "user",
                "content": [{"text": user_input}]
            })

            # Call Bedrock Converse API
            response = bedrock_runtime.converse(
                modelId=MODEL_ID,
                messages=messages,
                system=[{"text": system_prompt}],
                toolConfig=tool_config
            )

            output_message = response["output"]["message"]
            messages.append(output_message)

            # Check if the model invoked a tool
            stop_reason = response.get("stopReason")
            if stop_reason == "tool_use":
                for content_block in output_message["content"]:
                    if "toolUse" in content_block:
                        tool_use = content_block["toolUse"]
                        tool_name = tool_use["name"]
                        tool_input = tool_use["input"]
                        tool_use_id = tool_use["toolUseId"]

                        print(f"\n[tool call] {tool_name}")

                        # Execute the backend Lambda function directly with tool inputs
                        try:
                            lambda_response = lambda_client.invoke(
                                FunctionName=lambda_arn,
                                InvocationType="RequestResponse",
                                Payload=json.dumps(tool_input)
                            )
                            tool_result = json.loads(lambda_response["Payload"].read().decode("utf-8"))
                        except Exception as e:
                            tool_result = {"error": str(e)}

                        # Send tool result back to the model
                        messages.append({
                            "role": "user",
                            "content": [
                                {
                                "toolResult": {
                                    "toolUseId": tool_use_id,
                                    "content": [{"json": tool_result}],
                                    "status": "success"
                                }
                                }
                            ]
                        })

                        # Follow up call to get the final assistant response after tool execution
                        followup_response = bedrock_runtime.converse(
                            modelId=MODEL_ID,
                            messages=messages,
                            system=[{"text": system_prompt}],
                            toolConfig=tool_config
                        )
                        output_message = followup_response["output"]["message"]
                        messages.append(output_message)

            # Extract assistant text response
            assistant_text = ""
            for content_block in output_message.get("content", []):
                if "text" in content_block:
                    assistant_text += content_block["text"]

            print(f"\nAssistant: {assistant_text.strip()}")

        except KeyboardInterrupt:
            print("\nExiting chat...")
            break
        except Exception as err:
            print(f"\n[Error during chat session]: {err}")

if __name__ == "__main__":
    run_chat_session()