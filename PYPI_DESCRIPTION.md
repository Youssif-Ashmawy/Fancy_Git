# FancyGit

**An intelligent Git wrapper that makes version control approachable for beginners — without getting in the way of experienced developers.**

FancyGit sits on top of Git and adds smart features that guide you through everyday workflows, help you learn, and speed up your work.

---

## Key Features

### Shortcut Commands
Common multi-step Git operations condensed into single commands. Less typing, fewer mistakes.

```
fancygit ship       # pull + stage + commit + push in one step
fancygit sync       # fetch all branches and prune deleted remote branches
fancygit undo       # safely undo your last commit (soft, mixed, or hard)
fancygit redo       # restore a commit that was undone
fancygit explain    # explain what any Git command does
```

### AI Integration
FancyGit connects to local AI models via Ollama to help you:
- **Auto-generate commit messages** from your staged diff
- **Analyse your repo** and surface useful insights

No API key needed — runs entirely on your machine. To unlock the full AI experience, install the following Ollama models:

```bash
ollama pull codellama
ollama pull llama3.2
```

### Git Quizzes
Built-in interactive quizzes to help beginners learn Git concepts while they work.
- 320+ questions covering Git fundamentals to advanced topics
- Tracks which questions you've seen so you always get fresh ones
- Runs in your browser, no setup required

```
fancygit quiz
```

### Repo Visualizer
Generates an interactive visual diagram of your repository's branch history and file dependency graph, opened directly in your browser.

```
fancygit visualize
```

---

## Installation

```bash
pip install fancygit
```

Requires Python 3.6+ and Git installed on your system.

## Quick Start

```bash
fancygit --help        # see all available commands
fancygit quiz          # start a Git quiz
fancygit ship          # pull, stage everything, commit with AI message, and push
```
