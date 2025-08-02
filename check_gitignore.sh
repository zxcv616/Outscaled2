#!/bin/bash

# Check Gitignore Configuration
echo "🔍 CHECKING GITIGNORE CONFIGURATION"
echo "======================================"

# Check if .gitignore exists
if [ ! -f ".gitignore" ]; then
    echo "❌ No .gitignore file found in root directory"
    exit 1
fi

echo "✅ Root .gitignore found"

# Check backend .gitignore
if [ -f "backend/.gitignore" ]; then
    echo "✅ Backend .gitignore found"
else
    echo "⚠️  No backend/.gitignore found"
fi

# Check frontend .gitignore
if [ -f "frontend/.gitignore" ]; then
    echo "✅ Frontend .gitignore found"
else
    echo "⚠️  No frontend/.gitignore found"
fi

echo ""
echo "📊 CHECKING LARGE FILES THAT WOULD BE IGNORED"
echo "=============================================="

# Check for large CSV files
echo "🔍 Looking for CSV files..."
find . -name "*.csv" -type f 2>/dev/null | while read file; do
    size=$(du -h "$file" | cut -f1)
    echo "  📄 $file ($size)"
done

# Check for large image files
echo ""
echo "🔍 Looking for large image files..."
find . -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.gif" 2>/dev/null | while read file; do
    size=$(du -h "$file" | cut -f1)
    echo "  🖼️  $file ($size)"
done

# Check for Python cache files
echo ""
echo "🔍 Looking for Python cache files..."
find . -name "__pycache__" -type d 2>/dev/null | while read dir; do
    echo "  📁 $dir"
done

# Check for node_modules
echo ""
echo "🔍 Looking for node_modules..."
find . -name "node_modules" -type d 2>/dev/null | while read dir; do
    echo "  📁 $dir"
done

# Check for environment files
echo ""
echo "🔍 Looking for environment files..."
find . -name ".env*" -type f 2>/dev/null | while read file; do
    echo "  🔐 $file"
done

# Check for log files
echo ""
echo "🔍 Looking for log files..."
find . -name "*.log" -type f 2>/dev/null | while read file; do
    size=$(du -h "$file" | cut -f1)
    echo "  📝 $file ($size)"
done

echo ""
echo "🎯 GIT STATUS CHECK"
echo "=================="

# Check what would be ignored
echo "Files that would be ignored by Git:"
git status --ignored --porcelain 2>/dev/null | grep "^!!" | cut -c4- | head -20

echo ""
echo "📋 SUMMARY"
echo "=========="
echo "✅ Large datasets (*.csv) will be ignored"
echo "✅ Build artifacts (node_modules, __pycache__) will be ignored"
echo "✅ Environment files (.env*) will be ignored"
echo "✅ Log files (*.log) will be ignored"
echo "✅ IDE files (.vscode, .idea) will be ignored"
echo "✅ OS files (.DS_Store, Thumbs.db) will be ignored"

echo ""
echo "💡 TIPS"
echo "======="
echo "• To check what files are currently tracked: git ls-files"
echo "• To see what would be ignored: git status --ignored"
echo "• To force add a large file: git add -f path/to/file"
echo "• To remove a file from tracking: git rm --cached path/to/file" 