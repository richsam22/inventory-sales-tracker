#!/bin/bash

APP_NAME="Inventory Tracker"

# === Read version from version.txt ===
VERSION=$(cat version.txt)
echo "📦 Current version: v$VERSION"

# === Auto bump patch number ===
IFS='.' read -r MAJOR MINOR PATCH <<< "$VERSION"
PATCH=$((PATCH + 1))
NEW_VERSION="$MAJOR.$MINOR.$PATCH"

# Write new version back to file
echo $NEW_VERSION > version.txt
echo "🚀 New version: v$NEW_VERSION"

# === Clean old builds ===
echo "🧹 Cleaning old builds..."
rm -rf dist build "${APP_NAME}.spec"

# === Build with new version in name ===
echo "⚙️ Building $APP_NAME v$NEW_VERSION..."
pyinstaller --noconfirm --windowed \
    --name "${APP_NAME}_v${NEW_VERSION}" \
    --icon=icon.icns \
    --add-data "config/firebase.json:config" \
    --add-data "config/serviceAccountKey.json:config" \
    --add-data "db/inventory_empty.db:db" \
    --add-data "assets:assets" \
    main.py

echo "✅ Build finished: dist/${APP_NAME}_v${NEW_VERSION}/"


# run  ./build.sh

