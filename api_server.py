#!/usr/bin/env python3
"""
OpenAI-compatible API server for Gemini Web API
Provides /v1/chat/completions and /v1/models endpoints
"""

import asyncio
import json
import os
import random
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, List, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.gemini_webapi import GeminiClient
from src.gemini_webapi.constants import Model
from src.gemini_webapi.exceptions import APIError, AuthError, GeminiError


# Pydantic models for OpenAI API compatibility
class ChatMessage(BaseModel):
    role: str = Field(..., description="The role of the message author")
    content: str = Field(..., description="The content of the message")


class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="ID of the model to use")
    messages: List[ChatMessage] = Field(..., description="List of messages")
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    stream: Optional[bool] = Field(default=False)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    stop: Optional[Union[str, List[str]]] = Field(default=None)


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Dict[str, int]


class ChatCompletionStreamChoice(BaseModel):
    index: int
    delta: Dict[str, str]
    finish_reason: Optional[str] = None


class ChatCompletionStreamResponse(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionStreamChoice]


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "google"


class ModelsResponse(BaseModel):
    object: str = "list"
    data: List[ModelInfo]


# Cookie configuration
class CookieConfig:
    def __init__(self, secure_1psid: str, secure_1psidts: str = "", name: str = ""):
        self.secure_1psid = secure_1psid
        self.secure_1psidts = secure_1psidts
        self.name = name or f"Account-{secure_1psid[:8]}"
        self.client: Optional[GeminiClient] = None
        self.is_available = True
        self.last_used = 0
        self.error_count = 0
        self.max_errors = 3

    async def get_client(self) -> GeminiClient:
        """Get or create Gemini client for this cookie"""
        if self.client is None:
            self.client = GeminiClient(
                secure_1psid=self.secure_1psid,
                secure_1psidts=self.secure_1psidts,
                proxy=None
            )
            await self.client.init(timeout=30, auto_refresh=True)
        return self.client

    def mark_error(self):
        """Mark an error for this cookie"""
        self.error_count += 1
        if self.error_count >= self.max_errors:
            self.is_available = False

    def mark_success(self):
        """Mark successful usage"""
        self.error_count = 0
        self.is_available = True
        self.last_used = time.time()


