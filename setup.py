import os
from setuptools import setup, find_packages

# Read the contents of README.md
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

# Platform-specific dependencies
platform_deps = {
    'win32': ['win10toast', 'pywin32'],
    'darwin': [],  # macOS specific deps
    'linux': []    # Linux specific deps
}

# Requirements
install_requires = [
    'psutil>=5.9.0',
    'matplotlib>=3.5.0',
    'numpy>=1.20.0',
]

# Development requirements
dev_requires = [
    'pytest>=7.0.0',
    'pytest-cov>=4.0.0',
    'black>=22.0.0',
    'isort>=5.0.0',
    'pyinstaller>=5.0.0',
]

setup(
    name="powerpulse",
    version="0.1.0",
    author="Naveen Vasudevan",
    author_email="YOUR_EMAIL@example.com",  # Replace with your email
    description="A lightweight, cross-platform battery monitoring tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kuroonai/powerpulse",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Topic :: System :: Monitoring",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require={
        'dev': dev_requires,
        'windows': platform_deps['win32'],
        'macos': platform_deps['darwin'],
        'linux': platform_deps['linux'],
    },
    entry_points={
        'console_scripts': [
            'powerpulse=powerpulse.cli:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
