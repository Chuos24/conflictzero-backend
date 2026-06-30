import json
from .cors import get_cors_headers


def ok(event, data):
    return {
        'statusCode': 200,
        'headers': get_cors_headers(event),
        'body': json.dumps(data, default=str),
    }


def error(event, status, message):
    return {
        'statusCode': status,
        'headers': get_cors_headers(event),
        'body': json.dumps({'error': message}),
    }
