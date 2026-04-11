import React, { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../services/api'
import './Profile.css'

export default function Profile() {
  const { user, setUser } = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [formData, setFormData] = useState({
    contact_name: user?.contact_name || '',
    contact_phone: user?.contact_phone || '',
    razon_social: user?.razon_social || ''
  })

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage('')

    try {
      const response = await api.patch('/api/v1/company/profile', formData)
      setMessage('Perfil actualizado correctamente')
      setUser({ ...user, ...formData })
      setIsEditing(false)
    } catch (err) {
      setMessage('Error al actualizar perfil')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

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

        {message && (
          <div className={`message ${message.includes('Error') ? 'error' : 'success'}`}>
            {message}
          </div>
        )}

        {isEditing ? (
          <form onSubmit={handleSubmit} className="profile-form">
            <div className="form-group">
              <label>Razón Social</label>
              <input
                type="text"
                name="razon_social"
                value={formData.razon_social}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-group">
              <label>Nombre de Contacto</label>
              <input
                type="text"
                name="contact_name"
                value={formData.contact_name}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-group">
              <label>Teléfono</label>
              <input
                type="tel"
                name="contact_phone"
                value={formData.contact_phone}
                onChange={handleChange}
              />
            </div>
            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Guardando...' : 'Guardar Cambios'}
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
