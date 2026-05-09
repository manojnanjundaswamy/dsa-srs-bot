from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from task_engine.database import get_db
from task_engine.models import Interaction
from task_engine.schemas import InteractionCreate, InteractionResponse
from task_engine.asset_helpers import log_interaction

router = APIRouter(prefix="/api", tags=["interactions"])


@router.post("/interactions", response_model=InteractionResponse, status_code=201)
def create_interaction(body: InteractionCreate, db: Session = Depends(get_db)):
    """Log any user event (review, question, button tap, feedback)."""
    interaction = log_interaction(
        user_id=body.user_id,
        event_type=body.event_type,
        event_data=body.event_data,
        asset_id=body.asset_id,
        record_key=body.record_key,
        db=db,
    )
    return interaction


@router.get("/users/{user_id}/interactions", response_model=List[InteractionResponse])
def list_user_interactions(
    user_id: str,
    asset_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """Return a user's interaction history, latest first."""
    q = db.query(Interaction).filter(Interaction.user_id == user_id)
    if asset_id:
        q = q.filter(Interaction.asset_id == asset_id)
    if event_type:
        q = q.filter(Interaction.event_type == event_type)
    return q.order_by(Interaction.created_at.desc()).limit(limit).all()
