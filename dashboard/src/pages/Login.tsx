import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuth } from '../context/AuthContext'
import { loginSchema } from '../lib/validations'
import type { z } from 'zod'
import './Login.css'

type LoginFormData = z.infer<typeof loginSchema>

function Login(): JSX.Element {
  const { login } = useAuth()
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      ruc: '',
      password: '',
    },
  })

  const onSubmit = async (data: LoginFormData): Promise<void> => {
    try {
      const result = await login(data.ruc, data.password)
      if (result.success) {
        navigate('/dashboard')
      } else {
        setError('root', {
          message: result.error || 'Error al iniciar sesión',
        })
      }
    } catch (err) {
      setError('root', {
        message: 'Error de conexión. Intente nuevamente.',
      })
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo">
            <span className="logo-icon">CZ</span>
          </div>
          <h1>Conflict Zero</h1>
          <p>Plataforma de Compliance y Verificación</p>
        </div>

        {errors.root && (
          <div className="error-message">
            {errors.root.message}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="login-form" noValidate>
          <div className="form-group">
            <label htmlFor="ruc">RUC</label>
            <input
              type="text"
              id="ruc"
              placeholder="20123456789"
              maxLength={11}
              {...register('ruc')}
              aria-invalid={errors.ruc ? 'true' : 'false'}
            />
            {errors.ruc && (
              <span className="field-error" role="alert">{errors.ruc.message}</span>
            )}
          </div>

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

          <button
            type="submit"
            className="login-btn"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Ingresando...' : 'Ingresar'}
          </button>
        </form>

        <div className="login-footer">
          <p>¿No tienes cuenta? <Link to="/register">Regístrate</Link></p>
          <p className="founder-link">
            ¿Eres constructora? <Link to="/founders">Aplica al programa Founder</Link>
          </p>
        </div>
      </div>

      <div className="login-decoration">
        <div className="decoration-circle"></div>
        <div className="decoration-circle"></div>
      </div>
    </div>
  )
}

export default Login
