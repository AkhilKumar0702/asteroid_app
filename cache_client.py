import redis,yaml,logging
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

logger = logging.getLogger(__name__)

def get_config_filedata():
        try:
            with open('app.yaml', 'r') as data:
                return yaml.load(data, Loader=yaml.FullLoader)
        except FileNotFoundError:
            logger.debug("No such file exists")


def get_redis_client():
    config_data = get_config_filedata()
    conn = redis.Redis(host=config_data['redis']['host'],port=config_data['redis']['port'],decode_responses=True)
    return conn


def get_all_objects_from_cache(redis_conn):
    asteroid_list =[]
    for key in redis_conn.scan_iter():
        asteroid_list.append(key)
    return asteroid_list


def create_asteroid_report(redis_conn,redis_key_list):
    logger.debug('asteroid report creation')
    with open('asteroid_report.txt','a') as report_file:
        report_file.write('report created \n')
        for keys in redis_key_list:
            report_file.writelines(str(redis_conn.hgetall(keys))+ "\n")


def alert_danger_if_required(asteroid_dict,request_id):
    # logger.debug(f'alert_danger {asteroid_dict}')
    if int(asteroid_dict.get('size')) > 1000:
        logger.debug(f"request_id:{request_id}:{asteroid_dict.get('name')} is larger than 1 km. Beware!!!!")
    elif float(asteroid_dict.get('probability_of_collision')) > 0.9:
        logger.debug(f"request_id:{request_id}:{asteroid_dict.get('name')} has collision probability of {asteroid_dict.get('probability_of_collision')}. Beware!!!!")
    elif int(asteroid_dict.get('size')) > 100 and float(asteroid_dict.get('probability_of_collision')) > 0.7:
        logger.debug(f"request_id:{request_id}:{asteroid_dict.get('name')} has collision probability of {asteroid_dict.get('probability_of_collision')}, and size is larger than {asteroid_dict.get('size')}  Beware!!!!")



def get_crud_count(redis_conn):
    a = redis_conn.keys('Create*')
    b = redis_conn.keys('Read*')
    c = redis_conn.keys('Update*')
    d = redis_conn.keys('Delete*')
    return len(a),len(b),len(c),len(d)


    

