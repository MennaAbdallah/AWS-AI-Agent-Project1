import json
import os
import uuid
from datetime import datetime, timezone
import boto3

table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])

def lambda_handler(event, _):
    print("EVENT:", json.dumps(event, indent=2, default=str))

    # 1. Handle flat payload (passed by Bedrock Runtime converse tool use or Lambda Console test)
    if "description" in event or "stepsToReproduce" in event:
        body = event
    # 2. Handle Agent Core / Agents Classic enveloped payload structure if present
    elif event.get("parameters"):
        params = event.get("parameters") or []
        body = {
            p.get("name"): p.get("value")
            for p in params
            if isinstance(p, dict) and p.get("name") is not None
        }
    else:
        body = event

    description = (body.get("description") or "").strip()
    steps = (body.get("stepsToReproduce") or "").strip()
    environment = (body.get("environment") or "").strip()

    if not description:
        return _resp(event, {"error": "missing", "field": "description"})

    ticket_id = str(uuid.uuid4())
    item = {
        "ticketId": ticket_id,
        "description": description,
        "stepsToReproduce": steps,
        "environment": environment,
        "status": "OPEN",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    table.put_item(Item=item)

    # Return structure that works seamlessly with Bedrock / Lambda
    response_data = {"ticketId": ticket_id, "status": "OPEN"}
    
    if event.get("messageVersion") == "1.0":
        return _resp(event, response_data)
    
    return response_data


def _resp(event, obj):
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup"),
            "function": event.get("function"),
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json.dumps(obj)
                    }
                }
            },
        },
    }