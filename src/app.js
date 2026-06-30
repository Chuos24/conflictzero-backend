'use strict';

const express = require('express');
const corsMiddleware = require('./middleware/cors');

const app = express();

app.use(express.json());
app.use(corsMiddleware);

// Routes
app.use('/health',           require('./routes/health'));
app.use('/sunat',            require('./routes/sunat'));
app.use('/osce',             require('./routes/osce'));
app.use('/tce',              require('./routes/tce'));
app.use('/rnp',              require('./routes/rnp'));
app.use('/sunafil',          require('./routes/sunafil'));
app.use('/consulta-completa',require('./routes/consulta'));

// 404
app.use((req, res) => res.status(404).json({ error: 'Ruta no encontrada' }));

// Error handler
app.use((err, req, res, next) => {
  console.error('[ERROR]', err.message);
  res.status(500).json({ error: 'Error interno del servidor' });
});

module.exports = app;
