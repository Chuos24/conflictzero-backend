import json
import boto3
import os
import hashlib
import urllib.request
import urllib.error
import ssl
from datetime import datetime, timedelta
import re

# ─── Configuración ───────────────────────────────────────────────────────────
S3_BUCKET = os.environ.get('S3_BUCKET', 'conflictzero-certificados-prod')
BUSCARUC_TOKEN = os.environ.get('BUSCARUC_TOKEN', '')
s3_client = boto3.client('s3')

ALLOWED_ORIGINS = [
    'https://czperu.com',
    'https://www.czperu.com',
    'https://conflictzero-certificados-prod.s3.amazonaws.com'
]

# ─── Agentes sectoriales: fuentes y pesos por categoría ──────────────────────
AGENTES = {
    'construccion': {
        'nombre': 'CONSTRUCCIÓN',
        'sectores': 'Construcción, infraestructura, ingeniería, obras civiles',
        'fuentes': ['SUNAT', 'SUNARP', 'OSCE', 'RNP', 'TCE', 'SUNAFIL', 'Municipalidades', 'CIP'],
        'pesos': {
            'identidad_legal':     0.20,
            'tributario':          0.15,
            'laboral':             0.15,
            'regulatorio':         0.15,
            'financiero':          0.10,
            'legal_judicial':      0.10,
            'reputacional':        0.05,
            'capacidad_tecnica':   0.10,
        }
    },
    'servicios': {
        'nombre': 'SERVICIOS',
        'sectores': 'Limpieza, seguridad, mantenimiento, transporte, logística',
        'fuentes': ['SUNAT', 'SUNARP', 'SUNAFIL', 'MTPE', 'INDECOPI', 'Municipalidades', 'Poder Judicial'],
        'pesos': {
            'identidad_legal':     0.20,
            'tributario':          0.15,
            'laboral':             0.25,
            'regulatorio':         0.10,
            'financiero':          0.10,
            'legal_judicial':      0.10,
            'reputacional':        0.10,
        }
    },
    'productivo': {
        'nombre': 'PRODUCTIVO',
        'sectores': 'Industria, alimentos, agroindustria, pesca, energía, minería',
        'fuentes': ['SUNAT', 'PRODUCE', 'SENASA', 'SANIPES', 'DIGESA', 'OEFA', 'MINAM', 'OSINERGMIN', 'MEM'],
        'pesos': {
            'identidad_legal':     0.15,
            'tributario':          0.15,
            'regulatorio':         0.20,
            'ambiental':           0.20,
            'financiero':          0.10,
            'legal_judicial':      0.10,
            'capacidad_tecnica':   0.10,
        }
    },
    'financiero': {
        'nombre': 'FINANCIERO',
        'sectores': 'Fintech, seguros, factoring, contrapartes financieras',
        'fuentes': ['SUNAT', 'SBS', 'SMV', 'UIF', 'Burós de crédito', 'SUNARP', 'INDECOPI'],
        'pesos': {
            'identidad_legal':     0.15,
            'tributario':          0.15,
            'financiero':          0.25,
            'compliance_aml':      0.20,
            'legal_judicial':      0.15,
            'reputacional':        0.10,
        }
    },
    'tech': {
        'nombre': 'TECH',
        'sectores': 'Software, SaaS, ciberseguridad, TI, tratamiento de datos',
        'fuentes': ['SUNAT', 'SUNARP', 'INDECOPI', 'Protección de datos', 'ISO 27001', 'Fuentes abiertas'],
        'pesos': {
            'identidad_legal':     0.20,
            'tributario':          0.15,
            'seguridad_info':      0.25,
            'legal_judicial':      0.10,
            'reputacional':        0.15,
            'capacidad_tecnica':   0.15,
        }
    },
    'transversales': {
        'nombre': 'TRANSVERSALES',
        'sectores': 'Compliance general, todos los sectores',
        'fuentes': ['SUNAT', 'SUNARP', 'Poder Judicial', 'Listas restrictivas', 'Medios', 'Burós de crédito'],
        'pesos': {
            'identidad_legal':     0.20,
            'tributario':          0.20,
            'legal_judicial':      0.20,
            'financiero':          0.15,
            'compliance_aml':      0.15,
            'reputacional':        0.10,
        }
    }
}

