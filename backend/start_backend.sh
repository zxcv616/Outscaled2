#!/bin/bash

# Start Backend for Testing
echo "🚀 Starting Backend for Testing..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    echo "   On macOS: open -a Docker"
    echo "   On Windows: Start Docker Desktop"
    exit 1
fi

# Check if containers are already running
if docker ps | grep -q "outscaled2-backend"; then
    echo "✅ Backend is already running!"
    echo "   You can now run tests with:"
    echo "   python run_confidence_tests.py quick"
else
    echo "📦 Starting Docker containers..."
    cd ..
    docker-compose up -d
    
    echo "⏳ Waiting for backend to start..."
    sleep 10
    
    # Check if backend is responding
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ Backend is ready!"
        echo "   You can now run tests with:"
        echo "   cd backend && python run_confidence_tests.py quick"
    else
        echo "⚠️  Backend may still be starting. Please wait a moment and try again."
        echo "   Check logs with: docker logs outscaled2-backend-1"
    fi
fi

echo ""
echo "📚 Testing Guide:"
echo "   - Quick test: python run_confidence_tests.py quick"
echo "   - Full test: python run_confidence_tests.py"
echo "   - View logs: docker logs outscaled2-backend-1"
echo "   - Stop backend: docker-compose down" 