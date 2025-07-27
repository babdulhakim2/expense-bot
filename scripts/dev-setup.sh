#!/bin/bash

# =============================================================================
# Expense Bot Development Setup Script
# =============================================================================
# This script sets up a complete development environment for new developers

set -e  # Exit on any error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Utility functions
echo_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        echo_success "$1 is installed"
        return 0
    else
        echo_error "$1 is not installed"
        return 1
    fi
}

# Header
echo "🚀 Expense Bot Development Setup"
echo "================================="
echo ""

# Step 1: Check required tools
echo_info "Step 1: Checking required tools..."
missing_tools=()

if ! check_command "node"; then
    missing_tools+=("Node.js")
    echo_warning "Install Node.js from: https://nodejs.org/"
fi

if ! check_command "bun"; then
    missing_tools+=("Bun")
    echo_warning "Install Bun with: curl -fsSL https://bun.sh/install | bash"
fi

if ! check_command "python"; then
    missing_tools+=("Python")
    echo_warning "Install Python from: https://python.org/"
fi

if ! check_command "firebase"; then
    missing_tools+=("Firebase CLI")
    echo_warning "Install Firebase CLI with: npm install -g firebase-tools"
fi

if ! check_command "git"; then
    missing_tools+=("Git")
    echo_warning "Install Git from: https://git-scm.com/"
fi