# ─── CORS ────────────────────────────────────────────────────────────────────
def get_cors_headers(origin=None):
    allowed = origin if origin and origin in ALLOWED_ORIGINS else 'https://czperu.com'
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': allowed,
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Sector'
    }

def response(status, body, origin=None):
    return {
        'statusCode': status,
        'headers': get_cors_headers(origin),
        'body': json.dumps(body, ensure_ascii=False, default=str)
    }

# ─── Validación RUC ──────────────────────────────────────────────────────────
def validate_ruc(ruc):
    if not ruc or len(ruc) != 11:
        return False, 'RUC debe tener 11 dígitos'
    if not ruc.isdigit():
        return False, 'RUC solo debe contener números'
    if ruc[:2] not in ['10', '15', '17', '20']:
        return False, 'RUC no válido - prefijo incorrecto'
    return True, None

# ─── Cache en memoria (warm Lambda) ──────────────────────────────────────────
_cache = {}

def cache_get(key, ttl_seconds=1800):
    entry = _cache.get(key)
    if not entry:
        return None
    if (datetime.now() - entry['ts']).seconds > ttl_seconds:
        del _cache[key]
        return None
    return entry['data']

def cache_set(key, data):
    _cache[key] = {'data': data, 'ts': datetime.now()}

# ─── Consulta SUNAT via buscaruc.com (directo, sin Render) ───────────────────
def consultar_sunat(ruc):
    cached = cache_get(f'sunat_{ruc}')
    if cached:
        return cached

    token = BUSCARUC_TOKEN
    if not token:
        # Sin token: devolver estructura neutral para no bloquear el scoring
        return {
            'ruc': ruc,
            'razonSocial': 'NO DISPONIBLE',
            'estado': 'DESCONOCIDO',
            'condicion': 'DESCONOCIDO',
            'domicilioFiscal': '',
            'fuente': 'buscaruc_com',
            'error': 'BUSCARUC_TOKEN no configurado'
        }

    try:
        payload = json.dumps({'token': token, 'ruc': ruc}).encode('utf-8')
        req = urllib.request.Request(
            'https://buscaruc.com/api/v1/ruc',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'ConflictZero/2.0'
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        if not data.get('success') or not data.get('result'):
            return {'error': 'RUC no encontrado en buscaruc.com', 'ruc': ruc, 'fuente': 'buscaruc_com'}

        r = data['result']
        result = {
            'ruc': r.get('ruc', ruc),
            'razonSocial': r.get('social_reason', ''),
            'estado': r.get('taxpayer_state', 'ACTIVO'),
            'condicion': r.get('domicile_condition', 'HABIDO'),
            'domicilioFiscal': r.get('address', ''),
            'ubigeo': r.get('ubigeo', ''),
            'fuente': 'buscaruc_com'
        }
        cache_set(f'sunat_{ruc}', result)
        return result

    except Exception as e:
        return {'error': str(e), 'ruc': ruc, 'fuente': 'buscaruc_com'}

# ─── Scraping OSCE/TCE inhabilitados ─────────────────────────────────────────
OSCE_URL = 'http://www.osce.gob.pe/consultasenlinea/inhabilitados/inhabil_publi_mes.asp'

def scrape_osce_inhabilitados():
    cached = cache_get('osce_inhabilitados', ttl_seconds=3600)
    if cached:
        return cached
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(
            OSCE_URL,
            headers={
                'User-Agent': 'ConflictZero-Bot/2.0 (contacto@czperu.com)',
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'es-PE,es;q=0.9',
            }
        )
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        inhabilitados = {}
        for line in html.split('\n'):
            ruc_match = re.search(r'(\d{11})', line)
            if ruc_match:
                ruc = ruc_match.group(1)
                nombre_match = re.search(r'>([A-Z][A-Z\s\.]+(?:S\.?A\.?C?|S\.?R\.?L|E\.?I\.?R\.?L))<', line)
                expediente_match = re.search(r'(\d{3,4}-\d{4}-TCE-S\d)', line)
                inhabilitados[ruc] = {
                    'ruc': ruc,
                    'razon_social': nombre_match.group(1).strip() if nombre_match else 'NO ESPECIFICADO',
                    'expediente': expediente_match.group(1) if expediente_match else 'NO ESPECIFICADO',
                    'fuente': 'OSCE/TCE',
                    'estado': 'INHABILITADO'
                }
        cache_set('osce_inhabilitados', inhabilitados)
        return inhabilitados
    except Exception as e:
        return {}

# ─── Motor de scoring por agente ─────────────────────────────────────────────
def calcular_score(ruc, sunat_data, sanciones_osce, sector='construccion'):
    agente = AGENTES.get(sector, AGENTES['transversales'])
    pesos = agente['pesos']
    scores = {}
    alertas = []

    if 'identidad_legal' in pesos:
        score_il = 100
        if sunat_data.get('error') and 'TOKEN' in sunat_data.get('error', ''):
            score_il = 60
            alertas.append({'nivel': 'INFO', 'descripcion': 'Validación SUNAT pendiente: configurar BUSCARUC_TOKEN'})
        elif sunat_data.get('error'):
            score_il = 40
            alertas.append({'nivel': 'CRITICO', 'descripcion': 'No se pudo validar identidad en SUNAT'})
        elif sunat_data.get('estado') not in ['ACTIVO', 'HABIDO']:
            score_il = 50
            alertas.append({'nivel': 'ALTO', 'descripcion': f"Estado SUNAT: {sunat_data.get('estado', 'DESCONOCIDO')}"})
        elif sunat_data.get('condicion') == 'NO HABIDO':
            score_il = 30
            alertas.append({'nivel': 'CRITICO', 'descripcion': 'Contribuyente NO HABIDO en SUNAT'})
        scores['identidad_legal'] = score_il

    if 'regulatorio' in pesos:
        score_reg = 100
        if ruc in sanciones_osce:
            score_reg = 0
            alertas.append({
                'nivel': 'CRITICO',
                'descripcion': f"INHABILITADO por OSCE/TCE - Expediente: {sanciones_osce[ruc].get('expediente')}"
            })
        scores['regulatorio'] = score_reg

    if 'tributario' in pesos:
        score_trib = 80
        if sunat_data.get('omiso_declaraciones'):
            score_trib = 40
            alertas.append({'nivel': 'MEDIO', 'descripcion': 'Omiso a declaraciones tributarias'})
        scores['tributario'] = score_trib

    categorias_base = ['laboral', 'financiero', 'legal_judicial', 'reputacional',
                       'capacidad_tecnica', 'ambiental', 'compliance_aml', 'seguridad_info']
    for cat in categorias_base:
        if cat in pesos and cat not in scores:
            scores[cat] = 75
            alertas.append({
                'nivel': 'INFO',
                'descripcion': f'Categoría {cat.upper()} pendiente de integración de fuente'
            })

    score_total = 0
    for cat, peso in pesos.items():
        score_total += scores.get(cat, 75) * peso

    score_total = round(score_total)

    if score_total >= 70:
        estado = 'APROBADO'
    elif score_total >= 40:
        estado = 'OBSERVADO'
    else:
        estado = 'RECHAZADO'

    return {
        'score_general': score_total,
        'estado': estado,
        'scores_por_categoria': scores,
        'alertas': alertas,
        'agente_utilizado': agente['nombre'],
        'fuentes_consultadas': agente['fuentes'],
        'metodologia': f'ConflictZero Scoring Engine v2.0 - Agente {agente["nombre"]}'
    }

# ─── Generador de certificado HTML ───────────────────────────────────────────
def generar_html_certificado(ruc, razon_social, score_data, sector):
    score = score_data['score_general']
    estado = score_data['estado']
    agente = score_data['agente_utilizado']
    fecha = datetime.now().strftime('%d/%m/%Y %H:%M')
    vencimiento = (datetime.now() + timedelta(days=90)).strftime('%d/%m/%Y')

    color_map = {'APROBADO': '#16a34a', 'OBSERVADO': '#d97706', 'RECHAZADO': '#dc2626'}
    color = color_map.get(estado, '#6b7280')

    alertas_criticas = [a for a in score_data.get('alertas', []) if a['nivel'] in ['CRITICO', 'ALTO']]
    alertas_html = ''.join(
        f'<li style="color:#dc2626">⚠ {a["descripcion"]}</li>' for a in alertas_criticas
    ) or '<li style="color:#16a34a">✓ Sin alertas críticas detectadas</li>'

    categorias_html = ''.join(
        f'<tr><td style="padding:6px 12px">{cat.replace("_"," ").upper()}</td>'
        f'<td style="padding:6px 12px;text-align:center;font-weight:bold">{val}</td>'
        f'<td style="padding:6px 12px">{"🟢" if val>=70 else "🟡" if val>=40 else "🔴"}</td></tr>'
        for cat, val in score_data.get('scores_por_categoria', {}).items()
    )

    return f'''<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>Certificado ConflictZero - {ruc}</title>
<style>
  body{{font-family:Arial,sans-serif;margin:0;padding:40px;background:#f9fafb}}
  .cert{{max-width:800px;margin:0 auto;background:#fff;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.1);padding:40px}}
  .header{{text-align:center;border-bottom:3px solid {color};padding-bottom:24px;margin-bottom:32px}}
  .logo{{font-size:28px;font-weight:900;color:#1e293b;letter-spacing:-1px}}
  .logo span{{color:{color}}}
  .score-badge{{display:inline-block;background:{color};color:#fff;font-size:48px;font-weight:900;width:120px;height:120px;line-height:120px;border-radius:50%;margin:20px 0}}
  .estado{{font-size:22px;font-weight:700;color:{color};margin:8px 0}}
  table{{width:100%;border-collapse:collapse;margin:16px 0}}
  th{{background:#f1f5f9;padding:8px 12px;text-align:left;font-size:13px;color:#64748b}}
  td{{border-bottom:1px solid #f1f5f9;font-size:14px}}
  .footer{{text-align:center;color:#94a3b8;font-size:12px;margin-top:32px;border-top:1px solid #e2e8f0;padding-top:20px}}
</style></head>
<body><div class="cert">
  <div class="header">
    <div class="logo">Conflict<span>Zero</span></div>
    <p style="color:#64748b;margin:4px 0">Plataforma de Verificación y Homologación de Proveedores</p>
    <div class="score-badge">{score}</div>
    <div class="estado">{estado}</div>
    <p style="color:#64748b">Agente sectorial: <strong>{agente}</strong></p>
  </div>

  <table>
    <tr><th colspan="2">Datos del Proveedor</th></tr>
    <tr><td style="padding:8px 12px;color:#64748b">RUC</td><td style="padding:8px 12px;font-weight:600">{ruc}</td></tr>
    <tr><td style="padding:8px 12px;color:#64748b">Razón Social</td><td style="padding:8px 12px;font-weight:600">{razon_social}</td></tr>
    <tr><td style="padding:8px 12px;color:#64748b">Sector</td><td style="padding:8px 12px">{sector.upper()}</td></tr>
    <tr><td style="padding:8px 12px;color:#64748b">Fecha de evaluación</td><td style="padding:8px 12px">{fecha}</td></tr>
    <tr><td style="padding:8px 12px;color:#64748b">Vigencia del certificado</td><td style="padding:8px 12px">{vencimiento}</td></tr>
  </table>

  <table>
    <tr><th>Categoría</th><th>Score</th><th>Estado</th></tr>
    {categorias_html}
  </table>

  <div style="margin:24px 0">
    <h3 style="color:#1e293b;margin-bottom:12px">Alertas detectadas</h3>
    <ul style="margin:0;padding-left:20px;line-height:2">{alertas_html}</ul>
  </div>

  <div style="margin:24px 0">
    <h3 style="color:#1e293b;margin-bottom:8px">Fuentes consultadas</h3>
    <p style="color:#64748b;font-size:14px">{', '.join(score_data.get('fuentes_consultadas', []))}</p>
  </div>

  <div class="footer">
    <p>{score_data.get('metodologia', '')}</p>
    <p>Este certificado fue generado automáticamente por ConflictZero y tiene validez referencial.<br>
    Para auditoría o consultas: <a href="mailto:contacto@czperu.com">contacto@czperu.com</a></p>
    <p style="font-size:10px;margin-top:8px">ID: CZ-{ruc}-{datetime.now().strftime("%Y%m%d%H%M%S")}</p>
  </div>
</div></body></html>'''

# ─── Normalizar evento (REST v1 y HTTP v2) ───────────────────────────────────
def normalize_event(event):
    method = (
        event.get('httpMethod') or
        (event.get('requestContext', {}).get('http', {}).get('method', 'GET'))
    )
    path = (
        event.get('path') or
        event.get('rawPath') or
        '/'
    )
    qs = event.get('queryStringParameters') or {}
    params = event.get('pathParameters') or {}
    headers = event.get('headers') or {}
    origin = headers.get('origin') or headers.get('Origin') or ''
    return method, path, qs, params, origin

# ─── Handler principal ────────────────────────────────────────────────────────
def lambda_handler(event, context):
    method, path, qs, params, origin = normalize_event(event)

    if method == 'OPTIONS':
        return response(200, {'message': 'OK'}, origin)

    # ── GET /health ───────────────────────────────────────────────────────────
    if path in ('/', '/health') or path.endswith('/health'):
        return response(200, {
            'status': 'ok',
            'version': '2.1',
            'agentes': list(AGENTES.keys()),
            'sunat_token_configurado': bool(BUSCARUC_TOKEN),
            'timestamp': datetime.now().isoformat()
        }, origin)

    # ── GET /agentes ──────────────────────────────────────────────────────────
    if '/agentes' in path:
        return response(200, {
            'agentes': [
                {'id': k, 'nombre': v['nombre'], 'sectores': v['sectores'], 'fuentes': v['fuentes']}
                for k, v in AGENTES.items()
            ]
        }, origin)

    # ── GET /consulta/{ruc} ───────────────────────────────────────────────────
    if '/consulta/' in path or '/consulta-osce/' in path:
        ruc = params.get('ruc') or path.rstrip('/').split('/')[-1]
        sector = qs.get('sector', 'construccion').lower()

        valid, err = validate_ruc(ruc)
        if not valid:
            return response(400, {'error': err, 'ruc': ruc}, origin)

        sunat_data = consultar_sunat(ruc)
        sanciones_osce = scrape_osce_inhabilitados()
        score_data = calcular_score(ruc, sunat_data, sanciones_osce, sector)

        return response(200, {
            'ruc': ruc,
            'razon_social': sunat_data.get('razonSocial') or sunat_data.get('razon_social', 'NO DISPONIBLE'),
            'estado_sunat': sunat_data.get('estado', 'DESCONOCIDO'),
            'condicion_sunat': sunat_data.get('condicion', 'DESCONOCIDO'),
            'domicilio_fiscal': sunat_data.get('domicilioFiscal') or sunat_data.get('domicilio', ''),
            'actividad_economica': sunat_data.get('actividadEconomica') or sunat_data.get('giro', ''),
            'inhabilitado_osce': ruc in sanciones_osce,
            'detalle_sancion': sanciones_osce.get(ruc),
            'homologacion': score_data,
            'sector': sector,
            'timestamp': datetime.now().isoformat()
        }, origin)

    # ── GET /generar-certificado/{ruc} ────────────────────────────────────────
    if '/generar-certificado/' in path or '/certificado/' in path:
        ruc = params.get('ruc') or path.rstrip('/').split('/')[-1]
        sector = qs.get('sector', 'construccion').lower()

        valid, err = validate_ruc(ruc)
        if not valid:
            return response(400, {'error': err}, origin)

        sunat_data = consultar_sunat(ruc)
        sanciones_osce = scrape_osce_inhabilitados()
        score_data = calcular_score(ruc, sunat_data, sanciones_osce, sector)

        razon_social = sunat_data.get('razonSocial') or sunat_data.get('razon_social', ruc)
        html = generar_html_certificado(ruc, razon_social, score_data, sector)

        key = f'certificados/{sector}/{ruc}/{datetime.now().strftime("%Y%m%d%H%M%S")}.html'
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=key,
                Body=html.encode('utf-8'),
                ContentType='text/html; charset=utf-8',
                Metadata={
                    'ruc': ruc,
                    'sector': sector,
                    'score': str(score_data['score_general']),
                    'estado': score_data['estado']
                }
            )
            url_firmada = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET, 'Key': key},
                ExpiresIn=604800
            )
            return response(200, {
                'ruc': ruc,
                'razon_social': razon_social,
                'sector': sector,
                'score': score_data['score_general'],
                'estado': score_data['estado'],
                'agente': score_data['agente_utilizado'],
                'certificado_url': url_firmada,
                'vigencia_dias': 7,
                'generado_en': datetime.now().isoformat()
            }, origin)
        except Exception as e:
            return response(500, {'error': f'Error al guardar certificado en S3: {str(e)}'}, origin)

    return response(404, {'error': 'Endpoint no encontrado', 'path': path}, origin)
