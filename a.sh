#!/bin/bash
# generate_meetings.sh

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URL
API_URL="http://localhost:8000"
USER_ID="test_user_$(date +%s)"

echo -e "${BLUE}Starting meeting generation for user: ${USER_ID}${NC}"

# Function to call API and handle response
call_api() {
    local text="$1"
    local categories="$2"
    
    echo -e "${BLUE}Adding meeting: ${text}${NC}"
    response=$(curl -s -X POST "${API_URL}/process-meeting" \
         -H "Content-Type: application/json" \
         -d "{
           \"user_id\": \"${USER_ID}\",
           \"meeting_text\": \"${text}\",
           \"categories\": ${categories}
         }")
    echo -e "${GREEN}Response: ${response}${NC}\n"
    sleep 1
}

# API Development Track
call_api "Initial API planning meeting. Discussing RESTful endpoints and basic architecture." \
        "[\"api\", \"planning\"]"

call_api "API authentication design session. Decided to implement OAuth2 with JWT tokens." \
        "[\"api\", \"security\"]"

call_api "Sprint planning for API development phase 1. Timeline and resource allocation discussed." \
        "[\"api\", \"planning\"]"

# Security Track
call_api "Security audit preparation meeting. Review of current security protocols." \
        "[\"security\", \"review\"]"

call_api "Penetration testing results review. Found potential vulnerabilities in auth flow." \
        "[\"security\", \"review\"]"

call_api "Security implementation workshop. Fixing identified vulnerabilities." \
        "[\"security\"]"

# Mixed Context
call_api "API security review meeting. Discussing rate limiting and access controls." \
        "[\"api\", \"security\", \"review\"]"

call_api "Integration planning session. How the new API security measures affect existing systems." \
        "[\"api\", \"planning\", \"security\"]"

call_api "Final review of API security implementation. All critical issues addressed." \
        "[\"api\", \"security\", \"review\"]"

echo -e "${GREEN}Meeting generation complete!${NC}"