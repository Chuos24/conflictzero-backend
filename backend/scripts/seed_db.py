"""
Script para poblar la base de datos con datos de prueba
Uso: python seed_db.py
"""
import os
import sys
from datetime import datetime, timedelta
import hashlib

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, get_db, engine
from app.models_v2 import (
    Base, Company, FounderApplication, PublicProfile, Invite,
    VerificationRequest, CompanyHierarchy, ApiKey, AuditLog
)
from sqlalchemy.orm import Session


def hash_ruc(ruc: str) -> str:
    return hashlib.sha256(ruc.encode()).hexdigest()


def seed_database(db: Session):
    """Poblar DB con datos de prueba"""
    
    print("🌱 Seeding database...")
    
    # 1. Crear empresas de prueba
    companies_data = [
        {
            "ruc": "20100123091",
            "razon_social": "Constructora Demo SAC",
            "contact_email": "demo@constructora.com",
            "contact_name": "Juan Demo",
            "plan_tier": "founder",
            "is_founder": True,
            "founder_expires_at": datetime.utcnow() + timedelta(days=90),
            "contractual_obligation": True,
            "contractual_signed_at": datetime.utcnow()
        },
        {
            "ruc": "20529400790",
            "razon_social": "Grupo Constructor Beta",
            "contact_email": "contacto@betaconstructora.com",
            "contact_name": "María Beta",
            "plan_tier": "gold"
        },
        {
            "ruc": "20100212023",
            "razon_social": "Constructora Gamma EIRL",
            "contact_email": "admin@gammaconst.com",
            "contact_name": "Carlos Gamma",
            "plan_tier": "silver"
        },
        {
            "ruc": "20456789121",
            "razon_social": "Delta Construcciones",
            "contact_email": "info@deltaconst.com",
            "contact_name": "Ana Delta",
            "plan_tier": "bronze"
        }
    ]
    
    companies = []
    for data in companies_data:
        ruc_hash = hash_ruc(data["ruc"])
        
        # Verificar si ya existe
        existing = db.query(Company).filter(Company.ruc_hash == ruc_hash).first()
        if existing:
            print(f"  ⏭️  Company {data['razon_social']} already exists")
            companies.append(existing)
            continue
        
        company = Company(
            ruc_hash=ruc_hash,
            ruc_encrypted=data["ruc"].encode(),  # En producción: encriptar con AES
            razon_social=data["razon_social"],
            contact_email=data["contact_email"],
            contact_name=data["contact_name"],
            plan_tier=data.get("plan_tier", "bronze"),
            status="active",
            is_founder=data.get("is_founder", False),
            founder_expires_at=data.get("founder_expires_at"),
            contractual_obligation=data.get("contractual_obligation", False),
            contractual_signed_at=data.get("contractual_signed_at"),
            max_monthly_queries=10000 if data.get("is_founder") else 1000
        )
        db.add(company)
        db.flush()  # Para obtener el ID
        companies.append(company)
        print(f"  ✅ Created company: {data['razon_social']}")
    
    db.commit()
    
    # 2. Crear perfiles públicos
    for company in companies:
        existing_profile = db.query(PublicProfile).filter(
            PublicProfile.company_id == company.id
        ).first()
        
        if existing_profile:
            continue
        
        profile = PublicProfile(
            company_id=company.id,
            slug=f"cz{hash_ruc(company.ruc_hash)[:14]}",
            display_name=company.razon_social,
            sello_status="gold" if company.is_founder else "bronze",
            sello_expires_at=company.founder_expires_at if company.is_founder else datetime.utcnow() + timedelta(days=30),
            current_score=85 if company.is_founder else 65,
            risk_level="low" if company.is_founder else "medium",
            total_verifications=10 if company.is_founder else 2,
            last_verified_at=datetime.utcnow()
        )
        db.add(profile)
        print(f"  ✅ Created public profile for: {company.razon_social}")
    
    db.commit()
    
    # 3. Crear aplicaciones de Founder de prueba
    applications_data = [
        {
            "ruc": "20987654321",
            "company_name": "Mega Constructora Omega",
            "contact_name": "Pedro Omega",
            "contact_email": "pedro@omega.com",
            "annual_volume": "200M+",
            "subcontractor_count": "50+",
            "status": "pending"
        },
        {
            "ruc": "20876543210",
            "company_name": "Constructora Sigma Peru",
            "contact_name": "Laura Sigma",
            "contact_email": "laura@sigma.com",
            "annual_volume": "50-200M",
            "subcontractor_count": "20-50",
            "status": "under_review"
        },
        {
            "ruc": "20765432109",
            "company_name": "Grupo Tau Inmobiliaria",
            "contact_name": "Roberto Tau",
            "contact_email": "roberto@tau.com",
            "annual_volume": "10-50M",
            "subcontractor_count": "5-20",
            "status": "approved"
        }
    ]
    
    for data in applications_data:
        ruc_hash = hash_ruc(data["ruc"])
        
        existing = db.query(FounderApplication).filter(
            FounderApplication.ruc_hash == ruc_hash
        ).first()
        
        if existing:
            continue
        
        app = FounderApplication(
            ruc_hash=ruc_hash,
            ruc_encrypted=data["ruc"].encode(),
            company_name=data["company_name"],
            contact_name=data["contact_name"],
            contact_email=data["contact_email"],
            annual_volume=data["annual_volume"],
            subcontractor_count=data["subcontractor_count"],
            status=data["status"]
        )
        db.add(app)
        print(f"  ✅ Created founder application: {data['company_name']}")
    
    db.commit()
    
    # 4. Crear invitaciones para el Founder demo
    founder = companies[0]  # Constructora Demo SAC
    
    invites_data = [
        {"email": "sub1@example.com", "company": "Subcontratista Uno", "status": "paid"},
        {"email": "sub2@example.com", "company": "Subcontratista Dos", "status": "registered"},
        {"email": "sub3@example.com", "company": "Subcontratista Tres", "status": "opened"},
        {"email": "sub4@example.com", "company": "Subcontratista Cuatro", "status": "sent"},
        {"email": "sub5@example.com", "company": "Subcontratista Cinco", "status": "sent"}
    ]
    
    for i, data in enumerate(invites_data):
        import secrets
        import string
        
        code = "CZ-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4)) + "-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        
        invite = Invite(
            invite_code=code,
            inviter_id=founder.id,
            inviter_company_name=founder.razon_social,
            invitee_email=data["email"],
            invitee_company_name=data["company"],
            status=data["status"],
            depth_level=1,
            monthly_value=500.0 if data["status"] == "paid" else None,
            converted_to_paid_at=datetime.utcnow() if data["status"] == "paid" else None
        )
        db.add(invite)
    
    db.commit()
    print(f"  ✅ Created {len(invites_data)} invites for founder")
    
    # 5. Crear verificaciones de ejemplo
    for company in companies[:2]:  # Solo para 2 empresas
        for i in range(3):
            verification = VerificationRequest(
                consultant_id=founder.id,
                target_ruc_hash=hash_ruc(f"2099999999{i}"),
                target_company_name=f"Empresa Verificada {i}",
                score=70 + i * 10,
                risk_level="low" if i > 0 else "medium",
                sunat_debt=0.0,
                sunat_tax_status="HABIDO",
                sunat_contributor_status="ACTIVO",
                osce_sanctions_count=0,
                tce_sanctions_count=0,
                is_cached=True,
                cache_expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.add(verification)
    
    db.commit()
    print(f"  ✅ Created verification requests")
    
    print("\n✅ Database seeded successfully!")
    print(f"   - {len(companies)} companies")
    print(f"   - {len(applications_data)} founder applications")
    print(f"   - {len(invites_data)} invites")
    print(f"   - Multiple verifications")


if __name__ == "__main__":
    # Test database connection
    from app.core.database import test_connection
    
    if not test_connection():
        print("❌ Could not connect to database")
        sys.exit(1)
    
    # Create tables
    print("🗄️  Creating tables...")
    init_db()
    
    # Get session and seed
    db = next(get_db())
    try:
        seed_database(db)
    finally:
        db.close()