# Global cookie manager
class CookieManager:
    def __init__(self):
        self.cookies: List[CookieConfig] = []
        self.current_index = 0

    def load_cookies_from_env(self):
        """Load cookies from environment variables"""
        self.cookies.clear()

        # Load single cookie (backward compatibility)
        secure_1psid = os.getenv("SECURE_1PSID")
        secure_1psidts = os.getenv("SECURE_1PSIDTS", "")

        if secure_1psid:
            self.cookies.append(CookieConfig(
                secure_1psid=secure_1psid,
                secure_1psidts=secure_1psidts,
                name="Primary Account"
            ))

        # Load multiple cookies from JSON
        cookies_json = os.getenv("COOKIES_JSON")
        if cookies_json:
            try:
                cookies_data = json.loads(cookies_json)
                for i, cookie_data in enumerate(cookies_data):
                    self.cookies.append(CookieConfig(
                        secure_1psid=cookie_data["secure_1psid"],
                        secure_1psidts=cookie_data.get("secure_1psidts", ""),
                        name=cookie_data.get("name", f"Account-{i+1}")
                    ))
            except json.JSONDecodeError as e:
                print(f"Error parsing COOKIES_JSON: {e}")

        # Load from individual environment variables (COOKIE_1_PSID, COOKIE_1_PSIDTS, etc.)
        i = 1
        while True:
            psid_key = f"COOKIE_{i}_PSID"
            psidts_key = f"COOKIE_{i}_PSIDTS"
            name_key = f"COOKIE_{i}_NAME"

            psid = os.getenv(psid_key)
            if not psid:
                break

            self.cookies.append(CookieConfig(
                secure_1psid=psid,
                secure_1psidts=os.getenv(psidts_key, ""),
                name=os.getenv(name_key, f"Account-{i}")
            ))
            i += 1

        if not self.cookies:
            raise ValueError("No valid cookies found. Please set SECURE_1PSID or COOKIES_JSON environment variable.")

    def get_available_cookies(self) -> List[CookieConfig]:
        """Get list of available cookies"""
        return [cookie for cookie in self.cookies if cookie.is_available]

    def get_next_cookie(self) -> Optional[CookieConfig]:
        """Get next available cookie using round-robin"""
        available_cookies = self.get_available_cookies()
        if not available_cookies:
            return None

        # Round-robin selection
        cookie = available_cookies[self.current_index % len(available_cookies)]
        self.current_index = (self.current_index + 1) % len(available_cookies)
        return cookie

    def get_random_cookie(self) -> Optional[CookieConfig]:
        """Get random available cookie"""
        available_cookies = self.get_available_cookies()
        if not available_cookies:
            return None
        return random.choice(available_cookies)

    def get_least_used_cookie(self) -> Optional[CookieConfig]:
        """Get least recently used cookie"""
        available_cookies = self.get_available_cookies()
        if not available_cookies:
            return None
        return min(available_cookies, key=lambda c: c.last_used)

    async def get_client(self, strategy: str = "round_robin") -> GeminiClient:
        """Get a Gemini client using specified strategy"""
        if strategy == "round_robin":
            cookie = self.get_next_cookie()
        elif strategy == "random":
            cookie = self.get_random_cookie()
        elif strategy == "least_used":
            cookie = self.get_least_used_cookie()
        else:
            cookie = self.get_next_cookie()

        if not cookie:
            raise ValueError("No available cookies. All accounts may be rate limited or invalid.")

        try:
            client = await cookie.get_client()
            cookie.mark_success()
            return client
        except Exception as e:
            cookie.mark_error()
            # Try next available cookie
            available_cookies = self.get_available_cookies()
            if available_cookies:
                return await self.get_client(strategy)
            else:
                raise ValueError(f"All cookies failed. Last error: {e}")

    def get_status(self) -> Dict:
        """Get status of all cookies"""
        return {
            "total_cookies": len(self.cookies),
            "available_cookies": len(self.get_available_cookies()),
            "cookies": [
                {
                    "name": cookie.name,
                    "is_available": cookie.is_available,
                    "error_count": cookie.error_count,
                    "last_used": cookie.last_used
                }
                for cookie in self.cookies
            ]
        }


# Global cookie manager instance
cookie_manager = CookieManager()


# Available models mapping
AVAILABLE_MODELS = {
    "gemini-2.5-pro": Model.G_2_5_PRO,
    "gemini-2.5-flash": Model.G_2_5_FLASH,
    "gemini-2.0-flash": Model.G_2_0_FLASH,
    "gemini-2.0-flash-thinking": Model.G_2_0_FLASH_THINKING,
    "gemini-2.5-exp-advanced": Model.G_2_5_EXP_ADVANCED,
    "gemini-2.0-exp-advanced": Model.G_2_0_EXP_ADVANCED,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    try:
        cookie_manager.load_cookies_from_env()
        print(f"Initialized cookie manager with {len(cookie_manager.cookies)} cookies")
        for cookie in cookie_manager.cookies:
            print(f"  - {cookie.name}: {cookie.secure_1psid[:8]}...")
    except Exception as e:
        print(f"Failed to initialize cookie manager: {e}")
        raise

    yield

    # Shutdown
    print("Shutting down...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="Gemini API Server",
        description="OpenAI-compatible API server for Google Gemini",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()


async def initialize_cookie_manager():
    """Initialize the cookie manager"""
    try:
        cookie_manager.load_cookies_from_env()
        return cookie_manager
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize cookie manager: {str(e)}"
        )


async def get_gemini_client(strategy: str = "round_robin") -> GeminiClient:
    """Get a Gemini client using the specified strategy"""
    try:
        return await cookie_manager.get_client(strategy)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Gemini client: {str(e)}"
        )


