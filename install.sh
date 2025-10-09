#!/bin/bash

# Installation script for the Harvest Experiment Analysis Library

echo "🚀 Installing Harvest Experiment Analysis Library..."

# Check if we're in the right directory
if [ ! -f "setup.py" ]; then
    echo "❌ Error: setup.py not found. Please run this script from the library root directory."
    exit 1
fi

# Install the library in development mode
echo "📦 Installing library in development mode..."
pip install -e .

# Install additional requirements
echo "📋 Installing additional requirements..."
pip install -r requirements.txt

echo "✅ Installation complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Copy hex_notebook_template.py to a new Hex notebook"
echo "2. Modify the experiment parameters at the top"
echo "3. Run the analysis!"
echo ""
echo "📚 See README.md for detailed usage instructions."
