'use strict';

const { Router } = require('express');
const validateRuc = require('../middleware/validateRuc');
const sunatService = require('../services/sunat');
const osceService = require('../services/osce');
const tceService = require('../services/tce');
const rnpService = require('../services/rnp');
const sunafilService = require('../services/sunafil');

const router = Router();

// Factores de penalidad por tipo de sanción
const PENALIDADES = {
  RNP_INHABILITACION: { peso: 80, severidad: 4, decae: false },
  OSCE:               { peso: 20, severidad: 3, decae: false },
  TCE:                { peso: 20, severidad: 3, decae: false },
  SUNAFIL:            { peso: 30, severidad: 3, decae: true  },
  RNP_MULTA:          { peso: 5,  severidad: 1, decae: true  },
};

function factorDecaimiento(fechaStr) {
  if (!fechaStr) return 1.0;
  try {
    const anios = (Date.now() - new Date(fechaStr)) / (1000 * 60 * 60 * 24 * 365);
    if (anios < 2) return 1.0;
    if (anios < 5) return 0.5;
    return 0.25;
  } catch { return 1.0; }
}

router.get('/:ruc', validateRuc, async (req, res) => {
  const { ruc } = req.params;

  const [sunatRes, osceRes, tceRes, rnpRes, sunafilRes] = await Promise.allSettled([
    sunatService.consultarRUC(ruc),
    osceService.buscarPorRUC(ruc),
    tceService.buscarPorRUC(ruc),
    rnpService.buscarPorRUC(ruc),
    sunafilService.buscarPorRUC(ruc),
  ]);

  const sunat = sunatRes.status === 'fulfilled' ? sunatRes.value : null;

  const sanciones = [
    ...((osceRes.value?.data || []).map(s => ({ ...s, _tipo: 'OSCE' }))),
    ...((tceRes.value?.data || []).map(s => ({ ...s, _tipo: 'TCE' }))),
    ...((rnpRes.value?.inhabilitados || []).map(s => ({ ...s, _tipo: 'RNP_INHABILITACION' }))),
    ...((rnpRes.value?.multas || []).map(s => ({ ...s, _tipo: 'RNP_MULTA' }))),
    ...((sunafilRes.value?.sanciones || []).map(s => ({ ...s, _tipo: 'SUNAFIL' }))),
  ];

  let score = sunat ? 100 : 60;

  sanciones.forEach(s => {
    const p = PENALIDADES[s._tipo] || { peso: 10, decae: true };
    const factor = p.decae ? factorDecaimiento(s.fecha) : 1.0;
    score -= Math.round(p.peso * factor);
  });

  score = Math.max(0, Math.min(100, score));

  let nivel;
  if (score >= 80) nivel = 'BAJO';
  else if (score >= 60) nivel = 'MEDIO';
  else if (score >= 40) nivel = 'ALTO';
  else nivel = 'CRITICO';

  res.json({
    ruc,
    score,
    nivel_riesgo: nivel,
    sunat,
    sanciones: sanciones.map(({ _tipo, ...rest }) => ({ tipo: _tipo, ...rest })),
    total_sanciones: sanciones.length,
    timestamp: new Date().toISOString(),
  });
});

module.exports = router;
