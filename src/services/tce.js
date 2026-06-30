'use strict';

const axios = require('axios');
const cheerio = require('cheerio');
const { cached } = require('./cache');

const TCE_URL = 'http://www.osce.gob.pe/consultasenlinea/inhabilitados/inhabil_publi_mes.asp';
const HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Accept-Language': 'es-PE,es;q=0.9',
};

async function fetchInhabilitados() {
  return cached('tce', async () => {
    const response = await axios.get(TCE_URL, { timeout: 30000, headers: HEADERS });
    const $ = cheerio.load(response.data);
    const inhabilitados = [];

    $('table').each((tableIdx, table) => {
      $(table).find('tr').each((i, row) => {
        if (i === 0) return;
        const cols = $(row).find('td');
        if (cols.length < 4) return;

        let ruc = '';
        let expediente = '';
        let tipo = '';

        cols.each((j, col) => {
          const text = $(col).text().trim();
          if (!ruc && /^\d{11}$/.test(text)) ruc = text;
          else if (!expediente && (text.includes('TCE') || text.includes('EXP'))) expediente = text;
          else if (!tipo && text.length > 3 && text.length < 50) tipo = text;
        });

        if (ruc && expediente && expediente.includes('TCE')) {
          inhabilitados.push({
            ruc,
            entidad: 'TCE',
            expediente,
            tipo_sancion: tipo || 'INHABILITACION',
            fecha: new Date().toISOString().split('T')[0],
          });
        }
      });
    });

    return { total: inhabilitados.length, inhabilitados, fuente: 'tce_scraper', timestamp: new Date().toISOString() };
  });
}

async function buscarPorRUC(ruc) {
  const data = await fetchInhabilitados();
  const found = data.inhabilitados.filter(i => i.ruc === ruc);
  return { found: found.length > 0, total: found.length, data: found };
}

module.exports = { fetchInhabilitados, buscarPorRUC };
