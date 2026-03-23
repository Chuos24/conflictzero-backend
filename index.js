const express = require('express');
const axios = require('axios');
const cheerio = require('cheerio');
const app = express();
const PORT = process.env.PORT || 10000;
const BUSCARUC_TOKEN = process.env.BUSCARUC_TOKEN || 'eyJ1c2VySWQiOjU0NzAsInVzZXJUb2tlbklkIjo1NDY5fQ.QK8EdbO21g2rCk3jqUqdOf3pKKhNZqymmG30RTbMURhtp7-JPJcPX3xHXAaH46qAoHrTnQLgqTGo1yY1zu64QfPvLux0EbX2R9V_1tAy8Fdos2-Z-_XXTe7Wi0lRTBK55uh_zCm5zCiYs7VJBW4T9e2mZdd6EaXYaXOwEybmseE';

let osceCache = { data: null, timestamp: null };
let tceCache = { data: null, timestamp: null };

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

// ==================== TCE - NUEVO ====================
async function scrapeTCE() {
    const now = Date.now();
    if (tceCache.data && tceCache.timestamp && (now - tceCache.timestamp) < 1800000) {
        return tceCache.data;
    }
    try {
        const response = await axios.get('http://www.osce.gob.pe/consultasenlinea/inhabilitados/inhabil_publi_mes.asp', {
            timeout: 30000,
            headers: { 'User-Agent': 'Mozilla/5.0' }
        });
        const $ = cheerio.load(response.data);
        const inhabilitados = [];
        
        // Buscar en tablas - TCE publica en la misma página que OSCE
        $('table tr').each((i, row) => {
            const cols = $(row).find('td');
            if (cols.length >= 9) {
                const tipo = $(cols[0]).text().trim();
                const numero = $(cols[1]).text().trim();
                const nombre = $(cols[2]).text().trim();
                const ruc = $(cols[3]).text().trim();
                const expediente = $(cols[4]).text().trim();
                const duracion = $(cols[5]).text().trim();
                const fechaInicio = $(cols[6]).text().trim();
                const fechaFin = $(cols[7]).text().trim();
                const motivo = $(cols[8]).text().trim();
                
                // Solo incluir si tiene expediente TCE
                if (ruc && ruc.match(/^\d{11}$/) && expediente && expediente.includes('TCE')) {
                    inhabilitados.push({
                        ruc,
                        entidad: 'TCE',
                        tipo_sancion: tipo,
                        nombre,
                        expediente,
                        duracion,
                        fecha_inicio: fechaInicio,
                        fecha_fin: fechaFin,
                        motivo,
                        fecha: fechaInicio
                    });
                }
            }
        });
        
        const resultado = { total: inhabilitados.length, inhabilitados, fuente: 'tce_scraper' };
        tceCache = { data: resultado, timestamp: now };
        return resultado;
    } catch (error) {
        return { total: 0, inhabilitados: [], error: error.message };
    }
}

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

app.listen(PORT, () => console.log('Conflict Zero Backend v1.2.0 - Server on port ' + PORT));
