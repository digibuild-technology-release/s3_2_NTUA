from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy import create_engine, Column, DateTime, Float, String
from sqlalchemy.orm import sessionmaker, declarative_base
import requests, os
from settings import DIGIBUILD_PG, BUILDING_LIST
from dotenv import load_dotenv
from datetime import date, timedelta, datetime, time
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


load_dotenv()
app = FastAPI()
security = HTTPBearer()


my_database_connection = f"postgresql://{DIGIBUILD_PG['USER']}:{DIGIBUILD_PG['PASSWORD']}@{DIGIBUILD_PG['HOSTNAME']}:{DIGIBUILD_PG['PORT']}/{DIGIBUILD_PG['DB']}"
engine = create_engine(my_database_connection, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=True, bind=engine)
Base = declarative_base()


def verify_token(token: str = Header(...)):
    if not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Token")

    access_token = token.replace("Bearer ", "")

    return access_token


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class BaseTable(Base):
    __abstract__ = True  # This makes the class not directly mappable to a table


def get_table(table_name: str):
    class DynamicTable(BaseTable):
        __tablename__ = table_name
        __table_args__ = {'extend_existing': True}
        index = Column(String, primary_key=True)
        datetime = Column(DateTime)
        co2_class = Column(String)
        rank = Column(Float)
        inverted_rate = Column(Float)
        rate = Column(Float)

    return DynamicTable

def get_carbon_table(table_name: str):
    class DynamicCarbonTable(BaseTable):
        __tablename__ = table_name
        __table_args__ = {'extend_existing': True}
        index = Column(String, primary_key=True)
        datetime = Column(DateTime)
        hour = Column(String)
        percentage = Column(Float)
        predicted = Column(Float)
        co2_class = Column(String)
        energy = Column(Float)

    return DynamicCarbonTable


Base.metadata.create_all(bind=engine)


@app.get("/std_vikor/", tags=['Standard Vikor Per building'])
async def read_single(building_id: int = None, credentials: HTTPAuthorizationCredentials = Depends(security), db: SessionLocal = Depends(get_db)):
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    token = credentials.credentials
    url = "http://digibuild.epu.ntua.gr/auth/realms/DIGIBUILD/protocol/openid-connect/token/introspect/"

    payload = f'client_id={client_id}&client_secret={client_secret}&token={token}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response = response.json()
    if datetime.now().time() > time(20, 30):
        day = date.today() + timedelta(days=1)
    else:
        day = date.today()
    if not "active" in response:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized access",
            headers={"X-Error": "Invalid credentials"}
        )
    elif not response['active']:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized access",
            headers={"X-Error": "Expired token"}
        )
    elif building_id:
        if not building_id in BUILDING_LIST:
            raise HTTPException(
                status_code=404,
                detail="Item not found",
                headers={"X-Error": "Invalid building id"}
            )
        else:
            return_dict = dict({})
            return_dict['date'] = day
            return_dict['payload'] = list([])

            temp_dict = dict({})
            temp_dict['buildingId'] = building_id
            table_name = f'std_vikor_{building_id}'
            table = get_table(table_name)
            results = db.query(table).all()
            data_list = [data.__dict__ for data in results]
            for data in data_list:
                if "datetime" in data:
                    datetime_value = data.pop("datetime")
                    time_value = datetime_value.strftime("%H:%M")
                    data["time"] = time_value
            temp_dict['predictions'] = results
            return_dict['payload'].append(temp_dict)
            return return_dict

    else:
        return_dict = dict({})
        return_dict['date'] = day
        return_dict['payload'] = list([])
        for building in BUILDING_LIST:
            temp_dict = dict({})
            temp_dict['buildingId'] = building
            table_name = f'std_vikor_{building}'
            table = get_table(table_name)
            results = db.query(table).all()
            data_list = [data.__dict__ for data in results]
            for data in data_list:
                if "datetime" in data:
                    datetime_value = data.pop("datetime")
                    time_value = datetime_value.strftime("%H:%M")
                    data["time"] = time_value
            temp_dict['predictions'] = results
            return_dict['payload'].append(temp_dict)
        return return_dict

@app.get("/carbon_free/", tags=['Carbon Free Buildings - Resource Management'])
async def read_carbon(building_id: int = None, credentials: HTTPAuthorizationCredentials = Depends(security), db: SessionLocal = Depends(get_db)):
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    token = credentials.credentials
    url = "http://digibuild.epu.ntua.gr/auth/realms/DIGIBUILD/protocol/openid-connect/token/introspect/"

    payload = f'client_id={client_id}&client_secret={client_secret}&token={token}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response = response.json()

    if datetime.now().time() > time(20, 30):
        day = date.today() + timedelta(days=1)
    else:
        day = date.today()
    if not "active" in response:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized access",
            headers={"X-Error": "Invalid credentials"}
        )
    elif not response['active']:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized access",
            headers={"X-Error": "Expired token"}
        )


    elif building_id:
        if not building_id in BUILDING_LIST:
            raise HTTPException(
                status_code=404,
                detail="Item not found",
                headers={"X-Error": "Invalid building id"}
            )

        else:
            return_dict = dict({})
            return_dict['date'] = day
            return_dict['payload'] = list([])
            predicted_en = 0
            data_dict = dict({})
            data_dict['buildingId'] = building_id
            data_dict['chargers'] = list([])
            temp_dict = dict({})
            table_name = f"s325_man_{building_id['building_id']}"
            try:
                table = get_carbon_table(table_name)
                results = db.query(table).all()
                data_list = [data.__dict__ for data in results]
                for data in data_list:
                    if "datetime" in data:
                        datetime_value = data.pop("datetime")
                        time_value = datetime_value.strftime("%H:%M")
                        data["time"] = time_value
                        if "hour" in data:
                            data.pop("hour")
                        if "percentage" in data:
                            percentage = data.pop("percentage")
                            data["percUsage"] = percentage
                        if "predicted" in data:
                            predicted_en = data.pop("predicted")
                    temp_dict['predictedEnergy'] = predicted_en
                    temp_dict['plan'] = results
                    data_dict['chargers'].append(temp_dict)
                    return_dict['payload'].append(data_dict)
            except:
                raise HTTPException(
                    status_code=404,
                    detail="Item not found!",
                )
    else:
        return_dict = dict({})
        return_dict['date'] = day
        return_dict['payload'] = list([])

        for building in BUILDING_LIST:
            predicted_en = 0
            table_name = f"s325_man_{building}"
            try:
                data_dict = dict({})
                data_dict['chargers'] = list([])
                temp_dict = dict({})
                data_dict['buildingId'] = building
                table = get_carbon_table(table_name)
                results = db.query(table).all()
                data_list = [data.__dict__ for data in results]
                for data in data_list:
                    if "datetime" in data:
                        datetime_value = data.pop("datetime")
                        time_value = datetime_value.strftime("%H:%M")
                        data["time"] = time_value
                    if "hour" in data:
                        data.pop("hour")
                    if "percentage" in data:
                        percentage = data.pop("percentage")
                        data["percUsage"] = percentage
                    if "predicted" in data:
                        predicted_en = data.pop("predicted")
                temp_dict['predictedEnergy'] = predicted_en
                temp_dict['plan'] = results
                data_dict['chargers'].append(temp_dict)
                return_dict['payload'].append(data_dict)
            except:
                data_dict = dict({})
                data_dict['chargers'] = list([])
                temp_dict = dict({})
                data_dict['buildingId'] = building
                temp_dict['predictedEnergy'] = 0
                temp_dict['plan'] = []
                data_dict['chargers'].append(dict({}))
                return_dict['payload'].append(data_dict)
        return return_dict

