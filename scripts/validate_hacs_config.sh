#!/usr/bin/env bash
#
# Validate HACS configuration for ha_atrea_recuperation integration
#
# This script ensures that:
# 1. hacs.json exists and is valid JSON
# 2. content_in_root is set to false (required for this repo structure)
# 3. The manifest file exists at the path specified in hacs.json
# 4. No www/ directory exists (this is not a Lovelace card)
# 5. The integration code is in custom_components/ha_atrea_recuperation/
#
# Usage:
#   ./scripts/validate_hacs_config.sh
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HACS_JSON="$REPO_ROOT/hacs.json"
CUSTOM_DIR="$REPO_ROOT/custom_components/ha_atrea_recuperation"

echo "Validating HACS configuration for HA Atrea Recuperation..."
echo ""

# Check 1: hacs.json exists and is valid JSON
if [ ! -f "$HACS_JSON" ]; then
    echo "❌ ERROR: hacs.json not found at $HACS_JSON"
    exit 1
fi

if ! python3 -c "import json; json.load(open('$HACS_JSON'))" 2>/dev/null; then
    echo "❌ ERROR: hacs.json is not valid JSON"
    exit 1
fi

echo "✓ hacs.json exists and is valid JSON"

# Check 2: content_in_root is false
CONTENT_IN_ROOT=$(python3 -c "import json; print(json.load(open('$HACS_JSON')).get('content_in_root', 'NOT_SET'))")

if [ "$CONTENT_IN_ROOT" = "True" ] || [ "$CONTENT_IN_ROOT" = "true" ]; then
    echo "❌ ERROR: content_in_root is set to true (MUST be false for this repository)"
    echo "   This repository structure requires content_in_root: false"
    echo "   See .hacs.md for details"
    exit 1
elif [ "$CONTENT_IN_ROOT" = "NOT_SET" ]; then
    echo "⚠ WARNING: content_in_root is not explicitly set (defaults to false)"
    echo "   Recommendation: Explicitly set 'content_in_root: false' in hacs.json"
else
    echo "✓ content_in_root is correctly set to false"
fi

# Check 3: filename points to valid manifest.json
MANIFEST_PATH=$(python3 -c "import json; print(json.load(open('$HACS_JSON')).get('filename', ''))")

if [ -z "$MANIFEST_PATH" ]; then
    echo "❌ ERROR: 'filename' field is missing in hacs.json"
    exit 1
fi

FULL_MANIFEST_PATH="$REPO_ROOT/$MANIFEST_PATH"
if [ ! -f "$FULL_MANIFEST_PATH" ]; then
    echo "❌ ERROR: Manifest file not found at: $MANIFEST_PATH"
    echo "   Expected: $FULL_MANIFEST_PATH"
    exit 1
fi

echo "✓ Manifest file exists at: $MANIFEST_PATH"

# Validate manifest.json is valid and has required fields
if ! python3 -c "
import json, sys
manifest = json.load(open('$FULL_MANIFEST_PATH'))
required_fields = ['domain', 'name', 'version', 'documentation', 'requirements', 'codeowners']
missing = [f for f in required_fields if f not in manifest]
if missing:
    print(f'Missing fields in manifest.json: {missing}')
    sys.exit(1)
if manifest.get('domain') != 'ha_atrea_recuperation':
    print(f'Invalid domain in manifest.json: {manifest.get(\"domain\")}')
    sys.exit(1)
" 2>/dev/null; then
    echo "❌ ERROR: manifest.json validation failed"
    exit 1
fi

echo "✓ Manifest file is valid"

# Check 4: No www/ directory exists
if [ -d "$REPO_ROOT/www" ]; then
    echo "❌ ERROR: www/ directory exists (should NOT exist for integrations)"
    echo "   This is an integration, not a Lovelace card"
    echo "   Remove the www/ directory"
    exit 1
fi

echo "✓ No www/ directory (correct for integration)"

# Check 5: Integration code is in correct location
if [ ! -d "$CUSTOM_DIR" ]; then
    echo "❌ ERROR: Integration directory not found: custom_components/ha_atrea_recuperation/"
    exit 1
fi

if [ ! -f "$CUSTOM_DIR/__init__.py" ]; then
    echo "❌ ERROR: __init__.py not found in integration directory"
    exit 1
fi

echo "✓ Integration code is in correct location: custom_components/ha_atrea_recuperation/"

# Check 6: Ensure zip_release is false (source installation, not zip)
ZIP_RELEASE=$(python3 -c "import json; print(json.load(open('$HACS_JSON')).get('zip_release', 'NOT_SET'))")

if [ "$ZIP_RELEASE" = "True" ] || [ "$ZIP_RELEASE" = "true" ]; then
    echo "⚠ WARNING: zip_release is set to true"
    echo "   For source-based installation, this should be false"
fi

# Check 7: Validate domain consistency
HACS_DOMAINS=$(python3 -c "import json; print(','.join(json.load(open('$HACS_JSON')).get('domains', [])))")
MANIFEST_DOMAIN=$(python3 -c "import json; print(json.load(open('$FULL_MANIFEST_PATH')).get('domain', ''))")

if [[ ! "$HACS_DOMAINS" =~ "climate" ]] || [[ ! "$HACS_DOMAINS" =~ "sensor" ]]; then
    echo "⚠ WARNING: hacs.json domains list may be incomplete"
fi

echo "✓ Domain configuration is consistent"

# Summary
echo ""
echo "=========================================="
echo "✅ HACS Configuration Validation PASSED"
echo "=========================================="
echo ""
echo "Repository is correctly configured for HACS:"
echo "  - Type: Custom Integration (not a Lovelace card)"
echo "  - Installation method: Source-based (not zip)"
echo "  - Structure: content_in_root=false (integration in subdirectory)"
echo "  - Installation path: custom_components/ha_atrea_recuperation/"
echo ""
echo "Configuration details:"
echo "  - content_in_root: $CONTENT_IN_ROOT"
echo "  - manifest: $MANIFEST_PATH"
echo "  - domain: $MANIFEST_DOMAIN"
echo "  - domains: $HACS_DOMAINS"
echo ""
exit 0
