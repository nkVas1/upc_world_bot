"""Database models for UPC World Bot."""
from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlalchemy import (
    BigInteger, String, Integer, Boolean, DateTime, Text,
    Numeric, ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from bot.database.base import Base


class User(Base):
    """User model with website synchronization."""
    __tablename__ = "users"
    
    # Primary identification
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram ID
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Authentication & Sync
    telegram_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website_user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, unique=True)
    is_synced: Mapped[bool] = mapped_column(Boolean, default=False)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Membership
    is_member: Mapped[bool] = mapped_column(Boolean, default=False)
    membership_level: Mapped[str] = mapped_column(String(50), default="guest")  # guest, member, vip
    joined_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # UP Coins (внутренняя валюта)
    up_coins: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    
    # Referral System
    referral_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    referred_by_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    referral_count: Mapped[int] = mapped_column(Integer, default=0)
    referral_earnings: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    
    # QR Code
    qr_code_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    public_profile_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Activity tracking
    daily_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_daily_claim: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_events_attended: Mapped[int] = mapped_column(Integer, default=0)
    
    # Statistics
    total_spent: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_earned: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    
    # Meta
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    ban_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    referrals: Mapped[list["User"]] = relationship(
        "User", backref="referrer", remote_side=[id]
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="user", cascade="all, delete-orphan"
    )
    achievements: Mapped[list["UserAchievement"]] = relationship(
        "UserAchievement", back_populates="user", cascade="all, delete-orphan"
    )
    game_progress: Mapped[Optional["GameProgress"]] = relationship(
        "GameProgress", back_populates="user", uselist=False
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_user_telegram_id", "id"),
        Index("idx_user_referral_code", "referral_code"),
        Index("idx_user_website_id", "website_user_id"),
        Index("idx_user_membership", "membership_level"),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Transaction(Base):
    """Transaction history for UP Coins and payments."""
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    
    # Transaction details
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # earn, spend, referral, purchase
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Description
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Payment integration
    payment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payment_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Website sync
    website_transaction_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_synced: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="transactions")
    
    __table_args__ = (
        Index("idx_transaction_user", "user_id"),
        Index("idx_transaction_type", "type"),
        Index("idx_transaction_created", "created_at"),
    )


class Event(Base):
    """Events and parties information."""
    __tablename__ = "events"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Event details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    theme: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Location & Time
    location: Mapped[str] = mapped_column(String(500), nullable=False)
    event_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    doors_open: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    doors_close: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Capacity & Status
    max_capacity: Mapped[int] = mapped_column(Integer, default=300)
    current_attendees: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="upcoming")  # upcoming, ongoing, completed, cancelled
    
    # Images
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    gallery_urls: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    
    # Website sync
    website_event_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, unique=True)
    is_synced: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="event")
    
    __table_args__ = (
        Index("idx_event_date", "event_date"),
        Index("idx_event_status", "status"),
    )


class Ticket(Base):
    """Ticket purchases and management."""
    __tablename__ = "tickets"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    
    # Ticket details
    ticket_type: Mapped[str] = mapped_column(String(50), nullable=False)  # standard, freebar, vip
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # QR Code for entry
    qr_code: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    qr_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, used, refunded, cancelled
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Payment
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    transaction_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("transactions.id"), nullable=True
    )
    
    # Website sync
    website_ticket_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_synced: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tickets")
    event: Mapped["Event"] = relationship("Event", back_populates="tickets")
    
    __table_args__ = (
        Index("idx_ticket_user", "user_id"),
        Index("idx_ticket_event", "event_id"),
        Index("idx_ticket_qr", "qr_code"),
        UniqueConstraint("user_id", "event_id", name="uq_user_event"),
    )


class Achievement(Base):
    """Available achievements in the system."""
    __tablename__ = "achievements"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Rewards
    up_coins_reward: Mapped[int] = mapped_column(Integer, default=0)
    
    # Requirements
    requirement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    requirement_value: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserAchievement(Base):
    """User's earned achievements."""
    __tablename__ = "user_achievements"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    achievement_id: Mapped[int] = mapped_column(Integer, ForeignKey("achievements.id"), nullable=False)
    
    earned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="achievements")
    achievement: Mapped["Achievement"] = relationship("Achievement")
    
    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
        Index("idx_user_achievement_user", "user_id"),
    )


class GameProgress(Base):
    """User's game progress for card game and mini-games."""
    __tablename__ = "game_progress"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Card Game
    cards_owned: Mapped[list] = mapped_column(JSONB, default=list)
    cards_collection: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Mini-games scores
    mini_game_scores: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Leaderboard position
    global_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="game_progress")


class AdminLog(Base):
    """Admin actions logging."""
    __tablename__ = "admin_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_admin_log_admin", "admin_id"),
        Index("idx_admin_log_created", "created_at"),
    )
