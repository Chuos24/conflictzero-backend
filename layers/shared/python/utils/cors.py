import os

ALLOWED_ORIGINS = [
    os.environ.get('ALLOWED_ORIGIN', 'https://czperu.com'),
    'https://www.czperu.com',
    'http://localhost:3000',  # desarrollo local
]


def get_cors_headers(event):
    origin = (
        (event.get('headers') or {}).get('origin')
        or (event.get('headers') or {}).get('Origin', '')
    )
    allowed = origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0]
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': allowed,
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }


def options_response(event):
    return {'statusCode': 200, 'headers': get_cors_headers(event), 'body': '{}'}
