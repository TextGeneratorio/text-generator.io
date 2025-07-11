#!/bin/bash

# Test script to verify subscription enforcement

echo "Testing subscription enforcement implementation..."

# Test 1: Subscription Status API
echo "1. Testing subscription status API..."
STATUS=$(curl -s http://localhost:8080/api/subscription-status | jq -r '.is_subscribed')
if [ "$STATUS" = "false" ]; then
    echo "✓ Subscription status API working correctly (not subscribed)"
else
    echo "✗ Subscription status API issue"
fi

# Test 2: Check if pages load correctly
echo "2. Testing page loads..."

# AI Text Editor
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ai-text-editor)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ AI Text Editor page loads correctly"
else
    echo "✗ AI Text Editor page failed to load (HTTP $HTTP_CODE)"
fi

# Playground
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/playground)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ Playground page loads correctly"
else
    echo "✗ Playground page failed to load (HTTP $HTTP_CODE)"
fi

# Prompt Optimizer
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/tools/prompt-optimizer)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ Prompt Optimizer page loads correctly"
else
    echo "✗ Prompt Optimizer page failed to load (HTTP $HTTP_CODE)"
fi

# UX SEO Review
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/tools/ux-seo-review)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ UX SEO Review page loads correctly"
else
    echo "✗ UX SEO Review page failed to load (HTTP $HTTP_CODE)"
fi

# Test 3: Check if required static files exist
echo "3. Testing static files..."

# Check if subscription modal CSS exists
if [ -f "/home/lee/code/20-questions/static/css/subscription-modal.css" ]; then
    echo "✓ Subscription modal CSS exists"
else
    echo "✗ Subscription modal CSS missing"
fi

# Check if subscription modal JS exists
if [ -f "/home/lee/code/20-questions/static/js/subscription-modal.js" ]; then
    echo "✓ Subscription modal JS exists"
else
    echo "✗ Subscription modal JS missing"
fi

# Test 4: Check if utility functions exist
echo "4. Testing utility files..."

if [ -f "/home/lee/code/20-questions/questions/subscription_utils.py" ]; then
    echo "✓ Subscription utils exists"
else
    echo "✗ Subscription utils missing"
fi

echo "Test complete!"
