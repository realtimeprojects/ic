from setuptools import setup, find_packages

setup(
    name="ic",
    version="0.1.0",
    description="A flexible command line interface framework driven by YAML configurations",
    author="Your Name",
    package_dir={"": "sw"},  # Look for packages in the sw directory
    packages=find_packages(where="sw"),  # Find packages in sw directory
    install_requires=[
        "pyyaml>=6.0",  # For YAML configuration parsing
    ],
    entry_points={
        "console_scripts": [
            "ic=ic.cli:main",  # Points to cli.py for main implementation
        ],
    },
    package_data={
        'ic': ['data/*.yml'],  # Include YAML files from data directory
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
) 