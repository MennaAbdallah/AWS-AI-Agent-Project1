AWS Bedrock AgentCore Customer Support Chatbot (AWS-AI-Agent-Project1)
A customer support chatbot built on the Amazon Bedrock AgentCore managed harness. The system classifies customer inquiries using a single system prompt, handles multi-turn stateful slot filling for bug reporting, grounds store policy questions in an embedded FAQ, and persists engineering tickets to DynamoDB via an AgentCore Gateway and AWS Lambda tool execution.

Architecture & Data Flow
                                +-----------------------------------+
                                |     Client App / CLI (chat.py)    |
                                +-----------------+-----------------+
                                                  |
                                                  | User Messages
                                                  v
                                +-----------------------------------+
                                |   Amazon Bedrock AgentCore        |
                                |        Managed Harness            |
                                |    (us.amazon.nova-pro-v1:0)      |
                                +-----------------+-----------------+
                                                  |
                  +-------------------------------+-------------------------------+
                  |                               |                               |
                  v                               v                               v
       [1. BUG_REPORT Intent]          [2. PLATFORM_FAQ Intent]           [3. OTHER Intent]
       Stateful Slot Filling           Direct response grounded in        Polite hand-off to human
      - Bug Description                embedded FAQ database              support phone line
      - Steps to Reproduce             (online_shop_faq.md)               (1-800-555-0199)
      - Environment Details
                  |
                  | (All 3 slots satisfied)
                  v
       +--------------------+
       | AgentCore Gateway  |
       |  (Target: bugreports)
       +----------+---------+
                  |
                  v
       +--------------------+
       |  AWS Lambda Function
       +----------+---------+
                  |
                  v
       +--------------------+
       |  Amazon DynamoDB   |
       |  (Bug Ticket Table)|
       +--------------------+
Architectural Key Components
Bedrock AgentCore Managed Harness (create_harness.py): Runs the core agent loop using Amazon Nova Pro (us.amazon.nova-pro-v1:0), maintaining state across turns without requiring separate classifier or conditional orchestration nodes.

Single Prompt Routing (system_prompt.txt): Prompt engineering handles exact 3-way message routing, security guardrails against prompt injections, strict FAQ grounding, and stateful bug slot-filling rules.

AgentCore Gateway (setup_gateway.py): Registers and exposes the AWS Lambda tool as bugreports___create_bug_report to the Bedrock harness.

Ticket Storage (create_bug_report.py & cloudformation-tool.yaml): Persists generated bug tickets directly into the bug-report-tool-stack-bug-reports DynamoDB table.

Evaluations Engine (generate-eval-dataset.py & cloudformation-testing.yaml): Runs BYOI (Bring Your Own Inference) evaluation datasets through Amazon Bedrock Evaluations with an LLM-as-a-judge scoring methodology.

Project Structure
Plaintext
AWS-AI-Agent-Project1/
├── chat.py                       # Terminal client for multi-turn interactive testing
├── cleanup_agentcore.py          # Tears down Harness, Gateway Targets, and Gateway
├── cloudformation-testing.yaml   # CFN stack for S3 eval bucket & IAM eval roles
├── cloudformation-tool.yaml      # CFN stack for DynamoDB table, Lambda, and IAM roles
├── create_bug_report.py          # Lambda code for creating DynamoDB tickets
├── create_harness.py             # Script to deploy or update the AgentCore Harness
├── generate-eval-dataset.py      # Generates JSONL eval dataset from test suite
├── harness-tests.json            # Automated test suite covering all routing paths
├── online_shop_faq.md            # Store FAQ source embedded into system prompt
├── README.md                     # Project documentation
├── requirements.txt              # Project dependencies (boto3 1.43+)
├── setup_gateway.py              # Registers Lambda tool with AgentCore Gateway
└── system_prompt.txt             # System prompt template containing agent rules
Step-by-Step Setup & Deployment
Prerequisites
AWS Account with Bedrock access enabled in region us-east-1.

Model access granted for us.amazon.nova-pro-v1:0.

Python 3.9+ installed.

1. Initialize Virtual Environment & Dependencies
Bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
2. Deploy the Tool Infrastructure Stack
Deploys the DynamoDB table, Lambda function, and AgentCore IAM roles:

