import { z } from 'zod'

// Esquema de login
export const loginSchema = z.object({
  ruc: z
    .string()
    .min(1, 'El RUC es requerido')
    .length(11, 'El RUC debe tener exactamente 11 dígitos')
    .regex(/^\d+$/, 'El RUC solo debe contener números'),
  password: z
    .string()
    .min(1, 'La contraseña es requerida')
    .min(6, 'La contraseña debe tener al menos 6 caracteres'),
})

// Esquema de registro
export const registerSchema = z.object({
  ruc: z
    .string()
    .min(1, 'El RUC es requerido')
    .length(11, 'El RUC debe tener exactamente 11 dígitos')
    .regex(/^\d+$/, 'El RUC solo debe contener números'),
  razon_social: z
    .string()
    .min(1, 'La razón social es requerida')
    .min(3, 'La razón social debe tener al menos 3 caracteres'),
  contact_email: z
    .string()
    .min(1, 'El email es requerido')
    .email('Ingrese un email válido'),
  contact_phone: z
    .string()
    .optional()
    .refine((val) => !val || val.length >= 7, {
      message: 'El teléfono debe tener al menos 7 dígitos',
    }),
  password: z
    .string()
    .min(1, 'La contraseña es requerida')
    .min(8, 'La contraseña debe tener al menos 8 caracteres')
    .regex(/[A-Z]/, 'Debe contener al menos una mayúscula')
    .regex(/[a-z]/, 'Debe contener al menos una minúscula')
    .regex(/\d/, 'Debe contener al menos un número'),
  confirmPassword: z.string().min(1, 'Confirme su contraseña'),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Las contraseñas no coinciden',
  path: ['confirmPassword'],
})

// Esquema de perfil
export const profileSchema = z.object({
  razon_social: z
    .string()
    .min(1, 'La razón social es requerida')
    .min(3, 'Debe tener al menos 3 caracteres'),
  contact_name: z
    .string()
    .min(1, 'El nombre de contacto es requerido')
    .min(2, 'Debe tener al menos 2 caracteres'),
  contact_phone: z
    .string()
    .optional()
    .refine((val) => !val || /^\+?[\d\s-]{7,}$/.test(val), {
      message: 'Ingrese un teléfono válido',
    }),
})

// Esquema de verificación RUC
export const verifyRucSchema = z.object({
  ruc: z
    .string()
    .min(1, 'El RUC es requerido')
    .length(11, 'El RUC debe tener exactamente 11 dígitos')
    .regex(/^\d+$/, 'El RUC solo debe contener números'),
})

// Esquema de comparación
export const compareSchema = z.object({
  rucs: z
    .array(z.string().length(11).regex(/^\d+$/))
    .min(2, 'Seleccione al menos 2 RUCs para comparar')
    .max(10, 'Máximo 10 RUCs por comparación'),
})

// Esquema de invitación
export const inviteSchema = z.object({
  email: z
    .string()
    .min(1, 'El email es requerido')
    .email('Ingrese un email válido'),
  company_name: z
    .string()
    .min(1, 'El nombre de la empresa es requerido')
    .min(2, 'Debe tener al menos 2 caracteres'),
  message: z
    .string()
    .max(500, 'El mensaje no puede exceder 500 caracteres')
    .optional(),
})
