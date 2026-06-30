'use strict';

const { Router } = require('express');
const validateRuc = require('../middleware/validateRuc');
const sunafilService = require('../services/sunafil');

const router = Router();

router.get('/sanciones', async (req, res) => {
  try { res.json(await sunafilService.fetchSanciones()); }
  catch (err) { res.status(502).json({ error: err.message }); }
});

router.get('/ruc/:ruc', validateRuc, async (req, res) => {
  try { res.json(await sunafilService.buscarPorRUC(req.params.ruc)); }
  catch (err) { res.status(502).json({ error: err.message }); }
});

module.exports = router;
