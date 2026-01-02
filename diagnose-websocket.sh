#!/bin/bash
# WebSocket Diagnostics Script
# Usage: ./diagnose-websocket.sh

echo "🔍 WebSocket Connection Diagnostics"
echo "===================================="
echo ""

# 1. Check if backend is running
echo "1️⃣  Checking backend service..."
if docker-compose ps | grep -q "werewolf-backend.*Up"; then
    echo "✅ Backend service is running"
else
    echo "❌ Backend service is NOT running"
    echo "   Run: docker-compose up -d backend"
    exit 1
fi

# 2. Check backend health
echo ""
echo "2️⃣  Checking backend health endpoint..."
if curl -f -s http://localhost:8082/health > /dev/null; then
    echo "✅ Backend health check passed"
else
    echo "❌ Backend health check failed"
    echo "   Check logs: docker-compose logs backend"
fi

# 3. Check for errors in backend logs
echo ""
echo "3️⃣  Checking for WebSocket errors in logs..."
WS_ERRORS=$(docker-compose logs --tail=100 backend 2>&1 | grep -i "websocket\|ws.*error\|verify_player_token" || echo "")
if [ -z "$WS_ERRORS" ]; then
    echo "✅ No WebSocket errors found in recent logs"
else
    echo "⚠️  Found WebSocket related logs:"
    echo "$WS_ERRORS"
fi

# 4. Check JWT configuration
echo ""
echo "4️⃣  Checking JWT configuration..."
if docker-compose exec -T backend python -c "from app.core.config import settings; print('✅ JWT_SECRET_KEY:', 'SET' if settings.JWT_SECRET_KEY else 'MISSING')" 2>/dev/null; then
    :
else
    echo "❌ Cannot check JWT configuration"
fi

# 5. Test auth module import
echo ""
echo "5️⃣  Testing auth module..."
if docker-compose exec -T backend python -c "from app.core.auth import verify_player_token; print('✅ verify_player_token is available')" 2>/dev/null; then
    :
else
    echo "❌ verify_player_token function not found"
    echo "   Backend may need rebuild: docker-compose build backend"
fi

# 6. Show recent backend logs
echo ""
echo "6️⃣  Recent backend logs (last 20 lines):"
echo "========================================"
docker-compose logs --tail=20 backend

echo ""
echo "💡 Tips:"
echo "   - If JWT errors: Check .env file has JWT_SECRET_KEY"
echo "   - If import errors: Run 'docker-compose build --no-cache backend'"
echo "   - If connection errors: Check nginx.conf has WebSocket upgrade config"
echo "   - View live logs: docker-compose logs -f backend"