Bash
aws cloudformation deploy \
  --template-file cloudformation-tool.yaml \
  --stack-name bug-report-tool-stack \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
3. Setup the AgentCore Gateway
Registers the Lambda function behind an AgentCore Gateway target named bugreports:

Bash
python setup_gateway.py
4. Create and Deploy the Harness
Embeds online_shop_faq.md into system_prompt.txt and provisions the AgentCore harness:

Bash
python create_harness.py
Interactive Chat & Tool Testing
Run the terminal chat client to test multi-turn conversations:

Bash
python chat.py
Testing the Bug Report Tool Flow
User: "The app crashes when I click checkout."

(Assistant acknowledges bug and requests steps to reproduce / environment)

User: "I added an item, went to cart, clicked checkout. I am on Chrome on macOS."

(Assistant collects missing slots, invokes bugreports___create_bug_report, and returns the ticket ID)

Verify Record Creation in DynamoDB
Bash
aws dynamodb scan \
  --table-name bug-report-tool-stack-bug-reports \
  --region us-east-1
Automated Testing & Bedrock Evaluations
1. Generate Evaluation Dataset
Invokes the AgentCore harness against harness-tests.json to generate output_eval_dataset.jsonl:

Bash
python generate-eval-dataset.py --tests-json harness-tests.json
2. Deploy Testing Resources Stack
Bash
aws cloudformation deploy \
  --template-file cloudformation-testing.yaml \
  --stack-name bug-report-testing-stack \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
3. Retrieve Stack Outputs & Upload Dataset
Bash
# Retrieve outputs
aws cloudformation describe-stacks \
  --stack-name bug-report-testing-stack \
  --query 'Stacks[0].Outputs' \
  --output table \
  --region us-east-1

# Upload dataset to S3
aws s3 cp output_eval_dataset.jsonl s3://<EvalDatasetBucketName>/output_eval_dataset.jsonl --region us-east-1
4. Trigger Bedrock Evaluation Job
Bash
aws bedrock create-evaluation-job \
  --job-name support-chatbot-eval-run-1 \
  --role-arn <BedrockEvalRoleArn> \
  --evaluation-config '{
    "automated": {
      "datasetMetricConfigs": [{
        "taskType": "General",
        "dataset": {
          "name": "support-chatbot-eval-dataset",
          "datasetLocation": {
            "s3Uri": "s3://<EvalDatasetBucketName>/output_eval_dataset.jsonl"
          }
        },
        "metricNames": ["Builtin.Correctness"]
      }],
      "evaluatorModelConfig": {
        "bedrockEvaluatorModels": [{
          "modelIdentifier": "amazon.nova-pro-v1:0"
        }]
      }
    }
  }' \
  --inference-config '{
    "models": [{
      "precomputedInferenceSource": {
        "inferenceSourceIdentifier": "my-support-chatbot"
      }
    }]
  }' \
  --output-data-config '{"s3Uri": "s3://<EvalDatasetBucketName>/results/"}' \
  --region us-east-1
Evaluation Observations
Intent Routing Precision: The prompt's XML taxonomy (<routing_rules>) correctly isolates Bug Reports, FAQ Inquiries, and Hand-off Scenarios with zero misclassifications during testing.

Stateful Tool Safety: Tool calls (bugreports___create_bug_report) occur exclusively when all three parameters (description, stepsToReproduce, environment) are present in conversation memory, avoiding blank DynamoDB writes.

Zero-Hallucination Guardrails: Requests outside the embedded FAQ scope (e.g., Bitcoin payments or international shipping to unsupported regions) are consistently rejected and diverted to human support (1-800-555-0199).

Infrastructure Teardown
Run the following commands to delete all deployed resources and prevent recurring charges:

Bash
# 1. Delete AgentCore Harness, Target, and Gateway
python cleanup_agentcore.py

# 2. Empty S3 Evaluation Bucket
aws s3 rm s3://<EvalDatasetBucketName> --recursive --region us-east-1

# 3. Delete CloudFormation Stacks
aws cloudformation delete-stack --stack-name bug-report-testing-stack --region us-east-1
aws cloudformation delete-stack --stack-name bug-report-tool-stack --region us-east-1