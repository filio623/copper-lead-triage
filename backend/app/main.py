from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.reviews import router as reviews_router
from backend.app.api.runs import router as runs_router
from backend.app.models.db import create_database_engine, create_session_factory, initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create the shared DB engine, ensure tables exist, and store the
    # request session factory where API dependencies can access it.
    engine = create_database_engine()
    initialize_database(engine)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine=engine)

    yield

    # Shutdown: close SQLAlchemy's connection pool cleanly.
    engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(reviews_router)
app.include_router(runs_router)


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
