"""
Service layer for iikoCloud API integration
Handles database operations, data synchronization, and business logic
"""

import os
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError
import re

from app.core.config import settings
from app.core.database import db as central_db
from .iiko_client import IikoClient, get_iiko_client, IikoAPIError
from .iiko_models import (
    IikoToken, IikoProduct, IikoProductGroup, IikoSyncStatus,
    IikoTokenStatus, IikoProductSizePrice,
    IIKO_TOKENS_COLLECTION, IIKO_PRODUCTS_COLLECTION, 
    IIKO_GROUPS_COLLECTION, IIKO_SYNC_STATUS_COLLECTION,
    IIKO_PRODUCTS_INDEXES, IIKO_GROUPS_INDEXES, 
    IIKO_TOKENS_INDEXES, IIKO_SYNC_STATUS_INDEXES
)

logger = logging.getLogger(__name__)

class IikoService:
    """Service for managing iikoCloud integration data"""
    
    def __init__(self):
        # Use centralized database connection
        if central_db.db is None:
            central_db.connect()
        self.db = central_db.db
        
        # Initialize collections
        self.tokens: Collection = self.db[IIKO_TOKENS_COLLECTION]
        self.products: Collection = self.db[IIKO_PRODUCTS_COLLECTION]
        self.groups: Collection = self.db[IIKO_GROUPS_COLLECTION]
        self.sync_status: Collection = self.db[IIKO_SYNC_STATUS_COLLECTION]
        
        # Create indexes
        self._create_indexes()
        
        # Get iikoCloud client
        self.iiko_client = get_iiko_client()
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            # Products indexes
            for index in IIKO_PRODUCTS_INDEXES:
                self.products.create_index(index["keys"], name=index["name"])
            
            # Groups indexes  
            for index in IIKO_GROUPS_INDEXES:
                self.groups.create_index(index["keys"], name=index["name"])
            
            # Tokens indexes
            for index in IIKO_TOKENS_INDEXES:
                self.tokens.create_index(index["keys"], name=index["name"])
            
            # Sync status indexes
            for index in IIKO_SYNC_STATUS_INDEXES:
                self.sync_status.create_index(index["keys"], name=index["name"])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
    
    def connect_organization(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Connect to iikoCloud and get available organizations
        Returns organization list and token information
        """
        try:
            # Get access token
            token_info = self.iiko_client.get_access_token()
            
            # Get organizations
            organizations = self.iiko_client.list_organizations()
            
            # Store token information
            token_data = IikoToken(
                user_id=user_id,
                api_login=self.iiko_client.api_login,
                access_token="managed_by_client",  # Token is managed internally
                expires_at=datetime.fromisoformat(token_info["expires_at"].replace("Z", "+00:00")),
                status=IikoTokenStatus.ACTIVE
            )
            
            # Upsert token
            self.tokens.replace_one(
                {"user_id": user_id} if user_id else {"api_login": self.iiko_client.api_login},
                token_data.model_dump(by_alias=True),
                upsert=True
            )
            
            logger.info(f"Successfully connected to iikoCloud, found {len(organizations)} organizations")
            
            return {
                "status": "connected",
                "organizations": organizations,
                "token_expires_at": token_info["expires_at"]
            }
            
        except Exception as e:
            logger.error(f"Error connecting to iikoCloud: {str(e)}")
            raise IikoAPIError(f"Failed to connect: {str(e)}")
    
    def select_organization(self, organization_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Select organization for further operations
        Updates token record with selected organization
        """
        try:
            # Find token record
            query = {"user_id": user_id} if user_id else {"api_login": self.iiko_client.api_login}
            token_record = self.tokens.find_one(query)
            
            if not token_record:
                raise IikoAPIError("No active token found. Please connect first.")
            
            # Get organization details
            organizations = self.iiko_client.list_organizations()
            selected_org = next((org for org in organizations if org["id"] == organization_id), None)
            
            if not selected_org:
                raise IikoAPIError(f"Organization {organization_id} not found")
            
            # Update token record
            self.tokens.update_one(
                {"_id": token_record["_id"]},
                {
                    "$set": {
                        "organization_id": organization_id,
                        "organization_name": selected_org["name"],
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            logger.info(f"Selected organization: {selected_org['name']} ({organization_id})")
            
            return {
                "status": "selected",
                "organization": selected_org
            }
            
        except Exception as e:
            logger.error(f"Error selecting organization: {str(e)}")
            raise IikoAPIError(f"Failed to select organization: {str(e)}")
    
    def sync_nomenclature(self, organization_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Synchronize nomenclature from iikoCloud
        Updates products and groups in database
        """
        sync_id = None
        try:
            # Check if sync is already running
            if not force:
                running_sync = self.sync_status.find_one({
                    "organization_id": organization_id,
                    "sync_type": "nomenclature",
                    "status": "running"
                })
                if running_sync:
                    return {
                        "status": "already_running",
                        "sync_id": running_sync["_id"],
                        "started_at": running_sync["started_at"]
                    }
            
            # Create sync status record
            sync_record = IikoSyncStatus(
                organization_id=organization_id,
                sync_type="nomenclature",
                status="running"
            )
            
            result = self.sync_status.insert_one(sync_record.model_dump(by_alias=True))
            sync_id = result.inserted_id  # Keep as ObjectId for MongoDB queries
            
            logger.info(f"Starting nomenclature sync for organization {organization_id}")
            
            # Fetch nomenclature from iikoCloud
            nomenclature = self.iiko_client.fetch_nomenclature(organization_id)
            
            stats = {
                "products_processed": 0,
                "products_created": 0,
                "products_updated": 0,
                "products_deleted": 0
            }
            
            # Process products
            active_product_ids = set()
            for product_data in nomenclature.get("products", []):
                try:
                    active_product_ids.add(product_data["id"])
                    
                    # Normalize product data
                    normalized_product = self._normalize_product(product_data, organization_id)
                    
                    # Upsert product
                    existing = self.products.find_one({"_id": product_data["id"]})
                    if existing:
                        self.products.replace_one(
                            {"_id": product_data["id"]},
                            normalized_product.model_dump(by_alias=True)
                        )
                        stats["products_updated"] += 1
                    else:
                        self.products.insert_one(normalized_product.model_dump(by_alias=True))
                        stats["products_created"] += 1
                    
                    stats["products_processed"] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing product {product_data.get('id', 'unknown')}: {str(e)}")
            
            # Mark deleted products
            deleted_result = self.products.update_many(
                {
                    "organization_id": organization_id,
                    "_id": {"$nin": list(active_product_ids)},
                    "is_deleted": False
                },
                {
                    "$set": {
                        "is_deleted": True,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            stats["products_deleted"] = deleted_result.modified_count
            
            # Process groups
            for group_data in nomenclature.get("groups", []):
                try:
                    group = IikoProductGroup(
                        id=group_data["id"],
                        organization_id=organization_id,
                        name=group_data["name"],
                        parent_group=group_data.get("parent_group"),
                        is_deleted=group_data.get("is_deleted", False)
                    )
                    
                    self.groups.replace_one(
                        {"_id": group_data["id"]},
                        group.model_dump(by_alias=True),
                        upsert=True
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing group {group_data.get('id', 'unknown')}: {str(e)}")
            
            # Update sync status
            self.sync_status.update_one(
                {"_id": sync_id},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc),
                        **stats
                    }
                }
            )
            
            logger.info(f"Nomenclature sync completed. Stats: {stats}")
            
            return {
                "status": "completed",
                "sync_id": str(sync_id),
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error syncing nomenclature: {str(e)}")
            
            # Update sync status with error
            if sync_id:
                self.sync_status.update_one(
                    {"_id": sync_id},
                    {
                        "$set": {
                            "status": "failed",
                            "completed_at": datetime.now(timezone.utc),
                            "error_message": str(e)
                        }
                    }
                )
            
            raise IikoAPIError(f"Failed to sync nomenclature: {str(e)}")
    
    def _normalize_product(self, product_data: Dict[str, Any], organization_id: str) -> IikoProduct:
        """Normalize product data for storage"""
        
        # Normalize name for search
        name_normalized = re.sub(r'[^\w\s]', '', product_data["name"].lower())
        name_normalized = ' '.join(name_normalized.split())
        
        # Parse size prices
        size_prices = []
        for price_data in product_data.get("size_prices", []):
            size_price = IikoProductSizePrice(
                size_id=price_data.get("size_id"),
                price=price_data.get("price", 0.0)
            )
            size_prices.append(size_price)
        
        # Calculate price per unit (assuming first size price)
        price_per_unit = None
        if size_prices:
            price_per_unit = size_prices[0].price
        
        # Create product model
        product = IikoProduct(
            id=product_data["id"],
            organization_id=organization_id,
            name=product_data["name"],
            name_normalized=name_normalized,
            description=product_data.get("description"),
            group_id=product_data.get("group_id"),
            size_prices=size_prices,
            tags=product_data.get("tags", []),
            is_deleted=product_data.get("is_deleted", False),
            price_per_unit=price_per_unit
        )
        
        return product
    
    def search_products(self, organization_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search products in organization
        Returns matching products with match scores
        """
        try:
            # Prepare search pipeline
            pipeline = [
                {
                    "$match": {
                        "organization_id": organization_id,
                        "is_deleted": False,
                        "$or": [
                            {"name": {"$regex": query, "$options": "i"}},
                            {"name_normalized": {"$regex": query.lower(), "$options": "i"}},
                            {"article": {"$regex": query, "$options": "i"}}
                        ]
                    }
                },
                {
                    "$addFields": {
                        "match_score": {
                            "$cond": {
                                "if": {"$regexMatch": {"input": "$name", "regex": f"^{re.escape(query)}", "options": "i"}},
                                "then": 1.0,
                                "else": {
                                    "$cond": {
                                        "if": {"$regexMatch": {"input": "$name", "regex": re.escape(query), "options": "i"}},
                                        "then": 0.8,
                                        "else": 0.6
                                    }
                                }
                            }
                        }
                    }
                },
                {"$sort": {"match_score": -1, "name": 1}},
                {"$limit": limit}
            ]
            
            results = list(self.products.aggregate(pipeline))
            
            # Convert to response format
            products = []
            for result in results:
                product = {
                    "sku_id": result["_id"],
                    "name": result["name"],
                    "unit": result.get("unit", "pcs"),
                    "price_per_unit": result.get("price_per_unit", 0.0),
                    "currency": result.get("currency", "RUB"),
                    "asOf": result.get("synced_at", datetime.now(timezone.utc)).strftime("%Y-%m-%d"),
                    "match_score": result.get("match_score", 0.0),
                    "article": result.get("article"),
                    "group_name": result.get("group_name")
                }
                products.append(product)
            
            return products
            
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []
    
    def get_organizations(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get cached organizations or fetch from API"""
        try:
            # Try to get from token record first
            query = {"user_id": user_id} if user_id else {"api_login": self.iiko_client.api_login}
            token_record = self.tokens.find_one(query)
            
            if token_record and token_record.get("organization_id"):
                # Return selected organization
                org_data = {
                    "id": token_record["organization_id"],
                    "name": token_record.get("organization_name", "Unknown")
                }
                return [org_data]
            
            # Fetch from API
            return self.iiko_client.list_organizations()
            
        except Exception as e:
            logger.error(f"Error getting organizations: {str(e)}")
            return []
    
    def get_sync_status(self, organization_id: str) -> Dict[str, Any]:
        """Get latest sync status for organization"""
        try:
            sync_record = self.sync_status.find_one(
                {"organization_id": organization_id, "sync_type": "nomenclature"},
                sort=[("started_at", DESCENDING)]
            )
            
            if sync_record:
                return {
                    "sync_id": str(sync_record["_id"]),
                    "status": sync_record["status"],
                    "started_at": sync_record["started_at"],
                    "completed_at": sync_record.get("completed_at"),
                    "error_message": sync_record.get("error_message"),
                    "stats": {
                        "products_processed": sync_record.get("products_processed", 0),
                        "products_created": sync_record.get("products_created", 0),
                        "products_updated": sync_record.get("products_updated", 0),
                        "products_deleted": sync_record.get("products_deleted", 0)
                    }
                }
            
            return {"status": "never_synced"}
            
        except Exception as e:
            logger.error(f"Error getting sync status: {str(e)}")
            return {"status": "error", "error": str(e)}

# Global service instance
_iiko_service: Optional[IikoService] = None

def get_iiko_service() -> IikoService:
    """Get or create global IikoService instance"""
    global _iiko_service
    
    if _iiko_service is None:
        _iiko_service = IikoService()
    
    return _iiko_service