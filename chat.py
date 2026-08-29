import json
import uuid
import boto3

REGION = "us-east-1"

def run_chat_session():
    with open("agentcore_config.json", "r") as f:
        config = json.load(f)

    harness_arn = config.get("harnessArn")
    if not harness_arn:
        print("Error: Harness ARN not found in agentcore_config.json. Run create_harness.py first.")
        return

    runtime_client = boto3.client("bedrock-agentcore-runtime", region_name=REGION)
    session_id = f"session-{uuid.uuid4().hex[:10]}"

    print("\n=======================================================")
    print("      Customer Support Chatbot (AgentCore Session)      ")
    print(f"Session ID: {session_id}")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("=======================================================\n")

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("Ending session. Goodbye!")
                break

            response = runtime_client.invoke_harness(
                harnessArn=harness_arn,
                runtimeSessionId=session_id,
                inputText=user_input
            )

            if "toolCalls" in response:
                for tc in response["toolCalls"]:
                    print(f"\n[tool call] {tc.get('toolName', 'unknown_tool')}")

            assistant_text = response.get("outputText", "").strip()
            print(f"\nAssistant: {assistant_text}")

        except KeyboardInterrupt:
            print("\nExiting chat...")
            break
        except Exception as err:
            print(f"\n[Error invoking agentcore harness]: {err}")

if __name__ == "__main__":
    run_chat_session()