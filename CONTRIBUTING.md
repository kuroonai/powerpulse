# Contributing to PowerPulse

Thank you for your interest in contributing to PowerPulse! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)
- [Feature Requests](#feature-requests)
- [License](#license)

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to foster an inclusive and respectful community.

## Getting Started

1. **Fork the repository**:
   Click the 'Fork' button at the top right of the repository page.

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/powerpulse.git
   cd powerpulse
   ```

3. **Set up the upstream remote**:
   ```bash
   git remote add upstream https://github.com/kuroonai/powerpulse.git
   ```

4. **Create a new branch for your changes**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Environment

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   # or
   pip install -r requirements-dev.txt
   ```

3. **Install platform-specific dependencies**:
   - Windows:
     ```bash
     pip install win10toast pywin32
     ```
   - macOS/Linux:
     ```bash
     # No additional packages required for basic functionality
     ```

## Making Changes

1. **Keep your changes focused**:
   Make focused changes that address specific issues or add specific features.

2. **Follow the project structure**:
   ```
   powerpulse/
   ├── __init__.py
   ├── battery.py        # Battery information functionality
   ├── database.py       # Database operations
   ├── stats.py          # Statistics calculations
   ├── notifications.py  # Notification system
   ├── cli.py            # CLI interface
   ├── gui.py            # GUI interface
   └── utils.py          # Utility functions
   ```

3. **Maintain compatibility**:
   Ensure your changes work across Windows, macOS, and Linux platforms.

## Testing

1. **Run tests**:
   ```bash
   pytest
   ```

2. **Add tests for new features**:
   Create tests for any new functionality in the `tests/` directory.

3. **Manual testing**:
   Test your changes on different platforms if possible.

## Pull Request Process

1. **Update your fork**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push your changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a pull request**:
   - Go to your fork on GitHub and click "New Pull Request"
   - Ensure the base repository is `kuroonai/powerpulse` and the base branch is `main`
   - Provide a clear description of the changes

4. **Address review comments**:
   - Make requested changes and push updates to your branch
   - The pull request will update automatically

5. **Wait for approval**:
   - Maintainers will review your PR and either request changes or merge it

## Coding Standards

1. **Code Style**:
   - Follow PEP 8 guidelines
   - Use 4 spaces for indentation (no tabs)
   - Maximum line length of 88 characters

2. **Formatting Tools**:
   - Use `black` for code formatting
   - Use `isort` to organize imports

3. **Code Quality**:
   - Write clear, readable code
   - Add docstrings to classes and functions
   - Use meaningful variable and function names

## Documentation

1. **Code Documentation**:
   - Add docstrings to all functions, classes, and methods
   - Follow the Google docstring format

2. **Project Documentation**:
   - Update README.md with any new features or changes
   - Keep documentation in sync with code changes

## Issue Reporting

1. **Check existing issues**:
   Before creating a new issue, check if it already exists.

2. **Provide complete information**:
   - Description of the issue or feature request
   - Steps to reproduce (for bugs)
   - Expected behavior
   - Actual behavior
   - Screenshots if applicable
   - Operating system and version
   - Python version

## Feature Requests

1. **Check existing requests**:
   Review existing issues and pull requests before submitting.

2. **Provide clear details**:
   - Description of the feature
   - Use cases and benefits
   - Any implementation ideas

## License

By contributing to PowerPulse, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
