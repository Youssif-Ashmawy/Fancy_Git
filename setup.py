from setuptools import setup, find_packages
import os

# Read version from VERSION file or default to 1.0.0
def get_version():
    try:
        # Force fresh read by reopening file
        with open("VERSION", "r") as f:
            f.seek(0)  # Ensure we're at start
            version = f.read().strip()
            print(f"DEBUG: Read version '{version}' from VERSION file")
            return version
    except FileNotFoundError:
        print("DEBUG: VERSION file not found, using default 1.0.0")
        return "1.0.0"

# Always read fresh version during setup
version = get_version()

# Read requirements
def get_requirements():
    try:
        with open("requirements.txt", "r") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return ["requests>=2.25.0"]

requirements = get_requirements()

# Read README
def get_long_description():
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "FancyGit - A smart CLI tool for git"

long_description = get_long_description()

setup(
    name="fancygit",
    version=version,
    author="Youssif Ashmawy",
    author_email="ashmawyyoussif@gmail.com",
    description="A smart CLI tool that provides intelligent recommendations and helps solve merge conflicts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Youssif-Ashmawy/Fancy_Git",
    py_modules=["fancygit"],
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
