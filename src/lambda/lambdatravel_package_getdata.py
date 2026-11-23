import json
import os
import boto3

# Set as a Lambda environment variable (Lambda has no .env file).
TABLE_NAME = os.environ.get('TRAVEL_PACKAGES_TABLE', 'travel_packages')

def lambda_handler(event, context):
    city = event['city']
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.get_item(
        TableName=TABLE_NAME,
        Key={
            'city': {
                'S': city
            }
        }
    )
    print(response)
    return {
        'statusCode': 200,
        'body': json.dumps(response['Item'])
    }

