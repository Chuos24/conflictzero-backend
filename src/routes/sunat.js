'use strict';

const { Router } = require('express');
const validateRuc = require('../middleware/validateRuc');
const sunatService = require('../services/sunat');

const router = Router();

router.get('/ruc/:ruc', validateRuc, async (req, res) => {
  try {
    const data = await sunatService.consultarRUC(req.params.ruc);
    if (!data) return res.status(404).json({ error: 'RUC no encontrado', ruc: req.params.ruc });
    res.json(data);
  } catch (err) {
    res.status(502).json({ error: err.message });
  }
});

module.exports = router;
