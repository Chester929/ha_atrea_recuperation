#!/usr/bin/env bash
# Bump or set version, sync to custom_components/ha_atrea_recuperation/manifest.json,
# generate/update docs/changelog.md from git commits since last tag, run pre-release checks,
# commit, create tag and optionally push.
#
# Usage:
#   ./scripts/bump_version.sh patch
#   ./scripts/bump_version.sh minor
#   ./scripts/bump_version.sh major
#   ./scripts/bump_version.sh 1.2.3
# Options:
#   --no-push    : do not push commits/tags (local only)
#   --strict     : treat missing optional tools (flake8/black/pytest/mkdocs) as failures
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION_FILE="$REPO_ROOT/VERSION"
MANIFEST="$REPO_ROOT/custom_components/ha_atrea_recuperation/manifest.json"
CHANGELOG="$REPO_ROOT/docs/changelog.md"
PRECHECK_SCRIPT="$REPO_ROOT/scripts/pre_release_checks.sh"

if [ ! -f "$MANIFEST" ]; then
  echo "Error: manifest.json not found at $MANIFEST"
  exit 1
fi

if [ $# -lt 1 ]; then
  echo "Usage: $0 <major|minor|patch|X.Y.Z> [--no-push] [--strict]"
  exit 1
fi

CMD="$1"
shift || true

PUSH="yes"
STRICT_FLAG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --no-push) PUSH="no"; shift ;;
    --strict) STRICT_FLAG="--strict"; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# read current version
if [ -f "$VERSION_FILE" ]; then
  CUR_VER="$(tr -d ' \t\n\r' < "$VERSION_FILE")"
else
  CUR_VER="$(python3 - <<PY
import json
m=json.load(open("$MANIFEST"))
print(m.get("version","0.0.0"))
PY
)"
fi

if ! echo "$CUR_VER" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "Current version '$CUR_VER' does not look like semver. Please fix VERSION or manifest.json."
  exit 1
fi

# compute new version
if [ "$CMD" = "major" ] || [ "$CMD" = "minor" ] || [ "$CMD" = "patch" ]; then
  IFS='.' read -r MAJ MIN PAT <<< "$CUR_VER"
  case "$CMD" in
    major) MAJ=$((MAJ + 1)); MIN=0; PAT=0;;
    minor) MIN=$((MIN + 1)); PAT=0;;
    patch) PAT=$((PAT + 1));;
  esac
  NEW_VER="${MAJ}.${MIN}.${PAT}"
else
  if ! echo "$CMD" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    echo "Invalid version: $CMD"
    exit 1
  fi
  NEW_VER="$CMD"
fi

echo "Version: $CUR_VER -> $NEW_VER"

# generate changelog excerpt from git
set +e
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
set -e

if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
else
  RANGE="HEAD"
fi

mapfile -t LOG_LINES < <(git log --pretty=format:'%h%x09%an%x09%s%x09%b' --no-merges $RANGE || true)

COMMIT_LIST=""
if [ ${#LOG_LINES[@]} -eq 0 ]; then
  COMMIT_LIST="- No user-facing changes (internal or none)."
else
  for line in "${LOG_LINES[@]}"; do
    IFS=$'\t' read -r c_hash c_author c_subject c_body <<< "$line"
    prnum=""
    if echo "$c_subject" | grep -qE '\(#([0-9]+)\)'; then
      prnum="$(echo "$c_subject" | sed -nE 's/.*\(#([0-9]+)\).*/\1/p')"
    elif echo "$c_subject" | grep -qE '#[0-9]+'; then
      prnum="$(echo "$c_subject" | grep -oE '#[0-9]+' | head -n1 | tr -d '#')"
    elif echo "$c_body" | grep -qE '#[0-9]+'; then
      prnum="$(echo "$c_body" | grep -oE '#[0-9]+' | head -n1 | tr -d '#')"
    fi

    pr_display=""
    author_display="$c_author"
    if [ -n "$prnum" ]; then
      pr_display=" (#${prnum})"
    else
      pr_display=" (${c_hash})"
    fi

    subj_single="$(echo "$c_subject" | tr '\n' ' ' | sed -E 's/[[:space:]]+/ /g' | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"
    COMMIT_LIST="${COMMIT_LIST}- ${subj_single}${pr_display} — ${author_display}\n"
  done
fi

DATE="$(date -u +%Y-%m-%d)"
NEW_HEADER="## v${NEW_VER} — ${DATE}"
NEW_SECTION="${NEW_HEADER}\n\n${COMMIT_LIST}\n"

mkdir -p "$(dirname "$CHANGELOG")"

if [ -f "$CHANGELOG" ]; then
  if grep -qF "$NEW_HEADER" "$CHANGELOG"; then
    echo "Changelog already contains header '$NEW_HEADER' — skipping prepend."
  else
    TMP="$(mktemp)"
    {
      echo -e "$NEW_SECTION"
      echo ""
      cat "$CHANGELOG"
    } > "$TMP"
    mv "$TMP" "$CHANGELOG"
    echo "Prepended new changelog section to $CHANGELOG"
  fi
else
  cat > "$CHANGELOG" <<EOF
# Changelog

$NEW_SECTION
EOF
  echo "Created $CHANGELOG with new section"
fi

# update VERSION file
echo "$NEW_VER" > "$VERSION_FILE"
echo "Updated $VERSION_FILE"

# update manifest.json version field
python3 - <<PY
import json,sys
mf = "$MANIFEST"
with open(mf, "r", encoding="utf-8") as f:
    j = json.load(f)
j['version'] = "$NEW_VER"
with open(mf, "w", encoding="utf-8") as f:
    json.dump(j, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("Updated", mf)
PY

# Stage files for pre-release checks
git add "$VERSION_FILE" "$MANIFEST" "$CHANGELOG" || true

# Run pre-release checks
if [ ! -x "$PRECHECK_SCRIPT" ]; then
  echo "Pre-check script not found or not executable at $PRECHECK_SCRIPT"
  exit 1
fi

echo "Running pre-release checks..."
if ! "$PRECHECK_SCRIPT" "$NEW_VER" $STRICT_FLAG; then
  echo "Pre-release checks failed. Fix issues and retry. (Files are staged.)"
  exit 1
fi
echo "Pre-release checks passed."

# git commit
COMMIT_MESSAGE="Bump version to v${NEW_VER} and update changelog"
if git diff --cached --quiet; then
  echo "No staged changes to commit."
else
  git commit -m "$COMMIT_MESSAGE"
  echo "Committed: $COMMIT_MESSAGE"
fi

# create tag
TAG="v${NEW_VER}"
if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Tag $TAG already exists locally. Skipping tag creation."
else
  git tag -a "$TAG" -m "Release $TAG"
  echo "Created tag $TAG"
fi

# push if requested
if [ "$PUSH" = "yes" ]; then
  if git remote | grep -q origin; then
    echo "Pushing commits and tags to origin..."
    git push origin --follow-tags
    echo "Pushed."
  else
    echo "No 'origin' remote configured. Set remote and push manually:"
    echo "  git remote add origin git@github.com:Chester929/ha_atrea_recuperation.git"
    echo "  git push -u origin main --follow-tags"
  fi
else
  echo "PUSH disabled (--no-push). Local commit and tag created but not pushed."
fi

echo "Done: version is $NEW_VER (tag: $TAG)."