import sys
sys_path = '/opt/python'
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

import urllib.request
import html
import re
import json
from html.parser import HTMLParser
from utils.cors import get_cors_headers, options_response
from utils.ruc import validate_ruc
from utils.dynamo_cache import get as cache_get, put as cache_put
from utils.response import ok, error

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-PE,es;q=0.9',
}


class TableParser(HTMLParser):
    """Parser minimalista para extraer celdas de tablas HTML sin dependencias."""
    def __init__(self):
        super().__init__()
        self.rows = []
        self._current_row = []
        self._current_cell = ''
        self._in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self._current_row = []
        elif tag in ('td', 'th'):
            self._in_cell = True
            self._current_cell = ''

    def handle_endtag(self, tag):
        if tag in ('td', 'th'):
            self._current_row.append(html.unescape(self._current_cell.strip()))
            self._in_cell = False
        elif tag == 'tr':
            if self._current_row:
                self.rows.append(self._current_row)

    def handle_data(self, data):
        if self._in_cell:
            self._current_cell += data


def scrape_url(url: str) -> list[list[str]]:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as resp:
        body = resp.read().decode('utf-8', errors='replace')
    parser = TableParser()
    parser.feed(body)
    return parser.rows


def fetch_osce_inhabilitados() -> list[dict]:
    cached = cache_get('osce:inhabilitados')
    if cached:
        return cached

    url = 'http://www.osce.gob.pe/consultasenlinea/inhabilitados/inhabil_publi_mes.asp'
    try:
        rows = scrape_url(url)
    except Exception as e:
        print(f'[OSCE] Error: {e}')
        return []

    inhabilitados = []
    for row in rows:
        if len(row) < 5:
            continue
        ruc = row[3].strip()
        expediente = row[4].strip()
        if re.fullmatch(r'\d{11}', ruc) and expediente and 'TCE' not in expediente:
            inhabilitados.append({'ruc': ruc, 'entidad': 'OSCE', 'expediente': expediente, 'tipo': 'INHABILITACION'})

    cache_put('osce:inhabilitados', inhabilitados)
    return inhabilitados


def fetch_tce_inhabilitados() -> list[dict]:
    cached = cache_get('tce:inhabilitados')
    if cached:
        return cached

    url = 'http://www.osce.gob.pe/consultasenlinea/inhabilitados/inhabil_publi_mes.asp'
    try:
        rows = scrape_url(url)
    except Exception as e:
        print(f'[TCE] Error: {e}')
        return []

    inhabilitados = []
    for row in rows:
        if len(row) < 5:
            continue
        ruc = row[3].strip()
        expediente = row[4].strip()
        if re.fullmatch(r'\d{11}', ruc) and 'TCE' in expediente:
            inhabilitados.append({'ruc': ruc, 'entidad': 'TCE', 'expediente': expediente, 'tipo': 'INHABILITACION_TCE'})

    cache_put('tce:inhabilitados', inhabilitados)
    return inhabilitados


def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return options_response(event)

    ruc = (event.get('pathParameters') or {}).get('ruc', '')
    valid, msg = validate_ruc(ruc)
    if not valid:
        return error(event, 400, msg)

    try:
        osce = [s for s in fetch_osce_inhabilitados() if s['ruc'] == ruc]
        tce = [s for s in fetch_tce_inhabilitados() if s['ruc'] == ruc]
        sanciones = osce + tce
        return ok(event, {
            'ruc': ruc,
            'found': len(sanciones) > 0,
            'total': len(sanciones),
            'sanciones': sanciones,
            'fuentes': ['OSCE', 'TCE'],
        })
    except Exception as e:
        return error(event, 502, str(e))
