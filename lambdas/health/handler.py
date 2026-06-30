import json
from datetime import datetime


def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({
            'status': 'online',
            'service': 'ConflictZero API',
            'version': '3.0.0',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }),
    }
