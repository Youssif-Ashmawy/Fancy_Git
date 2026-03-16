from setuptools import setup, find_packages
import os

# Read version from VERSION file or default to 1.0.0
def get_version():
    try:
        with open("VERSION", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "1.0.0"

version = get_version()

# Read requirements
with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Read README
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="fancygit",
    version=version,
    author="Youssif Ashmawy",
    author_email="youssif@example.com",
    description="A smart CLI tool that provides intelligent recommendations and helps solve merge conflicts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Youssif-Ashmawy/Fancy_Git",
    py_modules=["fancygit", "launcher"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "fancygit=fancygit:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["VERSION", "README.md", "*.md"],
    },
)
