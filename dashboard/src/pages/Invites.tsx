import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuth } from '../context/AuthContext'
import { useInvites, useInviteStats, useCreateInvite } from '../hooks/useQueries'
import { inviteAPI } from '../services/api'
import { inviteSchema } from '../lib/validations'
import Skeleton from '../components/Skeleton'
import type { z } from 'zod'
import type { Invite } from '../types'
import './Invites.css'

type InviteFormData = z.infer<typeof inviteSchema>

function Invites(): JSX.Element {
  const { user } = useAuth()
  const [showForm, setShowForm] = useState<boolean>(false)
  const [actionError, setActionError] = useState<string>('')
  const [actionSuccess, setActionSuccess] = useState<string>('')

  const { data: invitesData, isLoading: loadingInvites } = useInvites()
  const { data: stats, isLoading: loadingStats } = useInviteStats()
  const createInvite = useCreateInvite()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<InviteFormData>({
    resolver: zodResolver(inviteSchema),
    defaultValues: {
      email: '',
      company_name: '',
      message: '',
    },
  })

  const onSubmit = async (data: InviteFormData): Promise<void> => {
    setActionError('')
    setActionSuccess('')

    try {
      await createInvite.mutateAsync(data)
      setActionSuccess('Invitación enviada exitosamente')
      reset()
      setShowForm(false)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Error al enviar invitación'
      setError('root', { message: msg })
      setActionError(msg)
    }
  }

  const handleResend = async (inviteId: string): Promise<void> => {
    setActionError('')
    setActionSuccess('')
    try {
      await inviteAPI.resend(inviteId)
      setActionSuccess('Invitación reenviada')
    } catch {
      setActionError('Error al reenviar')
    }
  }

  const getStatusBadge = (status: string): JSX.Element => {
    const statusConfig: Record<string, { class: string; label: string }> = {
      pending: { class: 'status-pending', label: 'Pendiente' },
      accepted: { class: 'status-accepted', label: 'Aceptada' },
      expired: { class: 'status-expired', label: 'Expirada' }
    }
    const config = statusConfig[status] || statusConfig.pending
    return <span className={`status-badge ${config.class}`}>{config.label}</span>
  }

  const loading = loadingInvites || loadingStats
  const invites: Invite[] = invitesData?.items || []
  const computedStats = {
    total_sent: invites.length,
    accepted: invites.filter(i => i.status === 'accepted').length,
    pending: invites.filter(i => i.status === 'pending').length,
    conversion_rate: invites.length > 0
      ? Math.round((invites.filter(i => i.status === 'accepted').length / invites.length) * 100)
      : 0
  }

  if (loading) {
    return (
      <div className="invites-page">
        <div className="page-header">
          <h1>Sistema de Invitaciones</h1>
          <p>Invita a otras constructoras y expande tu red de confianza</p>
        </div>
        <div className="stats-cards">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="stat-card">
              <Skeleton variant="circle" width={40} height={40} />
              <div className="stat-info">
                <Skeleton variant="text" width={60} height={24} />
                <Skeleton variant="text" width={100} height={16} />
              </div>
            </div>
          ))}
        </div>
        <Skeleton variant="rect" height={400} />
      </div>
    )
  }

  return (
    <div className="invites-page">
      <div className="page-header">
        <h1>Sistema de Invitaciones</h1>
        <p>Invita a otras constructoras y expande tu red de confianza</p>
      </div>

      <div className="stats-cards">
        <div className="stat-card">
          <div className="stat-icon">📧</div>
          <div className="stat-info">
            <span className="stat-value">{stats?.total_sent ?? 0}</span>
            <span className="stat-label">Invitaciones Enviadas</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-info">
            <span className="stat-value">{computedStats.accepted}</span>
            <span className="stat-label">Aceptadas</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⏳</div>
          <div className="stat-info">
            <span className="stat-value">{stats?.pending ?? 0}</span>
            <span className="stat-label">Pendientes</span>
          </div>
        </div>
        <div className="stat-card highlight">
          <div className="stat-icon">📈</div>
          <div className="stat-info">
            <span className="stat-value">{stats?.conversion_rate ?? 0}%</span>
            <span className="stat-label">Tasa de Conversión</span>
          </div>
        </div>
      </div>

      {errors.root && <div className="alert alert-error">{errors.root.message}</div>}
      {actionError && <div className="alert alert-error">{actionError}</div>}
      {actionSuccess && <div className="alert alert-success">{actionSuccess}</div>}

      <div className="invites-actions">
        <button
          className="btn btn-primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancelar' : '+ Nueva Invitación'}
        </button>
      </div>

      {showForm && (
        <div className="invite-form-card">
          <h3>Nueva Invitación</h3>
          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  type="email"
                  id="email"
                  placeholder="contacto@empresa.com"
                  {...register('email')}
                  aria-invalid={errors.email ? 'true' : 'false'}
                />
                {errors.email && (
                  <span className="field-error" role="alert">{errors.email.message}</span>
                )}
              </div>
              <div className="form-group">
                <label htmlFor="company_name">Nombre de la Empresa</label>
                <input
                  type="text"
                  id="company_name"
                  placeholder="Constructora Ejemplo S.A.C."
                  {...register('company_name')}
                  aria-invalid={errors.company_name ? 'true' : 'false'}
                />
                {errors.company_name && (
                  <span className="field-error" role="alert">{errors.company_name.message}</span>
                )}
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="message">Mensaje Personalizado (opcional)</label>
              <textarea
                id="message"
                placeholder="Hola, te invito a unirte a Conflict Zero..."
                rows={3}
                {...register('message')}
              />
              {errors.message && (
                <span className="field-error" role="alert">{errors.message.message}</span>
              )}
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting || createInvite.isPending}
            >
              {createInvite.isPending ? 'Enviando...' : 'Enviar Invitación'}
            </button>
          </form>
        </div>
      )}

      <div className="invites-list-card">
        <h3>Historial de Invitaciones</h3>
        {invites.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <p>No has enviado invitaciones aún</p>
            <span>Invita a tus socios comerciales a unirse</span>
          </div>
        ) : (
          <table className="invites-table">
            <thead>
              <tr>
                <th>Empresa</th>
                <th>Email</th>
                <th>Estado</th>
                <th>Fecha</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {invites.map((invite) => (
                <tr key={invite.id}>
                  <td>{invite.company_name}</td>
                  <td>{invite.email}</td>
                  <td>{getStatusBadge(invite.status)}</td>
                  <td>{new Date(invite.created_at).toLocaleDateString('es-PE')}</td>
                  <td>
                    {invite.status === 'pending' && (
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => handleResend(invite.id)}
                      >
                        Reenviar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {user?.plan_tier === 'founder' && (
        <div className="founder-notice">
          <div className="notice-icon">⭐</div>
          <div className="notice-content">
            <h4>Programa Founder Activo</h4>
            <p>Como Founder, tienes la obligación contractual de invitar a tus subcontratistas. Cada invitación cuenta para tu red de confianza.</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default Invites