if [ ${#missing_tools[@]} -ne 0 ]; then
    echo_error "Missing required tools: ${missing_tools[*]}"
    echo_warning "Please install the missing tools and run this script again"
    exit 1
fi

echo_success "All required tools are installed!"
echo ""

# Step 2: Environment setup
echo_info "Step 2: Setting up environment configuration..."
if [ ! -f ".env" ]; then
    echo_warning "No .env file found, creating from template..."
    ./scripts/setup-env.sh
else
    echo_success "Environment file exists"
    echo_info "Updating environment files..."
    ./scripts/setup-env.sh
fi
echo ""

# Step 3: Install dependencies
echo_info "Step 3: Installing dependencies..."
echo_info "Installing frontend dependencies..."
cd frontend && bun install
echo_success "Frontend dependencies installed"

echo_info "Installing backend dependencies..."
cd ../backend
if [ ! -d "venv" ]; then
    echo_info "Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else  
    source venv/bin/activate
fi

pip install -r requirements.txt
echo_success "Backend dependencies installed"

cd ..
echo ""

# Step 4: Firebase setup
echo_info "Step 4: Setting up Firebase..."
if ! firebase projects:list >/dev/null 2>&1; then
    echo_warning "Not logged into Firebase CLI"
    echo_info "Please run: firebase login"
else
    echo_success "Firebase CLI is authenticated"
fi

# Initialize Firebase project if needed
if [ ! -f ".firebaserc" ]; then
    echo_warning "No Firebase project configured"
    echo_info "Please run: firebase use --add"
    echo_info "And select your project ID: expense-bot-9906c"
else
    echo_success "Firebase project is configured"
fi
echo ""

# Step 5: Create development scripts
echo_info "Step 5: Creating development shortcuts..."

# Create a development runner script
cat > start-dev.sh << 'EOF'
#!/bin/bash
# Quick development startup script
echo "🚀 Starting Expense Bot development environment..."
echo "Press Ctrl+C to stop all services"

trap 'echo "🛑 Stopping all services..."; kill 0' SIGINT

# Start services in background
echo "🔥 Starting Firebase emulators..."
firebase emulators:start &

sleep 5

echo "🐍 Starting backend..."
cd backend && source venv/bin/activate && python app.py &

sleep 3

echo "⚛️ Starting frontend..."
cd ../frontend && bun run dev &

# Wait for all background processes
wait
EOF

chmod +x start-dev.sh
echo_success "Created start-dev.sh script"

# Create a health check script
cat > scripts/health-check.sh << 'EOF'
#!/bin/bash
# Health check script for development environment

echo "🏥 Running health check..."

# Check if services are running
check_service() {
    local service=$1
    local port=$2
    local name=$3
    
    if curl -s "http://localhost:$port" >/dev/null 2>&1; then
        echo "✅ $name is running on port $port"
    else
        echo "❌ $name is not running on port $port"
    fi
}

check_service "frontend" 3000 "Frontend (Next.js)"
check_service "backend" 9004 "Backend (Flask)"
check_service "emulator-firestore" 8080 "Firebase Firestore Emulator"
check_service "emulator-auth" 9099 "Firebase Auth Emulator"
check_service "emulator-ui" 4000 "Firebase Emulator UI"

echo ""
echo "🔗 Development URLs:"
echo "   Frontend:        http://localhost:3000"
echo "   Backend API:     http://localhost:9004"
echo "   Firebase UI:     http://localhost:4000"
echo "   Firestore:       http://localhost:8080"
echo "   Auth Emulator:   http://localhost:9099"
EOF

chmod +x scripts/health-check.sh
echo_success "Created health check script"
echo ""

# Step 6: Browser compatibility setup
echo_info "Step 6: Setting up browser compatibility..."
echo_info "Creating browser-specific instructions..."

cat > BROWSER_COMPATIBILITY.md << 'EOF'
# Browser Compatibility for Development

## Chrome Issues and Solutions

Chrome has stricter security policies that can cause issues with Firebase emulators:

### Common Issues:
1. **CORS errors** - Fixed with Next.js headers configuration
2. **Mixed content warnings** - Use localhost instead of 127.0.0.1
3. **Service worker issues** - Clear cache and hard refresh

### Solutions:
1. **Use incognito mode** for clean testing
2. **Clear cache** regularly: DevTools → Application → Storage → Clear
3. **Use Firefox or Safari** as alternatives
4. **Enable Chrome flags** (not recommended for production):
   - `chrome://flags/#disable-web-security`
   - `chrome://flags/#allow-running-insecure-content`

## Recommended Development Browsers:
1. **Safari** - Best compatibility with Firebase emulators
2. **Firefox** - Good compatibility, excellent dev tools
3. **Chrome** - Use with caution, may need frequent cache clearing

## If Firebase Emulator Doesn't Connect:
1. Check if emulators are running: `make health-check`
2. Restart emulators: `make emulators-stop && make emulators`
3. Clear browser cache and refresh
4. Try a different browser
5. Check console for specific error messages
EOF

echo_success "Created browser compatibility guide"
echo ""

# Step 7: Final checks and instructions
echo_info "Step 7: Final setup verification..."

# Check if we can run the health check
if ./scripts/health-check.sh >/dev/null 2>&1; then
    echo_success "Health check script is working"
else
    echo_warning "Health check script created but services not running yet"
fi

echo ""
echo_success "🎉 Development setup complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Review and edit .env with your actual API keys"
echo "2. Start development: make dev"
echo "3. Or use quick start: ./start-dev.sh"
echo "4. Check service health: make health-check"
echo "5. Read BROWSER_COMPATIBILITY.md for browser-specific tips"
echo ""
echo "🔗 Useful Commands:"
echo "   make help              - Show all available commands"
echo "   make dev               - Start all services"
echo "   make emulators         - Start only Firebase emulators"
echo "   make frontend          - Start only frontend"
echo "   make backend           - Start only backend"
echo "   make clean             - Clean build artifacts"
echo ""
echo "📖 Documentation:"
echo "   BROWSER_COMPATIBILITY.md - Browser-specific development tips"
echo "   .env.example             - Environment variable reference"
echo "   Makefile                 - All available commands"
echo ""

if [ ${#missing_tools[@]} -eq 0 ]; then
    echo_success "Setup completed successfully! 🚀"
else
    echo_warning "Setup completed with warnings. Please address missing tools."
fi