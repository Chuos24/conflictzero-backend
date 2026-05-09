"""
Configuración de pytest para tests de integraciones ERP.
Añade el directorio raíz del proyecto al PYTHONPATH para permitir imports absolutos.
"""

import sys
from pathlib import Path

# Añadir el directorio raíz del proyecto (conflict-zero-fase1) al PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
