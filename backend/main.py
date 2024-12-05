from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import open_app, search, reminders, email_draft, fun, weather_time, intent

app = FastAPI(title="VoiceAgent Backend")

# CORS middleware for frontend-backend communication
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Modular MCP routers for each feature
app.include_router(open_app.router, prefix="/mcp/open_app", tags=["Open Applications MCP"])
app.include_router(search.router, prefix="/mcp/search", tags=["Search MCP"])
app.include_router(reminders.router, prefix="/mcp/reminders", tags=["Reminders MCP"])
app.include_router(email_draft.router, prefix="/mcp/email_draft", tags=["Email Drafts MCP"])
app.include_router(fun.router, prefix="/mcp/fun", tags=["Fun MCP"])
app.include_router(weather_time.router, prefix="/mcp/weather_time", tags=["Weather & Time MCP"])
app.include_router(intent.router, prefix="/mcp/intent", tags=["Intent MCP"])

# Updated imports for .mcp files
from routers.open_app import router as open_app_router
from routers.search import router as search_router
from routers.reminders import router as reminders_router
from routers.email_draft import router as email_draft_router
from routers.fun import router as fun_router
from routers.weather_time import router as weather_time_router
from routers.intent import router as intent_router

# Updated router inclusions
app.include_router(open_app_router, prefix="/mcp/open_app", tags=["Open Applications MCP"])
app.include_router(search_router, prefix="/mcp/search", tags=["Search MCP"])
app.include_router(reminders_router, prefix="/mcp/reminders", tags=["Reminders MCP"])
app.include_router(email_draft_router, prefix="/mcp/email_draft", tags=["Email Drafts MCP"])
app.include_router(fun_router, prefix="/mcp/fun", tags=["Fun MCP"])
app.include_router(weather_time_router, prefix="/mcp/weather_time", tags=["Weather & Time MCP"])
app.include_router(intent_router, prefix="/mcp/intent", tags=["Intent MCP"])
