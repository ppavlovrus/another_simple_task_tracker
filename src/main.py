"""FastAPI application entry point.

This module initializes the FastAPI application and includes all API routers.
"""

from fastapi import FastAPI

from api.routers import attachments, tags, tasks, users
from database.pool import lifespan


# FastAPI application initialization
app = FastAPI(
    title="Task Tracker API",
    description="REST API for task management system",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(tags.router)
app.include_router(attachments.router)


# Application entry point
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
