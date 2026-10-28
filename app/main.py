import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .repository import Repository
from .routes import router


def create_app(database_path=None):
    repository = Repository(database_path or os.getenv('MINIDASH_DB', 'minidash.db'))

    @asynccontextmanager
    async def lifespan(app):
        repository.initialize()
        yield

    application = FastAPI(title='MiniDash', lifespan=lifespan)
    application.state.repository = repository
    application.include_router(router)
    return application


app = create_app()
