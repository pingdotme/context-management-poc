from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List
import logging
from datetime import datetime
from .context_manager import ContextManager
from .models import MeetingInput, MeetingDetails, MeetingSummary, MeetingHistory, MeetingCategory

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Meeting Assistant POC")

# Initialize context manager
context_manager = ContextManager()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.2.0"}

@app.post("/process-meeting", response_model=MeetingSummary)
async def process_meeting(meeting_input: MeetingInput):
    try:
        logger.info(f"Processing meeting for user: {meeting_input.user_id}")
        
        # Get relevant context first
        context = context_manager.get_relevant_context(
            meeting_input.user_id,
            meeting_input.meeting_text
        )
        
        # Store the new meeting
        stored = context_manager.store_meeting(
            meeting_input.user_id,
            meeting_input.meeting_text,
            meeting_input.categories
        )
        
        if not stored:
            raise HTTPException(
                status_code=500, 
                detail="Failed to store meeting in database"
            )
        
        # Create response message
        if context:
            summary = f"Successfully processed meeting with {len(context)} related historical items"
        else:
            summary = "Successfully processed meeting (no related context found)"
            
        return MeetingSummary(
            summary=summary,
            context_used=context,
            context_count=len(context),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error processing meeting: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/meetings/{user_id}/history", response_model=MeetingHistory)
async def get_meeting_history(
    user_id: str,
    limit: int = Query(default=10, le=100),
    skip: int = Query(default=0, ge=0),
    search_text: Optional[str] = None,
    categories: Optional[List[MeetingCategory]] = Query(default=None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get filtered and paginated meeting history"""
    try:
        meetings, total = context_manager.get_meeting_history(
            user_id=user_id,
            limit=limit,
            skip=skip,
            search_text=search_text,
            categories=categories,
            start_date=start_date,
            end_date=end_date
        )
        
        return MeetingHistory(
            meetings=meetings,
            total=total,
            skip=skip,
            limit=limit,
            filtered_total=len(meetings)
        )
    except Exception as e:
        logger.error(f"Error retrieving meeting history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/meetings/{user_id}/{meeting_id}")
async def delete_meeting(user_id: str, meeting_id: str):
    """Delete a specific meeting"""
    try:
        deleted = context_manager.delete_meeting(user_id, meeting_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return {"status": "success", "message": f"Meeting {meeting_id} deleted"}
    except Exception as e:
        logger.error(f"Error deleting meeting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))