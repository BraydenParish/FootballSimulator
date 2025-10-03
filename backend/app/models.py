"""SQLAlchemy models backing the NFL GM simulator database."""

from __future__ import annotations

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, synonym

Base = declarative_base()


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    abbreviation = Column(String, nullable=False, unique=True)
    conference = Column(String, nullable=False)
    division = Column(String, nullable=False)


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    team = Column(String, nullable=False, default="FA")
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    ovr = Column(Integer, nullable=False)
    overall_rating = Column(Integer, nullable=False)
    spd = Column(Integer)
    str = Column("strength", Integer)
    agi = Column(Integer)
    cod = Column(Integer)
    inj = Column(Integer)
    awr = Column(Integer)
    age = Column(Integer, default=25)
    status = Column(String, nullable=False, default="active")
    salary = Column(Integer, default=0)
    contract_years = Column(Integer, default=0)
    free_agent_year = Column(Integer, nullable=True)
    depth_chart_position = Column(String, nullable=True)
    depth_chart_order = Column(Integer, nullable=True)
    injury_status = Column(String, nullable=False, default="healthy")

    # Legacy aliases expected by existing services/queries.
    strength_rating = synonym("str")


class DepthChart(Base):
    __tablename__ = "depth_charts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team = Column(String, nullable=False)
    position = Column(String, nullable=False)
    player_name = Column(String, nullable=False)
    depth = Column(Integer, nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=True)


class FreeAgent(Base):
    __tablename__ = "free_agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    age = Column(Float)
    yoe = Column(Integer)  # Years of experience
    prev_team = Column(String)
    prev_aav = Column(Float)
    contract_type = Column(String)
    market_value = Column(Float)
    year = Column(Integer, nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=True)


class Schedule(Base):
    __tablename__ = "schedule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team = Column(String, nullable=False)
    week = Column(Integer, nullable=False)
    opponent = Column(String, nullable=False)
    home_game = Column(Boolean, default=True)
