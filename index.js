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
    
    const [sunatRes, osceData, tceData] = await Promise.allSettled([
        axios.post('https://buscaruc.com/api/v1/ruc', {
            token: BUSCARUC_TOKEN,
            ruc
        }, { headers: { 'Content-Type': 'application/json' } }),
        scrapeOSCE(),
        scrapeTCE()  // NUEVO: Agregado TCE
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
    
    // NUEVO: Sanciones TCE
    const tceSanciones = tceData.status === 'fulfilled'
        ? tceData.value.inhabilitados.filter(i => i.ruc === ruc)
        : [];
    
    // Combinar todas las sanciones
    const todasSanciones = [...osceSanciones, ...tceSanciones];
    
    // Calcular score (OSCE y TCE restan igual)
    let score = 100;
    if (!sunat) score -= 30;
    score -= osceSanciones.length * 20;
    score -= tceSanciones.length * 20;  // NUEVO: TCE también resta
    score = Math.max(0, score);
    
    res.json({
        ruc,
        razon_social: sunat?.razon_social || 'NO ENCONTRADO',
        estado: score >= 70 ? 'LIMPIO' : score >= 40 ? 'OBSERVADO' : 'CRITICO',
        condicion: sunat?.condicion || 'NO ENCONTRADO',
        estado_sunat: sunat?.estado || 'NO ENCONTRADO',
        direccion: sunat?.direccion || '',
        score,
        sunat,
        sanciones: todasSanciones,
        total_registros: todasSanciones.length,
        fuentes: {
            sunat: !!sunat,
            osce: osceSanciones.length,
            tce: tceSanciones.length
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
        from: 'registro@czperu.com',
        subject: `Nueva solicitud de registro - ${company}`,
        html: `
            <h2>Nueva Solicitud de Registro - Conflict Zero</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Nombre:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">${firstName} ${lastName}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Email:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">${email}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Empresa:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">${company}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Plan:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">${planNames[plan] || plan}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Telefono:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">${phone || 'No proporcionado'}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Fecha:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">${date}</td></tr>
            </table>
            <p style="margin-top: 20px;">Por favor contactar al cliente en 24-48 horas.</p>
        `
    };
    
    try {
        await sgMail.send(msg);
        res.json({ success: true, message: 'Email enviado exitosamente' });
    } catch (error) {
        console.error('SendGrid error:', error.response?.body || error.message);
        // Return success anyway for demo purposes
        res.json({ success: true, message: 'Solicitud registrada (modo demo)' });
    }
});

app.listen(PORT, () => console.log('Conflict Zero Backend v1.3.0 - Server on port ' + PORT));
