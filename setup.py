# setup.py
from setuptools import setup, find_packages

setup(
    name="resistor_matcher",
    version="0.1.0",
    description="Анализ и подбор комбинаций резисторов",
    author="Alexander Orlov",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
        "matplotlib>=3.7.0",
        "numpy>=1.24.0",
    ],
    entry_points={
        "console_scripts": [
            "resistor-matcher=cli.main:main",
            "resistor-select=cli.select:main",
            "resistor-estimate=cli.estimate:main",
        ],
    },
)