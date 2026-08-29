import json
import os
import uuid
from datetime import datetime, timezone
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
TABLE_NAME = os.environ.get('TABLE_NAME', 'bug-report-tool-stack-bug-reports')
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    AgentCore Gateway target handler for bug reports.
    Accepts raw JSON tool input parameters directly from the gateway harness.
    """
    print("Received event payload:", json.dumps(event))

    description = event.get('description', '').strip()
    steps_to_reproduce = event.get('stepsToReproduce', '').strip()
    environment = event.get('environment', '').strip()

    ticket_id = f"TICKET-{uuid.uuid4().hex[:8].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()

    item = {
        'ticketId': ticket_id,
        'description': description or 'Unspecified issue description',
        'stepsToReproduce': steps_to_reproduce or 'Not specified',
        'environment': environment or 'Not specified',
        'status': 'OPEN',
        'createdAt': created_at
    }

    try:
        table.put_item(Item=item)
        print(f"Successfully recorded ticket {ticket_id} in DynamoDB table {TABLE_NAME}")
        return {
            'ticketId': ticket_id,
            'status': 'OPEN',
            'message': f"Ticket {ticket_id} created successfully."
        }
    except Exception as e:
        print(f"Failed to record ticket: {str(e)}")
        raise e