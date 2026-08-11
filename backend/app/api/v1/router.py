from fastapi import APIRouter

from app.api.v1 import auth, dashboard, external_knowledge, knowledge, settings, tasks, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(tasks.router)
api_router.include_router(settings.router)
api_router.include_router(users.router)
api_router.include_router(knowledge.router)
api_router.include_router(external_knowledge.router)
api_router.include_router(dashboard.router)

