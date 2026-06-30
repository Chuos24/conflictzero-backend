'use strict';

const { Router } = require('express');
const validateRuc = require('../middleware/validateRuc');
const rnpService = require('../services/rnp');

const router = Router();

router.get('/inhabilitados', async (req, res) => {
  try { res.json(await rnpService.fetchSanciones()); }
  catch (err) { res.status(502).json({ error: err.message }); }
});

router.get('/ruc/:ruc', validateRuc, async (req, res) => {
  try { res.json(await rnpService.buscarPorRUC(req.params.ruc)); }
  catch (err) { res.status(502).json({ error: err.message }); }
});

module.exports = router;
