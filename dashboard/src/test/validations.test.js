import { describe, it, expect } from 'vitest'
import { loginSchema, registerSchema, profileSchema, verifyRucSchema, inviteSchema } from '../lib/validations'

describe('Validaciones Zod', () => {
  describe('loginSchema', () => {
    it('acepta credenciales válidas', () => {
      const result = loginSchema.safeParse({
        ruc: '20123456789',
        password: 'password123',
      })
      expect(result.success).toBe(true)
    })

    it('rechaza RUC vacío', () => {
      const result = loginSchema.safeParse({
        ruc: '',
        password: 'password123',
      })
      expect(result.success).toBe(false)
      expect(result.error?.issues[0].message).toContain('RUC es requerido')
    })

    it('rechaza RUC con letras', () => {
      const result = loginSchema.safeParse({
        ruc: '2012345678a',
        password: 'password123',
      })
      expect(result.success).toBe(false)
      expect(result.error?.issues[0].message).toContain('solo debe contener números')
    })

    it('rechaza RUC con menos de 11 dígitos', () => {
      const result = loginSchema.safeParse({
        ruc: '2012345678',
        password: 'password123',
      })
      expect(result.success).toBe(false)
      expect(result.error?.issues[0].message).toContain('exactamente 11 dígitos')
    })

    it('rechaza contraseña vacía', () => {
      const result = loginSchema.safeParse({
        ruc: '20123456789',
        password: '',
      })
      expect(result.success).toBe(false)
      expect(result.error?.issues[0].message).toContain('contraseña es requerida')
    })

    it('rechaza contraseña corta', () => {
      const result = loginSchema.safeParse({
        ruc: '20123456789',
        password: '123',
      })
      expect(result.success).toBe(false)
      expect(result.error?.issues[0].message).toContain('al menos 6 caracteres')
    })
  })

  describe('registerSchema', () => {
    it('acepta registro válido', () => {
      const result = registerSchema.safeParse({
        ruc: '20123456789',
        razon_social: 'Constructora ABC',
        contact_email: 'admin@abc.com',
        contact_phone: '987654321',
        password: 'Password123',
        confirmPassword: 'Password123',
      })
      expect(result.success).toBe(true)
    })

    it('rechaza email inválido', () => {
      const result = registerSchema.safeParse({
        ruc: '20123456789',
        razon_social: 'Constructora ABC',
        contact_email: 'not-an-email',
        password: 'Password123',
        confirmPassword: 'Password123',
      })
      expect(result.success).toBe(false)
      expect(result.error?.issues.some(i => i.message.includes('email válido'))).toBe(true)
    })

    it('rechaza contraseña débil', () => {
      const result = registerSchema.safeParse({
        ruc: '20123456789',
        razon_social: 'Constructora ABC',
        contact_email: 'admin@abc.com',
        password: '12345678',
        confirmPassword: '12345678',
      })
      expect(result.success).toBe(false)
      expect(result.error?.issues.some(i => i.message.includes('mayúscula'))).toBe(true)
    })

    it('rechaza contraseñas que no coinciden', () => {
      const result = registerSchema.safeParse({
        ruc: '20123456789',
        razon_social: 'Constructora ABC',
        contact_email: 'admin@abc.com',
        password: 'Password123',
        confirmPassword: 'Password456',
      })
      expect(result.success).toBe(false)
      expect(result.error?.issues.some(i => i.message.includes('no coinciden'))).toBe(true)
    })
  })

  describe('profileSchema', () => {
    it('acepta perfil válido', () => {
      const result = profileSchema.safeParse({
        razon_social: 'Constructora ABC S.A.C.',
        contact_name: 'Juan Pérez',
        contact_phone: '+51 987 654 321',
      })
      expect(result.success).toBe(true)
    })

    it('acepta teléfono vacío', () => {
      const result = profileSchema.safeParse({
        razon_social: 'Constructora ABC',
        contact_name: 'Juan',
        contact_phone: '',
      })
      expect(result.success).toBe(true)
    })

    it('rechaza razón social corta', () => {
      const result = profileSchema.safeParse({
        razon_social: 'AB',
        contact_name: 'Juan',
      })
      expect(result.success).toBe(false)
      expect(result.error?.issues.some(i => i.message.includes('al menos 3 caracteres'))).toBe(true)
    })
  })

  describe('verifyRucSchema', () => {
    it('acepta RUC válido', () => {
      const result = verifyRucSchema.safeParse({ ruc: '20123456789' })
      expect(result.success).toBe(true)
    })

    it('rechaza RUC corto', () => {
      const result = verifyRucSchema.safeParse({ ruc: '2012345678' })
      expect(result.success).toBe(false)
      expect(result.error?.issues[0].message).toContain('exactamente 11 dígitos')
    })
  })

  describe('inviteSchema', () => {
    it('acepta invitación válida', () => {
      const result = inviteSchema.safeParse({
        email: 'proveedor@ejemplo.com',
        company_name: 'Proveedor S.A.C.',
        message: 'Únete a nuestra red',
      })
      expect(result.success).toBe(true)
    })

    it('rechaza email inválido', () => {
      const result = inviteSchema.safeParse({
        email: 'invalid',
        company_name: 'Proveedor',
      })
      expect(result.success).toBe(false)
    })
  })
})
