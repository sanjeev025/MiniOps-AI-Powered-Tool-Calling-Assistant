from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(status_router)
    app.include_router(events_router)
    app.include_router(utcp_router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("demo_api.main:app", host="127.0.0.1", port=8000, reload=True)
