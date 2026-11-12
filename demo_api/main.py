from fastapi import FastAPI
from demo_api.routes.status import router as status_router
from demo_api.routes.events import router as events_router
from demo_api.utcp_manual import router as utcp_router


def create_app() -> FastAPI:
    """FastAPI application factory for MiniOps demo service."""
    app = FastAPI(
        title="MiniOps Demo Service",
        description="Demo service exposing status, events, and native UTCP manual endpoints.",
        version="1.0.0",
    )

    app.include_router(status_router)
    app.include_router(events_router)
    app.include_router(utcp_router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    from config.settings import settings

    uvicorn.run("demo_api.main:app", host=settings.DEMO_API_HOST, port=settings.DEMO_API_PORT, reload=True)
