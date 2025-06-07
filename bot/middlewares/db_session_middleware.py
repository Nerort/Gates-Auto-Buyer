from db.session import get_db_session


class DBSessionMiddleware:
    """Middleware to pass the database session to the handlers"""

    async def __call__(self, handler, event, data):
        with get_db_session() as db:
            data['db_session'] = db
            return await handler(event, data)
