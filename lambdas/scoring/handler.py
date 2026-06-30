import sys
sys_path = '/opt/python'
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

import os
import json
import urllib.request
import time
from datetime import datetime
from utils.cors import get_cors_headers, options_response
from utils.ruc import validate_ruc
from utils.dynamo_cache import get as cache_get, put as cache_put
from utils.response import ok, error

# URL base de la propia API Gateway (se setea como env var al desplegar)
API_BASE = os.environ.get('API_BASE_URL', '')

# Pesos de penalidad por tipo de sanción
PENALIDADES = {
    'OSCE':              {'peso': 20, 'decae': False},
    'TCE':               {'peso': 25, 'decae': False},
    'INHABILITACION_TCE': {'peso': 25, 'decae': False},
    'RNP_INHABILITACION': {'peso': 80, 'decae': False},
    'RNP_MULTA':          {'peso': 5,  'decae': True},
    'SUNAFIL':            {'peso': 30, 'decae': True},
}


def _decaimiento(fecha_str: str) -> float:
    if not fecha_str:
        return 1.0
    try:
        anios = (time.time() - datetime.fromisoformat(fecha_str).timestamp()) / (365.25 * 86400)
        if anios < 2: return 1.0
        if anios < 5: return 0.5
        return 0.25
    except Exception:
        return 1.0


def _invoke_internal(path: str) -> dict | None:
    """Llama a otro endpoint de la misma API Gateway."""
    if not API_BASE:
        return None
    try:
        req = urllib.request.Request(
            f'{API_BASE}{path}',
            headers={'Accept': 'application/json'},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f'[Scoring] Error invocando {path}: {e}')
        return None


def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return options_response(event)

    ruc = (event.get('pathParameters') or {}).get('ruc', '')
    valid, msg = validate_ruc(ruc)
    if not valid:
        return error(event, 400, msg)

    # Cache de scoring completo (5 min)
    cached = cache_get(f'scoring:{ruc}')
    if cached:
        return ok(event, cached)

    sunat = _invoke_internal(f'/prod/consulta-ruc/{ruc}')
    sanciones_resp = _invoke_internal(f'/prod/sanciones/{ruc}')

    sanciones = (sanciones_resp or {}).get('sanciones', [])

    # Calcular score
    score = 100 if sunat else 60
    for s in sanciones:
        p = PENALIDADES.get(s.get('tipo', ''), {'peso': 10, 'decae': True})
        factor = _decaimiento(s.get('fecha', '')) if p['decae'] else 1.0
        score -= round(p['peso'] * factor)
    score = max(0, min(100, score))

    if score >= 80:   nivel = 'BAJO'
    elif score >= 60: nivel = 'MEDIO'
    elif score >= 40: nivel = 'ALTO'
    else:             nivel = 'CRITICO'

    resultado = {
        'ruc': ruc,
        'score': score,
        'nivel_riesgo': nivel,
        'sunat': sunat,
        'sanciones': sanciones,
        'total_sanciones': len(sanciones),
        'timestamp': datetime.utcnow().isoformat() + 'Z',
    }

    cache_put(f'scoring:{ruc}', resultado, ttl_seconds=300)  # 5 min
    return ok(event, resultado)
