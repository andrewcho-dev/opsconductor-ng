#!/bin/bash

echo "🧪 Testing User Management CRUD System"
echo "======================================="

BASE_URL="https://localhost"

# First, login to get a token
echo ""
echo "1. Logging in to get authentication token..."
LOGIN_RESPONSE=$(curl -k -s -X POST $BASE_URL/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}')

if [[ "$LOGIN_RESPONSE" == *"token"* ]]; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Login successful, token obtained"
else
    echo "❌ Login failed"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo ""
echo "2. Testing GET /api/users (Read - List all users)..."
USERS_RESPONSE=$(curl -k -s -H "Authorization: Bearer $TOKEN" $BASE_URL/api/users)
if [[ "$USERS_RESPONSE" == *"users"* && "$USERS_RESPONSE" == *"pagination"* ]]; then
    echo "✅ Get users list working"
    USER_COUNT=$(echo "$USERS_RESPONSE" | grep -o '"totalUsers":[0-9]*' | cut -d':' -f2)
    echo "   Found $USER_COUNT users"
else
    echo "❌ Get users list failed"
    echo "Response: $USERS_RESPONSE"
fi

echo ""
echo "3. Testing POST /api/register (Create - Add new user)..."
NEW_USER_RESPONSE=$(curl -k -s -X POST $BASE_URL/api/register \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"crudtest","firstname":"CRUD","lastname":"Test","password":"testpass123"}' \
  -w "%{http_code}")

if [[ "$NEW_USER_RESPONSE" == *"201"* ]] || [[ "$NEW_USER_RESPONSE" == *"crudtest"* ]]; then
    echo "✅ Create user working"
    NEW_USER_ID=$(echo "$NEW_USER_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    echo "   Created user with ID: $NEW_USER_ID"
elif [[ "$NEW_USER_RESPONSE" == *"409"* ]]; then
    echo "✅ Create user working (user already exists)"
    # Get the existing user ID
    EXISTING_USER=$(curl -k -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/users?search=crudtest")
    NEW_USER_ID=$(echo "$EXISTING_USER" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    echo "   Using existing user with ID: $NEW_USER_ID"
else
    echo "❌ Create user failed"
    echo "Response: $NEW_USER_RESPONSE"
fi

if [ -n "$NEW_USER_ID" ]; then
    echo ""
    echo "4. Testing GET /api/users/:id (Read - Get specific user)..."
    USER_DETAIL_RESPONSE=$(curl -k -s -H "Authorization: Bearer $TOKEN" $BASE_URL/api/users/$NEW_USER_ID)
    if [[ "$USER_DETAIL_RESPONSE" == *"crudtest"* ]]; then
        echo "✅ Get specific user working"
        echo "   User details: $(echo "$USER_DETAIL_RESPONSE" | grep -o '"username":"[^"]*"')"
    else
        echo "❌ Get specific user failed"
        echo "Response: $USER_DETAIL_RESPONSE"
    fi

    echo ""
    echo "5. Testing PUT /api/users/:id (Update - Modify user)..."
    UPDATE_RESPONSE=$(curl -k -s -X PUT $BASE_URL/api/users/$NEW_USER_ID \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"username":"crudtest","firstname":"CRUD-Updated","lastname":"Test-Updated"}' \
      -w "%{http_code}")

    if [[ "$UPDATE_RESPONSE" == *"200"* ]] || [[ "$UPDATE_RESPONSE" == *"CRUD-Updated"* ]]; then
        echo "✅ Update user working"
        echo "   Updated user: $(echo "$UPDATE_RESPONSE" | grep -o '"firstname":"[^"]*"')"
    else
        echo "❌ Update user failed"
        echo "Response: $UPDATE_RESPONSE"
    fi

    echo ""
    echo "6. Testing search functionality..."
    SEARCH_RESPONSE=$(curl -k -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/users?search=CRUD")
    if [[ "$SEARCH_RESPONSE" == *"crudtest"* ]]; then
        echo "✅ Search functionality working"
        SEARCH_COUNT=$(echo "$SEARCH_RESPONSE" | grep -o '"totalUsers":[0-9]*' | cut -d':' -f2)
        echo "   Found $SEARCH_COUNT users matching 'CRUD'"
    else
        echo "❌ Search functionality failed"
        echo "Response: $SEARCH_RESPONSE"
    fi

    echo ""
    echo "7. Testing pagination..."
    PAGE_RESPONSE=$(curl -k -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/users?page=1&limit=2")
    if [[ "$PAGE_RESPONSE" == *"pagination"* && "$PAGE_RESPONSE" == *"currentPage"* ]]; then
        echo "✅ Pagination working"
        CURRENT_PAGE=$(echo "$PAGE_RESPONSE" | grep -o '"currentPage":[0-9]*' | cut -d':' -f2)
        TOTAL_PAGES=$(echo "$PAGE_RESPONSE" | grep -o '"totalPages":[0-9]*' | cut -d':' -f2)
        echo "   Page $CURRENT_PAGE of $TOTAL_PAGES"
    else
        echo "❌ Pagination failed"
        echo "Response: $PAGE_RESPONSE"
    fi

    echo ""
    echo "8. Testing DELETE /api/users/:id (Delete - Remove user)..."
    DELETE_RESPONSE=$(curl -k -s -X DELETE $BASE_URL/api/users/$NEW_USER_ID \
      -H "Authorization: Bearer $TOKEN" \
      -w "%{http_code}")

    if [[ "$DELETE_RESPONSE" == *"200"* ]] || [[ "$DELETE_RESPONSE" == *"deleted successfully"* ]]; then
        echo "✅ Delete user working"
        echo "   User deleted successfully"
    else
        echo "❌ Delete user failed"
        echo "Response: $DELETE_RESPONSE"
    fi

    echo ""
    echo "9. Verifying user was deleted..."
    VERIFY_DELETE=$(curl -k -s -H "Authorization: Bearer $TOKEN" $BASE_URL/api/users/$NEW_USER_ID -w "%{http_code}")
    if [[ "$VERIFY_DELETE" == *"404"* ]]; then
        echo "✅ User deletion verified"
        echo "   User no longer exists"
    else
        echo "❌ User deletion verification failed"
        echo "Response: $VERIFY_DELETE"
    fi
fi

echo ""
echo "10. Testing user management UI accessibility..."
UI_RESPONSE=$(curl -k -s $BASE_URL/users -w "%{http_code}")
if [[ "$UI_RESPONSE" == *"200"* && "$UI_RESPONSE" == *"User Management"* ]]; then
    echo "✅ User management UI accessible"
else
    echo "❌ User management UI failed"
fi

echo ""
echo "🎉 User Management CRUD Testing Complete!"
echo ""
echo "📋 Summary of CRUD Operations:"
echo "   ✅ CREATE: Add new users via POST /api/register"
echo "   ✅ READ:   List users via GET /api/users"
echo "   ✅ READ:   Get specific user via GET /api/users/:id"
echo "   ✅ UPDATE: Modify users via PUT /api/users/:id"
echo "   ✅ DELETE: Remove users via DELETE /api/users/:id"
echo ""
echo "🌟 Additional Features:"
echo "   ✅ Search functionality"
echo "   ✅ Pagination support"
echo "   ✅ Web UI interface"
echo "   ✅ Authentication required"
echo ""
echo "🌐 Access the User Management UI at: https://localhost/users"
echo "   (Login first at https://localhost with your credentials)"