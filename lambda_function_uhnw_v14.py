import json
import boto3
import os
import urllib.request
import ssl
from datetime import datetime, timedelta

S3_BUCKET = os.environ.get('S3_BUCKET', 'conflictzero-certificados-prod')
BACKEND_URL = 'https://conflictzero-backend1.onrender.com'
s3_client = boto3.client('s3')

ALLOWED_ORIGINS = [
    'https://czperu.com',
    'https://www.czperu.com', 
    'https://conflictzero-certificados-prod.s3.amazonaws.com'
]

def get_cors_headers(origin=None):
    allowed = origin if origin and origin in ALLOWED_ORIGINS else 'https://czperu.com'
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': allowed,
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    }

def validate_ruc(ruc):
    if not ruc or len(ruc) != 11:
        return False, "RUC debe tener 11 digitos"
    if not ruc.isdigit():
        return False, "RUC solo debe contener numeros"
    return True, None

def get_ruc_data_complete(ruc):
    """Consulta datos completos desde el backend (SUNAT + OSCE + TCE)"""
    try:
        url = f'{BACKEND_URL}/consulta-completa/{ruc}'
        headers = {'Accept': 'application/json'}
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=20, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except Exception as e:
        print(f"Error backend: {e}")
        return None

def generate_certificate_html(data, score):
    estado = 'APROBADO' if score >= 70 else 'OBSERVADO' if score >= 40 else 'RECHAZADO'
    estado_banner = '✓ SIN PROBLEMAS DETECTADOS' if score >= 70 else '⚠ OBSERVADO' if score >= 40 else '✗ RECHAZADO'
    color_banner = '#16a34a' if score >= 70 else '#ca8a04' if score >= 40 else '#dc2626'
    bg_banner = '#dcfce7' if score >= 70 else '#fef9c3' if score >= 40 else '#fee2e2'
    
    cert_id = f"CZ-{datetime.now().strftime('%Y%m%d')}-{data['ruc'][-6:]}"
    fecha_emision = datetime.now().strftime('%d de %B de %Y')
    fecha_vencimiento = (datetime.now() + timedelta(days=90)).strftime('%d de %B de %Y')
    
    direccion = data.get('direccion', '') or 'No disponible'
    condicion = data.get('condicion', 'HABIDO')
    estado_sunat = data.get('estado_sunat', 'ACTIVO')
    
    # Determinar mensaje según score
    if score >= 70:
        mensaje = "Empresa habilitada para contratación pública"
    elif score >= 40:
        mensaje = "Empresa con observaciones menores"
    else:
        mensaje = "Empresa con restricciones para contratación"
    
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Certificado de Verificación Empresarial | Conflict Zero</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Crimson Text', serif;
            background: #f5f5f0;
            min-height: 100vh;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        
        .certificate {{
            width: 210mm;
            min-height: 297mm;
            background: #fff;
            padding: 60px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
            position: relative;
            border: 2px solid #c9a227;
        }}
        
        .certificate::before {{
            content: '';
            position: absolute;
            top: 15px;
            left: 15px;
            right: 15px;
            bottom: 15px;
            border: 1px solid #c9a227;
            pointer-events: none;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            position: relative;
        }}
        
        .logo-circle {{
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #c9a227 0%, #b8941f 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 15px;
            box-shadow: 0 4px 15px rgba(201,162,39,0.3);
        }}
        
        .logo-text {{
            color: white;
            font-size: 32px;
            font-weight: 700;
            font-family: 'Inter', sans-serif;
            letter-spacing: 2px;
        }}
        
        .company-name {{
            font-size: 28px;
            font-weight: 700;
            color: #1a1a1a;
            letter-spacing: 3px;
            margin-bottom: 5px;
        }}
        
        .subtitle {{
            font-size: 12px;
            color: #666;
            letter-spacing: 4px;
            text-transform: uppercase;
            font-family: 'Inter', sans-serif;
        }}
        
        .divider {{
            width: 200px;
            height: 2px;
            background: linear-gradient(90deg, transparent, #c9a227, transparent);
            margin: 25px auto;
            position: relative;
        }}
        
        .divider::after {{
            content: '◆';
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 0 10px;
            color: #c9a227;
            font-size: 12px;
        }}
        
        .title {{
            font-size: 32px;
            font-weight: 700;
            text-align: center;
            color: #1a1a1a;
            margin-bottom: 30px;
        }}
        
        .intro {{
            text-align: center;
            font-size: 16px;
            color: #555;
            font-style: italic;
            margin-bottom: 30px;
        }}
        
        .company-highlight {{
            text-align: center;
            margin: 30px 0;
        }}
        
        .company-highlight h2 {{
            font-size: 28px;
            font-weight: 700;
            color: #1a1a1a;
            margin-bottom: 10px;
        }}
        
        .company-highlight .ruc {{
            font-size: 18px;
            color: #666;
            font-family: 'Inter', sans-serif;
            letter-spacing: 1px;
        }}
        
        .status-banner {{
            background: {bg_banner};
            border: 2px solid {color_banner};
            border-radius: 8px;
            padding: 20px 40px;
            text-align: center;
            margin: 40px 0;
        }}
        
        .status-banner h3 {{
            font-size: 24px;
            font-weight: 700;
            color: {color_banner};
            margin-bottom: 8px;
        }}
        
        .status-banner p {{
            font-size: 14px;
            color: #555;
            font-family: 'Inter', sans-serif;
        }}
        
        .verification-section {{
            margin: 40px 0;
        }}
        
        .verification-title {{
            font-size: 14px;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 15px;
            font-family: 'Inter', sans-serif;
        }}
        
        .sources {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .source-tag {{
            background: #f5f5f0;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            color: #c9a227;
            font-family: 'Inter', sans-serif;
            border: 1px solid #c9a227;
        }}
        
        .description {{
            font-size: 15px;
            line-height: 1.6;
            color: #444;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 40px 0;
            padding: 25px;
            background: #fafafa;
            border-radius: 8px;
        }}
        
        .info-item {{
            display: flex;
            flex-direction: column;
        }}
        
        .info-label {{
            font-size: 11px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
            font-family: 'Inter', sans-serif;
        }}
        
        .info-value {{
            font-size: 15px;
            font-weight: 600;
            color: #1a1a1a;
        }}
        
        .footer {{
            margin-top: 60px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}
        
        .signature {{
            text-align: center;
        }}
        
        .signature-line {{
            width: 200px;
            height: 1px;
            background: #1a1a1a;
            margin: 0 auto 10px;
        }}
        
        .signature-text {{
            font-size: 12px;
            color: #666;
            font-family: 'Inter', sans-serif;
        }}
        
        .seal {{
            width: 100px;
            height: 100px;
            background: linear-gradient(135deg, #c9a227 0%, #b8941f 100%);
            border-radius: 50%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: white;
            font-family: 'Inter', sans-serif;
            box-shadow: 0 4px 15px rgba(201,162,39,0.3);
        }}
        
        .seal .cz {{
            font-size: 28px;
            font-weight: 700;
            letter-spacing: 2px;
        }}
        
        .seal .oficial {{
            font-size: 8px;
            letter-spacing: 1px;
            text-transform: uppercase;
        }}
        
        .cert-id {{
            position: absolute;
            top: 25px;
            right: 30px;
            font-size: 11px;
            color: #888;
            font-family: 'Inter', sans-serif;
        }}
        
        .bottom-info {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e5e5;
            font-size: 11px;
            color: #888;
            font-family: 'Inter', sans-serif;
        }}
    </style>
</head>
<body>
    <div class="certificate">
        <div class="cert-id">N° {cert_id}</div>
        
        <div class="header">
            <div class="logo-circle">
                <span class="logo-text">CZ</span>
            </div>
            <div class="company-name">CONFLICT<span style="color:#c9a227;">ZERO</span></div>
            <div class="subtitle">Certificación de Verificación Empresarial</div>
        </div>
        
        <div class="divider"></div>
        
        <h1 class="title">Certificado de Verificación</h1>
        
        <p class="intro">Por medio del presente, ConflictZero S.A.C. certifica que:</p>
        
        <div class="company-highlight">
            <h2>{data['razon_social']}</h2>
            <div class="ruc">RUC: {data['ruc']}</div>
        </div>
        
        <div class="status-banner">
            <h3>{estado_banner}</h3>
            <p>{mensaje}</p>
        </div>
        
        <div class="verification-section">
            <div class="verification-title">La empresa ha sido verificada en:</div>
            <div class="sources">
                <span class="source-tag">SUNAT</span>
                <span class="source-tag">OSCE</span>
                <span class="source-tag">TCE</span>
            </div>
            <p class="description">
                Encontrándose apta para participar en procesos de licitación y contratación con el Estado peruano, 
                conforme a la información disponible en las fuentes oficiales consultadas.
            </p>
        </div>
        
        <div class="info-grid">
            <div class="info-item">
                <span class="info-label">Fecha de emisión</span>
                <span class="info-value">{fecha_emision}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Válido hasta</span>
                <span class="info-value">{fecha_vencimiento}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Estado SUNAT</span>
                <span class="info-value">{estado_sunat}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Condición</span>
                <span class="info-value">{condicion}</span>
            </div>
            <div class="info-item" style="grid-column: span 2;">
                <span class="info-label">ID del Certificado</span>
                <span class="info-value">{cert_id}</span>
            </div>
        </div>
        
        <div class="footer">
            <div class="signature">
                <div class="signature-line"></div>
                <div class="signature-text">
                    <strong>Director de Verificación</strong><br>
                    ConflictZero S.A.C.
                </div>
            </div>
            
            <div class="seal">
                <span class="cz">CZ</span>
                <span class="oficial">Oficial</span>
            </div>
        </div>
        
        <div class="bottom-info">
            ConflictZero S.A.C. — Av. José Larco 1234, Of. 501, Miraflores, Lima — RUC 20601234567<br>
            contacto@czperu.com | www.czperu.com | Ley N° 27269
        </div>
    </div>
</body>
</html>"""

def upload_certificate_to_s3(ruc, html_content):
    try:
        cert_id = f"CZ-{ruc}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        key = f"certificados/{cert_id}.html"
        
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=html_content.encode('utf-8'),
            ContentType='text/html'
        )
        
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': key},
            ExpiresIn=604800
        )
        
        return url
    except Exception as e:
        print(f"Error S3: {e}")
        return None

def lambda_handler(event, context):
    origin = event.get('headers', {}).get('origin') or event.get('headers', {}).get('Origin', '')
    cors_headers = get_cors_headers(origin)
    
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': cors_headers, 'body': json.dumps({'message': 'OK'})}
    
    try:
        path = event.get('path', '')
        path_params = event.get('pathParameters', {}) or {}
        ruc = path_params.get('ruc', '')
        
        if not ruc:
            path_parts = path.split('/')
            for i, part in enumerate(path_parts):
                if part in ['consulta-osce', 'generar-certificado'] and i + 1 < len(path_parts):
                    ruc = path_parts[i + 1]
                    break
        
        is_valid, error_msg = validate_ruc(ruc)
        if not is_valid:
            return {'statusCode': 400, 'headers': cors_headers, 'body': json.dumps({'error': 'RUC invalido', 'message': error_msg})}
        
        # Consultar datos completos desde el backend
        data = get_ruc_data_complete(ruc)
        
        if not data:
            return {
                'statusCode': 502,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Error consultando backend', 'ruc': ruc})
            }
        
        score = data.get('score', 0)
        
        # Formatear respuesta para el frontend
        response_data = {
            'ruc': data.get('ruc', ruc),
            'razon_social': data.get('razon_social', 'NO ENCONTRADO'),
            'estado': 'LIMPIO' if score >= 70 else 'OBSERVADO' if score >= 40 else 'CRITICO',
            'condicion': data.get('sunat', {}).get('condicion', 'HABIDO'),
            'estado_sunat': data.get('sunat', {}).get('estado', 'NO ENCONTRADO'),
            'score': score,
            'sanciones': data.get('sanciones', []),
            'inhabilitaciones': [],
            'sanciones_multa': [],
            'total_registros': len(data.get('sanciones', [])),
            'direccion': data.get('sunat', {}).get('direccion', ''),
            'departamento': 'Lima',
            'provincia': 'Lima',
            'distrito': '',
            'ubigeo': data.get('sunat', {}).get('ubigeo', ''),
            'fuentes_datos': data.get('fuentes', {})
        }
        
        path_clean = path.replace('/prod/', '/').replace('/dev/', '/')
        
        if '/consulta-osce/' in path_clean:
            response = {
                'success': True,
                'data': response_data,
                'score': score,
                'timestamp': datetime.now().isoformat()
            }
        elif '/generar-certificado/' in path_clean:
            cert_html = generate_certificate_html(response_data, score)
            pdf_url = upload_certificate_to_s3(ruc, cert_html)
            if not pdf_url:
                return {'statusCode': 500, 'headers': cors_headers, 'body': json.dumps({'success': False, 'error': 'Error S3'})}
            response = {
                'success': True,
                'certificado': {
                    'id': f"CZ-{ruc}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'ruc': ruc,
                    'razon_social': response_data['razon_social'],
                    'estado': response_data['estado'],
                    'score': score,
                    'pdf_url': pdf_url,
                    'fecha_emision': datetime.now().isoformat()
                }
            }
        else:
            return {'statusCode': 404, 'headers': cors_headers, 'body': json.dumps({'error': 'Endpoint no encontrado'})}
        
        return {'statusCode': 200, 'headers': cors_headers, 'body': json.dumps(response, default=str)}
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'statusCode': 500, 'headers': cors_headers, 'body': json.dumps({'error': 'Error interno', 'message': str(e)})}
