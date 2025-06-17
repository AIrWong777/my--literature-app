from setuptools import setup, find_packages

setup(
    name="literature-system",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.115.12",
        "uvicorn==0.33.0",
        "sqlalchemy==2.0.41",
        "bcrypt>=4.0.1",
        "python-jose[cryptography]==3.4.0",
        "python-multipart==0.0.20",
        "PyPDF2==3.0.1",
        "python-dotenv==1.0.1",
        "reportlab==4.1.0",
    ],
    python_requires=">=3.8",
)