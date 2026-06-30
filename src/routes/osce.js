'use strict';

const { Router } = require('express');
const validateRuc = require('../middleware/validateRuc');
const osceService = require('../services/osce');

const router = Router();

router.get('/inhabilitados', async (req, res) => {
  try { res.json(await osceService.fetchInhabilitados()); }
  catch (err) { res.status(502).json({ error: err.message }); }
});

router.get('/ruc/:ruc', validateRuc, async (req, res) => {
  try { res.json(await osceService.buscarPorRUC(req.params.ruc)); }
  catch (err) { res.status(502).json({ error: err.message }); }
});

module.exports = router;
