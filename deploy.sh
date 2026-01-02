#!/bin/bash
# Werewolf Game Deployment Script
# Usage: ./deploy.sh

set -e  # Exit on error

echo "🚀 Starting deployment..."

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Pull latest code
echo -e "${YELLOW}📥 Pulling latest code from GitHub...${NC}"
git pull origin main

# 2. Stop running containers
echo -e "${YELLOW}🛑 Stopping current containers...${NC}"
docker-compose down

# 3. Rebuild images
echo -e "${YELLOW}🔨 Rebuilding Docker images...${NC}"
docker-compose build --no-cache

# 4. Start services
echo -e "${YELLOW}▶️  Starting services...${NC}"
docker-compose up -d

# 5. Wait for services to be healthy
echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 10

# 6. Check service status
echo -e "${YELLOW}📊 Checking service status...${NC}"
docker-compose ps

# 7. Show backend logs (last 50 lines)
echo -e "${YELLOW}📜 Backend logs (last 50 lines):${NC}"
docker-compose logs --tail=50 backend

# 8. Test WebSocket endpoint
echo -e "${YELLOW}🔍 Testing backend health...${NC}"
curl -f http://localhost:8082/health || echo "⚠️  Health check failed"

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "To view live logs:"
echo "  docker-compose logs -f backend"
echo ""
echo "To restart a service:"
echo "  docker-compose restart backend"
