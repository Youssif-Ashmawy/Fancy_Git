from setuptools import setup, find_packages
from setuptools.command.build_py import build_py as _build_py
import os
import shutil

class CustomBuildPy(_build_py):
    def run(self):
        # Run the original build command
        _build_py.run(self)
        
        # Copy data files to build directory alongside fancygit.py
        build_lib = os.path.join(self.build_lib, '')
        if os.path.exists(build_lib):
            shutil.copy('command-list.txt', os.path.join(build_lib, 'command-list.txt'))
            shutil.copy('game_questions.json', os.path.join(build_lib, 'game_questions.json'))
            # Copy images folder for logo files
            if os.path.exists('images'):
                images_build_dir = os.path.join(build_lib, 'images')
                if os.path.exists(images_build_dir):
                    shutil.rmtree(images_build_dir)
                shutil.copytree('images', images_build_dir)

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
    license="Apache License 2.0",
    packages=find_packages(),
    py_modules=["fancygit", "welcome", "quiz_server"],
    include_package_data=True,
    cmdclass={'build_py': CustomBuildPy},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
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
)
