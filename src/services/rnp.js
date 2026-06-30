'use strict';

const axios = require('axios');
const cheerio = require('cheerio');
const { cached } = require('./cache');

const RNP_URL = 'https://www.rnp.gob.pe/consultasenlinea/inhabilitados/busqueda_vnv.asp?action=enviar&valor=4';
const HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Accept-Language': 'es-PE,es;q=0.9',
};

async function fetchSanciones() {
  return cached('rnp', async () => {
    const response = await axios.get(RNP_URL, { timeout: 30000, headers: HEADERS });
    const $ = cheerio.load(response.data);
    const inhabilitados = [];
    const multas = [];

    $('table').each((tableIdx, table) => {
      const isMultaTable = $(table).text().toLowerCase().includes('monto de multa');

      $(table).find('tr').each((i, row) => {
        if (i === 0) return;
        const cols = $(row).find('td');
        if (cols.length < 4) return;

        let ruc = '', razonSocial = '', resolucion = '', fecha = '', estado = '';

        cols.each((j, col) => {
          const text = $(col).text().trim();
          if (!ruc && /^\d{11}$/.test(text)) ruc = text;
          else if (!razonSocial && text.length > 10 && !/^\d+$/.test(text)) razonSocial = text;
          else if (!resolucion && /\d+-\d{4}-(TCP|TCE)-S\d+/.test(text)) resolucion = text;
          else if (!fecha && /^\d{2}\/\d{2}\/\d{4}$/.test(text)) fecha = text;
          else if (text === 'VIGENTE' || text === 'NO VIGENTE') estado = text;
        });

        if (ruc) {
          const item = { ruc, razon_social: razonSocial, entidad: 'RNP', resolucion, fecha, tipo_sancion: isMultaTable ? 'MULTA' : 'INHABILITACION', estado: estado || 'DESCONOCIDO' };
          isMultaTable ? multas.push(item) : inhabilitados.push(item);
        }
      });
    });

    return { total: inhabilitados.length + multas.length, inhabilitados, multas, fuente: 'rnp_scraper', timestamp: new Date().toISOString() };
  });
}

async function buscarPorRUC(ruc) {
  const data = await fetchSanciones();
  return {
    found: data.inhabilitados.some(i => i.ruc === ruc) || data.multas.some(m => m.ruc === ruc),
    inhabilitados: data.inhabilitados.filter(i => i.ruc === ruc),
    multas: data.multas.filter(m => m.ruc === ruc),
  };
}

module.exports = { fetchSanciones, buscarPorRUC };
