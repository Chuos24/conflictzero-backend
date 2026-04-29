from setuptools import setup, find_packages

setup(
    name="conflictzero",
    version="1.0.0",
    description="SDK oficial de Conflict Zero - Verificación y monitoreo de proveedores",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Conflict Zero",
    author_email="dev@conflictzero.com",
    url="https://github.com/conflictzero/sdk-python",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "responses>=0.23",
            "black>=23.0",
            "flake8>=6.0",
        ]
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
