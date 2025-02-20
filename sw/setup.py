from setuptools import setup, find_packages

setup(
    name="ic",
    version="0.1.0",
    description="A flexible command line interface framework driven by YAML configurations",
    author="Your Name",
    package_dir={"": "."},  # Changed from "sw" to "." since we're now in sw/
    packages=find_packages(),  # Changed since we're now in sw/
    install_requires=[
        "pyyaml>=6.0",  # For YAML configuration parsing
    ],
    entry_points={
        "console_scripts": [
            "ic=ic.main:main",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
) 