#!/bin/bash

# Test build script for CrystalGenius MVP

set -e

echo "🧪 Testing Docker builds..."
echo "=========================="
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker is not running"
    exit 1
fi

echo "✅ Docker is ready"
echo ""

# Test backend build
echo "🔨 Testing backend build..."
cd backend
if docker build -t crystalgenius-backend-test .; then
    echo "✅ Backend build successful"
    # Clean up test image
    docker rmi crystalgenius-backend-test
else
    echo "❌ Backend build failed"
    exit 1
fi
cd ..

echo ""

# Test frontend build
echo "🔨 Testing frontend build..."
cd frontend
if docker build -t crystalgenius-frontend-test .; then
    echo "✅ Frontend build successful"
    # Clean up test image
    docker rmi crystalgenius-frontend-test
else
    echo "❌ Frontend build failed"
    exit 1
fi
cd ..

echo ""
echo "🎉 All builds successful!"
echo ""
echo "You can now run:"
echo "  make up    # Start all services"
echo "  make logs  # View service logs"
