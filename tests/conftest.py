# -*- coding: utf-8 -*-
"""Fixtures compartidos para la suite de tests."""
import sys
from pathlib import Path

# Permite importar los módulos del proyecto sin instalación
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
