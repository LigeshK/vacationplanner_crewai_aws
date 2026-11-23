import json
import boto3

def lambda_handler(event, context):
    city = event['city']
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.get_item(
        TableName='travel_packages',
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

