"""Sphinx configuration for the Module 4 documentation."""

import os
import sys
from pathlib import Path

# Make modules in module_4/src available to autodoc.
MODULE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MODULE_ROOT / "src"))

# Provide configuration for imports without requiring local credentials.
# Building documentation must not execute database queries.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://localhost/gradcafe_module4_docs",
)

project = "Module 4 GradCafe Analysis"
author = "Karim Zaky"
release = "1.0"

extensions = ["sphinx.ext.autodoc"]

templates_path = ["_templates"]
exclude_patterns = []

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
