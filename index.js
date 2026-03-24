const express = require('express');
const axios = require('axios');
const cheerio = require('cheerio');

// SendGrid configuration
const sgMail = require('@sendgrid/mail');
const SENDGRID_API_KEY = process.env.SENDGRID_API_KEY || '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';
sgMail.setApiKey(SENDGRID_API_KEY);

const app = express();
const PORT = process.env.PORT || 10000;
const BUSCARUC_TOKEN = process.env.BUSCARUC_TOKEN || 'eyJ1c2VySWQiOjU0NzAsInVzZXJUb2tlbklkIjo1NDY5fQ.QK8EdbO21g2rCk3jqUqdOf3pKKhNZqymmG30RTbMURhtp7-JPJcPX3xHXAaH46qAoHrTnQLgqTGo1yY1zu64QfPvLux0EbX2R9V_1tAy8Fdos2-Z-_XXTe7Wi0lRTBK55uh_zCm5zCiYs7VJBW4T9e2mZdd6EaXYaXOwEybmseE';

let osceCache = { data: null, timestamp: null };
let tceCache = { data: null, timestamp: null };

app.use(express.json());
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type');
    next();
});

app.get('/health', (req, res) => {
    res.json({ status: 'online', timestamp: new Date().toISOString() });
});

app.get('/sunat/ruc/:ruc', async (req, res) => {
    const { ruc } = req.params;
    if (!ruc || ruc.length !== 11 || !/^\d+$/.test(ruc)) {
        return res.status(400).json({ error: 'RUC invalido' });
    }
    try {
        const response = await axios.post('https://buscaruc.com/api/v1/ruc', {
            token: BUSCARUC_TOKEN,
            ruc: ruc
        }, {
            headers: { 'Content-Type': 'application/json' },
            timeout: 15000
        });
        const data = response.data;
        if (!data.success || !data.result) {
            return res.status(404).json({ error: 'RUC no encontrado', ruc });
        }
        const r = data.result;
        res.json({
            ruc: r.ruc || ruc,
            razon_social: r.social_reason || '',
            estado: r.taxpayer_state || 'ACTIVO',
            condicion: r.domicile_condition || 'HABIDO',
            direccion: r.address || '',
            ubigeo: r.ubigeo || '',
            fuente: 'buscaruc_com'
        });
    } catch (error) {
        res.status(502).json({ error: error.message });
    }
});

async function scrapeOSCE() {
    const now = Date.now();
    if (osceCache.data && osceCache.timestamp && (now - osceCache.timestamp) < 1800000) {
        return osceCache.data;
    }
    try {
        const response = await axios.get('http://www.osce.gob.pe/consultasenlinea/inhabilitados/inhabil_publi_mes.asp', {
            timeout: 30000,
            headers: { 'User-Agent': 'Mozilla/5.0' }
        });
        const $ = cheerio.load(response.data);
        const inhabilitados = [];
        
        // Buscar en tablas
        $('table tr').each((i, row) => {
            const cols = $(row).find('td');
            if (cols.length >= 4) {
                const ruc = $(cols[3]).text().trim();
                const expediente = $(cols[4]).text().trim();
                
                if (ruc && ruc.match(/^\d{11}$/) && expediente && !expediente.includes('TCE')) {
                    inhabilitados.push({
                        ruc,
                        entidad: 'OSCE',
                        expediente: expediente,
                        tipo: 'INHABILITACION'
                    });
                }
            }
        });
        
        const resultado = { total: inhabilitados.length, inhabilitados, fuente: 'osce_scraper' };
        osceCache = { data: resultado, timestamp: now };
        return resultado;
    } catch (error) {
        return { total: 0, inhabilitados: [], error: error.message };
    }
}

// ==================== TCE - MEJORADO ====================
async function scrapeTCE() {
    const now = Date.now();
    if (tceCache.data && tceCache.timestamp && (now - tceCache.timestamp) < 1800000) {
        return tceCache.data;
    }
    try {
        // Intentar múltiples fuentes de datos TCE
        const response = await axios.get('http://www.osce.gob.pe/consultasenlinea/inhabilitados/inhabil_publi_mes.asp', {
            timeout: 30000,
            headers: { 
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'es-PE,es;q=0.9'
            }
        });
        
        const $ = cheerio.load(response.data);
        const inhabilitados = [];
        
        // DEBUG: Log para ver qué encontramos
        console.log('TCE Scraper - Tablas encontradas:', $('table').length);
        
        // La estructura de la página de OSCE/TCE tiene tablas con clase específica
        $('table').each((tableIndex, table) => {
            const rows = $(table).find('tr');
            console.log(`Tabla ${tableIndex}: ${rows.length} filas`);
            
            rows.each((i, row) => {
                if (i === 0) return; // Saltar header
                
                const cols = $(row).find('td');
                console.log(`Fila ${i}: ${cols.length} columnas`);
                
                if (cols.length >= 4) {
                    // Intentar diferentes índices de columna
                    let ruc = '';
                    let expediente = '';
                    let tipo = '';
                    
                    for (let j = 0; j < cols.length; j++) {
                        const texto = $(cols[j]).text().trim();
                        console.log(`  Col ${j}: "${texto.substring(0, 30)}"`);
                        
                        // Detectar RUC (11 dígitos)
                        if (!ruc && texto.match(/^\d{11}$/)) {
                            ruc = texto;
                        }
                        // Detectar expediente TCE
                        else if (!expediente && (texto.includes('TCE') || texto.includes('EXP'))) {
                            expediente = texto;
                        }
                        // Detectar tipo
                        else if (!tipo && texto.length > 3 && texto.length < 50) {
                            tipo = texto;
                        }
                    }
                    
                    console.log(`  -> Detectado: RUC=${ruc}, EXP=${expediente}, TIPO=${tipo}`);
                    
                    if (ruc && expediente && expediente.includes('TCE')) {
                        inhabilitados.push({
                            ruc,
                            entidad: 'TCE',
                            expediente: expediente,
                            tipo_sancion: tipo || 'INHABILITACION',
                            fecha: new Date().toISOString().split('T')[0]
                        });
                        console.log('  -> AGREGADO A TCE');
                    } else if (ruc && expediente && !expediente.includes('TCE')) {
                        // Es OSCE
                        console.log('  -> ES OSCE, no TCE');
                    }
                }
            });
        });
        
        console.log(`TCE Scraper - Total encontrados: ${inhabilitados.length}`);
        
        const resultado = { total: inhabilitados.length, inhabilitados, fuente: 'tce_scraper_v2', timestamp: new Date().toISOString() };
        tceCache = { data: resultado, timestamp: now };
        return resultado;
    } catch (error) {
        console.error('TCE Scraper Error:', error.message);
        return { total: 0, inhabilitados: [], error: error.message, fuente: 'tce_scraper_error' };
    }
}

