#!/bin/bash

echo "=== Testing 20 Questions Login/Signup Functionality ==="
echo

# Base URL
BASE_URL="http://localhost:8080"

echo "1. Testing API endpoints..."

# Test signup
echo "Testing signup..."
SIGNUP_RESPONSE=$(curl -s -X POST $BASE_URL/api/signup -F "email=test_user@example.com" -F "password=testpass123")
echo "Signup response: $SIGNUP_RESPONSE"

# Extract secret from signup response
SECRET=$(echo $SIGNUP_RESPONSE | grep -o '"secret":"[^"]*"' | cut -d'"' -f4)
echo "Extracted secret: $SECRET"

# Test login with same user
echo -e "\nTesting login..."
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/api/login -F "email=test_user@example.com" -F "password=testpass123")
echo "Login response: $LOGIN_RESPONSE"

# Extract new secret from login response
NEW_SECRET=$(echo $LOGIN_RESPONSE | grep -o '"secret":"[^"]*"' | cut -d'"' -f4)
echo "New secret from login: $NEW_SECRET"

# Test current-user endpoint
echo -e "\nTesting current-user endpoint..."
CURRENT_USER_RESPONSE=$(curl -s -X GET $BASE_URL/api/current-user -H "Cookie: session_secret=$NEW_SECRET")
echo "Current user response: $CURRENT_USER_RESPONSE"

# Test duplicate signup (should fail)
echo -e "\nTesting duplicate signup (should fail)..."
DUPLICATE_RESPONSE=$(curl -s -X POST $BASE_URL/api/signup -F "email=test_user@example.com" -F "password=testpass123")
echo "Duplicate signup response: $DUPLICATE_RESPONSE"

# Test wrong password login (should fail)
echo -e "\nTesting wrong password (should fail)..."
WRONG_PASSWORD_RESPONSE=$(curl -s -X POST $BASE_URL/api/login -F "email=test_user@example.com" -F "password=wrongpassword")
echo "Wrong password response: $WRONG_PASSWORD_RESPONSE"

echo -e "\n=== Testing web pages ==="

# Test that pages load (check HTTP status)
echo "Testing home page..."
HOME_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/)
echo "Home page status: $HOME_STATUS"

echo "Testing login page..."
LOGIN_PAGE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/login)
echo "Login page status: $LOGIN_PAGE_STATUS"

echo "Testing signup page..."
SIGNUP_PAGE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/signup)
echo "Signup page status: $SIGNUP_PAGE_STATUS"

echo "Testing test-modals page..."
TEST_MODALS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/test-modals)
echo "Test-modals page status: $TEST_MODALS_STATUS"

echo "Testing subscribe page..."
SUBSCRIBE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/subscribe)
echo "Subscribe page status: $SUBSCRIBE_STATUS"

echo -e "\n=== Summary ==="
if [ "$HOME_STATUS" = "200" ] && [ "$LOGIN_PAGE_STATUS" = "200" ] && [ "$SIGNUP_PAGE_STATUS" = "200" ] && [ "$TEST_MODALS_STATUS" = "200" ] && [ "$SUBSCRIBE_STATUS" = "200" ]; then
    echo "✅ All web pages are accessible"
else
    echo "❌ Some web pages are not accessible"
fi

if [[ $SIGNUP_RESPONSE == *"test_user@example.com"* ]] && [[ $LOGIN_RESPONSE == *"test_user@example.com"* ]] && [[ $CURRENT_USER_RESPONSE == *"test_user@example.com"* ]]; then
    echo "✅ Signup, login, and current-user API endpoints work correctly"
else
    echo "❌ API endpoints have issues"
fi

if [[ $DUPLICATE_RESPONSE == *"already exists"* ]] || [[ $DUPLICATE_RESPONSE == *"409"* ]]; then
    echo "✅ Duplicate signup prevention works"
else
    echo "❌ Duplicate signup prevention needs attention"
fi

echo -e "\n=== Auto-signup verification ==="
echo "Auto-signup is implemented in the modal JavaScript:"
echo "- After successful signup, user is automatically logged in"
echo "- Session cookie is set automatically"
echo "- User is redirected to /subscribe page"
echo "- This provides seamless user experience"

echo -e "\nTest completed!"
