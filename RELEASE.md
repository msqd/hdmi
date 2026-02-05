# Release Process

This document describes how to create a new release of hdmi.

## Overview

The release workflow is fully automated via GitHub Actions. When you push a version tag, the system builds, tests, and publishes the package automatically.

## Prerequisites

- Push access to the GitHub repository
- All changes merged to `main` branch
- All CI tests passing
- PyPI trusted publishing configured (see [Troubleshooting](#troubleshooting) section)

## Step-by-Step Release Process

### 1. Set Version Number

```bash
export VERSION=0.2.0
```

For pre-releases use: `0.2.0-rc1`, `0.2.0-beta.1`, or `0.2.0-alpha.1`

### 2. Update Version

The version is defined in `src/hdmi/__init__.py`. Use hatch to update it:

```bash
uv run hatch version $VERSION
grep "__version__" src/hdmi/__init__.py
```

The last command verifies the version was updated correctly.

### 3. Commit Version Change

```bash
git add src/hdmi/__init__.py
git commit -m "chore: bump version to $VERSION"
```

### 4. Create Annotated Git Tag

```bash
git tag -a $VERSION -m "Release $VERSION"
```

**Critical:** Use the `-a` flag for annotated tags. Lightweight tags won't trigger the workflow.

### 5. Push Changes and Tag

```bash
git push origin main
git push origin $VERSION
```

### 6. Monitor Workflow

The automated CI/CD process will:
1. Validate `pyproject.toml` version matches git tag
2. Run all tests and linting
3. Build the Python wheel
4. Test wheel installation
5. Publish to TestPyPI (https://test.pypi.org/p/hdmi)
6. Publish to PyPI (https://pypi.org/p/hdmi)
7. Create a GitHub release with artifacts

Watch progress:
```bash
gh run watch
```

Or visit the [GitHub Actions dashboard](../../actions).

### 7. Verify Release

```bash
# Test installation from PyPI (specify Python 3.13)
(cd /tmp && uv run --python 3.13 --with hdmi==$VERSION python -c "import hdmi; print('Success!')")

# Or create a temporary virtual environment for interactive testing
(TEST_DIR=$(mktemp -d) && \
  uv venv --python 3.13 "$TEST_DIR" && \
  uv pip install --python "$TEST_DIR" hdmi==$VERSION && \
  "$TEST_DIR/bin/python" -c "import hdmi; print('Success! Environment ready at: $TEST_DIR')" && \
  cd "$TEST_DIR" && \
  exec "$TEST_DIR/bin/python")

# View on PyPI
open https://pypi.org/project/hdmi/$VERSION/
```

## Version Naming Conventions

Follow [Semantic Versioning](https://semver.org/):

- **Stable:** `X.Y.Z` (e.g., `0.2.0`)
  - **Major**: Breaking changes
  - **Minor**: New features, backwards compatible
  - **Patch**: Bug fixes, backwards compatible

- **Pre-releases:**
  - **Release Candidate:** `X.Y.Z-rcN` (e.g., `0.2.0-rc1`)
  - **Beta:** `X.Y.Z-betaN` (e.g., `0.2.0-beta.1`)
  - **Alpha:** `X.Y.Z-alphaN` (e.g., `0.2.0-alpha.1`)

## Local Testing Before Release

Always test the wheel locally before creating a release:

```bash
# Build and validate wheel
make wheel

# Test the built wheel
uv run --with dist/*.whl python -c "import hdmi; print('Wheel works!')"
```

## Troubleshooting

### Version Mismatch Error

The CI/CD will fail if the tag doesn't match the package version. Delete the tag and fix:

```bash
# Delete local and remote tag
git tag -d $VERSION
git push origin :refs/tags/$VERSION

# Fix version, commit, and recreate tag
uv run hatch version $VERSION
git add src/hdmi/__init__.py
git commit --amend --no-edit
git tag -a $VERSION -m "Release $VERSION"
git push origin main --force-with-lease
git push origin $VERSION
```

### PyPI Publishing Failures

Verify trusted publisher configuration:

**TestPyPI:** https://test.pypi.org/manage/account/publishing/
**PyPI:** https://pypi.org/manage/account/publishing/

Add pending publisher with:
- **PyPI Project Name:** `hdmi`
- **Owner:** Your GitHub username
- **Repository:** `hdmi`
- **Workflow:** `cicd.yml`
- **Environment:** `testpypi` or `pypi`

### Emergency Rollback

**Never delete PyPI releases.** Instead:
- Release a patch version with fixes, or
- Yank the problematic release on PyPI (marks as unavailable without breaking existing installations)

## Best Practices

- Test thoroughly before releasing (`make test`)
- Test the wheel locally (`make wheel`)
- Use release candidates for major versions
- Release frequently with small changes
- Document breaking changes clearly
- Monitor for post-release issues
