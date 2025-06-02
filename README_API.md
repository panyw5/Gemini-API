# Gemini API Server

OpenAI-compatible API server for Google Gemini using reverse-engineered web API.

## Features

- **OpenAI Compatible**: Drop-in replacement for OpenAI API endpoints
- **Multiple Models**: Support for Gemini 2.5 Pro, 2.5 Flash, 2.0 Flash, and more
- **Streaming Support**: Real-time streaming responses
- **Docker Ready**: Easy deployment with Docker and Docker Compose
- **Cookie Persistence**: Automatic cookie management and refresh

## Quick Start

### 1. Get Google Cookies

1. Go to [https://gemini.google.com](https://gemini.google.com) and login
2. Press F12 for web inspector, go to **Network** tab and refresh the page
3. Click any request and copy cookie values of `__Secure-1PSID` and `__Secure-1PSIDTS`

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your cookies
nano .env
```

### 3. Deploy with Docker Compose

```bash
# Build and start the service
docker-compose up -d

# Check logs
docker-compose logs -f

# Check health
curl http://localhost:50014/health
```

## API Endpoints

### List Models
```bash
curl http://localhost:50014/v1/models
```

### Chat Completion (Non-streaming)
```bash
curl -X POST http://localhost:50014/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.5-pro",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ]
  }'
```

### Chat Completion (Streaming)
```bash
curl -X POST http://localhost:50014/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.5-flash",
    "messages": [
      {"role": "user", "content": "Tell me a story"}
    ],
    "stream": true
  }'
```

## Available Models

- `gemini-2.5-pro` - Gemini 2.5 Pro (daily usage limit)
- `gemini-2.5-flash` - Gemini 2.5 Flash
- `gemini-2.0-flash` - Gemini 2.0 Flash
- `gemini-2.0-flash-thinking` - Gemini 2.0 Flash Thinking
- `gemini-2.5-exp-advanced` - Gemini 2.5 Experimental Advanced (requires Gemini Advanced)
- `gemini-2.0-exp-advanced` - Gemini 2.0 Experimental Advanced (requires Gemini Advanced)

## Usage with OpenAI Libraries

### Python (openai library)
```python
import openai

client = openai.OpenAI(
    api_key="dummy",  # Not used but required
    base_url="http://localhost:50014/v1"
)

response = client.chat.completions.create(
    model="gemini-2.5-pro",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### Node.js
```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: 'dummy',
  baseURL: 'http://localhost:50014/v1',
});

const response = await openai.chat.completions.create({
  model: 'gemini-2.5-flash',
  messages: [{ role: 'user', content: 'Hello!' }],
});

console.log(response.choices[0].message.content);
```

## Configuration

### Environment Variables

- `SECURE_1PSID` (Required): Your Google `__Secure-1PSID` cookie
- `SECURE_1PSIDTS` (Optional): Your Google `__Secure-1PSIDTS` cookie
- `PROXY` (Optional): Proxy URL if needed
- `PORT` (Optional): Server port (default: 50014)

### Cookie Persistence

Cookies are automatically persisted in the `./gemini_cookies` directory to avoid re-authentication on container restarts.

## Troubleshooting

### Common Issues

1. **Authentication Error**: Make sure your cookies are valid and not expired
2. **Model Not Available**: Some models require Gemini Advanced subscription
3. **Rate Limiting**: Gemini has usage limits, especially for Pro models

### Logs

```bash
# View container logs
docker-compose logs -f gemini-api

# Check health status
curl http://localhost:50014/health
```

### Manual Cookie Refresh

If you encounter authentication issues, get fresh cookies:

1. Clear browser cache for gemini.google.com
2. Login again to https://gemini.google.com
3. Extract new cookie values
4. Update your `.env` file
5. Restart the container: `docker-compose restart`

## Development

### Local Development

```bash
# Install dependencies
pip install -e .

# Set environment variables
export SECURE_1PSID="your_cookie_here"
export SECURE_1PSIDTS="your_cookie_here"

# Run the server
python api_server.py
```

### Testing

```bash
# Test models endpoint
curl http://localhost:50014/v1/models

# Test chat completion
curl -X POST http://localhost:50014/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "gemini-2.5-flash", "messages": [{"role": "user", "content": "Test"}]}'
```

## License

This project uses the same license as the original Gemini-API project.
