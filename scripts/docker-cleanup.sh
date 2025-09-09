#!/bin/bash

# Docker cleanup script to free disk space

set -e

echo "🧹 Docker Cleanup Script"
echo "========================"
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

echo "📊 Docker disk usage before cleanup:"
docker system df
echo ""

echo "🗑️  Cleaning up Docker resources..."
echo ""

# Remove stopped containers
echo "🔸 Removing stopped containers..."
docker container prune -f

# Remove unused networks
echo "🔸 Removing unused networks..."
docker network prune -f

# Remove unused volumes
echo "🔸 Removing unused volumes..."
docker volume prune -f

# Remove unused images
echo "🔸 Removing unused images..."
docker image prune -f

# Remove build cache
echo "🔸 Removing build cache..."
docker builder prune -f

# For more aggressive cleanup, uncomment the following:
# echo "🔸 Removing ALL unused data (including unused images)..."
# docker system prune -a -f

echo ""
echo "📊 Docker disk usage after cleanup:"
docker system df
echo ""

echo "✅ Docker cleanup completed!"
echo ""
echo "💡 If you still have space issues, you can run:"
echo "   docker system prune -a -f  # WARNING: Removes all unused images"
echo "   docker volume prune -a -f  # WARNING: Removes all unused volumes"
