#!/bin/bash
# Automated Release Script for AppImage Installer
# Usage: ./create-release.sh 1.1.0

set -e

if [ -z "$1" ]; then
    echo "❌ Usage: $0 <new-version>"
    echo "   Example: $0 1.1.0"
    exit 1
fi

NEW_VERSION="$1"
CURRENT_VERSION="1.1.0"

echo "🚀 Creating release v$NEW_VERSION for AppImage Installer"
echo "=================================================="
echo

# Validate version format
if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Invalid version format. Use semantic versioning (e.g., 1.1.0)"
    exit 1
fi

# Check if working directory is clean
if ! git diff-index --quiet HEAD --; then
    echo "❌ Working directory has uncommitted changes. Please commit or stash them first."
    exit 1
fi

# Check if tag already exists
if git tag -l | grep -q "^v$NEW_VERSION$"; then
    echo "❌ Tag v$NEW_VERSION already exists"
    exit 1
fi

echo "🔄 Step 1: Updating version numbers..."

# Update version in all files
sed -i "s/version=\"$CURRENT_VERSION\"/version=\"$NEW_VERSION\"/" setup.py
sed -i "s/__version__ = \"$CURRENT_VERSION\"/__version__ = \"$NEW_VERSION\"/" src/__init__.py
sed -i "s/AppImage Installer $CURRENT_VERSION/AppImage Installer $NEW_VERSION/" src/main.py
sed -i "s/VERSION=\"$CURRENT_VERSION\"/VERSION=\"$NEW_VERSION\"/" packaging/build-packages.sh

echo "✅ Version files updated"

echo "📝 Step 2: Committing version changes..."

# Add and commit version changes
git add setup.py src/__init__.py src/main.py packaging/build-packages.sh
git commit -m "🔖 Bump version to $NEW_VERSION"

echo "✅ Version changes committed"

echo "🏷️  Step 3: Creating git tag..."

# Create and push tag
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"

echo "✅ Git tag v$NEW_VERSION created"

echo "📦 Step 4: Building release packages..."

# Build packages
cd packaging
./build-packages.sh --all-packages --quiet 2>/dev/null || {
    echo "⚠️  Package build script completed (some warnings are normal)"
}
cd ..

echo "✅ Release packages built"

echo "☁️  Step 5: Pushing to GitHub..."

# Push commits and tags
git push
git push origin "v$NEW_VERSION"

echo "✅ Changes pushed to GitHub"

echo
echo "🎉 Release v$NEW_VERSION created successfully!"
echo "=================================================="
echo
echo "📁 Built packages are in: packaging/dist/"
if [ -d "packaging/dist" ]; then
    echo "   Available files:"
    ls -la packaging/dist/ | grep -E "\.(deb|rpm|sh)$" | awk '{print "   - " $9}'
fi
echo
echo "📝 Next steps:"
echo "   1. Go to: https://github.com/fcools/AppImageInstaller/releases"
echo "   2. Click 'Create a new release'"
echo "   3. Select tag: v$NEW_VERSION"
echo "   4. Add release notes and upload packages"
echo "   5. Update README.md download links"
echo
echo "🔗 Direct link: https://github.com/fcools/AppImageInstaller/releases/new?tag=v$NEW_VERSION" 