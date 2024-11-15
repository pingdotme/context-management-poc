from pydantic import BaseModel, Field
from typing import Optional, List, Set
from datetime import datetime
from enum import Enum

class MeetingCategory(str, Enum):
    API = "api"
    SECURITY = "security"
    PLANNING = "planning"
    REVIEW = "review"
    OTHER = "other"

class MeetingInput(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    meeting_text: str = Field(..., min_length=1, max_length=10000)
    categories: Optional[List[MeetingCategory]] = Field(
        default_factory=list,
        description="Meeting categories"
    )

class MeetingDetails(BaseModel):
    meeting_id: str
    text: str
    timestamp: str
    categories: List[MeetingCategory] = Field(default_factory=list)
    similarity_score: Optional[float] = None

class MeetingSummary(BaseModel):
    summary: str
    context_used: List[MeetingDetails] = Field(
        default_factory=list,
        description="Related historical context with similarity scores"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Processing timestamp"
    )
    context_count: int = Field(
        default=0,
        description="Number of related context items found"
    )

class MeetingHistory(BaseModel):
    meetings: List[MeetingDetails]
    total: int
    skip: int
    limit: int
    filtered_total: Optional[int] = None 