"""
Dashboard Router - Endpoints para estadísticas del dashboard
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models_v2 import Company, VerificationRequest, Invite, ComparisonRequest

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    current_user: Company = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for current user"""
    company_id = current_user.id
    
    # Count verifications
    verifications_count = db.query(VerificationRequest).filter(
        VerificationRequest.company_id == company_id
    ).count()
    
    # Count comparisons
    comparisons_count = db.query(ComparisonRequest).filter(
        ComparisonRequest.company_id == company_id
    ).count()
    
    # Count invites
    invites_sent = db.query(Invite).filter(
        Invite.inviter_company_id == company_id
    ).count()
    
    invites_accepted = db.query(Invite).filter(
        and_(
            Invite.inviter_company_id == company_id,
            Invite.status == "accepted"
        )
    ).count()
    
    # Calculate compliance score (mock logic - can be enhanced)
    base_score = 85
    if current_user.plan_tier == "founder":
        base_score = 95
    elif current_user.plan_tier == "gold":
        base_score = 90
    elif current_user.plan_tier == "silver":
        base_score = 88
    
    return {
        "verifications_count": verifications_count,
        "comparisons_count": comparisons_count,
        "invites_sent": invites_sent,
        "invites_accepted": invites_accepted,
        "compliance_score": base_score,
        "plan_tier": current_user.plan_tier,
        "company_name": current_user.company_name
    }


@router.get("/chart-data")
async def get_chart_data(
    current_user: Company = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chart data for dashboard"""
    company_id = current_user.id
    
    # Get verifications by month (last 6 months)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    
    verifications = db.query(
        func.date_trunc('month', VerificationRequest.created_at).label('month'),
        func.count(VerificationRequest.id).label('count')
    ).filter(
        and_(
            VerificationRequest.company_id == company_id,
            VerificationRequest.created_at >= six_months_ago
        )
    ).group_by('month').order_by('month').all()
    
    # Generate month labels
    months = []
    for i in range(5, -1, -1):
        d = datetime.utcnow() - timedelta(days=i*30)
        months.append(d.strftime('%b'))
    
    # Default data if no verifications
    verifications_by_month = [
        {"month": month, "count": 0, "score": 80 + i*2} 
        for i, month in enumerate(months)
    ]
    
    # Fill with actual data
    for v in verifications:
        month_str = v[0].strftime('%b') if v[0] else None
        if month_str:
            for vm in verifications_by_month:
                if vm["month"] == month_str:
                    vm["count"] = v[1]
                    break
    
    # Compliance distribution (mock data based on plan)
    compliance_distribution = [
        {"name": "Compliant", "value": 75, "color": "#4caf50"},
        {"name": "Warning", "value": 15, "color": "#ff9800"},
        {"name": "Critical", "value": 10, "color": "#f44336"}
    ]
    
    if current_user.plan_tier == "founder":
        compliance_distribution = [
            {"name": "Compliant", "value": 90, "color": "#4caf50"},
            {"name": "Warning", "value": 8, "color": "#ff9800"},
            {"name": "Critical", "value": 2, "color": "#f44336"}
        ]
    
    # Top risk factors (mock data)
    top_risk_factors = [
        {"factor": "OSCE Sanciones", "count": 5},
        {"factor": "TCE Sanciones", "count": 3},
        {"factor": "Deuda Tributaria", "count": 2},
        {"factor": "Indecopi", "count": 1}
    ]
    
    return {
        "verificationsByMonth": verifications_by_month,
        "complianceDistribution": compliance_distribution,
        "topRiskFactors": top_risk_factors
    }


@router.get("/activity")
async def get_recent_activity(
    current_user: Company = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Get recent activity for dashboard"""
    company_id = current_user.id
    
    # Get recent verifications
    verifications = db.query(VerificationRequest).filter(
        VerificationRequest.company_id == company_id
    ).order_by(VerificationRequest.created_at.desc()).limit(limit).all()
    
    activity = []
    for v in verifications:
        activity.append({
            "title": f"Verificación: {v.ruc_hash[:8]}...",
            "date": v.created_at.strftime("%d/%m/%Y %H:%M") if v.created_at else "",
            "status": v.status or "completed",
            "type": "verification"
        })
    
    # Get recent comparisons
    comparisons = db.query(ComparisonRequest).filter(
        ComparisonRequest.company_id == company_id
    ).order_by(ComparisonRequest.created_at.desc()).limit(limit).all()
    
    for c in comparisons:
        activity.append({
            "title": f"Comparación de {len(c.rucs)} empresas",
            "date": c.created_at.strftime("%d/%m/%Y %H:%M") if c.created_at else "",
            "status": "completed",
            "type": "comparison"
        })
    
    # Sort by date (newest first)
    activity.sort(key=lambda x: x["date"], reverse=True)
    
    return activity[:limit]


@router.get("/export/csv")
async def export_csv(
    current_user: Company = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export verification history as CSV"""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    
    company_id = current_user.id
    
    verifications = db.query(VerificationRequest).filter(
        VerificationRequest.company_id == company_id
    ).order_by(VerificationRequest.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "ID", "RUC Hash", "Status", "Risk Score", 
        "Created At", "Completed At"
    ])
    
    # Write data
    for v in verifications:
        writer.writerow([
            str(v.id),
            v.ruc_hash,
            v.status or "pending",
            v.risk_score or "N/A",
            v.created_at.isoformat() if v.created_at else "",
            v.completed_at.isoformat() if v.completed_at else ""
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=verifications_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )
