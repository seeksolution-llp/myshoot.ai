import json
import torch
import open_clip
import numpy as np
from fastapi import HTTPException
from app.match_result.models import MatchResult
from app.face_data.models import FaceData
from app.media.models import Media
from app.match_result.schemas import MatchResultCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Initialize CLIP model globally for Natural Language Search
clip_model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
clip_tokenizer = open_clip.get_tokenizer("ViT-B-32")

async def create_match_entry(session: AsyncSession, data: MatchResultCreate):
    # Validate face index context
    face_stmt = select(FaceData).where(FaceData.face_id == data.face_id)
    face_res = await session.scalars(face_stmt)
    if not face_res.first():
        raise HTTPException(status_code=404, detail="Face data reference profile not found")
        
    # Validate media asset context
    media_stmt = select(Media).where(Media.media_id == data.media_id)
    media_res = await session.scalars(media_stmt)
    if not media_res.first():
        raise HTTPException(status_code=404, detail="Media reference file target not found")

    match_entry = MatchResult(
        face_id=data.face_id,
        media_id=data.media_id,
        confidence_score=data.confidence_score
    )
    session.add(match_entry)
    await session.commit()
    await session.refresh(match_entry)
    return match_entry

async def get_matches_by_face(session: AsyncSession, face_id: str):
    """Retrieves all matched media entries linked to a specific user face fingerprint"""
    stmt = select(MatchResult).where(MatchResult.face_id == face_id)
    result = await session.execute(stmt)
    # Use result.scalars().all() to ensure the list is populated from the result buffer
    return result.scalars().all()

async def search_media_by_text(session: AsyncSession, event_id: str, query: str, top_k: int = 5):
    """Natural language search using CLIP to find specific photos (e.g., 'red hair')"""
    # 1. Fetch all media for the event that has a CLIP embedding
    stmt = select(Media).where(Media.event_id == event_id).where(Media.clip_embedding.is_not(None))
    media_records = (await session.scalars(stmt)).all()

    if not media_records:
        return []

    # 2. Process the text query into a vector
    text_tokens = clip_tokenizer([query])
    with torch.no_grad():
        text_feature = clip_model.encode_text(text_tokens)
        
    text_feature /= text_feature.norm(dim=-1, keepdim=True)
    text_vector = text_feature[0].cpu().numpy().astype("float32")

    results = []
    # 3. Compare the text vector against the media embeddings
    for media in media_records:
        media_emb = np.array(json.loads(media.clip_embedding), dtype="float32")
        
        # Calculate Cosine Similarity for text-to-image
        similarity = float(np.dot(text_vector, media_emb))
        
        if similarity >= 0.20:  # Threshold for CLIP text-to-image
            results.append({
                "media": media,
                "score": similarity
            })

    # 4. Sort and return top K results
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    return [res["media"] for res in results[:top_k]]