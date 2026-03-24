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
    
    const [sunatRes, osceData, tceData, rnpData] = await Promise.allSettled([
        axios.post('https://buscaruc.com/api/v1/ruc', {
            token: BUSCARUC_TOKEN,
            ruc
        }, { headers: { 'Content-Type': 'application/json' } }),
        scrapeOSCE(),
        scrapeTCE(),
        scrapeRNP()  // NUEVO: Agregado RNP
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
    
    // NUEVO: Sanciones RNP (inhabilitaciones + multas)
    const rnpInhabilitaciones = rnpData.status === 'fulfilled'
        ? rnpData.value.inhabilitados.filter(i => i.ruc === ruc)
        : [];
    const rnpMultas = rnpData.status === 'fulfilled'
        ? rnpData.value.multas.filter(m => m.ruc === ruc)
        : [];
    
    // Combinar todas las sanciones con metadatos de severidad
    const todasSanciones = [
        ...osceSanciones.map(s => ({ ...s, severidad: 3, peso: 20 })),
        ...tceSanciones.map(s => ({ ...s, severidad: 3, peso: 20 })),
        ...rnpInhabilitaciones.map(s => ({ ...s, severidad: 2, peso: 15 })),
        ...rnpMultas.map(s => ({ ...s, severidad: 1, peso: 5 }))
    ];
    
    // Calcular score mejorado con ponderacion por severidad
    let score = 100;
    
    // Penalidad base si no esta en SUNAT
    if (!sunat) score -= 25;
    
    // Penalidad por sanciones (ponderadas por severidad)
    let penalidadSanciones = 0;
    todasSanciones.forEach(s => {
        penalidadSanciones += s.peso;
    });
    
    // Bonus por antiguedad (sanciones viejas penalizan menos)
    const ahora = new Date();
    todasSanciones.forEach(s => {
        if (s.fecha) {
            const fechaSancion = new Date(s.fecha);
            const mesesAntiguedad = (ahora - fechaSancion) / (1000 * 60 * 60 * 24 * 30);
            if (mesesAntiguedad > 24) {
                // Sanciones mayores a 2 años restan solo la mitad
                penalidadSanciones -= s.peso * 0.5;
            }
        }
    });
    
    score -= penalidadSanciones;
    
    // Penalidad adicional por cantidad de sanciones (efecto acumulativo)
    if (todasSanciones.length >= 3) score -= 10;
    if (todasSanciones.length >= 5) score -= 15;
    
    // Asegurar rango 0-100
    score = Math.max(0, Math.min(100, Math.round(score)));
    
    // Determinar estado con umbrales ajustados
    let estadoFinal;
    if (score >= 80) estadoFinal = 'LIMPIO';
    else if (score >= 50) estadoFinal = 'OBSERVADO';
    else estadoFinal = 'CRITICO';
    
    res.json({
        ruc,
        razon_social: sunat?.razon_social || 'NO ENCONTRADO',
        estado: estadoFinal,
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
            tce: tceSanciones.length,
            rnp: {
                inhabilitaciones: rnpInhabilitaciones.length,
                multas: rnpMultas.length,
                total: rnpInhabilitaciones.length + rnpMultas.length
            }
        },
        detalle_score: {
            base: 100,
            penalidad_sunat: !sunat ? -25 : 0,
            penalidad_sanciones: -penalidadSanciones,
            penalidad_acumulativa: todasSanciones.length >= 5 ? -15 : todasSanciones.length >= 3 ? -10 : 0,
            score_final: score
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
