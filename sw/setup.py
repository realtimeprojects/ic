from setuptools import setup, find_packages

setup(
    name="ac",
    version="0.1.0",
    description="A flexible command line interface framework driven by YAML configurations",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0",  # For YAML configuration parsing
    ],
    entry_points={
        "console_scripts": [
            "ac=ac.main:main",
        ],
    },
    python_requires=">=3.7",
) 