import os
import json
import urllib.request
import urllib.error
sys_path = '/opt/python'
import sys
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from utils.cors import get_cors_headers, options_response
from utils.ruc import validate_ruc
from utils.dynamo_cache import get as cache_get, put as cache_put
from utils.response import ok, error

BUSCARUC_TOKEN = os.environ.get('BUSCARUC_TOKEN', '')


def fetch_sunat(ruc: str) -> dict | None:
    """Consulta SUNAT via BuscarRUC API."""
    cached = cache_get(f'sunat:{ruc}')
    if cached:
        return cached

    payload = json.dumps({'token': BUSCARUC_TOKEN, 'ruc': ruc}).encode()
    req = urllib.request.Request(
        'https://buscaruc.com/api/v1/ruc',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        if not data.get('success') or not data.get('result'):
            return None
        r = data['result']
        result = {
            'ruc': r.get('ruc', ruc),
            'razon_social': r.get('social_reason', ''),
            'estado': r.get('taxpayer_state', 'ACTIVO'),
            'condicion': r.get('domicile_condition', 'HABIDO'),
            'direccion': r.get('address', ''),
            'ubigeo': r.get('ubigeo', ''),
            'fuente': 'sunat',
        }
        cache_put(f'sunat:{ruc}', result)
        return result
    except Exception as e:
        print(f'[SUNAT] Error: {e}')
        return None


def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return options_response(event)

    ruc = (event.get('pathParameters') or {}).get('ruc', '')
    valid, msg = validate_ruc(ruc)
    if not valid:
        return error(event, 400, msg)

    data = fetch_sunat(ruc)
    if not data:
        return error(event, 404, f'RUC {ruc} no encontrado en SUNAT')

    return ok(event, data)
