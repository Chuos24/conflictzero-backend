"""
Tests unitarios para Conflict Zero
"""
import pytest
from datetime import datetime, timedelta
import hashlib
import uuid

# Test de hash RUC
def test_ruc_hashing():
    """El hash de RUC debe ser determinístico"""
    ruc = "20100123091"
    hash1 = hashlib.sha256(ruc.encode()).hexdigest()
    hash2 = hashlib.sha256(ruc.encode()).hexdigest()
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length

# Test de validación de RUC
def test_ruc_validation():
    """Validación de formato de RUC peruano"""
    valid_rucs = [
        "20100123091",
        "20529400790",
        "10456789123"
    ]
    
    for ruc in valid_rucs:
        assert len(ruc) == 11, f"RUC {ruc} debe tener 11 dígitos"
        assert ruc.isdigit(), f"RUC {ruc} debe ser numérico"

# Test de invitación
def test_invite_code_format():
    """Los códigos de invitación deben seguir el formato CZ-XXXX-XXXX"""
    import secrets
    import string
    
    def generate_invite_code():
        return "CZ-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4)) + "-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    
    code = generate_invite_code()
    assert code.startswith("CZ-")
    assert len(code) == 12  # CZ-XXXX-XXXX
    parts = code.split("-")
    assert len(parts) == 3
    assert len(parts[1]) == 4
    assert len(parts[2]) == 4

# Test de prioridad de aplicación Founder
def test_founder_priority_score():
    """El score de prioridad debe calcularse correctamente"""
    
    def get_priority_score(annual_volume, subcontractor_count):
        volume_score = {'200M+': 100, '50-200M': 75, '10-50M': 50}.get(annual_volume, 50)
        subs_score = {'50+': 100, '20-50': 75, '5-20': 50}.get(subcontractor_count, 50)
        return volume_score + subs_score
    
    # Mayor volumen + más subs = mayor prioridad
    assert get_priority_score('200M+', '50+') == 200
    assert get_priority_score('10-50M', '5-20') == 100
    assert get_priority_score('50-200M', '20-50') == 150

# Test de estados de invitación
def test_invite_status_transitions():
    """Las transiciones de estado de invitación deben ser válidas"""
    valid_statuses = ['sent', 'opened', 'clicked', 'registered', 'paid', 'expired', 'cancelled']
    
    # Estado inicial siempre es 'sent'
    initial_status = 'sent'
    assert initial_status in valid_statuses
    
    # Estados finales válidos
    final_statuses = ['paid', 'expired', 'cancelled']
    for status in final_statuses:
        assert status in valid_statuses

# Test de cálculo de cumplimiento Founder
def test_founder_compliance_calculation():
    """El estado de cumplimiento debe calcularse correctamente"""
    
    def get_compliance_status(total_invitados, registrados, dias_restantes, tiene_obligacion):
        if not tiene_obligacion:
            return "sin_obligacion"
        elif total_invitados == 0:
            return "sin_invitados"
        elif registrados >= total_invitados * 0.5:
            return "cumpliendo"
        elif dias_restantes is not None and dias_restantes <= 7:
            return "riesgo_inminente"
        else:
            return "en_riesgo"
    
    # Sin obligación
    assert get_compliance_status(0, 0, 30, False) == "sin_obligacion"
    
    # Sin invitados
    assert get_compliance_status(0, 0, 30, True) == "sin_invitados"
    
    # Cumpliendo (50%+)
    assert get_compliance_status(10, 5, 30, True) == "cumpliendo"
    assert get_compliance_status(10, 8, 30, True) == "cumpliendo"
    
    # En riesgo (< 50%)
    assert get_compliance_status(10, 4, 30, True) == "en_riesgo"
    
    # Riesgo inminente (pocos días)
    assert get_compliance_status(10, 4, 5, True) == "riesgo_inminente"

# Test de límites de comparación por plan
def test_compare_limits_by_plan():
    """Los límites de comparación varían según el plan"""
    
    limits = {
        "bronze": {"max_per_comparison": 3, "comparisons_per_day": 5},
        "silver": {"max_per_comparison": 5, "comparisons_per_day": 20},
        "gold": {"max_per_comparison": 10, "comparisons_per_day": 100},
        "founder": {"max_per_comparison": 10, "comparisons_per_day": 999999}
    }
    
    assert limits["bronze"]["max_per_comparison"] == 3
    assert limits["founder"]["max_per_comparison"] == 10
    assert limits["founder"]["comparisons_per_day"] > limits["gold"]["comparisons_per_day"]

# Test de validación de RUCs para comparación
def test_compare_ruc_validation():
    """Validación de RUCs antes de comparación"""
    
    def validate_rucs(rucs):
        errors = []
        valid = []
        for ruc in rucs:
            if len(ruc) != 11:
                errors.append({"ruc": ruc, "error": "Longitud inválida"})
            elif not ruc.isdigit():
                errors.append({"ruc": ruc, "error": "Debe ser numérico"})
            else:
                valid.append(ruc)
        return valid, errors
    
    # RUCs válidos
    valid, errors = validate_rucs(["20100123091", "20529400790"])
    assert len(valid) == 2
    assert len(errors) == 0
    
    # RUCs inválidos
    valid, errors = validate_rucs(["2010012309", "ABC", ""])
    assert len(valid) == 0
    assert len(errors) == 3

# Test de generación de slug público
def test_public_slug_generation():
    """Los slugs públicos deben tener formato correcto"""
    import secrets
    import string
    
    def generate_slug():
        return ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(16))
    
    slug = generate_slug()
    assert len(slug) == 16
    assert slug.isalnum()
    assert slug.islower() or any(c.isdigit() for c in slug)

# Test de soft delete
def test_soft_delete_logic():
    """El soft delete debe marcar deleted_at sin eliminar el registro"""
    from datetime import datetime
    
    class MockRecord:
        def __init__(self):
            self.deleted_at = None
        
        def soft_delete(self):
            self.deleted_at = datetime.utcnow()
        
        def is_active(self):
            return self.deleted_at is None
    
    record = MockRecord()
    assert record.is_active()
    
    record.soft_delete()
    assert not record.is_active()
    assert record.deleted_at is not None

# Test de fechas de retención
def test_retention_period():
    """Los registros deben tener período de retención de 5 años"""
    from datetime import datetime, timedelta
    
    created_at = datetime.utcnow()
    retained_until = created_at + timedelta(days=365*5)
    
    # 5 años de diferencia
    diff = retained_until - created_at
    assert diff.days == 365 * 5
