import re


def validate_ruc(ruc: str) -> tuple[bool, str | None]:
    """Valida formato de RUC peruano (11 dígitos numéricos)."""
    if not ruc or len(ruc) != 11 or not re.fullmatch(r'\d{11}', ruc):
        return False, 'RUC inválido. Debe tener exactamente 11 dígitos numéricos.'
    return True, None
