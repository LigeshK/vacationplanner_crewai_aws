
import json
import boto3
import uuid

def lambda_handler(event, context):

    # Create a client connection with Bedrock AgentCore
    client = boto3.client(
        'bedrock-agentcore',
        region_name='ap-southeast-2'
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
        agentRuntimeArn='arn:aws:bedrock-agentcore:ap-southeast-2:248317805748:runtime/vacation_planner_agent-MZP7J53xCF',
        runtimeSessionId=session_id,
        payload=payload,
        qualifier="vacation_planner01"
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
