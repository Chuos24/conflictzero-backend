'use strict';

module.exports = function validateRuc(req, res, next) {
  const { ruc } = req.params;
  if (!ruc || ruc.length !== 11 || !/^\d+$/.test(ruc)) {
    return res.status(400).json({ error: 'RUC inválido. Debe tener 11 dígitos numéricos.' });
  }
  next();
};
