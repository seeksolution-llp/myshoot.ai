from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.db.config import Base, engine
from app.admin import routers as admin
from app.studios import routers as studio
from app.event import routers as event
from app.user import routers as user
from app.face_data import routers as face_data
from app.media import routers as media
from app.match_result import routers as match_result
from app.auth import routers as auth


app = FastAPI()

# Mount upload directories dynamically to serve images over URLs cleanly
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Application Module Routers
app.include_router(admin.router , prefix="/admins", tags=["Admin"])
app.include_router(studio.router, prefix="/studios", tags=["Studios"])
app.include_router(event.router, prefix="/events", tags=["Events"])
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(face_data.router, prefix="/face-data" , tags=["Face Data"])
app.include_router(media.router, prefix="/media", tags=["Media"])
app.include_router(match_result.router, prefix="/match-result", tags=["Match Result"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication Engine"])


@app.get("/")
def root():
    return {"message": "My Shoot AI Backend"}
