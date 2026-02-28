#!/bin/bash
# Development environment bootstrap script
# Sets up dependencies and configuration for local epg-enricharr development

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo "=== epg-enricharr Development Setup ==="
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install Python 3.8+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Found Python $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "Setting up Python virtual environment..."
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    python3 -m venv "$PROJECT_ROOT/venv"
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source "$PROJECT_ROOT/venv/bin/activate"

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install --quiet --upgrade pip setuptools wheel

# Core dependencies for plugin development
pip install --quiet \
    django>=4.0 \
    requests>=2.28.0 \
    pytest>=7.0 \
    pytest-cov>=4.0 \
    lxml>=4.9.0 \
    xmlschema>=2.0

echo "✅ Dependencies installed"

# Create directories
echo ""
echo "Creating project directories..."
mkdir -p tests/fixtures
mkdir -p scripts
mkdir -p docs
mkdir -p build
echo "✅ Directories created"

# Create .env file if it doesn't exist
echo ""
echo "Setting up environment configuration..."
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env" 2>/dev/null || \
    cat > "$PROJECT_ROOT/.env" <<EOF
# Local Development Configuration
DISPATCHARR_HOST=http://localhost:8000
DISPATCHARR_DB_PATH=./data/db.sqlite3
EPG_TEST_DATA_PATH=./tests/fixtures/sample-epg.xml
DEBUG=True
LOG_LEVEL=DEBUG
EOF
    echo "✅ .env file created (customize as needed)"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Activate environment: source venv/bin/activate"
echo "  2. Generate plugin: make test-zip"
echo "  3. Run validation: make validate"
echo "  4. (Optional) Set up Dispatcharr: make setup-dispatcharr"
echo ""
