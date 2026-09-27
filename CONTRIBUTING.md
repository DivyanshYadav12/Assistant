# Contributing to Aether

Thank you for your interest in contributing to Aether! This document provides guidelines and instructions for contributing to the project.

## 🤝 How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**: What happened and what you expected
- **Steps to reproduce**: Minimal steps to reproduce the issue
- **Environment**: OS version, Python version, Ollama version
- **Logs**: Relevant error messages or logs
- **Screenshots**: If applicable, screenshots showing the issue

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:

- Use a clear and descriptive title
- Provide a detailed description of the proposed enhancement
- Explain why this enhancement would be useful
- Provide examples of how the enhancement would be used

### Pull Requests

#### Development Workflow

1. **Fork the repository** and create your branch from `main`
```bash
git checkout -b feature/your-feature-name
```

2. **Set up your development environment**
```bash
cd assistant/planner
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

3. **Make your changes** following the code style guidelines

4. **Test your changes**
```bash
# Run tests (when test suite is available)
pytest

# Run linting
ruff check src/
ruff format src/

# Run type checking
mypy src/
```

5. **Commit your changes** with clear, descriptive messages
```bash
git commit -m "feat: add new skill for browser automation"
```

6. **Push to your fork** and create a pull request

#### Code Style Guidelines

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Keep functions focused and single-purpose
- Add docstrings to all public functions and classes
- Write descriptive variable and function names
- Limit line length to 100 characters (configured in ruff)

#### Commit Message Convention

Use conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Maintenance tasks

Examples:
```
feat(hotkey): add configurable hotkey support
fix(wake): improve wake word detection accuracy
docs(readme): update installation instructions
```

## 🏗️ Project Structure

```
hive/
├── assistant/
│   ├── planner/
│   │   ├── src/assistant/
│   │   │   ├── core/          # Core systems (planner, gate, TTS, STT)
│   │   │   ├── skills/        # Skill implementations
│   │   │   ├── learning/      # Learning engine
│   │   │   └── memory/        # Memory system
│   │   ├── data/              # Runtime data (gitignored)
│   │   ├── pyproject.toml     # Python dependencies
│   │   └── .venv/             # Virtual environment (gitignored)
│   └── docs/                  # Documentation
├── src/
│   └── hive/                  # Multi-agent email/calendar system
├── README.md
├── LICENSE
├── CONTRIBUTING.md
└── .gitignore
```

## 🧪 Adding New Skills

Skills are the primary way to extend Aether's capabilities. To add a new skill:

1. **Create a new skill file** in `assistant/planner/src/assistant/skills/`
```python
from assistant.skills.base import Skill, SkillResult

class MySkill(Skill):
    """Description of what this skill does."""

    def match(self, text: str) -> bool:
        """Return True if this skill should handle the command."""
        # Check if the command matches this skill
        return "my keyword" in text.lower()

    def execute(self, text: str) -> SkillResult:
        """Execute the skill and return the result."""
        try:
            # Your skill logic here
            result = "Success message"
            return SkillResult(success=True, message=result)
        except Exception as e:
            return SkillResult(success=False, message=f"Error: {str(e)}")
```

2. **Register the skill** in the planner (see `assistant/planner/src/assistant/core/planner.py`)

3. **Add documentation** to `assistant/docs/COMMANDS.md`

4. **Add tests** (when test suite is available)

5. **Submit a pull request**

## 📝 Documentation Contributions

Documentation improvements are highly valued! You can:

- Fix typos or clarify existing documentation
- Add examples to existing features
- Document new features you've added
- Translate documentation to other languages
- Create tutorials or guides

## 🐛 Bug Fix Priorities

- **Critical**: Security vulnerabilities, data loss, crashes
- **High**: Core functionality broken
- **Medium**: Edge cases, minor functionality issues
- **Low**: UI/UX improvements, nice-to-haves

## 🎯 Areas Needing Help

We're particularly looking for contributions in:

- **Additional Skills**:
  - Browser automation (Selenium/Playwright integration)
  - Smart home integration (Home Assistant, Philips Hue)
  - Task management (Todoist, Notion, Linear)
  - Knowledge base integration (Obsidian, Confluence)

- **Cross-Platform Support**:
  - macOS wake word detection
  - Linux audio handling
  - Platform-specific window management

- **UI/UX**:
  - Tauri desktop app with tray icon
  - Web dashboard for configuration
  - Visual feedback for voice input

- **Testing**:
  - Integration tests for skills
  - End-to-end testing
  - Performance benchmarks

- **Documentation**:
  - Video tutorials
  - API documentation
  - Architecture diagrams

## 📜 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone.

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, trolling, or insulting/derogatory comments
- Personal or political attacks
- Public or private harassment
- Publishing others' private information without permission
- Unwelcome sexual attention

### Enforcement

Project maintainers have the right and responsibility to remove, edit, or reject comments, commits, code, wiki edits, issues, and other contributions that are not aligned with this Code of Conduct.

## 🔒 Security

If you discover a security vulnerability, please do not open a public issue. Instead:

1. Email the maintainer privately (if contact info is available)
2. Provide details of the vulnerability
3. Wait for a fix to be released before disclosing publicly

## 📧 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check existing docs first

## 🙏 Recognition

Contributors will be recognized in:
- The CONTRIBUTORS.md file
- Release notes for their contributions
- The project's README for significant contributions

Thank you for contributing to Aether! 🎉
