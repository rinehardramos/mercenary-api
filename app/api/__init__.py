"""
API endpoints for mercenary service.
"""

from app.api.auth import auth_router
from app.api.bounties import bounties_router
from app.api.agents import agents_router
from app.api.wallet import wallet_router

__all__ = ["auth_router", "bounties_router", "agents_router", "wallet_router"]
