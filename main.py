# from fastapi import FastAPI
# from pydantic import BaseModel
# from typing import List, Optional
# from datetime import datetime
# app = FastAPI()

# sightings_list = []

# class Sighting(BaseModel):
#     species: str
#     location: str
#     date: str  # 'YYYYY-MM-DD'
#     time: str  #'HH:MM'


# @app.post("/sightings/")
# def add_sighting(sighting: Sighting):
#     try:
#         datetime.strptime(sighting.date, "%Y-%m-%d")
#     except ValueError:
#         return {"error": "Invalid date format. Use YYYY-MM-DD."}
#     try:
#         datetime.strptime(sighting.time, "%H:%M")
#     except ValueError:
#         return {"error": "Invalid time format. Use HH:MM."}
#     sightings_list.append(sighting.dict())
#     return {"message": "Sighting added successfully!", "sighting": sighting}


# @app.get("/sightings/", response_model=List[Sighting])
# def view_sightings():
#     if not sightings_list:
#         return {"message": "No sightings recorded."}
#     return sightings_list

# @app.get("/sightings/search/", response_model=List[Sighting])
# def search_sightings_by_species(species: Optional[str] = None):
#     if not species:
#         return {"message": "Species name is required."}

#     found_sightings = [s for s in sightings_list if s['species'].lower() == species.lower()]

#     if not found_sightings:
#         return {"message": f"No sightings found for species '{species}'."}

#     return found_sightings
# ____________________________________________________________________________________________________________________________________________

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from databases import Database

app = FastAPI()

DATABASE_URL = "postgresql://postgres:1234@localhost:5432/wildlife_tracking"
database = Database(DATABASE_URL)

class Sighting(BaseModel):
    species: str
    location: str
    date: str  # 'YYYY-MM-DD'
    time: str  # 'HH:MM'

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/sightings/")
async def add_sighting(sighting: Sighting):
    try:
        datetime.strptime(sighting.date, "%Y-%m-%d")
        datetime.strptime(sighting.time, "%H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time format.")
    try:
        query = "INSERT INTO sightings (species, location, date, time) VALUES (:species, :location, :date, :time)"
        await database.execute(query, values=sighting.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database insert failed: {str(e)}")

    return {"message": "Sighting added successfully!", "sighting": sighting}


@app.get("/sightings/", response_model=List[Sighting])
async def view_sightings():
    query = "SELECT species, location, date, time FROM sightings"
    sightings = await database.fetch_all(query)
    return sightings

@app.get("/sightings/search/", response_model=List[Sighting])
async def search_sightings_by_species(species: Optional[str] = None):
    if not species:
        raise HTTPException(status_code=400, detail="Species name is required.")

    query = "SELECT species, location, date, time FROM sightings WHERE LOWER(species) = LOWER(:species)"
    found_sightings = await database.fetch_all(query, values={"species": species})

    if not found_sightings:
        raise HTTPException(status_code=404, detail=f"No sightings found for species '{species}'.")

    return found_sightings

@app.put("/sightings/{sighting_id}")
async def update_sighting(sighting_id: int, updated_sighting: Sighting):
    query = "SELECT * FROM sightings WHERE id = :sighting_id"
    existing_sighting = await database.fetch_one(query, values={"sighting_id": sighting_id})

    if not existing_sighting:
        raise HTTPException(status_code=404, detail="Sighting not found.")
    update_query = """
    UPDATE sightings
    SET species = :species, location = :location, date = :date, time = :time
    WHERE id = :sighting_id
    """
    await database.execute(update_query, values={**updated_sighting.dict(), "sighting_id": sighting_id})
    return {"message": "Sighting updated successfully!", "sighting": updated_sighting}

@app.delete("/sightings/{sighting_id}")
async def delete_sighting(sighting_id: int):
    query = "SELECT * FROM sightings WHERE id = :sighting_id"
    existing_sighting = await database.fetch_one(query, values={"sighting_id": sighting_id})

    if not existing_sighting:
        raise HTTPException(status_code=404, detail="Sighting not found.")
    delete_query = "DELETE FROM sightings WHERE id = :sighting_id"
    await database.execute(delete_query, values={"sighting_id": sighting_id})
    return {"message": "Sighting deleted successfully!"}

