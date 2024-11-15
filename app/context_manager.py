from typing import List, Optional, Set
import chromadb
from chromadb.config import Settings
import logging
from datetime import datetime
import hashlib
from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path
from .models import MeetingDetails, MeetingCategory

logger = logging.getLogger(__name__)

class ContextManager:
    def __init__(self):
        self.data_dir = Path("data/vector_store")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB with modern settings
        self.client = chromadb.PersistentClient(path=str(self.data_dir))
        
        # Initialize the sentence transformer model
        try:
            self.embedding_model = SentenceTransformer('BAAI/bge-small-en-v1.5')
            logger.info("Successfully initialized sentence transformer model")
        except Exception as e:
            logger.error(f"Error initializing sentence transformer: {str(e)}")
            raise
        
    def _get_collection(self, user_id: str):
        """Get or create a collection for the user"""
        collection_name = f"user_{user_id}_meetings"
        try:
            # Try to get existing collection
            return self.client.get_collection(name=collection_name)
        except Exception as e:
            logger.info(f"Creating new collection for user {user_id}")
            # Create new collection with embedding function
            return self.client.create_collection(
                name=collection_name,
                metadata={"user_id": user_id},
                embedding_function=self.embedding_model.encode
            )
    
    def _truncate_text(self, text: str, max_length: int = 500) -> str:
        """Truncate text to max_length and add ellipsis if needed"""
        return text[:max_length] + '...' if len(text) > max_length else text
        
    def _deduplicate_context(self, context: List[str]) -> List[str]:
        """Remove duplicates while preserving order"""
        seen: Set[str] = set()
        return [x for x in context if not (x in seen or seen.add(x))]
        
    def get_relevant_context(self, user_id: str, current_text: str, n_results: int = 3) -> List[MeetingDetails]:
        """Retrieve relevant meeting history with similarity scores and categories"""
        try:
            collection = self._get_collection(user_id)
            
            if collection.count() == 0:
                return []
            
            # Query with supported include fields
            results = collection.query(
                query_texts=[current_text],
                n_results=min(n_results, collection.count()),
                include=["documents", "metadatas", "distances"]
            )
            
            context = []
            for i in range(len(results['documents'][0])):
                metadata = results['metadatas'][0][i]
                
                # Convert categories string back to list
                categories_str = metadata.get('categories', MeetingCategory.OTHER.value)
                meeting_categories = [
                    MeetingCategory(cat.strip()) 
                    for cat in categories_str.split(',')
                ] if categories_str else [MeetingCategory.OTHER]
                
                # Calculate similarity score
                similarity_score = 1 - results['distances'][0][i]
                
                # Use stored meeting ID from metadata
                meeting_id = metadata.get('meeting_id', f"unknown_meeting_{i}")
                
                context.append(MeetingDetails(
                    meeting_id=meeting_id,
                    text=self._truncate_text(results['documents'][0][i]),
                    timestamp=metadata['timestamp'],
                    categories=meeting_categories,
                    similarity_score=round(similarity_score, 3)
                ))
            
            # Log the found context
            logger.info(f"Found {len(context)} relevant meetings for context")
            for item in context:
                logger.debug(f"Context item: {item.meeting_id} - {item.text[:50]}... (score: {item.similarity_score})")
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}", exc_info=True)
            return []

    def _categorize_meeting(self, text: str) -> List[MeetingCategory]:
        """Automatically categorize meeting based on content"""
        text_lower = text.lower()
        categories = set()
        
        if any(word in text_lower for word in ['api', 'endpoint', 'rest']):
            categories.add(MeetingCategory.API)
        if any(word in text_lower for word in ['security', 'auth', 'oauth']):
            categories.add(MeetingCategory.SECURITY)
        if any(word in text_lower for word in ['plan', 'roadmap', 'timeline']):
            categories.add(MeetingCategory.PLANNING)
        if any(word in text_lower for word in ['review', 'assess', 'evaluate']):
            categories.add(MeetingCategory.REVIEW)
        
        return list(categories) if categories else [MeetingCategory.OTHER]

    def get_meeting_history(
        self,
        user_id: str,
        limit: int = 10,
        skip: int = 0,
        search_text: Optional[str] = None,
        categories: Optional[List[MeetingCategory]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> tuple[List[MeetingDetails], int]:
        """Get filtered and paginated meeting history"""
        try:
            collection = self._get_collection(user_id)
            
            # Get all meetings
            results = collection.get(
                include=["documents", "metadatas"]
            )
            
            # Convert to MeetingDetails objects
            meetings = []
            for i in range(len(results['ids'])):
                # Skip empty meetings
                if not results['documents'][i].strip():
                    continue
                    
                # Convert categories string back to list
                categories_str = results['metadatas'][i].get('categories', MeetingCategory.OTHER.value)
                meeting_categories = [
                    MeetingCategory(cat.strip()) 
                    for cat in categories_str.split(',')
                ] if categories_str else [MeetingCategory.OTHER]
                    
                meeting = MeetingDetails(
                    meeting_id=results['ids'][i],
                    text=self._truncate_text(results['documents'][i]),
                    timestamp=results['metadatas'][i]['timestamp'],
                    categories=meeting_categories
                )
                
                # Apply filters
                if search_text and search_text.lower() not in meeting.text.lower():
                    continue
                if categories and not any(cat in meeting.categories for cat in categories):
                    continue
                if start_date and meeting.timestamp < start_date:
                    continue
                if end_date and meeting.timestamp > end_date:
                    continue
                    
                meetings.append(meeting)
            
            # Sort by timestamp (newest first)
            meetings.sort(key=lambda x: x.timestamp, reverse=True)
            
            total = len(meetings)
            
            # Apply pagination
            meetings = meetings[skip:skip + limit]
            
            return meetings, total
            
        except Exception as e:
            logger.error(f"Error retrieving meeting history: {str(e)}")
            return [], 0

    def store_meeting(self, user_id: str, meeting_text: str, categories: Optional[List[MeetingCategory]] = None) -> bool:
        """Store a meeting with categories and duplicate detection"""
        try:
            if not meeting_text.strip():
                logger.error("Attempted to store empty meeting text")
                return False
                
            collection = self._get_collection(user_id)
            
            # Clean and truncate text first
            meeting_text = self._truncate_text(meeting_text.strip(), max_length=1000)
            
            # Generate content hash
            content_hash = hashlib.md5(meeting_text.encode()).hexdigest()
            
            # Create meeting ID first
            meeting_id = f"meeting_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{content_hash[:8]}"
            
            # Check for exact duplicates using content hash
            existing_meetings = collection.get()
            for metadata in existing_meetings['metadatas']:
                if metadata.get('hash') == content_hash:
                    logger.info(f"Skipping duplicate content (identical hash)")
                    return True
            
            # Auto-categorize if categories not provided
            if not categories:
                categories = self._categorize_meeting(meeting_text)
            
            # Convert categories to string for ChromaDB metadata
            categories_str = ",".join(cat.value for cat in categories)
            
            # Add to collection with string metadata
            collection.add(
                documents=[meeting_text],
                metadatas=[{
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "categories": categories_str,
                    "length": len(meeting_text),
                    "hash": content_hash,
                    "meeting_id": meeting_id  # Store the meeting ID in metadata
                }],
                ids=[meeting_id]  # Use same ID for ChromaDB document
            )
            
            logger.info(f"Successfully stored meeting {meeting_id} for user {user_id} with categories: {categories_str}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing meeting: {str(e)}")
            return False

    def delete_meeting(self, user_id: str, meeting_id: str) -> bool:
        """Delete a specific meeting"""
        try:
            collection = self._get_collection(user_id)
            collection.delete(ids=[meeting_id])
            logger.info(f"Deleted meeting {meeting_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting meeting: {str(e)}")
            return False