# Import os for use in this module.
import os

# Import asynccontextmanager from contextlib.
from contextlib import asynccontextmanager

# Import FastAPI from fastapi.
from fastapi import FastAPI

# Import Repository from .repository.
from .repository import Repository

# Import router from .routes.
from .routes import router


# Define create app.
def create_app(database_path=None):

    # Set repository to Repository(database_path or os.getenv('MINIDASH_DB',
    # 'minidash.db')).
    repository = Repository(database_path or os.getenv('MINIDASH_DB', 'minidash.db'))

    # Apply this decorator to configure the function defined below.
    @asynccontextmanager
    # Define lifespan.
    async def lifespan(app):

        # Call repository.initialize().
        repository.initialize()

        # Yield control to the caller.
        yield

    # Set application to FastAPI(title='MiniDash', lifespan=lifespan).
    application = FastAPI(title='MiniDash', lifespan=lifespan)

    # Set application.state.repository to repository.
    application.state.repository = repository

    # Call application.include_router(router).
    application.include_router(router)

    # Return application.
    return application


# Set app to create_app().
app = create_app()
