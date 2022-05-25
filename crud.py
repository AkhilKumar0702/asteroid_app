import ast,datetime,json,logging
from operator import and_
from sqlalchemy.orm import Session
from cache_client import get_redis_client
import uuid
from sqlalchemy import or_

import models, schemas
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

logger = logging.getLogger(__name__)

redis_conn = get_redis_client()
def create_asteroid(db: Session, asteroid: schemas.Asteroids):
    db_asteroid = models.Asteroids(name=asteroid.name, type=asteroid.type, size=asteroid.size, distance=asteroid.distance,
    probability_of_collision=asteroid.probability_of_collision, location=asteroid.location, observation_time=datetime.datetime.now())
    db.add(db_asteroid)
    db.commit()
    db.refresh(db_asteroid)
    redis_conn.set(f'Create_{str(uuid.uuid4())}',asteroid.name)
    return db_asteroid

def get_asteroids(db: Session):
    redis_conn.set(f'Read_all_{str(uuid.uuid4())}',"All")
    return db.query(models.Asteroids).all()

def get_dangerous_asteroids(db: Session):
    redis_conn.set(f'Read_{str(uuid.uuid4())}',"Dangerous_Asteroids")
    return db.query(models.Asteroids).filter(or_(models.Asteroids.size > 1000, models.Asteroids.probability_of_collision > 0.9, and_(models.Asteroids.size > 100, models.Asteroids.probability_of_collision > 0.7))).all()

def get_asteroid_by_name(db: Session, name = None):
    if name:
        redis_conn.set(f'Read_{str(uuid.uuid4())}',name)
        return db.query(models.Asteroids).filter(models.Asteroids.name == name).first()
    return None


def delete_asteroid_by_id(db: Session, asteroid: schemas.Asteroids):
    db.delete(asteroid)
    db.commit()
    redis_conn.set(f'Delete_{str(uuid.uuid4())}',asteroid.name)
    # db.refresh(asteroid)
    return None



def update_asteroid_details(db: Session, asteroid: schemas.Asteroids, asteroid_update: schemas.Asteroids_update):
    asteroid_data = asteroid_update.dict(exclude_unset=True)
    logger.debug(f"{asteroid_data}")
    for k,v in asteroid_data.items():
        logger.debug(f"{k}:{v}")
        setattr(asteroid,k,v)
    # db_asteroid = models.Asteroids(name=asteroid.name, type=asteroid.type, size=asteroid.size, distance=asteroid.distance,
    # probability_of_collision=asteroid.probability_of_collision, location=asteroid.location, observation_time=datetime.datetime.now())
    # db.add(asteroid)
    db.commit()
    db.refresh(asteroid)
    redis_conn.set(f'Update{str(uuid.uuid4())}',asteroid.name)
    return asteroid