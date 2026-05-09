import { describe, it, expect } from 'vitest';
import { z } from 'zod';
import { loginSchema, rucSchema, inviteSchema } from '../lib/validations';

describe('validations', () => {
  describe('loginSchema', () => {
    it('should validate correct email and password', () => {
      const result = loginSchema.safeParse({
        email: 'test@conflictzero.com',
        password: 'password123',
      });
      expect(result.success).toBe(true);
    });

    it('should reject invalid email', () => {
      const result = loginSchema.safeParse({
        email: 'not-an-email',
        password: 'password123',
      });
      expect(result.success).toBe(false);
    });

    it('should reject short password', () => {
      const result = loginSchema.safeParse({
        email: 'test@conflictzero.com',
        password: '123',
      });
      expect(result.success).toBe(false);
    });
  });

  describe('rucSchema', () => {
    it('should validate correct RUC (11 digits)', () => {
      const result = rucSchema.safeParse({ ruc: '20100154387' });
      expect(result.success).toBe(true);
    });

    it('should reject RUC with less than 11 digits', () => {
      const result = rucSchema.safeParse({ ruc: '2010015438' });
      expect(result.success).toBe(false);
    });

    it('should reject RUC with non-numeric characters', () => {
      const result = rucSchema.safeParse({ ruc: '2010015438a' });
      expect(result.success).toBe(false);
    });
  });

  describe('inviteSchema', () => {
    it('should validate correct invite data', () => {
      const result = inviteSchema.safeParse({
        email: 'supplier@example.com',
        ruc: '20100154387',
        message: 'Please join our network',
      });
      expect(result.success).toBe(true);
    });

    it('should reject invalid email', () => {
      const result = inviteSchema.safeParse({
        email: 'invalid-email',
        ruc: '20100154387',
      });
      expect(result.success).toBe(false);
    });

    it('should accept invite without optional message', () => {
      const result = inviteSchema.safeParse({
        email: 'supplier@example.com',
        ruc: '20100154387',
      });
      expect(result.success).toBe(true);
    });
  });
});
