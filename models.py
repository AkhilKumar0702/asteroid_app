from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, Enum, DateTime, JSON
from sqlalchemy.orm import relationship

from database import Base


class Asteroids(Base):
    __tablename__ = "Asteroids"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(Enum('S','C','M'))
    size = Column(Float)
    distance = Column(Float)
    location = Column(JSON)
    probability_of_collision = Column(Float)
    observation_time = Column(DateTime)

