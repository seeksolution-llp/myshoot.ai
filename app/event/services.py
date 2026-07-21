import io
import base64
import uuid
import qrcode
from fastapi import HTTPException
from app.event.models import Event
from app.event.schemas import EventCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# --- NEW: IMPORT FOR ALBUM CLUSTERING ---
from PIL import Image
from PIL.ExifTags import TAGS

def generate_qr_base64(event_id: str) -> str:
    """Generates a QR code image as a base64 string containing the event ID."""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(event_id)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"

# --- NEW: METADATA EXTRACTION FOR ALBUM CLUSTERING ---
def get_image_metadata(path: str) -> dict:
    """Extracts date and GPS info from image EXIF data."""
    try:
        img = Image.open(path)
        exif = img.getexif()
        data = {}
        for k, v in exif.items():
            tag = TAGS.get(k, k)
            data[tag] = v
        return {
            "date": data.get("DateTimeOriginal", "Unknown"),
            "gps": data.get("GPSInfo", "Unknown")
        }
    except Exception:
        return {"date": "Unknown", "gps": "Unknown"}

async def create_event(session: AsyncSession, data: EventCreate, studio_id: str):
    stmt = select(Event).where(Event.event_name == data.event_name, Event.studio_id == studio_id)
    result = await session.scalars(stmt)
    if result.first():
        raise HTTPException(status_code=400, detail="An event with this name already exists for your studio")
    
    event_uuid = str(uuid.uuid4())
    qr_code_data = generate_qr_base64(event_uuid)
    
    event = Event(
        event_id=event_uuid,
        studio_id=studio_id,
        event_name=data.event_name,
        event_type=data.event_type,
        event_date=data.event_date,
        event_time=data.event_time,
        owner_name=data.owner_name,
        qr_code=qr_code_data
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event

async def get_studio_events(session: AsyncSession, studio_id: str):
    stmt = select(Event).where(Event.studio_id == studio_id)
    events = await session.scalars(stmt)
    return events.all()

async def get_event_by_id(session: AsyncSession, event_id: str):
    stmt = select(Event).where(Event.event_id == event_id)
    result = await session.scalars(stmt)
    event = result.first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event