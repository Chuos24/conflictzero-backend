import sys
sys_path = '/opt/python'
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

import os
import json
import boto3
import urllib.request
from datetime import datetime, timedelta
from utils.cors import get_cors_headers, options_response
from utils.ruc import validate_ruc
from utils.response import ok, error

S3_BUCKET = os.environ.get('S3_BUCKET', 'conflictzero-certificados-prod')
API_BASE = os.environ.get('API_BASE_URL', '')
s3 = boto3.client('s3')


def get_scoring(ruc: str) -> dict | None:
    if not API_BASE:
        return None
    try:
        req = urllib.request.Request(
            f'{API_BASE}/prod/consulta-completa/{ruc}',
            headers={'Accept': 'application/json'},
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f'[Certificado] Error scoring: {e}')
        return None


def generate_html(data: dict, score: int) -> str:
    estado = 'APROBADO' if score >= 70 else 'OBSERVADO' if score >= 40 else 'RECHAZADO'
    banner_text = '✓ SIN PROBLEMAS DETECTADOS' if score >= 70 else '⚠ OBSERVADO' if score >= 40 else '✗ RECHAZADO'
    color = '#16a34a' if score >= 70 else '#ca8a04' if score >= 40 else '#dc2626'
    bg = '#dcfce7' if score >= 70 else '#fef9c3' if score >= 40 else '#fee2e2'
    cert_id = f"CZ-{datetime.utcnow().strftime('%Y%m%d')}-{data['ruc'][-6:]}"
    vence = (datetime.utcnow() + timedelta(days=90)).strftime('%d/%m/%Y')

    return f"""<!DOCTYPE html>
<html lang="es"><head>
<meta charset="UTF-8">
<title>Certificado ConflictZero - {data['ruc']}</title>
<style>
  body{{font-family:Inter,sans-serif;background:#f5f5f0;display:flex;justify-content:center;padding:20px}}
  .cert{{width:210mm;min-height:297mm;background:#fff;padding:60px;border:2px solid #c9a227;position:relative}}
  .cert::before{{content:'';position:absolute;top:15px;left:15px;right:15px;bottom:15px;border:1px solid #c9a227;pointer-events:none}}
  .header{{text-align:center;margin-bottom:30px}}
  .logo{{width:70px;height:70px;background:linear-gradient(135deg,#c9a227,#b8941f);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;color:#fff;font-size:28px;font-weight:700;letter-spacing:2px}}
  h1{{font-size:28px;color:#1a1a1a;text-align:center;margin:20px 0}}
  .banner{{background:{bg};border:2px solid {color};border-radius:8px;padding:18px;text-align:center;margin:30px 0;color:{color};font-size:20px;font-weight:700}}
  .grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;background:#fafafa;padding:20px;border-radius:8px;margin:20px 0}}
  .field label{{font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;display:block}}
  .field span{{font-size:15px;font-weight:600;color:#1a1a1a}}
  .footer{{margin-top:40px;display:flex;justify-content:space-between;align-items:flex-end}}
  .seal{{width:90px;height:90px;background:linear-gradient(135deg,#c9a227,#b8941f);border-radius:50%;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff}}
  .certid{{position:absolute;top:22px;right:28px;font-size:11px;color:#888}}
  .bottom{{text-align:center;margin-top:30px;padding-top:16px;border-top:1px solid #e5e5e5;font-size:11px;color:#888}}
</style></head>
<body><div class="cert">
  <div class="certid">N° {cert_id}</div>
  <div class="header">
    <div class="logo">CZ</div>
    <div style="font-size:24px;font-weight:700">CONFLICT<span style="color:#c9a227">ZERO</span></div>
    <div style="font-size:11px;letter-spacing:3px;color:#666;text-transform:uppercase">Certificación de Verificación Empresarial</div>
  </div>
  <h1>Certificado de Verificación</h1>
  <p style="text-align:center;color:#555;font-style:italic">Por medio del presente, ConflictZero certifica que:</p>
  <div style="text-align:center;margin:20px 0">
    <h2 style="font-size:24px">{data.get('sunat', {}).get('razon_social', data.get('ruc', ''))}</h2>
    <div style="color:#666">RUC: {data['ruc']}</div>
  </div>
  <div class="banner">{banner_text}</div>
  <div class="grid">
    <div class="field"><label>Estado SUNAT</label><span>{data.get('sunat', {}).get('estado', 'N/A')}</span></div>
    <div class="field"><label>Condición</label><span>{data.get('sunat', {}).get('condicion', 'N/A')}</span></div>
    <div class="field"><label>Score de Riesgo</label><span>{score}/100</span></div>
    <div class="field"><label>Nivel</label><span>{data.get('nivel_riesgo', 'N/A')}</span></div>
    <div class="field"><label>Fecha de Emisión</label><span>{datetime.utcnow().strftime('%d/%m/%Y')}</span></div>
    <div class="field"><label>Válido Hasta</label><span>{vence}</span></div>
    <div class="field" style="grid-column:span 2"><label>ID Certificado</label><span>{cert_id}</span></div>
  </div>
  <div class="footer">
    <div style="text-align:center">
      <div style="width:200px;height:1px;background:#1a1a1a;margin:0 auto 8px"></div>
      <div style="font-size:12px;color:#666"><strong>Director de Verificación</strong><br>ConflictZero S.A.C.</div>
    </div>
    <div class="seal"><span style="font-size:26px;font-weight:700">CZ</span><span style="font-size:8px;letter-spacing:1px">OFICIAL</span></div>
  </div>
  <div class="bottom">ConflictZero S.A.C. | contacto@czperu.com | www.czperu.com</div>
</div></body></html>"""


def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return options_response(event)

    ruc = (event.get('pathParameters') or {}).get('ruc', '')
    valid, msg = validate_ruc(ruc)
    if not valid:
        return error(event, 400, msg)

    scoring = get_scoring(ruc)
    if not scoring:
        return error(event, 502, 'No se pudo obtener datos de scoring')

    score = scoring.get('score', 0)
    cert_html = generate_html(scoring, score)
    cert_id = f"CZ-{ruc}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    key = f'certificados/{cert_id}.html'

    try:
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=cert_html.encode('utf-8'), ContentType='text/html')
        url = s3.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': key}, ExpiresIn=604800)
    except Exception as e:
        return error(event, 500, f'Error S3: {e}')

    return ok(event, {
        'success': True,
        'certificado': {
            'id': cert_id,
            'ruc': ruc,
            'score': score,
            'nivel_riesgo': scoring.get('nivel_riesgo'),
            'pdf_url': url,
            'fecha_emision': datetime.utcnow().isoformat() + 'Z',
        },
    })
