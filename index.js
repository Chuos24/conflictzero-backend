'use strict';

const app = require('./src/app');
const config = require('./src/config');

app.listen(config.port, () => {
  console.log(`[ConflictZero Backend] v2.0.0 corriendo en puerto ${config.port}`);
  console.log(`[ConflictZero Backend] Entorno: ${config.nodeEnv}`);
});
