# Fancy Git

![FancyGit Overview](images/overview.png)

A smart CLI tool that provides intelligent recommendations and helps solve merge conflicts by analyzing git command outputs.

## Overview

FancyGit is a CLI wrapper around git commands that:
- Runs git commands and captures their output
- Detects warnings and errors in real-time
- Provides user confirmation for clean operations
- Prepares for AI-powered recommendations (future phase)

## Current Implementation (Phase 1)

### ✅ Features Implemented
- **CLI Interface**: `fancygit` command works system-wide
- **Git Commands**: Full support for `add`, `commit`, `push`, and `pull` with argument passing
- **Warning/Error Detection**: Regex-based pattern matching for common git issues
- **User Confirmation**: Prompts for confirmation when no issues detected
- **Cross-platform**: Works on macOS, Linux, and Windows

### 🔍 Detection Patterns

**Error Patterns:**
- `error:`, `fatal:`, `failed`, `rejected`
- `conflict`, `merge conflict`, `unable to`

**Warning Patterns:**
- `warning:`, `WARNING:`, `behind`, `ahead`, `diverged`

## Installation

### Quick Setup

Run the automated cross-platform launcher script:
```bash
python3 launcher.py
```

This script will:
- Automatically detect your operating system (Linux, macOS, or Windows)
- Run the appropriate installation script for your system
- Check Python 3.6+ and Git installation
- Make fancygit.py executable
- Create system-wide symlink (Unix-like systems) or add to PATH (Windows)
- Test the installation

## Usage

### Basic Commands
```bash
# Add files
fancygit add .
fancygit add filename.txt

# Commit changes
fancygit commit -m "Your commit message"
fancygit commit --amend

# Push to remote
fancygit push origin main

# Pull from remote  
fancygit pull origin main

# With additional arguments
fancygit push origin main --force-with-lease
fancygit pull origin main --rebase
```

### How It Works

1. **Command Execution**: Runs the actual git command
2. **Output Analysis**: Scans stdout/stderr for warning/error patterns
3. **User Feedback**: 
   - If issues detected: Shows detailed error/warning messages
   - If no issues: Prompts for confirmation with "enter 'y' to run the command"
4. **Action**: Executes or cancels based on user input

### Example Output

**No Issues:**
```
Running: git push origin main
✅ No warnings or errors detected
No warning messages - enter 'y' to run the command: y
Command executed successfully!
```

**Issues Detected:**
```
Running: git pull origin main
❌ Errors detected:
    error: couldn't find remote ref refs/heads/main
```

## Architecture

```
FancyGit CLI → Git Commands → Collect Output → Pattern Matching → User Interface (CLI)
```

## Future Roadmap

### Phase 2: AI Pipeline
- Implement AI model for parsing warnings/errors
- Generate intelligent recommendations
- Add confidence scoring (backend only)

### Phase 3: Smart Resolution
- Automatic conflict resolution suggestions
- Context-aware recommendations
- Integration with popular Git workflows

## File Structure

```
Fancy_Git/
├── fancygit.py          # Main CLI application
├── launcher.py          # Cross-platform launcher script
├── README.md            # This file
├── images/              # Images and documentation
│   └── overview.png     # Project overview image
└── .git/                # Git repository
```

*Note: Platform-specific installation scripts (`start.sh`, `start.bat`) are included but automatically managed by `launcher.py`.*

## Requirements

- Python 3.6+
- Git installed and configured
- System permissions for symlink creation
- Note: No external dependecies for now so no environment setup required 

## License

MIT License (For now as it is still a private project)
