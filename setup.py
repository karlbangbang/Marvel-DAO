from setuptools import setup, find_packages

setup(
    name="freelance-hunter",
    version="1.0.0",
    description="Outil pour trouver des missions freelance et générer des candidatures",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "rich>=13.7.0",
        "click>=8.1.0",
        "jinja2>=3.1.0",
        "pydantic>=2.5.0",
        "fake-useragent>=1.4.0",
    ],
    entry_points={
        "console_scripts": [
            "freelance-hunter=freelance_hunter.cli:main",
        ],
    },
)
