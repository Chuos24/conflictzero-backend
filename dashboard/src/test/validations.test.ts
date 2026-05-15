import { describe, it, expect } from 'vitest';
import { z } from 'zod';

import { loginSchema, inviteSchema, verifyRucSchema } from '../lib/validations';

describe('validations', () => {
  describe('loginSchema', () => {
    it('should validate correct RUC and password', () => {
      const result = loginSchema.safeParse({
        ruc: '20100154387',
        password: 'password123',
      });
      expect(result.success).toBe(true);
    });

    it('should reject invalid RUC (less than 11 digits)', () => {
      const result = loginSchema.safeParse({
        ruc: '2010015438',
        password: 'password123',
      });
      expect(result.success).toBe(false);
    });

    it('should reject short password', () => {
      const result = loginSchema.safeParse({
        ruc: '20100154387',
        password: '123',
      });
      expect(result.success).toBe(false);
    });
  });

  describe('verifyRucSchema', () => {
    it('should validate correct RUC (11 digits)', () => {
      const result = verifyRucSchema.safeParse({ ruc: '20100154387' });
      expect(result.success).toBe(true);
    });

    it('should reject RUC with less than 11 digits', () => {
      const result = verifyRucSchema.safeParse({ ruc: '2010015438' });
      expect(result.success).toBe(false);
    });

    it('should reject RUC with non-numeric characters', () => {
      const result = verifyRucSchema.safeParse({ ruc: '2010015438a' });
      expect(result.success).toBe(false);
    });
  });

  describe('inviteSchema', () => {
    it('should validate correct invite data', () => {
      const result = inviteSchema.safeParse({
        email: 'supplier@example.com',
        company_name: 'Acme Corp',
        message: 'Please join our network',
      });
      expect(result.success).toBe(true);
    });

    it('should reject invalid email', () => {
      const result = inviteSchema.safeParse({
        email: 'invalid-email',
        company_name: 'Acme Corp',
      });
      expect(result.success).toBe(false);
    });

    it('should accept invite without optional message', () => {
      const result = inviteSchema.safeParse({
        email: 'supplier@example.com',
        company_name: 'Acme Corp',
      });
      expect(result.success).toBe(true);
    });
  });
});
