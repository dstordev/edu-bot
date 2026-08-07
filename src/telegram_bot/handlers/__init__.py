from aiogram import Router

from .admin import admin_router
from .error import error_router
from .registered import registered_router
from .unregistered import unregistered_router

global_router = Router()

global_router.include_routers(
    admin_router, registered_router, unregistered_router, error_router
)

__all__ = ["global_router"]
