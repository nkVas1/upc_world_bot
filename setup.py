"""Setup for UPC World Bot."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="upc-world-bot",
    version="3.0.0",
    author="Under People Club",
    author_email="tech@underpeople.club",
    description="Modern Telegram Bot for Under People Club",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/underpeople/upc-world-bot",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "upc-bot=bot.main:main",
        ],
    },
)
