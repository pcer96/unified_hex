#!/bin/bash

# GitHub Repository Setup Script

echo "🚀 Setting up GitHub repository for Harvest Experiment Analysis Library..."

# Check if we're in the right directory
if [ ! -f "setup.py" ]; then
    echo "❌ Error: setup.py not found. Please run this script from the library root directory."
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git branch -M main
fi

# Add all files
echo "📁 Adding files to git..."
git add .

# Initial commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: Centralized experiment analysis library

- Core analysis engine with ExperimentAnalyzer
- Configuration system with ExperimentConfig  
- All standard metrics (C2S, C2P, ARPU, ARPS, Retention, AutoRenewOff)
- Hex secrets integration
- Team collaboration workflow
- Comprehensive documentation and examples"

echo "✅ Local git repository ready!"
echo ""
echo "🎯 Next steps:"
echo "1. Create a new repository on GitHub:"
echo "   - Go to https://github.com/new"
echo "   - Name: unified_hex_harvest"
echo "   - Description: Centralized experiment analysis library for Hex notebooks"
echo "   - Make it private (recommended)"
echo ""
echo "2. Connect your local repository:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/unified_hex_harvest.git"
echo "   git push -u origin main"
echo ""
echo "3. Set up team access:"
echo "   - Go to repository Settings → Manage access"
echo "   - Invite your team members"
echo ""
echo "4. Configure Hex integration:"
echo "   - Add secrets to your Hex project"
echo "   - Use: ! pip install git+https://github.com/YOUR_USERNAME/unified_hex_harvest.git"
echo ""
echo "📚 See TEAM_WORKFLOW.md for detailed team collaboration instructions."
