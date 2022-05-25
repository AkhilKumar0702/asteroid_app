from typing import List
import logging,random,string
from urllib import request
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import json, uuid, contextvars
import crud, models, schemas
from database import SessionLocal, engine
from cache_client import get_redis_client, create_asteroid_report,alert_danger_if_required, get_crud_count
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)
request_id_contextvar = contextvars.ContextVar("request_id", default='None')
redis_tmp_key_list=[]

app = FastAPI()

templates = Jinja2Templates(directory="templates")
redis_conn = get_redis_client()
# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# setup loggers
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

# get root logger
logger = logging.getLogger(__name__)


@app.middleware("http")
async def request_middleware(request, call_next):
    request_id = str(uuid.uuid4())
    request_id_contextvar.set(request_id)
    redis_conn.set(f'req_id_{request_id}',request_id)

    logger.debug(f"request_id:{request_id}: Request started")

    try:
        response = await call_next(request)
        logger.debug(f"request_id:{request_id}: Status Code:{response.status_code}")
        return response

    except Exception as ex:
        logger.debug(f"request_id:{request_id}: Request failed: {ex}")
        return JSONResponse(content={"success": False}, status_code=500)

    finally:
        assert request_id_contextvar.get() == request_id
        logger.debug(f"request_id:{request_id}: Status Code:{response.status_code} ")


@app.get('/')
def home(request: Request, db: Session = Depends(get_db)):
    request_id = request_id_contextvar.get()
    logger.debug(f"request_id:{request_id}: Rendering data to html")
    create,read,update,delete = get_crud_count(redis_conn)
    lst = crud.get_dangerous_asteroids(db)
    return templates.TemplateResponse('index.html', context={'request': request, 'create':create,'read':read,'update':update,'delete':delete, "lst":lst})



@app.post("/create_asteroids/", response_model=schemas.Asteroids)
def create_asteroid(asteroid: schemas.Asteroids, db: Session = Depends(get_db)):
    request_id = request_id_contextvar.get()
    logger.debug(f"request_id:{request_id}: creating asteroid")
    if asteroid.probability_of_collision > 1 or asteroid.probability_of_collision < 0:
        logger.debug(f"request_id:{request_id} Probability of Collision should be between 0 and 1.")
        raise HTTPException(status_code=400, detail="Probability of Collision should be between 0 and 1.")
    if not asteroid.name:
        asteroid.name = f"{asteroid.type}_{''.join(random.choices(string.ascii_letters, k=5))}"
    db_user = crud.get_asteroid_by_name(db, name=asteroid.name)
    if db_user:
        logger.debug(f"request_id:{request_id} Asteroid with the name {asteroid.name} already exists")
        raise HTTPException(status_code=400, detail="Asteroid with the same name already exists")
    response = crud.create_asteroid(db=db, asteroid=asteroid)
    rs_dict = {"name": str(response.name),"type":response.type, "size":response.size, "distance":response.distance,
    "probability_of_collision":response.probability_of_collision, "location":json.dumps(response.location), "observation_time":str(response.observation_time)}
    redis_conn.hmset(response.name,rs_dict)
    redis_tmp_key_list.append(response.name)
    if len(redis_tmp_key_list) % 1 == 0:
        logger.debug(f"{request_id}: {create_asteroid_report(redis_conn,redis_tmp_key_list)}")
        redis_tmp_key_list.clear()
    logger.debug(f"request_id:{request_id}: Calling Alert Function ")
    alert_danger_if_required(rs_dict,request_id)
    logger.debug(f"request_id:{request_id}: {rs_dict}")
    return {"name": response.name,"type":response.type, "size":response.size, "distance":response.distance,
    "probability_of_collision":response.probability_of_collision, "location":response.location, "observation_time":str(response.observation_time)}


@app.get("/asteroids/", response_model=List[schemas.Asteroids])
def get_all_asteroids(db: Session = Depends(get_db)):
    request_id = request_id_contextvar.get()
    logger.debug(f"request_id:{request_id}: Get All Asteroids")
    asteroids = crud.get_asteroids(db)
    lst=[]
    for response in asteroids:
        a = {"name": response.name,"type":response.type, "size":response.size, "distance":response.distance,
    "probability_of_collision":response.probability_of_collision, "location":response.location, "observation_time":str(response.observation_time)}
        lst.append(a)
    return lst

@app.get("/asteroids/{asteroid_name}", response_model=schemas.Asteroids)
def get_asteroid(asteroid_name: str, db: Session = Depends(get_db)):
    request_id = request_id_contextvar.get()
    logger.debug(f"request_id:{request_id}: Get Asteroid by name: {asteroid_name}")
    response = crud.get_asteroid_by_name(db, name=asteroid_name)
    if response is None:
        logger.debug(f"request_id:{request_id} Asteroid with the name {asteroid_name} does not exist")
        raise HTTPException(status_code=404, detail="Asteroid not found")
    return {"name": response.name,"type":response.type, "size":response.size, "distance":response.distance,
    "probability_of_collision":response.probability_of_collision, "location":response.location, "observation_time":str(response.observation_time)}


@app.patch("/update_asteroids/", response_model=schemas.Asteroids)
def update_asteroid(asteroid: schemas.Asteroids_update , db: Session = Depends(get_db)):
    request_id = request_id_contextvar.get()
    logger.debug(f"request_id:{request_id}: Update Asteroid Details for {asteroid.name}")
    if asteroid.probability_of_collision and  (asteroid.probability_of_collision > 1 or asteroid.probability_of_collision < 0):
        logger.debug(f"request_id:{request_id} Probability of Collision should be between 0 and 1.")
        raise HTTPException(status_code=400, detail="Probability of Collision should be between 0 and 1.")
    asteroid_data = crud.get_asteroid_by_name(db, name=asteroid.name)
    if asteroid_data is None:
        logger.debug(f"request_id:{request_id} Asteroid with the name {asteroid.name} does not exist")
        raise HTTPException(status_code=404, detail="Asteroid not found")
    else:
        response = crud.update_asteroid_details(db=db, asteroid_update=asteroid, asteroid=asteroid_data)
    return {"name": response.name,"type":response.type, "size":response.size, "distance":response.distance,
    "probability_of_collision":response.probability_of_collision, "location":response.location, "observation_time":str(response.observation_time)}

@app.delete("/asteroids/{asteroid_name}")
def delete_asteroid(asteroid_name: str, db: Session = Depends(get_db)):
    request_id = request_id_contextvar.get()
    logger.debug(f"request_id:{request_id}: Delete Asteroid by Name {asteroid_name}")
    asteroid = crud.get_asteroid_by_name(db, name=asteroid_name)
    if asteroid is None:
        logger.debug(f"request_id:{request_id} Asteroid with the name {asteroid_name} does not exist")
        raise HTTPException(status_code=404, detail="Asteroid not found")
    else:
        crud.delete_asteroid_by_id(db=db, asteroid=asteroid )
    return f"Asteroid {asteroid_name} deleted successfully!!"



