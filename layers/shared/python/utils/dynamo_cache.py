import os
import json
import time
import boto3
from boto3.dynamodb.conditions import Key

TABLE = os.environ.get('DYNAMODB_TABLE', 'conflictzero-consultas')
_dynamo = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
_table = _dynamo.Table(TABLE)

DEFAULT_TTL_SECONDS = 30 * 60  # 30 minutos


def get(pk: str):
    """Lee un item del cache. Retorna None si no existe o expiró."""
    try:
        resp = _table.get_item(Key={'pk': pk})
        item = resp.get('Item')
        if not item:
            return None
        if item.get('ttl', 0) < int(time.time()):
            return None
        return json.loads(item['payload'])
    except Exception as e:
        print(f'[DynamoDB Cache] get error: {e}')
        return None


def put(pk: str, data, ttl_seconds: int = DEFAULT_TTL_SECONDS):
    """Guarda un item en el cache con TTL."""
    try:
        _table.put_item(Item={
            'pk': pk,
            'payload': json.dumps(data, default=str),
            'ttl': int(time.time()) + ttl_seconds,
        })
    except Exception as e:
        print(f'[DynamoDB Cache] put error: {e}')
