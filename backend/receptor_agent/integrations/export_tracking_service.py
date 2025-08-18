"""
Export Wizard v1: Export Tracking Service
Tracks export history, audit logs, and validation integration
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from bson import ObjectId

logger = logging.getLogger(__name__)


class ExportTrackingService:
    """Service for tracking export history and audit logs"""
    
    def __init__(self):
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/receptor_dev')
        self.client = MongoClient(mongo_url)
        self.db = self.client.get_default_database()
        self.exports = self.db.export_history
        self.audit_logs = self.db.export_audit
        
        # Create indexes
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create necessary database indexes"""
        try:
            # Export history indexes
            self.exports.create_index([("organization_id", 1), ("techcard_id", 1), ("timestamp", -1)])
            self.exports.create_index([("user_email", 1), ("timestamp", -1)])
            
            # Audit log indexes  
            self.audit_logs.create_index([("timestamp", -1)])
            self.audit_logs.create_index([("organization_id", 1), ("action", 1)])
            
            logger.info("Export tracking indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Failed to create export tracking indexes: {e}")
    
    def record_export(self, 
                     organization_id: str,
                     techcard_id: str, 
                     techcard_title: str,
                     user_email: str,
                     export_type: str = "iiko_xlsx",
                     ingredients_count: int = 0,
                     file_size_bytes: int = 0,
                     result: str = "success",
                     error_message: Optional[str] = None) -> Dict[str, Any]:
        """Record export attempt in history and audit log"""
        
        timestamp = datetime.now(timezone.utc)
        
        # Export history record (for "last export" display)
        export_record = {
            "organization_id": organization_id,
            "techcard_id": techcard_id,
            "techcard_title": techcard_title,
            "user_email": user_email,
            "export_type": export_type,
            "timestamp": timestamp,
            "ingredients_count": ingredients_count,
            "file_size_bytes": file_size_bytes,
            "result": result,  # success, failed, blocked
            "error_message": error_message
        }
        
        # Insert export record
        export_id = self.exports.insert_one(export_record).inserted_id
        
        # Audit log record (for analytics and compliance)
        audit_record = {
            "export_id": str(export_id),
            "organization_id": organization_id,
            "action": "techcard_export",
            "user_email": user_email,
            "timestamp": timestamp,
            "details": {
                "techcard_id": techcard_id,
                "techcard_title": techcard_title,
                "export_type": export_type,
                "ingredients_count": ingredients_count,
                "file_size_bytes": file_size_bytes,
                "result": result
            },
            "ip_address": None,  # Would be filled by API layer
            "user_agent": None   # Would be filled by API layer
        }
        
        if error_message:
            audit_record["details"]["error_message"] = error_message
        
        audit_id = self.audit_logs.insert_one(audit_record).inserted_id
        
        logger.info(f"Recorded export: {techcard_title} by {user_email} - {result}")
        
        return {
            "export_id": str(export_id),
            "audit_id": str(audit_id),
            "timestamp": timestamp.isoformat(),
            "result": result
        }
    
    def get_last_export(self, organization_id: str, techcard_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get last successful export for organization or specific techcard"""
        
        query = {
            "organization_id": organization_id,
            "result": "success"
        }
        
        if techcard_id:
            query["techcard_id"] = techcard_id
        
        last_export = self.exports.find_one(
            query,
            sort=[("timestamp", -1)]
        )
        
        if last_export:
            # Convert ObjectId to string
            last_export["_id"] = str(last_export["_id"])
            
            # Add human-readable timestamp
            timestamp = last_export["timestamp"]
            now = datetime.now(timezone.utc)
            
            # Calculate relative time
            diff = now - timestamp
            
            if diff.days == 0:
                if diff.seconds < 3600:  # Less than 1 hour
                    minutes = diff.seconds // 60
                    human_time = f"{minutes} минут назад" if minutes > 0 else "только что"
                else:  # Same day
                    hour = timestamp.strftime("%H:%M")
                    human_time = f"сегодня в {hour}"
            elif diff.days == 1:
                hour = timestamp.strftime("%H:%M") 
                human_time = f"вчера в {hour}"
            else:
                human_time = timestamp.strftime("%d.%m.%Y в %H:%M")
            
            last_export["human_time"] = human_time
            
        return last_export
    
    def get_export_history(self, organization_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent export history for organization"""
        
        exports = list(self.exports.find(
            {"organization_id": organization_id},
            sort=[("timestamp", -1)],
            limit=limit
        ))
        
        # Convert ObjectIds to strings
        for export in exports:
            export["_id"] = str(export["_id"])
        
        return exports
    
    def get_audit_logs(self, 
                      organization_id: Optional[str] = None,
                      user_email: Optional[str] = None,
                      hours_back: int = 24,
                      limit: int = 50) -> List[Dict[str, Any]]:
        """Get audit logs with optional filters"""
        
        query = {}
        
        if organization_id:
            query["organization_id"] = organization_id
            
        if user_email:
            query["user_email"] = user_email
        
        # Time filter
        if hours_back:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            query["timestamp"] = {"$gte": cutoff_time}
        
        logs = list(self.audit_logs.find(
            query,
            sort=[("timestamp", -1)],
            limit=limit
        ))
        
        # Convert ObjectIds to strings
        for log in logs:
            log["_id"] = str(log["_id"])
        
        return logs
    
    def export_stats(self, organization_id: str, days_back: int = 7) -> Dict[str, Any]:
        """Get export statistics for organization"""
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        pipeline = [
            {
                "$match": {
                    "organization_id": organization_id,
                    "timestamp": {"$gte": cutoff_time}
                }
            },
            {
                "$group": {
                    "_id": "$result",
                    "count": {"$sum": 1},
                    "total_ingredients": {"$sum": "$ingredients_count"},
                    "total_size_bytes": {"$sum": "$file_size_bytes"}
                }
            }
        ]
        
        stats = list(self.exports.aggregate(pipeline))
        
        # Format stats
        result_stats = {}
        for stat in stats:
            result_stats[stat["_id"]] = {
                "count": stat["count"],
                "total_ingredients": stat["total_ingredients"], 
                "total_size_bytes": stat["total_size_bytes"]
            }
        
        # Total exports
        total_exports = sum(stat["count"] for stat in result_stats.values())
        
        return {
            "period_days": days_back,
            "total_exports": total_exports,
            "by_result": result_stats,
            "success_rate": round(result_stats.get("success", {}).get("count", 0) / max(total_exports, 1) * 100, 1)
        }


# Global service instance
_export_tracking_service: Optional[ExportTrackingService] = None

def get_export_tracking_service() -> ExportTrackingService:
    """Get or create global ExportTrackingService instance"""
    global _export_tracking_service
    
    if _export_tracking_service is None:
        _export_tracking_service = ExportTrackingService()
    
    return _export_tracking_service