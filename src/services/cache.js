'use strict';

const config = require('../config');

const store = new Map();

/**
 * @param {string} key
 * @param {() => Promise<any>} fetcher
 * @param {number} [ttlMs]
 */
async function cached(key, fetcher, ttlMs = config.cacheDurationMs) {
  const entry = store.get(key);
  const now = Date.now();
  if (entry && now - entry.timestamp < ttlMs) return entry.data;
  const data = await fetcher();
  store.set(key, { data, timestamp: now });
  return data;
}

function bust(key) {
  store.delete(key);
}

module.exports = { cached, bust };
