"""Event repository."""
from typing import Optional
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Event


class EventRepository:
    """Repository for event operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, event_id: int) -> Optional[Event]:
        """Get event by ID."""
        result = await self.session.execute(
            select(Event).where(Event.id == event_id)
        )
        return result.scalar_one_or_none()
    
    async def get_upcoming_events(self, limit: int = 10) -> list[Event]:
        """Get upcoming events."""
        now = datetime.utcnow()
        result = await self.session.execute(
            select(Event)
            .where(Event.event_date >= now)
            .where(Event.status == "upcoming")
            .order_by(Event.event_date.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_past_events(self, limit: int = 10) -> list[Event]:
        """Get past events."""
        now = datetime.utcnow()
        result = await self.session.execute(
            select(Event)
            .where(Event.event_date < now)
            .order_by(Event.event_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