// Endpoint de debug para ver raw data
app.get('/debug/tce-raw', async (req, res) => {
    try {
        const response = await axios.get('http://www.osce.gob.pe/consultasenlinea/inhabilitados/inhabil_publi_mes.asp', {
            timeout: 30000,
            headers: { 'User-Agent': 'Mozilla/5.0' }
        });
        // Devolver primeros 5000 caracteres para ver estructura
        res.json({ 
            preview: response.data.substring(0, 5000),
            length: response.data.length,
            tables: (response.data.match(/<table/g) || []).length
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/tce/inhabilitados', async (req, res) => {
    const data = await scrapeTCE();
    res.json(data);
});

app.get('/tce/ruc/:ruc', async (req, res) => {
    const { ruc } = req.params;
    const data = await scrapeTCE();
    const found = data.inhabilitados.filter(i => i.ruc === ruc);
    res.json({ found: found.length > 0, total: found.length, data: found });
});
// ====================================================

// ==================== RNP - NUEVO ====================
let rnpCache = { data: null, timestamp: null };

async function scrapeRNP() {
    const now = Date.now();
    if (rnpCache.data && rnpCache.timestamp && (now - rnpCache.timestamp) < 1800000) {
        return rnpCache.data;
    }
    try {
        // URL de inhabilitados definitivos
        const response = await axios.get('https://www.rnp.gob.pe/consultasenlinea/inhabilitados/busqueda_vnv.asp?action=enviar&valor=4', {
            timeout: 30000,
            headers: { 
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'es-PE,es;q=0.9'
            }
        });
        
        const $ = cheerio.load(response.data);
        const inhabilitados = [];
        const multas = [];
        
        console.log('RNP Scraper - Tablas encontradas:', $('table').length);
        
        // Buscar en todas las tablas
        $('table').each((tableIndex, table) => {
            const rows = $(table).find('tr');
            let isMultaTable = false;
            
            // Detectar si es tabla de multas por el encabezado
            const headerText = $(table).text().toLowerCase();
            if (headerText.includes('monto de multa') || headerText.includes('s/.')) {
                isMultaTable = true;
            }
            
            rows.each((i, row) => {
                if (i === 0) return; // Saltar header
                
                const cols = $(row).find('td');
                if (cols.length >= 4) {
                    let ruc = '';
                    let razonSocial = '';
                    let resolucion = '';
                    let fecha = '';
                    let tipo = isMultaTable ? 'MULTA' : 'INHABILITACION';
                    let estado = '';
                    
                    cols.each((j, col) => {
                        const texto = $(col).text().trim();
                        
                        // Detectar RUC (11 dígitos)
                        if (!ruc && texto.match(/^\d{11}$/)) {
                            ruc = texto;
                        }
                        // Razón social (texto largo, no números)
                        else if (!razonSocial && texto.length > 10 && !texto.match(/^\d+$/)) {
                            razonSocial = texto;
                        }
                        // Resolución (formato XXX-YYYY-TCP/TCE-SX)
                        else if (!resolucion && texto.match(/\d+-\d{4}-(TCP|TCE)-S\d+/)) {
                            resolucion = texto;
                        }
                        // Fecha (formato DD/MM/YYYY)
                        else if (!fecha && texto.match(/^\d{2}\/\d{2}\/\d{4}$/)) {
                            fecha = texto;
                        }
                        // Estado
                        else if (texto === 'VIGENTE' || texto === 'NO VIGENTE') {
                            estado = texto;
                        }
                    });
                    
                    if (ruc) {
                        const item = {
                            ruc,
                            razon_social: razonSocial,
                            entidad: 'RNP',
                            resolucion,
                            fecha,
                            tipo_sancion: tipo,
                            estado: estado || 'DESCONOCIDO'
                        };
                        
                        if (isMultaTable) {
                            multas.push(item);
                        } else {
                            inhabilitados.push(item);
                        }
                    }
                }
            });
        });
        
        console.log(`RNP Scraper - Inhabilitados: ${inhabilitados.length}, Multas: ${multas.length}`);
        
        const resultado = { 
            total: inhabilitados.length + multas.length,
            inhabilitados, 
            multas,
            fuente: 'rnp_scraper', 
            timestamp: new Date().toISOString() 
        };
        rnpCache = { data: resultado, timestamp: now };
        return resultado;
    } catch (error) {
        console.error('RNP Scraper Error:', error.message);
        return { total: 0, inhabilitados: [], multas: [], error: error.message, fuente: 'rnp_scraper_error' };
    }
}

app.get('/rnp/inhabilitados', async (req, res) => {
    const data = await scrapeRNP();
    res.json(data);
});

app.get('/rnp/ruc/:ruc', async (req, res) => {
    const { ruc } = req.params;
    const data = await scrapeRNP();
    const inhabilitados = data.inhabilitados.filter(i => i.ruc === ruc);
    const multas = data.multas.filter(m => m.ruc === ruc);
    res.json({ 
        found: inhabilitados.length > 0 || multas.length > 0, 
        total_inhabilitaciones: inhabilitados.length,
        total_multas: multas.length,
        inhabilitados, 
        multas 
    });
});
// ====================================================

// ====================================================
// ==================== SUNAFIL SCRAPER ===============
// ====================================================
let sunafilCache = { data: null, timestamp: null };

// ==================== SUNAFIL SCRAPER (PLAYWRIGHT) ====
// =====================================================

async function scrapeSUNAFILWithPlaywright() {
    console.log('Scrapeando SUNAFIL con Playwright...');
    
    let browser;
    try {
        // Importar playwright
        const { chromium } = require('playwright');
        
        // Launch options para entornos cloud (Render)
        browser = await chromium.launch({
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920,1080'
            ]
        });
        
        const context = await browser.newContext({
            viewport: { width: 1920, height: 1080 },
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        });
        
        const page = await context.newPage();
        
        const todasSanciones = [];
        const categorias = {
            sst: [], accidentes: [], trabajo_infantil: [], discriminacion: []
        };
        
        const urls = [
            { cat: 'sst', nombre: 'Seguridad y Salud en el Trabajo', url: 'https://www.sunafil.gob.pe/empresas-sancionadas/seguridad-y-salud-en-el-trabajo' },
            { cat: 'accidentes', nombre: 'Accidentes Mortales', url: 'https://www.sunafil.gob.pe/empresas-sancionadas/accidentes-mortales' },
            { cat: 'trabajo_infantil', nombre: 'Trabajo Infantil', url: 'https://www.sunafil.gob.pe/empresas-sancionadas/trabajo-infantil' },
            { cat: 'discriminacion', nombre: 'Discriminacion', url: 'https://www.sunafil.gob.pe/empresas-sancionadas/igualdad-y-no-discriminacion' }
        ];
        
        for (const item of urls) {
            try {
                console.log(`  Navegando ${item.cat}...`);
                
                await page.goto(item.url, { 
                    waitUntil: 'networkidle', 
                    timeout: 20000 
                });
                
                // Esperar a que cargue la tabla
                await page.waitForSelector('table tbody tr', { timeout: 10000 });
                
                // Extraer datos
                const sancionesCat = await page.evaluate(({ categoria, categoriaNombre }) => {
                    const filas = document.querySelectorAll('table tbody tr');
                    const datos = [];
                    
                    filas.forEach(fila => {
                        const celdas = fila.querySelectorAll('td');
                        if (celdas.length >= 3) {
                            const razonSocial = celdas[0]?.textContent?.trim() || '';
                            const rucTexto = celdas[1]?.textContent?.trim() || '';
                            const ruc = rucTexto.replace(/\D/g, '');
                            const resolucion = celdas[2]?.textContent?.trim() || '';
                            
                            if (ruc && ruc.length === 11) {
                                datos.push({
                                    ruc,
                                    razon_social: razonSocial,
                                    categoria,
                                    categoria_nombre: categoriaNombre,
                                    resolucion,
                                    estado: 'VIGENTE',
                                    fecha_extraccion: new Date().toISOString()
                                });
                            }
                        }
                    });
                    
                    return datos;
                }, { categoria: item.cat, categoriaNombre: item.nombre });
                
                todasSanciones.push(...sancionesCat);
                categorias[item.cat] = sancionesCat;
                console.log(`    ${sancionesCat.length} sanciones`);
                
            } catch (err) {
                console.log(`    Error ${item.cat}: ${err.message}`);
            }
        }
        
        await browser.close();
        
        return {
            total: todasSanciones.length,
            sanciones: todasSanciones,
            categorias,
            fuente: 'sunafil_portal_playwright',
            timestamp: new Date().toISOString(),
            nota: `Datos extraidos con Playwright: ${todasSanciones.length} sanciones laborales`
        };
        
    } catch (error) {
        console.error('SUNAFIL Playwright Error:', error.message);
        if (browser) await browser.close();
        return null;
    }
}

async function scrapeSUNAFIL() {
    const now = new Date();
    const CACHE_DURATION = 30 * 60 * 1000;
    
    if (sunafilCache.data && sunafilCache.timestamp && (now - sunafilCache.timestamp) < CACHE_DURATION) {
        console.log('Retornando SUNAFIL desde cache');
        return sunafilCache.data;
    }
    
    // Intentar con Playwright primero
    const playwrightData = await scrapeSUNAFILWithPlaywright();
    if (playwrightData && playwrightData.total > 0) {
        sunafilCache = { data: playwrightData, timestamp: now };
        return playwrightData;
    }
    
    // Fallback: Intentar con axios (por si acaso)
    console.log('Puppeteer fallo, intentando axios...');
    
    try {
        const headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9'
        };
        
        const urls = [
            { cat: 'sst', nombre: 'Seguridad y Salud en el Trabajo', url: 'https://www.sunafil.gob.pe/empresas-sancionadas/seguridad-y-salud-en-el-trabajo' },
            { cat: 'accidentes', nombre: 'Accidentes Mortales', url: 'https://www.sunafil.gob.pe/empresas-sancionadas/accidentes-mortales' }
        ];
        
        const todasSanciones = [];
        const categorias = { sst: [], accidentes: [], trabajo_infantil: [], discriminacion: [] };
        
        for (const item of urls) {
            try {
                const response = await axios.get(item.url, { headers, timeout: 8000 });
                const $ = cheerio.load(response.data);
                const filas = $('table tbody tr');
                
                filas.each((i, elem) => {
                    const celdas = $(elem).find('td');
                    if (celdas.length >= 3) {
                        const ruc = $(celdas[1]).text().trim().replace(/\D/g, '');
                        const razonSocial = $(celdas[0]).text().trim();
                        
                        if (ruc && ruc.length === 11) {
                            const sancion = {
                                ruc, razon_social: razonSocial,
                                categoria: item.cat, categoria_nombre: item.nombre,
                                estado: 'VIGENTE', fecha_extraccion: new Date().toISOString()
                            };
                            todasSanciones.push(sancion);
                            categorias[item.cat].push(sancion);
                        }
                    }
                });
            } catch (e) {}
        }
        
        const resultado = {
            total: todasSanciones.length,
            sanciones: todasSanciones,
            categorias,
            fuente: 'sunafil_portal_axios',
            timestamp: new Date().toISOString(),
            nota: todasSanciones.length > 0 ? 'Datos extraidos' : 'Portal protegido - datos no disponibles'
        };
        
        sunafilCache = { data: resultado, timestamp: now };
        return resultado;
        
    } catch (error) {
        const resultado = {
            total: 0, sanciones: [], categorias: { sst: [], accidentes: [], trabajo_infantil: [], discriminacion: [] },
            fuente: 'sunafil_error', timestamp: new Date().toISOString(),
            nota: 'Error accediendo a SUNAFIL: ' + error.message
        };
        sunafilCache = { data: resultado, timestamp: now };
        return resultado;
    }
}

app.get('/sunafil/sanciones', async (req, res) => {
    const data = await scrapeSUNAFIL();
    res.json(data);
});

app.get('/sunafil/ruc/:ruc', async (req, res) => {
    const { ruc } = req.params;
    const data = await scrapeSUNAFIL();
    const sanciones = data.sanciones.filter(s => s.ruc === ruc);
    res.json({ 
        found: sanciones.length > 0, 
        total: sanciones.length,
        sanciones 
    });
});
// ====================================================

// ====================================================
// ==================== INDECOPI SCRAPER ==============
// ====================================================
let indecopiCache = { data: null, timestamp: null };

async function scrapeINDECOPI() {
    const now = new Date();
    const CACHE_DURATION = 30 * 60 * 1000;
    
    if (indecopiCache.data && indecopiCache.timestamp && (now - indecopiCache.timestamp) < CACHE_DURATION) {
        console.log('Retornando INDECOPI desde cache');
        return indecopiCache.data;
    }
    
    console.log('Scrapeando INDECOPI...');
    
    // INDECOPI no tiene listado publico masivo
    // Solo consulta por RUC especifico
    const resultado = {
        total: 0,
        sanciones: [],
        fuente: 'indecopi_mira_a_quien_le_compras',
        timestamp: new Date().toISOString(),
        nota: 'INDECOPI requiere busqueda por RUC especifico. Use /indecopi/ruc/:ruc',
        url_consulta: 'https://www.indecoopi.gob.pe/mira-a-quien-le-compras'
    };
    
    indecopiCache = { data: resultado, timestamp: now };
    return resultado;
}

app.get('/indecopi/sanciones', async (req, res) => {
    const data = await scrapeINDECOPI();
    res.json(data);
});

app.get('/indecopi/ruc/:ruc', async (req, res) => {
    const { ruc } = req.params;
    
    try {
        // Intentar buscar en el portal "Mira a quién le compras"
        const searchUrl = `https://www.indecoopi.gob.pe/mira-a-quien-le-compras?ruc=${ruc}`;
        
        const headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9'
        };
        
        const response = await axios.get(searchUrl, { headers, timeout: 15000 });
        const $ = cheerio.load(response.data);
        
        // Buscar resultados en la página
        const sanciones = [];
        
        $('.resultado-sancion, .sancion-item, table tbody tr').each((i, elem) => {
            const celdas = $(elem).find('td');
            if (celdas.length >= 2) {
                const tipo = $(celdas[0]).text().trim();
                const fecha = $(celdas[1]).text().trim();
                const monto = $(celdas[2]) ? $(celdas[2]).text().trim() : '';
                
                sanciones.push({
                    tipo_sancion: tipo,
                    fecha,
                    monto,
                    estado: 'VIGENTE',
                    fuente: 'INDECOPI'
                });
            }
        });
        
        res.json({
            found: sanciones.length > 0,
            ruc,
            total: sanciones.length,
            sanciones,
            url_consulta: searchUrl,
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        res.json({
            found: false,
            ruc,
            sanciones: [],
            nota: 'Consulta INDECOPI por RUC requiere automatización avanzada de formulario',
            url_manual: `https://www.indecoopi.gob.pe/mira-a-quien-le-compras?ruc=${ruc}`,
            error: error.message
        });
    }
});
// ====================================================

// ==================== SUNARP SCRAPER ================
// Superintendencia Nacional de los Registros Publicos
// Consulta de propiedades inmuebles y vehiculos
// ====================================================
let sunarpCache = { data: null, timestamp: null };

async function scrapeSUNARP() {
    const now = new Date();
    const CACHE_DURATION = 60 * 60 * 1000; // 1 hora
    
    if (sunarpCache.data && sunarpCache.timestamp && (now - sunarpCache.timestamp) < CACHE_DURATION) {
        console.log('Retornando SUNARP desde cache');
        return sunarpCache.data;
    }
    
    try {
        // SUNARP no tiene una lista publica descargable
        // La consulta es por RUC/DNI especifico
        // Retornamos estructura base indicando como consultar
        
        const resultado = {
            total: 0,
            propiedades: [],
            fuente: 'sunarp_portal',
            timestamp: new Date().toISOString(),
            nota: 'SUNARP requiere consulta por RUC especifico. Usar /sunarp/ruc/:ruc',
            url_base: 'https://www.sunarp.gob.pe',
            servicios: {
                consulta_inmuebles: 'https://www.sunarp.gob.pe/consulta-inmuebles/',
                consulta_vehicular: 'https://www.sunarp.gob.pe/consulta-vehicular/',
                consulta_titularidad: 'https://www.sunarp.gob.pe/consulta-titularidad/'
            }
        };
        
        sunarpCache = { data: resultado, timestamp: now };
        return resultado;
        
    } catch (error) {
        console.error('SUNARP Error:', error.message);
        return {
            total: 0,
            propiedades: [],
            fuente: 'sunarp_error',
            timestamp: new Date().toISOString(),
            error: error.message
        };
    }
}

async function consultaSUNARPPorRUC(ruc) {
    try {
        // SUNARP tiene proteccion CAPTCHA en consultas automatizadas
        // Intentamos obtener informacion basica del portal de titularidad
        
        const consultaUrl = `https://www.sunarp.gob.pe/consulta-titularidad/?tipo=2&numero=${ruc}`;
        
        const headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-PE,es;q=0.9'
        };
        
        const response = await axios.get(consultaUrl, { headers, timeout: 15000 });
        const $ = cheerio.load(response.data);
        
        const propiedades = [];
        
        // Buscar resultados de titularidad
        $('.resultado-titularidad, .propiedad-item, table tbody tr').each((i, elem) => {
            const celdas = $(elem).find('td');
            if (celdas.length >= 3) {
                const tipo = $(celdas[0]).text().trim();
                const partida = $(celdas[1]).text().trim();
                const direccion = $(celdas[2]).text().trim();
                
                if (partida && partida.length > 3) {
                    propiedades.push({
                        tipo: tipo || 'INMUEBLE',
                        partida_registral: partida,
                        direccion,
                        estado: 'REGISTRADO',
                        fuente: 'SUNARP'
                    });
                }
            }
        });
        
        return {
            found: propiedades.length > 0,
            ruc,
            total: propiedades.length,
            propiedades,
            url_consulta: consultaUrl,
            timestamp: new Date().toISOString(),
            nota: propiedades.length > 0 
                ? 'Propiedades encontradas en SUNARP' 
                : 'No se encontraron propiedades registradas o el portal requiere CAPTCHA'
        };
        
    } catch (error) {
        return {
            found: false,
            ruc,
            propiedades: [],
            nota: 'Consulta SUNARP requiere verificacion CAPTCHA',
            url_manual: `https://www.sunarp.gob.pe/consulta-titularidad/?tipo=2&numero=${ruc}`,
            error: error.message,
            timestamp: new Date().toISOString()
        };
    }
}

app.get('/sunarp/propiedades', async (req, res) => {
    const data = await scrapeSUNARP();
    res.json(data);
});

app.get('/sunarp/ruc/:ruc', async (req, res) => {
    const { ruc } = req.params;
    if (!ruc || ruc.length !== 11 || !/^\d+$/.test(ruc)) {
        return res.status(400).json({ error: 'RUC invalido' });
    }
    
    const data = await consultaSUNARPPorRUC(ruc);
    res.json(data);
});
// ====================================================

app.get('/osce/inhabilitados', async (req, res) => {
    const data = await scrapeOSCE();
    res.json(data);
});

app.get('/osce/ruc/:ruc', async (req, res) => {
    const { ruc } = req.params;
    const data = await scrapeOSCE();
    const found = data.inhabilitados.find(i => i.ruc === ruc);
    res.json({ found: !!found, data: found });
});

app.get('/consulta-completa/:ruc', async (req, res) => {
    const { ruc } = req.params;
    
    const [sunatRes, osceData, tceData, rnpData, sunafilData, indecopiData, sunarpData] = await Promise.allSettled([
        axios.post('https://buscaruc.com/api/v1/ruc', {
            token: BUSCARUC_TOKEN,
            ruc
        }, { headers: { 'Content-Type': 'application/json' } }),
        scrapeOSCE(),
        scrapeTCE(),
        scrapeRNP(),
        scrapeSUNAFIL(),  // NUEVO: SUNAFIL
        scrapeINDECOPI(),  // NUEVO: INDECOPI
        consultaSUNARPPorRUC(ruc)  // NUEVO: SUNARP
    ]);
    
    let sunat = null;
    if (sunatRes.status === 'fulfilled' && sunatRes.value.data.success) {
        const r = sunatRes.value.data.result;
        sunat = {
            ruc: r.ruc,
            razon_social: r.social_reason,
            estado: r.taxpayer_state,
            condicion: r.domicile_condition,
            direccion: r.address
        };
    }
    
    const osceSanciones = osceData.status === 'fulfilled' 
        ? osceData.value.inhabilitados.filter(i => i.ruc === ruc) 
        : [];
    
    // Sanciones TCE
    const tceSanciones = tceData.status === 'fulfilled'
        ? tceData.value.inhabilitados.filter(i => i.ruc === ruc)
        : [];
    
    // Sanciones RNP (inhabilitaciones + multas)
    const rnpInhabilitaciones = rnpData.status === 'fulfilled'
        ? rnpData.value.inhabilitados.filter(i => i.ruc === ruc)
        : [];
    const rnpMultas = rnpData.status === 'fulfilled'
        ? rnpData.value.multas.filter(m => m.ruc === ruc)
        : [];
    
    // NUEVO: Sanciones SUNAFIL
    const sunafilSanciones = sunafilData.status === 'fulfilled'
        ? sunafilData.value.sanciones.filter(s => s.ruc === ruc && s.estado === 'VIGENTE')
        : [];
    
    // NUEVO: Sanciones INDECOPI
    const indecopiSanciones = indecopiData.status === 'fulfilled'
        ? indecopiData.value.sanciones.filter(s => s.ruc === ruc)
        : [];
    
    // NUEVO: Propiedades SUNARP
    const sunarpPropiedades = sunarpData.status === 'fulfilled'
        ? sunarpData.value.propiedades || []
        : [];
    
    // Combinar todas las sanciones con metadatos de severidad
    const todasSanciones = [
        ...osceSanciones.map(s => ({ ...s, severidad: 3, peso: 20, tipo: 'OSCE' })),
        ...tceSanciones.map(s => ({ ...s, severidad: 3, peso: 20, tipo: 'TCE' })),
        ...rnpInhabilitaciones.map(s => ({ ...s, severidad: 4, peso: 80, tipo: 'RNP_INHABILITACION' })),
        ...rnpMultas.map(s => ({ ...s, severidad: 1, peso: 5, tipo: 'RNP_MULTA' })),
        ...sunafilSanciones.map(s => ({ ...s, severidad: 3, peso: 30, tipo: 'SUNAFIL' })),  // NUEVO
        ...indecopiSanciones.map(s => ({ ...s, severidad: 2, peso: 15, tipo: 'INDECOPI' }))  // NUEVO
    ];
    
    // ==================== OPCION B: PONDERADA POR TIEMPO ====================
    
    // Función para calcular años de antigüedad de una sanción
    function calcularAntiguedadAnios(fechaSancion) {
        if (!fechaSancion) return 0;
        try {
            const fecha = new Date(fechaSancion);
            const hoy = new Date();
            const diffTime = hoy - fecha;
            return diffTime / (1000 * 60 * 60 * 24 * 365);
        } catch {
            return 0;
        }
    }
    
    // Función para calcular factor de decaimiento según antigüedad
    function calcularFactorDecaimiento(anios) {
        if (anios < 2) return 1.0;        // < 2 años: 100% peso
        if (anios < 5) return 0.5;        // 2-5 años: 50% peso
        return 0.25;                       // > 5 años: 25% peso
    }
    
    // CRÍTICO: Detectar inhabilitaciones DEFINITIVAS y VIGENTES
    // Las inhabilitaciones son "todo o nada" - no decaen con el tiempo
    const inhabilitacionesDefinitivasVigentes = todasSanciones.filter(s => 
        (s.tipo === 'RNP_INHABILITACION' || s.tipo === 'OSCE' || s.tipo === 'TCE') &&
        s.estado === 'VIGENTE'
    );
    
    const tieneInhabilitacionGrave = inhabilitacionesDefinitivasVigentes.length > 0;
    
    // Calcular score con decaimiento temporal
    let score = 100;
    let detallePenalidades = [];
    let sancionesProcesadas = [];
    
    // Penalidad base si no está en SUNAT (CRÍTICO)
    if (!sunat) {
        score -= 40;
        detallePenalidades.push({ razon: 'No encontrado en SUNAT', puntos: -40, tipo: 'CRITICO' });
    }
    
    // Procesar cada sanción con factor de antigüedad
    todasSanciones.forEach(s => {
        if (s.estado === 'VIGENTE') {
            const antiguedad = calcularAntiguedadAnios(s.fecha);
            
            // Las inhabilitaciones no decaen (siempre 100% peso)
            const esInhabilitacion = s.tipo === 'RNP_INHABILITACION' || s.tipo === 'OSCE' || s.tipo === 'TCE';
            const factor = esInhabilitacion ? 1.0 : calcularFactorDecaimiento(antiguedad);
            
            const penalidadAplicada = Math.round(s.peso * factor);
            score -= penalidadAplicada;
            
            sancionesProcesadas.push({
                tipo: s.tipo,
                resolucion: s.resolucion || 'S/N',
                fecha: s.fecha,
                antiguedad_anios: Math.round(antiguedad * 10) / 10,
                factor_aplicado: factor,
                peso_original: s.peso,
                penalidad_final: penalidadAplicada
            });
            
            detallePenalidades.push({
                razon: `${s.tipo} - ${s.resolucion || 'S/N'}`,
                puntos: -penalidadAplicada,
                antiguedad: Math.round(antiguedad * 10) / 10 + ' años',
                factor: factor
            });
        }
    });
    
    // Bonus por patrimonio (estabilidad financiera)
    const tienePropiedades = sunarpPropiedades.length > 0;
    if (tienePropiedades) {
        const bonus = Math.min(10, sunarpPropiedades.length * 2); // Max +10
        score += bonus;
        detallePenalidades.push({
            razon: `Patrimonio registrado (${sunarpPropiedades.length} propiedades)`,
            puntos: +bonus,
            tipo: 'BONUS'
        });
    }
    
    // Penalidad acumulativa por patrón de incumplimiento
    const sancionesGraves = todasSanciones.filter(s => s.severidad >= 3 && s.estado === 'VIGENTE');
    if (sancionesGraves.length >= 3) {
        score -= 15;
        detallePenalidades.push({ razon: 'Patrón de incumplimiento recurrente', puntos: -15 });
    }
    
    // Asegurar rango 0-100
    score = Math.max(0, Math.min(100, Math.round(score)));
    
    // ==================== CLASIFICACIÓN OPCIÓN B ====================
    let estadoFinal;
    let puedeContratar = true;
    let alertas = [];
    let nivelRiesgo;
    
    if (tieneInhabilitacionGrave) {
        // INHABILITACIÓN = Rechazo automático (no negociable legalmente)
        estadoFinal = 'RECHAZADO';
        nivelRiesgo = 'CRITICO';
        puedeContratar = false;
        score = 0; // Forzar a 0
        alertas.push('INHABILITADA_LEGALMENTE_PARA_CONTRATAR_ESTADO');
    } else if (score >= 90) {
        estadoFinal = 'LIMPIO';
        nivelRiesgo = 'BAJO';
    } else if (score >= 70) {
        estadoFinal = 'OBSERVADO_LEVE';
        nivelRiesgo = 'MEDIO';
        alertas.push('SANCIONES_ANTIGUAS_O_LEVES');
    } else if (score >= 40) {
        estadoFinal = 'OBSERVADO_GRAVE';
        nivelRiesgo = 'ALTO';
        puedeContratar = false;
        alertas.push('HISTORIAL_RECIENTE_DE_SANCIONES');
    } else {
        estadoFinal = 'RECHAZADO';
        nivelRiesgo = 'CRITICO';
        puedeContratar = false;
        alertas.push('PATRON_INFRACTOR');
    }
    
    res.json({
        ruc,
        razon_social: sunat?.razon_social || 'NO ENCONTRADO',
        estado: estadoFinal,
        nivel_riesgo: nivelRiesgo,
        puede_contratar: puedeContratar,
        alertas: alertas,
        condicion: sunat?.condicion || 'NO ENCONTRADO',
        estado_sunat: sunat?.estado || 'NO ENCONTRADO',
        direccion: sunat?.direccion || '',
        score,
        sunat,
        sanciones: todasSanciones,
        sanciones_procesadas: sancionesProcesadas,
        total_registros: todasSanciones.length,
        inhabilitaciones_vigentes: inhabilitacionesDefinitivasVigentes.length,
        fuentes: {
            sunat: !!sunat,
            osce: osceSanciones.filter(s => s.estado === 'VIGENTE').length,
            tce: tceSanciones.filter(s => s.estado === 'VIGENTE').length,
            rnp: {
                inhabilitaciones: rnpInhabilitaciones.filter(s => s.estado === 'VIGENTE').length,
                multas: rnpMultas.filter(s => s.estado === 'VIGENTE').length,
                total: rnpInhabilitaciones.filter(s => s.estado === 'VIGENTE').length + rnpMultas.filter(s => s.estado === 'VIGENTE').length
            },
            sunafil: sunafilSanciones.length,
            indecopi: indecopiSanciones.length,
            sunarp: sunarpPropiedades.length
        },
        patrimonio: {
            propiedades_registradas: sunarpPropiedades.length,
            tiene_inmuebles: sunarpPropiedades.length > 0,
            detalle_propiedades: sunarpPropiedades
        },
        formula_utilizada: 'B - PONDERADA_POR_TIEMPO',
        detalle_score: {
            score_final: score,
            penalidades: detallePenalidades,
            total_penalidad: detallePenalidades.reduce((sum, p) => sum + (p.puntos || 0), 0),
            escalas: {
                '90-100': 'LIMPIO - Sin sanciones recientes',
                '70-89': 'OBSERVADO_LEVE - Sanciones antiguas o leves',
                '40-69': 'OBSERVADO_GRAVE - Historial reciente, requiere análisis',
                '0-39': 'RECHAZADO - Patrón infractor o inhabilitación legal'
            }
        },
        notas_fuentes: {
            sunafil: 'Datos de fiscalizaciones laborales (SST, jornada, discriminación)',
            indecopi: 'Datos de competencia desleal y protección al consumidor',
            sunarp: 'Registros de propiedad inmueble y vehicular'
        }
    });
});

// ==================== REGISTRATION EMAIL - SENDGRID ====================
app.post('/api/register', async (req, res) => {
    const { firstName, lastName, email, company, plan, phone, date } = req.body;
    
    if (!email || !firstName || !lastName) {
        return res.status(400).json({ error: 'Datos incompletos' });
    }
    
    const planNames = {
        starter: 'Starter ($400/mes)',
        professional: 'Professional ($800/mes)', 
        enterprise: 'Enterprise ($2,500/mes)'
    };
    
    const msg = {
        to: 'contacto@czperu.com',
        from: {
            email: 'noreply@czperu.com',
            name: 'Conflict Zero - Registros'
        },
        replyTo: email,
        subject: `[CONFLICT ZERO] Nueva solicitud: ${company || 'Empresa'} - ${plan || 'Sin plan'}`,
        html: `
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #c9a961 0%, #d4b978 100%); padding: 20px; text-align: center;">
                    <h2 style="color: white; margin: 0;">Conflict Zero</h2>
                    <p style="color: white; margin: 5px 0 0 0; font-size: 14px;">Nueva Solicitud de Registro</p>
                </div>
                
                <div style="padding: 30px; background: #fafafa; border: 1px solid #e0e0e0; border-top: none;">
                    <p style="color: #666; margin-bottom: 20px;">Se ha recibido una nueva solicitud de registro con los siguientes datos:</p>
                    
                    <table style="width: 100%; border-collapse: collapse; background: white;">
                        <tr>
                            <td style="padding: 12px; border: 1px solid #e0e0e0; font-weight: bold; width: 35%; background: #f5f5f5;">Nombre:</td>
                            <td style="padding: 12px; border: 1px solid #e0e0e0;">${firstName} ${lastName}</td>
                        </tr>
                        <tr>
                            <td style="padding: 12px; border: 1px solid #e0e0e0; font-weight: bold; background: #f5f5f5;">Email:</td>
                            <td style="padding: 12px; border: 1px solid #e0e0e0;"><a href="mailto:${email}" style="color: #c9a961;">${email}</a></td>
                        </tr>
                        <tr>
                            <td style="padding: 12px; border: 1px solid #e0e0e0; font-weight: bold; background: #f5f5f5;">Empresa:</td>
                            <td style="padding: 12px; border: 1px solid #e0e0e0;">${company || 'No especificado'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 12px; border: 1px solid #e0e0e0; font-weight: bold; background: #f5f5f5;">Plan:</td>
                            <td style="padding: 12px; border: 1px solid #e0e0e0;"><strong style="color: #c9a961;">${planNames[plan] || plan}</strong></td>
                        </tr>
                        <tr>
                            <td style="padding: 12px; border: 1px solid #e0e0e0; font-weight: bold; background: #f5f5f5;">Telefono:</td>
                            <td style="padding: 12px; border: 1px solid #e0e0e0;">${phone || 'No proporcionado'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 12px; border: 1px solid #e0e0e0; font-weight: bold; background: #f5f5f5;">Fecha:</td>
                            <td style="padding: 12px; border: 1px solid #e0e0e0;">${date}</td>
                        </tr>
                    </table>
                    
                    <div style="margin-top: 25px; padding: 15px; background: #fff3cd; border-left: 4px solid #c9a961;">
                        <p style="margin: 0; color: #856404; font-size: 14px;">
                            <strong>Accion requerida:</strong> Contactar al cliente en 24-48 horas.
                        </p>
                    </div>
                    
                    <div style="margin-top: 20px; text-align: center;">
                        <a href="mailto:${email}?subject=RE: Solicitud Conflict Zero - ${company || 'Empresa'}" 
                           style="display: inline-block; padding: 12px 30px; background: #c9a961; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">
                            Responder al cliente
                        </a>
                    </div>
                </div>
                
                <div style="padding: 20px; text-align: center; background: #f0f0f0; border: 1px solid #e0e0e0; border-top: none;">
                    <p style="color: #999; font-size: 12px; margin: 0;">
                        Conflict Zero S.A.C. - Sistema automatico de registro<br>
                        <a href="https://czperu.com" style="color: #c9a961;">www.czperu.com</a>
                    </p>
                </div>
            </div>
        `
    };
    
    try {
        const result = await sgMail.send(msg);
        console.log('SendGrid email sent:', result);
        res.json({ success: true, message: 'Email enviado exitosamente' });
    } catch (error) {
        console.error('SendGrid error details:', error);
        if (error.response) {
            console.error('SendGrid error body:', error.response.body);
        }
        // Return success anyway for demo purposes
        res.json({ success: true, message: 'Solicitud registrada', email_error: error.message });
    }
});

app.listen(PORT, () => console.log('Conflict Zero Backend v1.3.0 - Server on port ' + PORT));
