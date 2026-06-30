'use strict';

const axios = require('axios');
const cheerio = require('cheerio');
const { cached } = require('./cache');

const OSCE_URL = 'http://www.osce.gob.pe/consultasenlinea/inhabilitados/inhabil_publi_mes.asp';
const HEADERS = { 'User-Agent': 'Mozilla/5.0' };

async function fetchInhabilitados() {
  return cached('osce', async () => {
    const response = await axios.get(OSCE_URL, { timeout: 30000, headers: HEADERS });
    const $ = cheerio.load(response.data);
    const inhabilitados = [];

    $('table tr').each((i, row) => {
      const cols = $(row).find('td');
      if (cols.length >= 4) {
        const ruc = $(cols[3]).text().trim();
        const expediente = $(cols[4]).text().trim();
        if (ruc && /^\d{11}$/.test(ruc) && expediente && !expediente.includes('TCE')) {
          inhabilitados.push({ ruc, entidad: 'OSCE', expediente, tipo: 'INHABILITACION' });
        }
      }
    });

    return { total: inhabilitados.length, inhabilitados, fuente: 'osce_scraper' };
  });
}

async function buscarPorRUC(ruc) {
  const data = await fetchInhabilitados();
  const found = data.inhabilitados.filter(i => i.ruc === ruc);
  return { found: found.length > 0, total: found.length, data: found };
}

module.exports = { fetchInhabilitados, buscarPorRUC };
