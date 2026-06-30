'use strict';

module.exports = {
  port: process.env.PORT || 10000,
  nodeEnv: process.env.NODE_ENV || 'development',
  sendgridApiKey: process.env.SENDGRID_API_KEY,
  buscarucToken: process.env.BUSCARUC_TOKEN,
  cacheDurationMs: 30 * 60 * 1000, // 30 min
  aws: {
    region: process.env.AWS_REGION || 'us-east-1',
    dynamoTable: process.env.DYNAMODB_TABLE_CONSULTAS || 'conflictzero-consultas',
  },
};
