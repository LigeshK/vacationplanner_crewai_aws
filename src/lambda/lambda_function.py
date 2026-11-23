
import json
import os
import boto3
import uuid

# Set these as Lambda environment variables (Lambda has no .env file).
# Defaults keep the already-deployed function working until they are set.
AWS_REGION = os.environ.get('AWS_REGION', 'ap-southeast-2')
AGENT_RUNTIME_ARN = os.environ.get(
    'AGENT_RUNTIME_ARN',
    'arn:aws:bedrock-agentcore:ap-southeast-2:248317805748:runtime/vacation_planner_agent-MZP7J53xCF',
)
AGENT_RUNTIME_QUALIFIER = os.environ.get('AGENT_RUNTIME_QUALIFIER', 'vacation_planner01')

def lambda_handler(event, context):

    # Create a client connection with Bedrock AgentCore
    client = boto3.client(
        'bedrock-agentcore',
        region_name=AWS_REGION
    )

    # Get user input from event
    user_input = event.get('prompt', 'Tokyo')

    # Prepare Agent payload
    payload = json.dumps({"topic": user_input})

    # Generate unique session ID (33+ characters)
    session_id = f"lambda_session_{str(uuid.uuid4()).replace('-', '')}"

    print(f"Invoking AgentCore with payload: {payload}")
    print(f"Session ID: {session_id}")

    # Invoke Bedrock AgentCore Runtime
    response = client.invoke_agent_runtime(
        agentRuntimeArn=AGENT_RUNTIME_ARN,
        runtimeSessionId=session_id,
        payload=payload,
        qualifier=AGENT_RUNTIME_QUALIFIER
    )

    # Read and parse AgentCore response
    response_body = response['response'].read()
    print(f"AgentCore response: {response_body}")

    response_data = json.loads(response_body)

    # Return successful Lambda response with CORS headers
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'session_id': session_id,
            'result': response_data
        })
    }
