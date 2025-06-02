#!/bin/bash

# Gemini API Server - cURL Examples

BASE_URL="http://localhost:50014"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_example() {
    echo -e "${BLUE}$1${NC}"
    echo "----------------------------------------"
}

print_command() {
    echo -e "${YELLOW}Command:${NC}"
    echo "$1"
    echo
}

print_response() {
    echo -e "${GREEN}Response:${NC}"
}

# Example 1: Health Check
print_example "1. Health Check"
cmd="curl -s $BASE_URL/health"
print_command "$cmd"
print_response
eval $cmd | jq '.' 2>/dev/null || eval $cmd
echo -e "\n"

# Example 2: List Models
print_example "2. List Available Models"
cmd="curl -s $BASE_URL/v1/models"
print_command "$cmd"
print_response
eval $cmd | jq '.' 2>/dev/null || eval $cmd
echo -e "\n"

# Example 3: Simple Chat Completion
print_example "3. Simple Chat Completion"
cmd='curl -s -X POST '$BASE_URL'/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '"'"'{
    "model": "gemini-2.5-flash",
    "messages": [
      {"role": "user", "content": "Hello! Please respond with a short greeting."}
    ]
  }'"'"''
print_command "$cmd"
print_response
eval $cmd | jq '.' 2>/dev/null || eval $cmd
echo -e "\n"

# Example 4: Chat with System Prompt
print_example "4. Chat with System Prompt"
cmd='curl -s -X POST '$BASE_URL'/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '"'"'{
    "model": "gemini-2.5-flash",
    "messages": [
      {"role": "system", "content": "You are a helpful coding assistant."},
      {"role": "user", "content": "Explain what a Python list is in one sentence."}
    ]
  }'"'"''
print_command "$cmd"
print_response
eval $cmd | jq '.' 2>/dev/null || eval $cmd
echo -e "\n"

# Example 5: Streaming Response
print_example "5. Streaming Chat Completion"
cmd='curl -s -X POST '$BASE_URL'/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '"'"'{
    "model": "gemini-2.5-flash",
    "messages": [
      {"role": "user", "content": "Tell me a very short joke."}
    ],
    "stream": true
  }'"'"''
print_command "$cmd"
print_response
echo "Streaming response:"
eval $cmd
echo -e "\n"

# Example 6: Using Gemini 2.5 Pro
print_example "6. Using Gemini 2.5 Pro Model"
cmd='curl -s -X POST '$BASE_URL'/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '"'"'{
    "model": "gemini-2.5-pro",
    "messages": [
      {"role": "user", "content": "What is the capital of France?"}
    ]
  }'"'"''
print_command "$cmd"
print_response
eval $cmd | jq '.' 2>/dev/null || eval $cmd
echo -e "\n"

# Example 7: Multi-turn Conversation
print_example "7. Multi-turn Conversation"
cmd='curl -s -X POST '$BASE_URL'/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '"'"'{
    "model": "gemini-2.5-flash",
    "messages": [
      {"role": "user", "content": "What is 2+2?"},
      {"role": "assistant", "content": "2+2 equals 4."},
      {"role": "user", "content": "What about 2+3?"}
    ]
  }'"'"''
print_command "$cmd"
print_response
eval $cmd | jq '.' 2>/dev/null || eval $cmd
echo -e "\n"

echo -e "${GREEN}All examples completed!${NC}"
echo
echo "Tips:"
echo "- Install jq for better JSON formatting: sudo apt-get install jq"
echo "- Check server logs: docker-compose logs -f"
echo "- Test server health: curl $BASE_URL/health"
