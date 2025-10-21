"""
Support database service for loading and managing WM support content.
"""
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.support_entry import SupportEntry
from ..config import get_settings

logger = logging.getLogger(__name__)


class SupportDBService:
    """Service for managing the WM support database."""
    
    def __init__(self):
        self.settings = get_settings()
        self._entries: List[SupportEntry] = []
        self._entries_by_id: Dict[str, SupportEntry] = {}
        self._entries_by_category: Dict[str, List[SupportEntry]] = {}
        self._last_loaded: Optional[datetime] = None
    
    def load_database(self) -> bool:
        """Load the support database from JSON file."""
        try:
            db_path = Path(self.settings.support_database_path)
            
            if not db_path.exists():
                logger.error(f"Support database file not found: {db_path}")
                return False
            
            with open(db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                logger.error("Support database must be a JSON array")
                return False
            
            # Clear existing data
            self._entries.clear()
            self._entries_by_id.clear()
            self._entries_by_category.clear()
            
            # Load entries
            for item in data:
                try:
                    entry = SupportEntry(**item)
                    self._entries.append(entry)
                    self._entries_by_id[entry.id] = entry
                    
                    if entry.category not in self._entries_by_category:
                        self._entries_by_category[entry.category] = []
                    self._entries_by_category[entry.category].append(entry)
                    
                except Exception as e:
                    logger.warning(f"Failed to load support entry: {item.get('id', 'unknown')} - {e}")
                    continue
            
            self._last_loaded = datetime.utcnow()
            logger.info(f"Loaded {len(self._entries)} support entries from {db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load support database: {e}")
            return False
    
    def get_all_entries(self) -> List[SupportEntry]:
        """Get all support entries."""
        return self._entries.copy()
    
    def get_entry_by_id(self, entry_id: str) -> Optional[SupportEntry]:
        """Get a support entry by ID."""
        return self._entries_by_id.get(entry_id)
    
    def get_entries_by_category(self, category: str) -> List[SupportEntry]:
        """Get all support entries for a specific category."""
        return self._entries_by_category.get(category, []).copy()
    
    def get_categories(self) -> List[str]:
        """Get all available categories."""
        return list(self._entries_by_category.keys())
    
    def search_entries(self, query: str, limit: int = 10) -> List[SupportEntry]:
        """Search support entries by keywords and content."""
        if not query or not query.strip():
            return []
        
        query_lower = query.lower().strip()
        # Split query into words for better matching
        query_words = [word.strip() for word in query_lower.split() if word.strip()]
        results = []
        
        for entry in self._entries:
            score = 0
            
            # Check title (exact match gets highest score)
            if query_lower in entry.title.lower():
                score += 5
            else:
                # Check for word matches in title
                title_lower = entry.title.lower()
                for word in query_words:
                    if word in title_lower:
                        score += 2
            
            # Check keywords (exact match gets high score)
            for keyword in entry.keywords:
                keyword_lower = keyword.lower()
                if query_lower in keyword_lower or keyword_lower in query_lower:
                    score += 4
                else:
                    # Check for word matches in keywords
                    for word in query_words:
                        if word in keyword_lower:
                            score += 2
            
            # Check content (word matches)
            content_lower = entry.content.lower()
            for word in query_words:
                if word in content_lower:
                    score += 1
            
            if score > 0:
                results.append((entry, score))
        
        # Sort by score (highest first) and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in results[:limit]]
    
    def get_entry_count(self) -> int:
        """Get the total number of support entries."""
        return len(self._entries)
    
    def is_loaded(self) -> bool:
        """Check if the database is loaded."""
        return len(self._entries) > 0 and self._last_loaded is not None
    
    def get_last_loaded_time(self) -> Optional[datetime]:
        """Get when the database was last loaded."""
        return self._last_loaded
    
    def validate_database(self) -> Dict[str, Any]:
        """Validate the support database and return validation results."""
        validation_results = {
            'is_valid': True,
            'total_entries': len(self._entries),
            'categories': {},
            'errors': [],
            'warnings': []
        }
        
        if not self._entries:
            validation_results['is_valid'] = False
            validation_results['errors'].append("No support entries loaded")
            return validation_results
        
        # Check categories
        for category, entries in self._entries_by_category.items():
            validation_results['categories'][category] = len(entries)
        
        # Check for duplicate IDs
        seen_ids = set()
        for entry in self._entries:
            if entry.id in seen_ids:
                validation_results['errors'].append(f"Duplicate ID found: {entry.id}")
                validation_results['is_valid'] = False
            seen_ids.add(entry.id)
        
        # Check for entries without URLs (warning)
        entries_without_urls = [e for e in self._entries if not e.url]
        if entries_without_urls:
            validation_results['warnings'].append(f"{len(entries_without_urls)} entries without URLs")
        
        return validation_results
    
    def initialize_database(self) -> bool:
        """Initialize the support database (load and validate)."""
        logger.info("Initializing support database...")
        
        if not self.load_database():
            return False
        
        validation_results = self.validate_database()
        
        if not validation_results['is_valid']:
            logger.error(f"Database validation failed: {validation_results['errors']}")
            return False
        
        if validation_results['warnings']:
            logger.warning(f"Database validation warnings: {validation_results['warnings']}")
        
        logger.info(f"Support database initialized successfully with {validation_results['total_entries']} entries")
        return True
