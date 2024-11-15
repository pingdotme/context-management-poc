#!/bin/bash
# test_coherence.sh

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Base URL
API_URL="http://localhost:8000"
USER_ID="$1"

if [ -z "$USER_ID" ]; then
    echo -e "${RED}Please provide a user_id as argument${NC}"
    exit 1
fi

echo -e "${BLUE}Testing system coherence for user: ${USER_ID}${NC}\n"

# Function to test and display results
test_endpoint() {
    local endpoint="$1"
    local description="$2"
    local method="$3"
    local data="$4"
    
    echo -e "${YELLOW}Testing: ${description}${NC}"
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -X GET "${API_URL}${endpoint}")
    else
        response=$(curl -s -X POST "${API_URL}${endpoint}" \
             -H "Content-Type: application/json" \
             -d "${data}")
    fi
    
    echo -e "${GREEN}Response: ${response}${NC}\n"
    sleep 1
}

# Test 1: Get all meetings
echo -e "${BLUE}Test 1: Retrieving all meetings${NC}"
test_endpoint "/meetings/${USER_ID}/history" "Get all meetings" "GET"

# Test 2: Get security-related meetings
echo -e "${BLUE}Test 2: Retrieving security meetings${NC}"
test_endpoint "/meetings/${USER_ID}/history?categories=security" "Get security meetings" "GET"

# Test 3: Get API-related meetings
echo -e "${BLUE}Test 3: Retrieving API meetings${NC}"
test_endpoint "/meetings/${USER_ID}/history?categories=api" "Get API meetings" "GET"

# Test 4: Test semantic search
echo -e "${BLUE}Test 4: Testing semantic search${NC}"
test_endpoint "/process-meeting" "Semantic search test" "POST" \
    "{
        \"user_id\": \"${USER_ID}\",
        \"meeting_text\": \"Need to review API security measures\",
        \"categories\": [\"api\", \"security\"]
    }"

# Test 5: Check for duplicates
echo -e "${BLUE}Test 5: Testing duplicate detection${NC}"
test_endpoint "/process-meeting" "Duplicate detection test" "POST" \
    "{
        \"user_id\": \"${USER_ID}\",
        \"meeting_text\": \"API security review meeting. Discussing rate limiting and access controls.\",
        \"categories\": [\"api\", \"security\"]
    }"

# Test 6: Export meetings
echo -e "${BLUE}Test 6: Testing export functionality${NC}"
test_endpoint "/meetings/${USER_ID}/export" "Export meetings" "GET"

# Test 7: Cleanup duplicates
echo -e "${BLUE}Test 7: Testing duplicate cleanup${NC}"
test_endpoint "/meetings/${USER_ID}/cleanup" "Cleanup duplicates" "POST"

echo -e "${GREEN}Coherence testing complete!${NC}"