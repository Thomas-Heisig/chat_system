# Contributing Guide

Thank you for your interest in contributing to the Universal Chat System!

## 📋 Table of Contents

1. [Code of Conduct](code-of-conduct.md) - Community guidelines
2. [Getting Started](getting-started.md) - First-time contributors
3. [Development Workflow](development-workflow.md) - Git workflow and branching
4. [Coding Standards](coding-standards.md) - Code style guidelines
5. [Testing Requirements](testing-requirements.md) - Testing guidelines
6. [Documentation Standards](documentation-standards.md) - Documentation guidelines
7. [Pull Request Process](pull-request-process.md) - PR guidelines and review
8. [Issue Guidelines](issue-guidelines.md) - Reporting bugs and requesting features

## Quick Start for Contributors

### 1. Fork and Clone
```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR-USERNAME/chat_system.git
cd chat_system
```

### 2. Set Up Development Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 3. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 4. Make Your Changes
- Follow coding standards
- Write tests for new functionality
- Update documentation
- Ensure all tests pass

### 5. Submit Pull Request
```bash
# Commit your changes
git add .
git commit -m "Add your feature"

# Push to your fork
git push origin feature/your-feature-name

# Open a Pull Request on GitHub
```

## Ways to Contribute

### 🐛 Report Bugs
Found a bug? [Open an issue](https://github.com/Thomas-Heisig/chat_system/issues) with:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- System information
- Logs if applicable

### 💡 Suggest Features
Have an idea? [Open a feature request](https://github.com/Thomas-Heisig/chat_system/issues) with:
- Use case description
- Proposed solution
- Alternative approaches
- Potential impact

### 📝 Improve Documentation
- Fix typos or unclear explanations
- Add examples and tutorials
- Translate documentation
- Update outdated content

### 🔧 Submit Code
- Fix bugs
- Implement new features
- Improve performance
- Refactor code
- Add tests

### ⭐ Other Ways
- Star the repository
- Share the project
- Help answer questions
- Review pull requests

## Code Quality Standards

### Code Style
- **Python**: Follow PEP 8
- **Line Length**: 100 characters
- **Formatter**: Black
- **Import Sorting**: isort (profile: black)
- **Linter**: flake8
- **Type Checking**: mypy

### Running Quality Checks
```bash
# Format code
black --line-length 100 .
isort --profile black .

# Check code quality
flake8 .
mypy .

# Run tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Testing Requirements

### Test Coverage
- New features: Minimum 80% coverage
- Bug fixes: Include regression test
- Refactoring: Maintain or improve coverage

### Test Types
- **Unit Tests**: Test individual components
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows

### Writing Tests
```python
import pytest
from services.message_service import MessageService

def test_create_message():
    """Test message creation"""
    service = MessageService()
    message = service.create_message(
        username="testuser",
        content="Test message"
    )
    assert message.username == "testuser"
    assert message.message == "Test message"
```

## Documentation Requirements

### For New Features
- Add user-facing documentation
- Add API documentation
- Add code examples
- Update relevant README files

### For Bug Fixes
- Update troubleshooting guide if applicable
- Add notes to CHANGES.md
- Update affected documentation

### Documentation Standards
- Use Markdown format
- Include code examples
- Add screenshots for UI changes
- Keep language clear and concise
- Follow existing structure

## Pull Request Process

### Before Submitting
1. ✅ Code follows style guidelines
2. ✅ All tests pass
3. ✅ New tests added for new features
4. ✅ Documentation updated
5. ✅ No merge conflicts
6. ✅ Commits are clear and descriptive

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests pass
```

### Review Process
1. Automated checks must pass
2. Code review by maintainer(s)
3. Address feedback
4. Approval and merge

## Communication

### GitHub Discussions
Use for:
- Questions about usage
- Feature discussions
- General community topics

### GitHub Issues
Use for:
- Bug reports
- Feature requests
- Documentation issues

### Pull Requests
Use for:
- Code contributions
- Documentation changes

## Recognition

Contributors are recognized in:
- README.md acknowledgments
- CONTRIBUTORS.md file
- Release notes
- Git history

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Quick Links

- **Developer Guide**: [Development Documentation](../03-developer-guide/README.md)
- **Architecture**: [Architecture Documentation](../05-architecture/README.md)
- **Testing Guide**: [Testing Documentation](../03-developer-guide/testing-guide.md)

---

**Version:** 2.0.0  
**Last Updated:** 2025-12-06  
**Maintainer:** Thomas Heisig

Thank you for contributing to the Universal Chat System! 🙏
