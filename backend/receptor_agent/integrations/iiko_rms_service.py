"""
Service layer for iiko RMS integration
Handles database operations, data synchronization, and business logic for RMS integration
"""

import os
import logging
import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError
from fuzzywuzzy import fuzz

from .iiko_rms_client import IikoRmsClient, get_iiko_rms_client, IikoRmsAPIError
from .iiko_rms_models import (
    IikoRmsCredentials, IikoRmsProduct, IikoRmsGroup, IikoRmsSyncStatus, IikoRmsMapping,
    IikoRmsConnectionStatus,
    IIKO_RMS_CREDENTIALS_COLLECTION, IIKO_RMS_PRODUCTS_COLLECTION,
    IIKO_RMS_GROUPS_COLLECTION, IIKO_RMS_SYNC_STATUS_COLLECTION, IIKO_RMS_MAPPINGS_COLLECTION,
    IIKO_RMS_PRODUCTS_INDEXES, IIKO_RMS_GROUPS_INDEXES, 
    IIKO_RMS_CREDENTIALS_INDEXES, IIKO_RMS_SYNC_STATUS_INDEXES, IIKO_RMS_MAPPINGS_INDEXES
)

logger = logging.getLogger(__name__)

class IikoRmsService:
    """Service for managing iiko RMS integration data and operations"""
    
    def __init__(self):
        # Get MongoDB connection
        mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
        db_name = os.getenv('DB_NAME', 'receptor_pro')
        
        self.client = MongoClient(mongo_url)
        self.db = self.client[db_name.strip('"')]
        
        # Initialize collections
        self.credentials: Collection = self.db[IIKO_RMS_CREDENTIALS_COLLECTION]
        self.products: Collection = self.db[IIKO_RMS_PRODUCTS_COLLECTION]
        self.groups: Collection = self.db[IIKO_RMS_GROUPS_COLLECTION]
        self.sync_status: Collection = self.db[IIKO_RMS_SYNC_STATUS_COLLECTION]
        self.mappings: Collection = self.db[IIKO_RMS_MAPPINGS_COLLECTION]
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            # Products indexes
            for index in IIKO_RMS_PRODUCTS_INDEXES:
                self.products.create_index(index["keys"], name=index["name"])
            
            # Groups indexes
            for index in IIKO_RMS_GROUPS_INDEXES:
                self.groups.create_index(index["keys"], name=index["name"])
            
            # Credentials indexes
            for index in IIKO_RMS_CREDENTIALS_INDEXES:
                self.credentials.create_index(index["keys"], name=index["name"])
            
            # Sync status indexes
            for index in IIKO_RMS_SYNC_STATUS_INDEXES:
                self.sync_status.create_index(index["keys"], name=index["name"])
            
            # Mappings indexes
            for index in IIKO_RMS_MAPPINGS_INDEXES:
                self.mappings.create_index(index["keys"], name=index["name"])
            
            logger.info("RMS database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating RMS indexes: {str(e)}")
    
    def connect_rms(self, host: str, login: str, password: str, 
                   user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Connect to iiko RMS server and store credentials
        Returns connection status and organization information
        """
        try:
            # Create RMS client and test connection
            rms_client = IikoRmsClient(host, login, password)
            
            # Test authentication
            session_key = rms_client.authenticate()
            
            # Get organizations
            organizations = rms_client.get_organizations()
            
            # Store/update credentials
            credentials = IikoRmsCredentials(
                user_id=user_id,
                host=host,
                login=login,
                password=password,  # In production, should encrypt this
                status=IikoRmsConnectionStatus.CONNECTED,
                last_connection=datetime.now(timezone.utc),
                session_key=session_key,
                session_expires_at=datetime.now(timezone.utc) + timedelta(hours=2)
            )
            
            # Upsert credentials using update_one with $set to avoid _id conflicts
            query = {"user_id": user_id} if user_id else {"host": host, "login": login}
            credentials_data = credentials.model_dump(by_alias=True, exclude={"_id"})
            self.credentials.update_one(
                query,
                {"$set": credentials_data},
                upsert=True
            )
            
            logger.info(f"Successfully connected to iiko RMS: {host}")
            
            return {
                "status": "connected",
                "host": host,
                "organizations": organizations,
                "session_expires_at": credentials.session_expires_at.isoformat()
            }
            
        except Exception as e:
            # Store failed connection attempt
            try:
                credentials = IikoRmsCredentials(
                    user_id=user_id,
                    host=host,
                    login=login,
                    password=password,
                    status=IikoRmsConnectionStatus.ERROR
                )
                
                query = {"user_id": user_id} if user_id else {"host": host, "login": login}
                credentials_data = credentials.model_dump(by_alias=True, exclude={"_id"})
                self.credentials.replace_one(
                    query,
                    credentials_data,
                    upsert=True
                )
            except:
                pass
                
            logger.error(f"Failed to connect to iiko RMS {host}: {str(e)}")
            raise IikoRmsAPIError(f"Failed to connect: {str(e)}")
    
    def select_rms_organization(self, organization_id: str, 
                              user_id: Optional[str] = None) -> Dict[str, Any]:
        """Select organization for RMS operations"""
        try:
            # Find credentials record
            query = {"user_id": user_id} if user_id else {}
            if not user_id:
                # Find the most recent connection
                credentials_record = self.credentials.find_one(
                    {"status": IikoRmsConnectionStatus.CONNECTED},
                    sort=[("last_connection", DESCENDING)]
                )
            else:
                credentials_record = self.credentials.find_one(query)
            
            if not credentials_record:
                raise IikoRmsAPIError("No active RMS connection found. Please connect first.")
            
            # Get RMS client and verify organization exists
            rms_client = IikoRmsClient(
                credentials_record["host"],
                credentials_record["login"], 
                credentials_record["password"]
            )
            
            organizations = rms_client.get_organizations()
            selected_org = next((org for org in organizations if org["id"] == organization_id), None)
            
            if not selected_org:
                raise IikoRmsAPIError(f"Organization {organization_id} not found")
            
            # Update credentials with selected organization
            self.credentials.update_one(
                {"_id": credentials_record["_id"]},
                {
                    "$set": {
                        "organization_id": organization_id,
                        "organization_name": selected_org["name"],
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            logger.info(f"Selected RMS organization: {selected_org['name']} ({organization_id})")
            
            return {
                "status": "selected",
                "organization": selected_org
            }
            
        except Exception as e:
            logger.error(f"Error selecting RMS organization: {str(e)}")
            raise IikoRmsAPIError(f"Failed to select organization: {str(e)}")
    
    def sync_rms_nomenclature(self, organization_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Synchronize nomenclature from iiko RMS server
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
                        "sync_id": str(running_sync["_id"]),
                        "started_at": running_sync["started_at"]
                    }
            
            # Get RMS client from credentials
            rms_client = self._get_rms_client_for_org(organization_id)
            
            # Create sync status record
            sync_record = IikoRmsSyncStatus(
                organization_id=organization_id,
                sync_type="nomenclature",
                status="running",
                host=rms_client.host
            )
            
            result = self.sync_status.insert_one(sync_record.model_dump(by_alias=True))
            sync_id = str(result.inserted_id)
            
            logger.info(f"Starting RMS nomenclature sync for organization {organization_id}")
            
            # Fetch nomenclature from RMS
            nomenclature = rms_client.fetch_nomenclature(organization_id)
            
            stats = {
                "products_processed": 0,
                "products_created": 0,
                "products_updated": 0,
                "products_deleted": 0,
                "groups_processed": 0,
                "groups_created": 0,
                "groups_updated": 0
            }
            
            # Process products
            active_product_ids = set()
            for product_data in nomenclature.get("products", []):
                try:
                    active_product_ids.add(product_data["id"])
                    
                    # Normalize and store product
                    normalized_product = self._normalize_rms_product(product_data, organization_id)
                    
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
                    logger.error(f"Error processing RMS product {product_data.get('id', 'unknown')}: {str(e)}")
            
            # Mark deleted products (products no longer in RMS)
            deleted_result = self.products.update_many(
                {
                    "organization_id": organization_id,
                    "_id": {"$nin": list(active_product_ids)},
                    "active": True
                },
                {
                    "$set": {
                        "active": False,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            stats["products_deleted"] = deleted_result.modified_count
            
            # Process groups
            active_group_ids = set()
            for group_data in nomenclature.get("groups", []):
                try:
                    active_group_ids.add(group_data["id"])
                    
                    group = IikoRmsGroup(
                        id=group_data["id"],
                        organization_id=organization_id,
                        name=group_data["name"],
                        parent_id=group_data.get("parent_id"),
                        active=group_data.get("active", True)
                    )
                    
                    existing = self.groups.find_one({"_id": group_data["id"]})
                    if existing:
                        self.groups.replace_one(
                            {"_id": group_data["id"]},
                            group.model_dump(by_alias=True)
                        )
                        stats["groups_updated"] += 1
                    else:
                        self.groups.insert_one(group.model_dump(by_alias=True))
                        stats["groups_created"] += 1
                    
                    stats["groups_processed"] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing RMS group {group_data.get('id', 'unknown')}: {str(e)}")
            
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
            
            # Generate auto-mappings
            self._generate_auto_mappings(organization_id)
            
            logger.info(f"RMS nomenclature sync completed. Stats: {stats}")
            
            return {
                "status": "completed",
                "sync_id": sync_id,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error syncing RMS nomenclature: {str(e)}")
            
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
            
            raise IikoRmsAPIError(f"Failed to sync RMS nomenclature: {str(e)}")
    
    def _normalize_rms_product(self, product_data: Dict[str, Any], organization_id: str) -> IikoRmsProduct:
        """Normalize RMS product data for storage"""
        
        # Normalize name for search
        name_normalized = re.sub(r'[^\w\s]', '', product_data["name"].lower())
        name_normalized = ' '.join(name_normalized.split())
        
        # Get group name if available
        group_name = None
        if product_data.get("group_id"):
            group_record = self.groups.find_one({"_id": product_data["group_id"]})
            if group_record:
                group_name = group_record["name"]
        
        # Create product model
        product = IikoRmsProduct(
            id=product_data["id"],
            organization_id=organization_id,
            name=product_data["name"],
            name_normalized=name_normalized,
            article=product_data.get("article"),
            group_id=product_data.get("group_id"),
            group_name=group_name,
            unit=product_data["unit"],
            unit_coefficient=product_data["unit_coefficient"],
            price=product_data.get("price"),
            price_per_unit=product_data.get("price_per_unit"),
            active=product_data.get("active", True),
            description=product_data.get("description"),
            barcode=product_data.get("barcode"),
            product_type=product_data.get("type", "product")
        )
        
        return product
    
    def search_rms_products(self, organization_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search RMS products in organization with intelligent matching
        Returns matching products with match scores
        """
        try:
            # Prepare search pipeline with multiple matching strategies
            pipeline = [
                {
                    "$match": {
                        "organization_id": organization_id,
                        "active": True,
                        "$or": [
                            {"name": {"$regex": re.escape(query), "$options": "i"}},
                            {"name_normalized": {"$regex": re.escape(query.lower()), "$options": "i"}},
                            {"article": {"$regex": re.escape(query), "$options": "i"}}
                        ]
                    }
                },
                {
                    "$addFields": {
                        "match_score": {
                            "$cond": {
                                # Exact name match
                                "if": {"$eq": [{"$toLower": "$name"}, query.lower()]},
                                "then": 1.0,
                                "else": {
                                    "$cond": {
                                        # Exact article match
                                        "if": {"$eq": [{"$toLower": "$article"}, query.lower()]},
                                        "then": 0.95,
                                        "else": {
                                            "$cond": {
                                                # Name starts with query
                                                "if": {"$regexMatch": {"input": "$name", "regex": f"^{re.escape(query)}", "options": "i"}},
                                                "then": 0.9,
                                                "else": {
                                                    "$cond": {
                                                        # Name contains query
                                                        "if": {"$regexMatch": {"input": "$name", "regex": re.escape(query), "options": "i"}},
                                                        "then": 0.7,
                                                        "else": 0.5
                                                    }
                                                }
                                            }
                                        }
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
            
            # Enhance with fuzzy matching for better results
            enhanced_results = []
            for result in results:
                # Calculate fuzzy match score for name
                fuzzy_score = fuzz.ratio(query.lower(), result["name"].lower()) / 100.0
                
                # Use the better score
                final_score = max(result.get("match_score", 0.0), fuzzy_score)
                
                product = {
                    "sku_id": result["_id"],
                    "name": result["name"],
                    "article": result.get("article", ""),
                    "unit": result["unit"],
                    "price_per_unit": result.get("price_per_unit", 0.0),
                    "currency": "RUB",
                    "asOf": result.get("synced_at", datetime.now(timezone.utc)).strftime("%Y-%m-%d"),
                    "match_score": final_score,
                    "group_name": result.get("group_name"),
                    "source": "iiko_rms",
                    "product_type": result.get("product_type", "product"),
                    "active": result.get("active", True)
                }
                enhanced_results.append(product)
            
            # Sort by final match score
            enhanced_results.sort(key=lambda x: x["match_score"], reverse=True)
            
            return enhanced_results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching RMS products: {str(e)}")
            return []
    
    def _get_rms_client_for_org(self, organization_id: str) -> IikoRmsClient:
        """Get RMS client for specific organization"""
        # Find credentials for organization
        credentials_record = self.credentials.find_one({
            "organization_id": organization_id,
            "status": IikoRmsConnectionStatus.CONNECTED
        })
        
        if not credentials_record:
            # Try to find any active connection
            credentials_record = self.credentials.find_one({
                "status": IikoRmsConnectionStatus.CONNECTED
            }, sort=[("last_connection", DESCENDING)])
        
        if not credentials_record:
            raise IikoRmsAPIError("No active RMS connection found")
        
        return IikoRmsClient(
            credentials_record["host"],
            credentials_record["login"],
            credentials_record["password"]
        )
    
    def _generate_auto_mappings(self, organization_id: str):
        """Generate automatic mappings for common ingredients"""
        try:
            # Load anchors map for synonym matching
            anchors_file = "/app/backend/data/anchors_map.json"
            anchors_map = {}
            
            if os.path.exists(anchors_file):
                import json
                with open(anchors_file, 'r', encoding='utf-8') as f:
                    anchors_map = json.load(f)
            
            # Get all RMS products
            rms_products = list(self.products.find({
                "organization_id": organization_id,
                "active": True
            }))
            
            # Generate mappings for each product
            mappings_created = 0
            
            for product in rms_products:
                try:
                    # Check if mapping already exists
                    existing = self.mappings.find_one({
                        "rms_product_id": product["_id"]
                    })
                    
                    if existing:
                        continue
                    
                    # Find best matching ingredient name from anchors
                    best_match = None
                    best_score = 0.0
                    
                    product_name = product["name"].lower()
                    
                    # Check anchors map
                    for canonical_name, synonyms in anchors_map.items():
                        # Check exact match
                        if product_name in [s.lower() for s in synonyms]:
                            best_match = canonical_name
                            best_score = 1.0
                            break
                        
                        # Check fuzzy match
                        for synonym in synonyms:
                            score = fuzz.ratio(product_name, synonym.lower()) / 100.0
                            if score > best_score and score >= 0.85:
                                best_match = canonical_name
                                best_score = score
                    
                    # Create mapping if good match found
                    if best_match and best_score >= 0.85:
                        mapping = IikoRmsMapping(
                            ingredient_name=best_match,
                            ingredient_name_normalized=best_match.lower(),
                            rms_product_id=product["_id"],
                            rms_product_name=product["name"],
                            rms_article=product.get("article"),
                            mapping_type="auto",
                            match_score=best_score,
                            approved=best_score >= 0.95  # Auto-approve high confidence matches
                        )
                        
                        self.mappings.insert_one(mapping.model_dump(by_alias=True))
                        mappings_created += 1
                        
                except Exception as e:
                    logger.warning(f"Error creating auto-mapping for product {product['name']}: {str(e)}")
                    continue
            
            logger.info(f"Generated {mappings_created} automatic RMS mappings")
            
        except Exception as e:
            logger.error(f"Error generating auto-mappings: {str(e)}")
    
    def get_rms_connection_status(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get RMS connection status"""
        try:
            query = {"user_id": user_id} if user_id else {}
            credentials_record = self.credentials.find_one(
                query,
                sort=[("last_connection", DESCENDING)]
            )
            
            if not credentials_record:
                return {"status": "not_connected"}
            
            return {
                "status": credentials_record["status"],
                "host": credentials_record["host"],
                "login": credentials_record["login"][:3] + "***",
                "organization_id": credentials_record.get("organization_id"),
                "organization_name": credentials_record.get("organization_name"),
                "last_connection": credentials_record.get("last_connection"),
                "session_expires_at": credentials_record.get("session_expires_at")
            }
            
        except Exception as e:
            logger.error(f"Error getting RMS connection status: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def get_rms_sync_status(self, organization_id: str) -> Dict[str, Any]:
        """Get latest RMS sync status for organization"""
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
                    "host": sync_record.get("host"),
                    "stats": {
                        "products_processed": sync_record.get("products_processed", 0),
                        "products_created": sync_record.get("products_created", 0),
                        "products_updated": sync_record.get("products_updated", 0),
                        "products_deleted": sync_record.get("products_deleted", 0),
                        "groups_processed": sync_record.get("groups_processed", 0),
                        "groups_created": sync_record.get("groups_created", 0),
                        "groups_updated": sync_record.get("groups_updated", 0)
                    }
                }
            
            return {"status": "never_synced"}
            
        except Exception as e:
            logger.error(f"Error getting RMS sync status: {str(e)}")
            return {"status": "error", "error": str(e)}

# Global RMS service instance
_iiko_rms_service: Optional[IikoRmsService] = None

def get_iiko_rms_service() -> IikoRmsService:
    """Get or create global IikoRmsService instance"""
    global _iiko_rms_service
    
    if _iiko_rms_service is None:
        _iiko_rms_service = IikoRmsService()
    
    return _iiko_rms_service