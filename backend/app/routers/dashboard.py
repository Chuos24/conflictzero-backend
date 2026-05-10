"""
Dashboard Router - Endpoints para estadísticas del dashboard
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_company
from app.models_v2 import Company, VerificationRequest, Invite, ComparisonRequest

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for current user"""
    company_id = current_company.id
    
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
    
    # Calculate compliance score based on real data
    # Score = weighted average of verification health + invite activity
    verifications_all = db.query(VerificationRequest).filter(
        VerificationRequest.company_id == company_id
    ).all()
    
    total_verifications = len(verifications_all)
    if total_verifications > 0:
        avg_risk_score = sum(v.risk_score or 50 for v in verifications_all) / total_verifications
        # Lower avg risk score = higher compliance (invert)
        verification_health = max(0, min(100, 100 - avg_risk_score))
    else:
        verification_health = 50  # neutral if no verifications
    
    # Founder bonus based on invite conversion
    founder_bonus = 0
    if current_company.is_founder and invites_sent > 0:
        conversion_rate = (invites_accepted / invites_sent) * 100
        founder_bonus = min(15, conversion_rate * 0.3)  # up to 15 points
    
    # Plan base bonus
    plan_bonus = {"bronze": 0, "silver": 3, "gold": 5, "founder": 10}.get(
        current_company.plan_tier, 0
    )
    
    compliance_score = min(100, int(verification_health + founder_bonus + plan_bonus))
    
    return {
        "verifications_count": verifications_count,
        "comparisons_count": comparisons_count,
        "invites_sent": invites_sent,
        "invites_accepted": invites_accepted,
        "compliance_score": base_score,
        "plan_tier": current_company.plan_tier,
        "company_name": current_company.razon_social
    }


@router.get("/chart-data")
async def get_chart_data(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Get chart data for dashboard"""
    company_id = current_company.id
    
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
    
    # Compliance distribution - based on real verification data
    verifications_all = db.query(VerificationRequest).filter(
        VerificationRequest.company_id == company_id,
        VerificationRequest.created_at >= six_months_ago
    ).all()
    
    risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for v in verifications_all:
        score = v.risk_score or 50
        if score <= 30:
            risk_counts["low"] += 1
        elif score <= 60:
            risk_counts["medium"] += 1
        elif score <= 80:
            risk_counts["high"] += 1
        else:
            risk_counts["critical"] += 1
    
    total_verifications = sum(risk_counts.values()) or 1  # avoid division by zero
    compliance_distribution = [
        {"name": "Compliant", "value": round(risk_counts["low"] / total_verifications * 100), "color": "#4caf50"},
        {"name": "Warning", "value": round(risk_counts["medium"] / total_verifications * 100), "color": "#ff9800"},
        {"name": "High Risk", "value": round((risk_counts["high"] + risk_counts["critical"]) / total_verifications * 100), "color": "#f44336"}
    ]
    
    # Top risk factors - based on real data from verification results
    # Count issues from verification requests that have result data
    osce_count = 0
    tce_count = 0
    debt_count = 0
    indecopi_count = 0
    
    for v in verifications_all:
        result = v.result_data or {}
        osce_data = result.get("osce", {})
        tce_data = result.get("tce", {})
        sunat_data = result.get("sunat", {})
        
        if osce_data.get("total_sanciones", 0) > 0:
            osce_count += 1
        if tce_data.get("total_sanciones", 0) > 0:
            tce_count += 1
        if sunat_data.get("deuda", 0) > 0:
            debt_count += 1
        if result.get("indecopi_sanciones", 0) > 0:
            indecopi_count += 1
    
    top_risk_factors = [
        {"factor": "OSCE Sanciones", "count": osce_count},
        {"factor": "TCE Sanciones", "count": tce_count},
        {"factor": "Deuda Tributaria", "count": debt_count},
        {"factor": "Indecopi", "count": indecopi_count}
    ]
    
    # Sort by count descending
    top_risk_factors.sort(key=lambda x: x["count"], reverse=True)
    
    return {
        "verificationsByMonth": verifications_by_month,
        "complianceDistribution": compliance_distribution,
        "topRiskFactors": top_risk_factors
    }


@router.get("/activity")
async def get_recent_activity(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Get recent activity for dashboard"""
    company_id = current_company.id
    
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
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Export verification history as CSV"""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    
    company_id = current_company.id
    
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
