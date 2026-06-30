'use strict';

const { Router } = require('express');
const router = Router();

router.get('/', (req, res) => {
  res.json({ status: 'online', timestamp: new Date().toISOString(), version: '2.0.0' });
});

module.exports = router;