def messages_to_prompt(messages: List[ChatMessage]) -> str:
    """Convert OpenAI messages format to a single prompt"""
    prompt_parts = []
    
    for message in messages:
        role = message.role
        content = message.content
        
        if role == "system":
            prompt_parts.append(f"System: {content}")
        elif role == "user":
            prompt_parts.append(f"User: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")
    
    return "\n\n".join(prompt_parts)


async def generate_stream_response(
    prompt: str,
    model: Model,
    request_id: str,
    model_name: str
) -> AsyncGenerator[str, None]:
    """Generate streaming response for chat completion"""
    client = await get_gemini_client()
    
    try:
        # Generate content using Gemini
        response = await client.generate_content(prompt, model=model)
        
        # Split response into chunks for streaming
        text = response.text
        words = text.split()
        
        # Send chunks
        for i, word in enumerate(words):
            chunk = ChatCompletionStreamResponse(
                id=request_id,
                created=int(time.time()),
                model=model_name,
                choices=[
                    ChatCompletionStreamChoice(
                        index=0,
                        delta={"content": word + " " if i < len(words) - 1 else word},
                        finish_reason=None
                    )
                ]
            )
            yield f"data: {chunk.model_dump_json()}\n\n"
            await asyncio.sleep(0.05)  # Small delay for streaming effect
        
        # Send final chunk
        final_chunk = ChatCompletionStreamResponse(
            id=request_id,
            created=int(time.time()),
            model=model_name,
            choices=[
                ChatCompletionStreamChoice(
                    index=0,
                    delta={},
                    finish_reason="stop"
                )
            ]
        )
        yield f"data: {final_chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        error_chunk = ChatCompletionStreamResponse(
            id=request_id,
            created=int(time.time()),
            model=model_name,
            choices=[
                ChatCompletionStreamChoice(
                    index=0,
                    delta={"content": f"Error: {str(e)}"},
                    finish_reason="error"
                )
            ]
        )
        yield f"data: {error_chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"


@app.get("/v1/models")
async def list_models() -> ModelsResponse:
    """List available models"""
    models = []
    created_time = int(time.time())
    
    for model_id in AVAILABLE_MODELS.keys():
        models.append(
            ModelInfo(
                id=model_id,
                created=created_time,
                owned_by="google"
            )
        )
    
    return ModelsResponse(data=models)


@app.post("/v1/chat/completions", response_model=None)
async def create_chat_completion(request: ChatCompletionRequest):
    """Create a chat completion"""
    
    # Validate model
    if request.model not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{request.model}' not found. Available models: {list(AVAILABLE_MODELS.keys())}"
        )
    
    # Convert messages to prompt
    prompt = messages_to_prompt(request.messages)
    model = AVAILABLE_MODELS[request.model]
    request_id = f"chatcmpl-{uuid.uuid4().hex}"
    
    if request.stream:
        # Return streaming response
        return StreamingResponse(
            generate_stream_response(prompt, model, request_id, request.model),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    else:
        # Return non-streaming response
        try:
            client = await get_gemini_client()
            response = await client.generate_content(prompt, model=model)
            
            return ChatCompletionResponse(
                id=request_id,
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(role="assistant", content=response.text),
                        finish_reason="stop"
                    )
                ],
                usage={
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": len(response.text.split()),
                    "total_tokens": len(prompt.split()) + len(response.text.split())
                }
            )
        except (APIError, AuthError, GeminiError) as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        await get_gemini_client()
        return {"status": "healthy", "gemini_client": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.get("/cookies/status")
async def cookies_status():
    """Get status of all cookies"""
    try:
        status = cookie_manager.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cookies status: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Gemini API Server",
        "version": "1.0.0",
        "endpoints": {
            "models": "/v1/models",
            "chat_completions": "/v1/chat/completions",
            "health": "/health",
            "cookies_status": "/cookies/status"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 50014)),
        reload=False,
        log_level="info"
    )
