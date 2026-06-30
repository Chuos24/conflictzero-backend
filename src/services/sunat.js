'use strict';

const axios = require('axios');
const config = require('../config');

async function consultarRUC(ruc) {
  const response = await axios.post(
    'https://buscaruc.com/api/v1/ruc',
    { token: config.buscarucToken, ruc },
    { headers: { 'Content-Type': 'application/json' }, timeout: 15000 }
  );

  const data = response.data;
  if (!data.success || !data.result) {
    return null;
  }

  const r = data.result;
  return {
    ruc: r.ruc || ruc,
    razon_social: r.social_reason || '',
    estado: r.taxpayer_state || 'ACTIVO',
    condicion: r.domicile_condition || 'HABIDO',
    direccion: r.address || '',
    ubigeo: r.ubigeo || '',
    fuente: 'buscaruc_com',
  };
}

module.exports = { consultarRUC };
