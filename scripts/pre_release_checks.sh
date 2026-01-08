#!/usr/bin/env bash
#
# Run validation checks before creating a release.
#
# Usage:
#   scripts/pre_release_checks.sh <version> [--strict]
#
# Checks performed:
# - JSON validity for manifest.json and hacs.json (if present)
# - manifest.json contains expected fields (domain, version)
# - manifest.json.version matches provided <version>
# - Python syntax check (compileall) for custom_components/
# - Run pytest if tests/ exists
# - Run flake8 (if installed) on custom_components/ and scripts/ (optional)
# - Run black --check (if installed) on custom_components/ and scripts/ (optional)
# - Build docs with mkdocs build (if mkdocs installed) to validate docs
# - Ensure git working tree has no unstaged changes (staged changes are allowed)
#
# Notes:
# - If --strict is provided, missing optional tools (flake8/black/pytest/mkdocs)
#   are treated as failures. Otherwise they will be only warned.
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CUSTOM_DIR="$REPO_ROOT/custom_components/ha_atrea_recuperation"
MANIFEST="$CUSTOM_DIR/manifest.json"
HACS_JSON="$REPO_ROOT/hacs.json"
VERSION="$1"
STRICT="no"
if [ "${2-}" = "--strict" ] || [ "${3-}" = "--strict" ]; then
  STRICT="yes"
fi

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

warn() {
  echo "WARNING: $*" >&2
}

info() {
  echo "INFO: $*"
}

# 1) Ensure we are in a git repo and no unstaged changes exist
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  fail "Not inside a git repository (run from repo root)."
fi

# Allow staged changes (we expect VERSION/manifest/changelog to be staged),
# but disallow unstaged modifications.
if [ -n "$(git ls-files --modified)" ]; then
  echo "Unstaged changes detected (these must be staged before release):"
  git ls-files --modified
  fail "Please git add/commit or stash changes before running pre-release checks."
fi

info "Git working tree is clean (no unstaged changes)."

# 2) Validate JSON files
if [ -f "$MANIFEST" ]; then
  info "Validating $MANIFEST JSON..."
  if ! python3 -c "import json,sys; json.load(open('$MANIFEST'))" >/dev/null 2>&1; then
    fail "Invalid JSON in $MANIFEST"
  fi
else
  fail "manifest.json not found at $MANIFEST"
fi

if [ -f "$HACS_JSON" ]; then
  info "Validating $HACS_JSON JSON..."
  if ! python3 -c "import json,sys; json.load(open('$HACS_JSON'))" >/dev/null 2>&1; then
    fail "Invalid JSON in $HACS_JSON"
  fi
else
  warn "hacs.json not found at repo root (optional for HACS)."
fi

# 3) Check manifest contains required fields and version matches
info "Checking manifest.json required fields..."
python3 - <<PY || fail "manifest.json validation failed"
import json,sys
mf = "$MANIFEST"
j = json.load(open(mf))
required = ["domain","name","version"]
for k in required:
    if k not in j:
        print(f"Missing key in manifest.json: {k}", file=sys.stderr)
        sys.exit(2)
if j.get("version") != "$VERSION":
    print(f"manifest.json version ({j.get('version')}) does not match expected version ($VERSION)", file=sys.stderr)
    sys.exit(2)
print("manifest.json OK")
PY

# 4) Python syntax check (compileall)
if [ -d "$CUSTOM_DIR" ]; then
  info "Checking Python syntax in $CUSTOM_DIR (compileall)..."
  python3 -m py_compile $(find "$CUSTOM_DIR" -name '*.py') || fail "Python syntax errors detected in integration files."
else
  fail "Integration directory $CUSTOM_DIR not found."
fi

# 5) Run pytest if tests directory exists
if [ -d "$REPO_ROOT/tests" ]; then
  if command -v pytest >/dev/null 2>&1; then
    info "Running pytest..."
    pytest -q || fail "pytest returned failures."
  else
    if [ "$STRICT" = "yes" ]; then
      fail "pytest not installed but --strict given. Install pytest to run tests."
    else
      warn "pytest not installed; skipping tests. Install pytest to run them."
    fi
  fi
else
  info "No tests/ directory found; skipping pytest."
fi

# 6) Static analysis: flake8 (optional)
if command -v flake8 >/dev/null 2>&1; then
  info "Running flake8 (static linting)..."
  # Only lint the integration and scripts
  flake8 "$CUSTOM_DIR" scripts || fail "flake8 reported issues."
else
  if [ "$STRICT" = "yes" ]; then
    fail "flake8 not installed but --strict given. Install flake8 or remove --strict."
  else
    warn "flake8 not installed; skipping linting. Install flake8 for lint checks."
  fi
fi

# 7) Code style: black --check (optional)
if command -v black >/dev/null 2>&1; then
  info "Running black --check..."
  black --check "$CUSTOM_DIR" scripts || fail "black --check failed (run 'black' to format)."
else
  if [ "$STRICT" = "yes" ]; then
    fail "black not installed but --strict given. Install black or remove --strict."
  else
    warn "black not installed; skipping format check. Install black for style enforcement."
  fi
fi

# 8) Build docs with mkdocs (optional)
if command -v mkdocs >/dev/null 2>&1; then
  info "Building docs with mkdocs to validate documentation..."
  # Build to a temporary dir
  TMPDIR="$(mktemp -d)"
  if mkdocs build -d "$TMPDIR" >/dev/null 2>&1; then
    info "mkdocs build successful."
    rm -rf "$TMPDIR"
  else
    rm -rf "$TMPDIR"
    fail "mkdocs build failed. Fix documentation or mkdocs config."
  fi
else
  if [ "$STRICT" = "yes" ]; then
    fail "mkdocs not installed but --strict given. Install mkdocs or remove --strict."
  else
    warn "mkdocs not installed; skipping docs build. Install mkdocs to validate docs."
  fi
fi

# 9) Ensure changelog contains the version header (basic check)
if [ -f "$REPO_ROOT/docs/changelog.md" ]; then
  if grep -q "## v$VERSION" "$REPO_ROOT/docs/changelog.md"; then
    info "Found changelog section for v$VERSION."
  else
    warn "docs/changelog.md does not yet contain '## v$VERSION' header."
  fi
else
  warn "docs/changelog.md not found (optional)."
fi

info "All pre-release checks passed."
exit 0