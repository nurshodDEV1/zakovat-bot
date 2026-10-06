from .start import router as start_router
from .game import router as game_router
from .admin import router as admin_router
from .group import router as group_router

__all__ = ["start_router", "game_router", "admin_router", "group_router"]
