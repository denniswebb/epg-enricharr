#!/bin/bash
set -e

# Deploy plugin to remote Dispatcharr instance
# Requires .env with DISPATCHARR_HOST and DISPATCHARR_AUTH_TOKEN

echo "🚀 Deploying epg-enricharr plugin..."

# Load environment variables
if [ ! -f .env ]; then
    echo "❌ .env file not found. Create one from .env.example"
    exit 1
fi

# Source .env but only extract the variables we need
DISPATCHARR_HOST=$(grep "^DISPATCHARR_HOST=" .env | cut -d'=' -f2)
DISPATCHARR_AUTH_TOKEN=$(grep "^DISPATCHARR_AUTH_TOKEN=" .env | cut -d'=' -f2)

if [ -z "$DISPATCHARR_HOST" ]; then
    echo "❌ DISPATCHARR_HOST not set in .env"
    exit 1
fi

if [ -z "$DISPATCHARR_AUTH_TOKEN" ]; then
    echo "❌ DISPATCHARR_AUTH_TOKEN not set in .env"
    exit 1
fi

# Find latest ZIP file
ZIP_FILE=$(ls -t epg-enricharr-*.zip 2>/dev/null | head -1)
if [ -z "$ZIP_FILE" ]; then
    echo "❌ No plugin ZIP found. Run 'mise run test-zip' first"
    exit 1
fi

echo "📦 Found plugin: $ZIP_FILE"
echo "🌐 Target: $DISPATCHARR_HOST"

# Upload plugin
echo "⬆️  Uploading plugin..."
IMPORT_RESPONSE=$(curl -s --insecure \
    -X POST \
    -H "Authorization: Bearer $DISPATCHARR_AUTH_TOKEN" \
    -F "file=@$ZIP_FILE" \
    "$DISPATCHARR_HOST/api/plugins/plugins/import/")

if echo "$IMPORT_RESPONSE" | grep -q "error\|Error"; then
    echo "❌ Upload failed: $IMPORT_RESPONSE"
    exit 1
fi

echo "✅ Plugin uploaded"

# Trigger refresh
echo "🔄 Triggering plugin refresh..."
REFRESH_RESPONSE=$(curl -s --insecure \
    -X GET \
    -H "Authorization: Bearer $DISPATCHARR_AUTH_TOKEN" \
    "$DISPATCHARR_HOST/api/plugins/plugins/")

if echo "$REFRESH_RESPONSE" | grep -q "error\|Error"; then
    echo "⚠️  Refresh returned: $REFRESH_RESPONSE"
    exit 1
fi

echo "✅ Plugin refresh triggered"
echo ""
echo "🎉 Deployment complete!"
echo "   Plugin: $ZIP_FILE"
echo "   Target: $DISPATCHARR_HOST/api/plugins/plugins/"
