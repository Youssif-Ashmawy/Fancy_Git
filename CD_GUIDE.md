# Unified CI/CD Pipeline Guide

This guide explains how to use the unified CI/CD pipeline for FancyGit that combines testing and deployment into a single workflow.

## Overview

The unified CI/CD pipeline (`ci-cd.yml`) provides:
- **Automated testing**: Runs tests on multiple Python versions and OS
- **Patch releases**: Automatic version bumps and releases when pushing to `developer`
- **Tag releases**: Manual releases when pushing tags
- **Manual releases**: On-demand releases with version bumping
- **Email notifications**: Status updates for all operations

## Pipeline Flow

### 1. Test Phase (Always Runs)
- Runs on `ubuntu-latest`, `windows-latest`, `macos-latest`
- Tests Python 3.11
- Unit and integration tests
- Coverage reporting to Codecov

### 2. Deployment Phase (Runs Only if Tests Pass)
- **Patch releases**: Automatic on `developer` branch push
- **Tag releases**: Manual on tag push
- **Manual releases**: On-demand with version selection

## Pipeline Triggers

### 1. Automatic Patch Releases
- **Trigger**: Push to `developer` branch
- **Flow**: Tests → If successful → Version bump → Release
- **Action**: 
  - Bumps patch version (e.g., 1.0.0 → 1.0.1)
  - Creates git tag
  - Builds package
  - Creates GitHub Release
  - Commits version bump (only after successful release)

### 2. Tag-based Releases
- **Trigger**: Push tag starting with `v` (e.g., `v1.2.3`)
- **Flow**: Tests → If successful → Release from tag
- **Action**:
  - Builds package from tag
  - Creates GitHub Release
  - Publishes to PyPI (if configured) -- Maybe Later

### 3. Manual Releases
- **Trigger**: Manual workflow dispatch
- **Flow**: Tests → If successful → Version bump → Release
- **Action**:
  - Bumps version (patch/minor/major)
  - Creates git tag
  - Triggers release workflow

## Setup Required

### 1. GitHub Secrets
Add these secrets to your repository:

```bash
# For PyPI publishing (optional) -- Maybe Later
PYPI_API_TOKEN=your_pypi_token

```

### 2. VERSION File
The pipeline uses a `VERSION` file to track the current version:
- Created automatically if missing
- Format: `1.0.0`
- Updated automatically by releases

## Usage Examples

### Automatic Patch Release
```bash
# Make changes to developer branch
git checkout developer
git add .
git commit -m "fix: important bug fix"
git push origin developer
# → Automatically creates v1.0.1 release
```

### Manual Minor Release
1. Go to GitHub Actions → Workflows → "Continuous Deployment"
2. Click "Run workflow"
3. Select release type: `minor`
4. Click "Run workflow"
5. → Creates v1.1.0 release

### Manual Major Release
```bash
# Same as minor but select "major" in workflow
# → Creates v2.0.0 release
```

### Tag-based Release
```bash
# Create and push a tag
git tag -a v1.5.0 -m "Release version 1.5.0"
git push origin v1.5.0
# → Triggers release workflow
```

## Pipeline Jobs

### Build Job
- Runs tests (reuses CI logic)
- Builds package with `python -m build`
- Uploads coverage to Codecov

### Patch Job
- Runs only on developer branch pushes
- Bumps patch version automatically
- Creates commit and tag
- Creates GitHub Release
- Publishes to PyPI

### Release Job
- Runs on tags or manual dispatch
- Builds package from specific version
- Creates GitHub Release
- Publishes to PyPI

### Manual-Bump Job
- Runs only on manual workflow dispatch
- Bumps version based on input (patch/minor/major)
- Creates commit and tag
- Triggers release workflow

### Notify Job
- Runs after any deployment job
- Sends email notifications
- Reports success/failure status

## Version Management

### Version Format
- Semantic versioning: `MAJOR.MINOR.PATCH`
- Example: `1.2.3`

### Bump Rules
- **Patch**: `1.0.0` → `1.0.1` (bug fixes)
- **Minor**: `1.0.0` → `1.1.0` (new features)
- **Major**: `1.0.0` → `2.0.0` (breaking changes)

### VERSION File
- Contains current version
- Updated automatically by pipeline
- Format: plain text file with version number

## GitHub Release Features

### Automatic Release Notes
Each release includes:
- Installation instructions
- Quick start guide
- Version-specific information

### Release Assets
- Built Python package (`dist/*`)
- Source distribution
- Wheel distribution

### Release Types
- **Patch**: "Automated patch release from main branch"
- **Tag/Manual**: Full release with changelog

## PyPI Publishing (Optional)

### Setup
1. Create PyPI account
2. Generate API token
3. Add `PYPI_API_TOKEN` to GitHub secrets

### Publishing
- Automatic for all releases
- Uses `twine upload`
- Publishes to PyPI as `fancygit`

## Monitoring and Notifications

### Email Notifications
- Success: `deployed_success`
- Failure: `deployed_failure`
- Sent to commit author

### GitHub Actions Status
- Monitor workflow runs in GitHub
- Check job logs for debugging
- View release artifacts

## Troubleshooting

### Common Issues

#### Version Conflicts
```bash
# Check current version
cat VERSION

# Manually fix if needed
echo "1.0.0" > VERSION
git add VERSION && git commit -m "fix version"
```

#### Build Failures
- Check `requirements.txt` for missing dependencies
- Verify `setup.py` configuration
- Review test failures in build job

#### PyPI Publishing Issues
- Verify `PYPI_API_TOKEN` is correct
- Check package name availability
- Review PyPI upload logs

### Debug Steps

1. **Check workflow logs** in GitHub Actions
2. **Verify VERSION file** contents
3. **Test build locally**:
   ```bash
   python -m pip install build twine
   python -m build
   twine check dist/*
   ```
4. **Check git tags**:
   ```bash
   git tag -l
   git ls-remote --tags origin
   ```

## Best Practices

### Branch Management
- `developer`: Development code with automatic patch releases
- `main`: Production-ready code (stable)
- Feature branches: New features

### Release Planning
1. Test thoroughly on `developer`
2. Push to `developer` for automatic patch releases
3. Merge to `main` for stable production releases
4. Use manual releases for significant updates
5. Tag releases for specific versions

### Version Strategy
- Use patch releases for bug fixes
- Use minor releases for new features
- Use major releases for breaking changes
- Keep CHANGELOG for major/minor releases

## Integration with CI

The CD pipeline integrates with your existing CI:
- Reuses test logic from `test.yml`
- Runs after successful tests
- Maintains code quality standards
- Provides consistent deployment process

## Security Considerations

- **Tokens**: Store API tokens in GitHub secrets
- **Permissions**: Limit workflow permissions
- **Access**: Control who can trigger releases
- **Audit**: Monitor workflow runs and releases
