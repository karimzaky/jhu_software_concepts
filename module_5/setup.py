"""Install the Module 5 source modules for local development and CI."""

from pathlib import Path
from setuptools import setup

ROOT = Path(__file__).resolve().parent
requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()

setup(
    name="gradcafe-module5",
    version="0.1.0",
    description="GradCafe analysis with secure SQL and automated verification",
    author="Karim Zaky",
    python_requires=">=3.13",
    package_dir={"": "src"},
    py_modules=sorted(path.stem for path in (ROOT / "src").glob("*.py")
                      if path.stem != "__init__"),
    install_requires=[line for line in requirements
                      if line.strip() and not line.startswith("#")],
    entry_points={"console_scripts": ["gradcafe-module5=app:main"]},
)
