'use strict';

const axios = require('axios');
const cheerio = require('cheerio');
const { cached } = require('./cache');

const SUNAFIL_URLS = [
  { cat: 'sst', nombre: 'Seguridad y Salud en el Trabajo', url: 'https://www.sunafil.gob.pe/empresas-sancionadas/seguridad-y-salud-en-el-trabajo' },
  { cat: 'accidentes', nombre: 'Accidentes Mortales', url: 'https://www.sunafil.gob.pe/empresas-sancionadas/accidentes-mortales' },
  { cat: 'trabajo_infantil', nombre: 'Trabajo Infantil', url: 'https://www.sunafil.gob.pe/empresas-sancionadas/trabajo-infantil' },
  { cat: 'discriminacion', nombre: 'Discriminación', url: 'https://www.sunafil.gob.pe/empresas-sancionadas/igualdad-y-no-discriminacion' },
];

const HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Accept-Language': 'es-ES,es;q=0.9',
};

async function fetchSanciones() {
  return cached('sunafil', async () => {
    // Primero intento con Playwright (más confiable)
    try {
      const { chromium } = require('playwright');
      const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
      });
      const page = await (await browser.newContext({ userAgent: HEADERS['User-Agent'] })).newPage();
      const todasSanciones = [];

      for (const item of SUNAFIL_URLS) {
        try {
          await page.goto(item.url, { waitUntil: 'networkidle', timeout: 20000 });
          await page.waitForSelector('table tbody tr', { timeout: 10000 });

          const sanciones = await page.evaluate(({ cat, nombre }) => {
            return [...document.querySelectorAll('table tbody tr')].reduce((acc, fila) => {
              const celdas = fila.querySelectorAll('td');
              if (celdas.length >= 3) {
                const ruc = (celdas[1]?.textContent?.trim() || '').replace(/\D/g, '');
                if (ruc.length === 11) {
                  acc.push({
                    ruc,
                    razon_social: celdas[0]?.textContent?.trim() || '',
                    categoria: cat,
                    categoria_nombre: nombre,
                    resolucion: celdas[2]?.textContent?.trim() || '',
                    estado: 'VIGENTE',
                  });
                }
              }
              return acc;
            }, []);
          }, { cat: item.cat, nombre: item.nombre });

          todasSanciones.push(...sanciones);
        } catch (e) {
          console.warn(`[SUNAFIL] Error en categoría ${item.cat}: ${e.message}`);
        }
      }

      await browser.close();
      if (todasSanciones.length > 0) {
        return { total: todasSanciones.length, sanciones: todasSanciones, fuente: 'sunafil_playwright', timestamp: new Date().toISOString() };
      }
    } catch (e) {
      console.warn('[SUNAFIL] Playwright falló, usando axios fallback:', e.message);
    }

    // Fallback con axios
    const todasSanciones = [];
    for (const item of SUNAFIL_URLS.slice(0, 2)) {
      try {
        const response = await axios.get(item.url, { headers: HEADERS, timeout: 8000 });
        const $ = cheerio.load(response.data);
        $('table tbody tr').each((i, elem) => {
          const celdas = $(elem).find('td');
          if (celdas.length >= 3) {
            const ruc = $(celdas[1]).text().trim().replace(/\D/g, '');
            if (ruc.length === 11) {
              todasSanciones.push({ ruc, razon_social: $(celdas[0]).text().trim(), categoria: item.cat, categoria_nombre: item.nombre, estado: 'VIGENTE' });
            }
          }
        });
      } catch (e) {}
    }

    return { total: todasSanciones.length, sanciones: todasSanciones, fuente: 'sunafil_axios', timestamp: new Date().toISOString() };
  });
}

async function buscarPorRUC(ruc) {
  const data = await fetchSanciones();
  const sanciones = data.sanciones.filter(s => s.ruc === ruc);
  return { found: sanciones.length > 0, total: sanciones.length, sanciones };
}

module.exports = { fetchSanciones, buscarPorRUC };
