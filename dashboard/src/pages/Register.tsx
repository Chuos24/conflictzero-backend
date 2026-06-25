import { useNavigate, Link } from 'react-router-dom'
import { useState, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { registerSchema } from '../lib/validations'
import { authAPI } from '../services/api'
import type { z } from 'zod'
import './Register.css'

type RegisterFormData = z.infer<typeof registerSchema>

interface CountryConfig {
  code: string
  name: string
  label: string
  placeholder: string
  mask?: string
  maxLength: number
}

const COUNTRIES: CountryConfig[] = [
  { code: 'PE', name: 'Perú', label: 'RUC', placeholder: '20123456789', maxLength: 11 },
  { code: 'CL', name: 'Chile', label: 'RUT', placeholder: '12.345.678-K', maxLength: 12 },
  { code: 'CO', name: 'Colombia', label: 'NIT', placeholder: '901234567', maxLength: 10 },
  { code: 'MX', name: 'México', label: 'RFC', placeholder: 'ABCD010101ABC', maxLength: 13 },
  { code: 'ES', name: 'España', label: 'NIF/CIF', placeholder: 'A12345678', maxLength: 9 },
]

function Register(): JSX.Element {
  const navigate = useNavigate()
  const [selectedCountry, setSelectedCountry] = useState<CountryConfig>(COUNTRIES[0])
  const [docError, setDocError] = useState('')
  const [isValidating, setIsValidating] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
    setValue,
    watch,
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      country_code: 'PE',
      ruc: '',
      razon_social: '',
      contact_email: '',
      contact_phone: '',
      password: '',
      confirmPassword: '',
    },
  })

  const watchedCountry = watch('country_code')

  const handleCountryChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    const country = COUNTRIES.find(c => c.code === e.target.value) || COUNTRIES[0]
    setSelectedCountry(country)
    setValue('country_code', country.code)
    setValue('ruc', '')
    setDocError('')
  }, [setValue])

  const validateDocument = useCallback(async (value: string) => {
    if (!value || value.length < 8) return
    setIsValidating(true)
    setDocError('')
    try {
      const res = await fetch('/api/v1/countries/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ country_code: selectedCountry.code, document: value }),
      })
      const data = await res.json()
      if (!data.valid) {
        setDocError(data.error || 'Documento inválido')
      }
    } catch {
      // Silenciar errores de red para no bloquear el registro
    } finally {
      setIsValidating(false)
    }
  }, [selectedCountry.code])

  const onSubmit = async (data: RegisterFormData): Promise<void> => {
    if (docError) {
      setError('ruc', { message: docError })
      return
    }
    try {
      const res = await authAPI.register({
        ruc: data.ruc,
        country_code: data.country_code,
        razon_social: data.razon_social,
        contact_email: data.contact_email,
        contact_phone: data.contact_phone || undefined,
        password: data.password,
      })
      if (res.status === 200 || res.status === 201) {
        navigate('/login', { state: { registered: true } })
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      setError('root', {
        message: e.response?.data?.detail || 'Error al registrar. Intente nuevamente.',
      })
    }
  }

  return (
    <div className="register-container">
      <div className="register-card">
        <div className="register-header">
          <div className="register-logo">
            <span className="logo-icon">CZ</span>
          </div>
          <h1>Registro</h1>
          <p>Conflict Zero - Verificación de Riesgo</p>
        </div>

        {errors.root && (
          <div className="error-message">{errors.root.message}</div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="register-form" noValidate>
          {/* Selector de país */}
          <div className="form-group">
            <label htmlFor="country_code">País</label>
            <select
              id="country_code"
              {...register('country_code')}
              onChange={handleCountryChange}
              value={watchedCountry}
              aria-invalid={errors.country_code ? 'true' : 'false'}
            >
              {COUNTRIES.map(c => (
                <option key={c.code} value={c.code}>
                  {c.name} ({c.label})
                </option>
              ))}
            </select>
            {errors.country_code && (
              <span className="field-error" role="alert">{errors.country_code.message}</span>
            )}
          </div>

          {/* Documento (RUC/RUT/NIT/RFC/NIF) */}
          <div className="form-group">
            <label htmlFor="ruc">{selectedCountry.label}</label>
            <input
              type="text"
              id="ruc"
              placeholder={selectedCountry.placeholder}
              maxLength={selectedCountry.maxLength}
              {...register('ruc', {
                onChange: (e) => {
                  setDocError('')
                  validateDocument(e.target.value)
                },
              })}
              aria-invalid={errors.ruc || docError ? 'true' : 'false'}
            />
            {isValidating && <span className="field-info">Validando...</span>}
            {errors.ruc && <span className="field-error" role="alert">{errors.ruc.message}</span>}
            {docError && <span className="field-error" role="alert">{docError}</span>}
          </div>

          {/* Razón social */}
          <div className="form-group">
            <label htmlFor="razon_social">Razón Social</label>
            <input
              type="text"
              id="razon_social"
              placeholder="Empresa S.A.C."
              {...register('razon_social')}
              aria-invalid={errors.razon_social ? 'true' : 'false'}
            />
            {errors.razon_social && (
              <span className="field-error" role="alert">{errors.razon_social.message}</span>
            )}
          </div>

          {/* Email */}
          <div className="form-group">
            <label htmlFor="contact_email">Email de Contacto</label>
            <input
              type="email"
              id="contact_email"
              placeholder="contacto@empresa.com"
              {...register('contact_email')}
              aria-invalid={errors.contact_email ? 'true' : 'false'}
            />
            {errors.contact_email && (
              <span className="field-error" role="alert">{errors.contact_email.message}</span>
            )}
          </div>

          {/* Teléfono */}
          <div className="form-group">
            <label htmlFor="contact_phone">Teléfono (opcional)</label>
            <input
              type="tel"
              id="contact_phone"
              placeholder="+51 999 999 999"
              {...register('contact_phone')}
              aria-invalid={errors.contact_phone ? 'true' : 'false'}
            />
            {errors.contact_phone && (
              <span className="field-error" role="alert">{errors.contact_phone.message}</span>
            )}
          </div>

          {/* Contraseña */}
          <div className="form-group">
            <label htmlFor="password">Contraseña</label>
            <input
              type="password"
              id="password"
              placeholder="••••••••"
              {...register('password')}
              aria-invalid={errors.password ? 'true' : 'false'}
            />
            {errors.password && (
              <span className="field-error" role="alert">{errors.password.message}</span>
            )}
          </div>

          {/* Confirmar contraseña */}
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirmar Contraseña</label>
            <input
              type="password"
              id="confirmPassword"
              placeholder="••••••••"
              {...register('confirmPassword')}
              aria-invalid={errors.confirmPassword ? 'true' : 'false'}
            />
            {errors.confirmPassword && (
              <span className="field-error" role="alert">{errors.confirmPassword.message}</span>
            )}
          </div>

          <button
            type="submit"
            className="register-btn"
            disabled={isSubmitting || !!docError}
          >
            {isSubmitting ? 'Registrando...' : 'Crear Cuenta'}
          </button>
        </form>

        <div className="register-footer">
          <p>¿Ya tienes cuenta? <Link to="/login">Iniciar sesión</Link></p>
        </div>
      </div>

      <div className="register-decoration">
        <div className="decoration-circle"></div>
        <div className="decoration-circle"></div>
      </div>
    </div>
  )
}

export default Register
