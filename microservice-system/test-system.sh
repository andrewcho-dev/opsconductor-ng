#!/bin/bash

echo "🧪 Testing Microservice System"
echo "==============================="

BASE_URL="https://localhost"

echo ""
echo "1. Testing HTTPS redirect..."
HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost)
if [ "$HTTP_RESPONSE" = "301" ]; then
    echo "✅ HTTP to HTTPS redirect working"
else
    echo "❌ HTTP to HTTPS redirect failed (got $HTTP_RESPONSE)"
fi

echo ""
echo "2. Testing SSL certificate..."
SSL_TEST=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost)
if [ "$SSL_TEST" = "200" ]; then
    echo "✅ SSL certificate working (self-signed)"
else
    echo "❌ SSL certificate failed (got $SSL_TEST)"
fi

echo ""
echo "3. Testing frontend service..."
FRONTEND_TEST=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost/)
if [ "$FRONTEND_TEST" = "200" ]; then
    echo "✅ Frontend service responding"
else
    echo "❌ Frontend service failed (got $FRONTEND_TEST)"
fi

echo ""
echo "4. Testing user registration..."
REGISTER_RESPONSE=$(curl -k -s -X POST https://localhost/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","firstname":"Test","lastname":"User","password":"testpass123"}' \
  -w "%{http_code}")

if [[ "$REGISTER_RESPONSE" == *"201"* ]]; then
    echo "✅ User registration working"
elif [[ "$REGISTER_RESPONSE" == *"409"* ]]; then
    echo "✅ User registration working (user already exists)"
else
    echo "❌ User registration failed"
    echo "Response: $REGISTER_RESPONSE"
fi

echo ""
echo "5. Testing user login..."
LOGIN_RESPONSE=$(curl -k -s -X POST https://localhost/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}')

if [[ "$LOGIN_RESPONSE" == *"token"* ]]; then
    echo "✅ User login working"
    
    # Extract token for further testing
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    
    echo ""
    echo "6. Testing token verification..."
    VERIFY_RESPONSE=$(curl -k -s -X POST https://localhost/api/verify \
      -H "Authorization: Bearer $TOKEN" \
      -w "%{http_code}")
    
    if [[ "$VERIFY_RESPONSE" == *"200"* ]]; then
        echo "✅ Token verification working"
    else
        echo "❌ Token verification failed"
    fi
else
    echo "❌ User login failed"
    echo "Response: $LOGIN_RESPONSE"
fi

echo ""
echo "7. Testing service health endpoints..."

# Test direct service access through nginx
AUTH_HEALTH=$(curl -k -s https://localhost/auth/health)
if [[ "$AUTH_HEALTH" == *"auth-service"* ]]; then
    echo "✅ Auth service health check working"
else
    echo "❌ Auth service health check failed"
fi

USER_HEALTH=$(curl -k -s https://localhost/users/health)
if [[ "$USER_HEALTH" == *"user-service"* ]]; then
    echo "✅ User service health check working"
else
    echo "❌ User service health check failed"
fi

echo ""
echo "🎉 System test completed!"
echo ""
echo "🌐 Access your application at: https://localhost"
echo "   (Accept the self-signed certificate warning)"
echo ""
echo "📝 Test credentials:"
echo "   Username: testuser"
echo "   Password: testpass123"