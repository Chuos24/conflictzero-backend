import React, { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { profileSchema } from '../lib/validations'
import api from '../services/api'
import './Profile.css'

export default function Profile() {
  const { user, setUser } = useAuth()
  const { showToast } = useToast()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
    setError,
  } = useForm({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      razon_social: user?.razon_social || '',
      contact_name: user?.contact_name || '',
      contact_phone: user?.contact_phone || '',
    },
  })

  // Sync form when user data changes
  useEffect(() => {
    if (user) {
      reset({
        razon_social: user.razon_social || '',
        contact_name: user.contact_name || '',
        contact_phone: user.contact_phone || '',
      })
    }
  }, [user, reset])

  const onSubmit = async (data) => {
    try {
      const response = await api.patch('/api/v1/company/profile', data)
      setUser({ ...user, ...data })
      showToast('Perfil actualizado correctamente', 'success')
    } catch (err) {
      const message = err.response?.data?.detail || 'Error al actualizar perfil'
      setError('root', { message })
      showToast(message, 'error')
    }
  }

  const [isEditing, setIsEditing] = React.useState(false)

  return (
    <div className="profile-container">
      <h1>Perfil de Empresa</h1>

      <div className="profile-card">
        <div className="profile-header">
          <div className="company-avatar">
            {user?.razon_social?.charAt(0).toUpperCase() || 'C'}
          </div>
          <div className="company-info">
            <h2>{user?.razon_social}</h2>
            <span className={`plan-badge ${user?.plan_tier}`}>
              {user?.plan_tier?.toUpperCase()}
            </span>
            {user?.is_founder && (
              <span className="founder-badge">FOUNDER</span>
            )}
          </div>
        </div>

        {errors.root && (
          <div className="message error">{errors.root.message}</div>
        )}

        {isEditing ? (
          <form onSubmit={handleSubmit(onSubmit)} className="profile-form" noValidate>
            <div className="form-group">
              <label htmlFor="razon_social">Razón Social</label>
              <input
                type="text"
                id="razon_social"
                {...register('razon_social')}
                aria-invalid={errors.razon_social ? 'true' : 'false'}
              />
              {errors.razon_social && (
                <span className="field-error" role="alert">{errors.razon_social.message}</span>
              )}
            </div>
            <div className="form-group">
              <label htmlFor="contact_name">Nombre de Contacto</label>
              <input
                type="text"
                id="contact_name"
                {...register('contact_name')}
                aria-invalid={errors.contact_name ? 'true' : 'false'}
              />
              {errors.contact_name && (
                <span className="field-error" role="alert">{errors.contact_name.message}</span>
              )}
            </div>
            <div className="form-group">
              <label htmlFor="contact_phone">Teléfono</label>
              <input
                type="tel"
                id="contact_phone"
                {...register('contact_phone')}
                aria-invalid={errors.contact_phone ? 'true' : 'false'}
              />
              {errors.contact_phone && (
                <span className="field-error" role="alert">{errors.contact_phone.message}</span>
              )}
            </div>
            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={isSubmitting}>
                {isSubmitting ? 'Guardando...' : 'Guardar Cambios'}
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setIsEditing(false)}
              >
                Cancelar
              </button>
            </div>
          </form>
        ) : (
          <div className="profile-details">
            <div className="detail-row">
              <span className="label">RUC:</span>
              <span className="value">{user?.ruc_hash}</span>
            </div>
            <div className="detail-row">
              <span className="label">Email:</span>
              <span className="value">{user?.contact_email}</span>
            </div>
            <div className="detail-row">
              <span className="label">Contacto:</span>
              <span className="value">{user?.contact_name || 'No especificado'}</span>
            </div>
            <div className="detail-row">
              <span className="label">Teléfono:</span>
              <span className="value">{user?.contact_phone || 'No especificado'}</span>
            </div>
            <div className="detail-row">
              <span className="label">Estado:</span>
              <span className={`value status-${user?.status}`}>{user?.status}</span>
            </div>
            <div className="detail-row">
              <span className="label">Consultas este mes:</span>
              <span className="value">
                {user?.used_queries_this_month} / {user?.max_monthly_queries}
              </span>
            </div>
            <button
              className="btn-primary edit-btn"
              onClick={() => setIsEditing(true)}
            >
              Editar Perfil
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
