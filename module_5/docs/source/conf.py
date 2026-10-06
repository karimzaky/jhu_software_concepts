"""Sphinx configuration for the Module 5 documentation."""
import os
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MODULE_ROOT / "src"))
# Autodoc imports modules but does not run database queries.
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/gradcafe_module5_docs")
project = "Module 5 Secure GradCafe Development"
author = "Karim Zaky"
release = "1.0"
extensions = ["sphinx.ext.autodoc"]
templates_path = ["_templates"]
exclude_patterns = []
html_theme = "sphinx_rtd_theme"
html_static_path = []
