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
    IikoRmsCredentials, IikoRmsProduct, IikoRmsGroup, IikoRmsSyncStatus, IikoRmsMapping, IikoRmsPrice,  # IK-03: Added IikoRmsPrice
    IikoRmsConnectionStatus,
    IIKO_RMS_CREDENTIALS_COLLECTION, IIKO_RMS_PRODUCTS_COLLECTION,
    IIKO_RMS_GROUPS_COLLECTION, IIKO_RMS_SYNC_STATUS_COLLECTION, IIKO_RMS_MAPPINGS_COLLECTION,
    IIKO_RMS_PRICES_COLLECTION,  # IK-03: Added prices collection
    IIKO_RMS_PRODUCTS_INDEXES, IIKO_RMS_GROUPS_INDEXES, 
    IIKO_RMS_CREDENTIALS_INDEXES, IIKO_RMS_SYNC_STATUS_INDEXES, IIKO_RMS_MAPPINGS_INDEXES,
    IIKO_RMS_PRICES_INDEXES  # IK-03: Added prices indexes
)

logger = logging.getLogger(__name__)

class IikoRmsService:
    """Service for managing iiko RMS integration data and operations"""
    
    def __init__(self):
        # Get MongoDB connection
        mongo_url = os.getenv('MONGODB_URI') or os.getenv('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
        db_name = os.getenv('DB_NAME', 'receptor_pro')
        
        self.client = MongoClient(mongo_url)
        self.db = self.client[db_name.strip('"')]
        
        # Initialize collections
        self.credentials: Collection = self.db[IIKO_RMS_CREDENTIALS_COLLECTION]
        self.products: Collection = self.db[IIKO_RMS_PRODUCTS_COLLECTION]
        self.groups: Collection = self.db[IIKO_RMS_GROUPS_COLLECTION]
        self.sync_status: Collection = self.db[IIKO_RMS_SYNC_STATUS_COLLECTION]
        self.mappings: Collection = self.db[IIKO_RMS_MAPPINGS_COLLECTION]
        self.prices: Collection = self.db[IIKO_RMS_PRICES_COLLECTION]  # IK-03: Prices collection
        
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
            
            # IK-03: Prices indexes
            for index in IIKO_RMS_PRICES_INDEXES:
                self.prices.create_index(index["keys"], name=index["name"])
            
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
            credentials_data = credentials.model_dump(by_alias=True, exclude={"id"})
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
                credentials_data = credentials.model_dump(by_alias=True, exclude={"id"})
                self.credentials.update_one(
                    query,
                    {"$set": credentials_data},
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
            # КРИТИЧЕСКИ ВАЖНО: всегда требовать user_id для изоляции пользователей
            if not user_id:
                return {"error": "user_id is required"}
                
            # Find credentials record for specific user
            query = {"user_id": user_id}
            credentials_record = self.credentials.find_one(
                query,
                sort=[("last_connection", DESCENDING)]
            )
            
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
            article=product_data.get("article"),  # Номенклатурный код (из 'num')
            quick_dial_code=product_data.get("quick_dial_code"),  # Код быстрого набора (из 'code')
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
    
    def search_rms_products_enhanced(self, organization_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Enhanced search for RMS products with RU-normalization and improved scoring
        P0: SKU Search (iiko) — 0-hit bugfix implementation
        """
        try:
            if not query.strip():
                return []
            
            # Normalize query for better matching
            normalized_query = self._normalize_ru_text(query.strip())
            
            # Get all active products for organization (remove hidden filters)
            products_cursor = self.products.find({
                "organization_id": organization_id,
                # Remove hidden filters - don't filter by price or active status
                # "active": True,  # Allow inactive products
                # "price_per_unit": {"$gt": 0}  # Allow products without price
            })
            
            products = list(products_cursor)
            logger.info(f"Found {len(products)} total products for enhanced search")
            
            if not products:
                return []
            
            matches = []
            
            # Enhanced matching with multiple strategies
            for product in products:
                product_name = product.get("name", "")
                if not product_name:
                    continue
                
                # Strategy 1: Normalized RU text matching
                normalized_product_name = self._normalize_ru_text(product_name)
                
                # Strategy 2: Multi-level scoring
                scores = []
                
                # Exact match
                if normalized_query.lower() == normalized_product_name.lower():
                    scores.append(1.0)
                
                # Substring match
                elif normalized_query.lower() in normalized_product_name.lower():
                    scores.append(0.95)
                elif normalized_product_name.lower() in normalized_query.lower():
                    scores.append(0.90)
                
                # Word-level matching
                query_words = normalized_query.lower().split()
                product_words = normalized_product_name.lower().split()
                
                word_matches = sum(1 for qw in query_words 
                                 if any(qw in pw or pw in qw for pw in product_words))
                
                if word_matches > 0:
                    word_score = min(0.85, 0.60 + (word_matches / len(query_words)) * 0.25)
                    scores.append(word_score)
                
                # Lemmatization-based matching for common ingredients
                lemmatized_score = self._lemmatized_match_score(normalized_query, normalized_product_name)
                if lemmatized_score > 0.60:
                    scores.append(lemmatized_score)
                
                # Use best score
                if scores:
                    best_score = max(scores)
                    
                    # Create result item
                    match_item = {
                        "_id": str(product["_id"]),
                        "sku_id": str(product["_id"]),
                        "name": product_name,
                        "article": product.get("article", ""),
                        "unit": product.get("unit", "г"),
                        "group_name": product.get("group_name", ""),
                        "price_per_unit": product.get("price_per_unit", 0.0),
                        "currency": "RUB",
                        "vat_pct": product.get("vat_pct", 0.0),
                        "asOf": product.get("updated_at", datetime.now(timezone.utc)).isoformat(),
                        "match_score": best_score,
                        "product_type": product.get("product_type", "product"),
                        "active": product.get("active", True)
                    }
                    
                    matches.append(match_item)
            
            # Sort by match score (descending) and return top results
            matches.sort(key=lambda x: x["match_score"], reverse=True)
            
            # Return top-5 candidates even with low scores (as per requirement)
            result = matches[:max(5, limit)]
            
            logger.info(f"Enhanced search for '{query}' returned {len(result)} matches")
            return result
            
        except Exception as e:
            logger.error(f"Enhanced RMS product search error: {str(e)}")
            return []
    
    def _normalize_ru_text(self, text: str) -> str:
        """
        Normalize Russian text for better matching
        P0: RU-нормализация (lower, ё→е, лемматизация)
        """
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower().strip()
        
        # Replace ё with е
        normalized = normalized.replace('ё', 'е')
        
        # Remove common noise words
        noise_words = ['свежий', 'свежая', 'свежее', 'домашний', 'домашняя', 'домашнее', 
                      'столовый', 'столовая', 'столовое', 'пищевой', 'пищевая', 'пищевое']
        words = normalized.split()
        words = [w for w in words if w not in noise_words]
        normalized = ' '.join(words)
        
        # Remove extra spaces
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _lemmatized_match_score(self, query: str, product_name: str) -> float:
        """
        Simple lemmatization-based matching for common Russian ingredients
        картоф → картофель, картошка
        """
        # Simple lemmatization rules for common ingredients
        lemma_rules = {
            'картоф': ['картофель', 'картошка', 'клубни'],
            'молок': ['молоко', 'молочный'],
            'яйц': ['яйцо', 'яйца', 'яичный'],
            'мяс': ['мясо', 'мясной'],
            'говяд': ['говядина', 'говяжий'],
            'свин': ['свинина', 'свиной'],
            'курин': ['курица', 'куриный'],
            'сметан': ['сметана', 'сметановый'],
            'творог': ['творог', 'творожный'],
            'сыр': ['сыр', 'сырный'],
            'масл': ['масло', 'масляный'],
            'лук': ['лук', 'луковый'],
            'морков': ['морковь', 'морковный'],
            'помидор': ['помидор', 'томат', 'томатный'],
            'огурц': ['огурец', 'огуречный'],
            'капуст': ['капуста', 'капустный'],
            'перец': ['перец', 'перечный'],
            'чеснок': ['чеснок', 'чесночный'],
            'петрушк': ['петрушка'],
            'укроп': ['укроп'],
            'базилик': ['базилик'],
            'соль': ['соль', 'солёный', 'соленый'],
            'сахар': ['сахар', 'сахарный']
        }
        
        query_lower = query.lower()
        product_lower = product_name.lower()
        
        # Check if query contains any lemma root
        for lemma_root, variants in lemma_rules.items():
            if lemma_root in query_lower:
                # Check if product name contains any variant
                if any(variant in product_lower for variant in variants):
                    return 0.85  # High confidence for lemmatized matches
                if lemma_root in product_lower:
                    return 0.80
        
        # Check reverse: if product contains lemma root and query contains variant
        for lemma_root, variants in lemma_rules.items():
            if lemma_root in product_lower:
                if any(variant in query_lower for variant in variants):
                    return 0.85
        
        return 0.0
    
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
    
    def search_rms_products_by_article(self, organization_id: str, article: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        FIX-A SRCH-02: Search products by exact article match
        
        Args:
            organization_id: Organization ID
            article: Article number to search for
            limit: Maximum results
            
        Returns:
            List of matching products
        """
        try:
            # Exact article match query
            pipeline = [
                {
                    "$match": {
                        "organization_id": organization_id,
                        "article": article  # Exact match
                    }
                },
                {"$sort": {"name": 1}},
                {"$limit": limit}
            ]
            
            results = list(self.products.aggregate(pipeline))
            
            enhanced_results = []
            for result in results:
                product = {
                    "sku_id": result["_id"],
                    "name": result["name"],
                    "article": result.get("article", ""),
                    "unit": result["unit"],
                    "price_per_unit": result.get("price_per_unit", 0.0),
                    "currency": "RUB",
                    "asOf": result.get("synced_at", datetime.now(timezone.utc)).strftime("%Y-%m-%d"),
                    "match_score": 1.0,  # Perfect match for exact article
                    "group_name": result.get("group_name"),
                    "source": "iiko_rms",
                    "product_type": result.get("product_type", "product"),
                    "active": result.get("active", True)
                }
                enhanced_results.append(product)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error searching RMS products by article: {str(e)}")
            return []
    
    def search_rms_products_by_id(self, organization_id: str, sku_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        FIX-A MAP-01: Search products by exact ID match for article lookup
        
        Args:
            organization_id: Organization ID
            sku_id: SKU ID to search for
            limit: Maximum results
            
        Returns:
            List of matching products
        """
        try:
            # Exact ID match query
            result = self.products.find_one({
                "organization_id": organization_id,
                "_id": sku_id
            })
            
            if not result:
                return []
            
            product = {
                "sku_id": result["_id"],
                "name": result["name"],
                "article": result.get("article", ""),
                "unit": result["unit"],
                "price_per_unit": result.get("price_per_unit", 0.0),
                "currency": "RUB",
                "asOf": result.get("synced_at", datetime.now(timezone.utc)).strftime("%Y-%m-%d"),
                "match_score": 1.0,  # Perfect match for exact ID
                "group_name": result.get("group_name"),
                "source": "iiko_rms",
                "product_type": result.get("product_type", "product"),
                "active": result.get("active", True)
            }
            
            return [product]
            
        except Exception as e:
            logger.error(f"Error searching RMS product by ID: {str(e)}")
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
    
    def disconnect_rms(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Disconnect from iiko RMS and clear stored credentials
        Implements "Забыть подключение" functionality
        """
        try:
            logger.info(f"Disconnecting iiko RMS for user: {user_id}")
            
            # КРИТИЧЕСКИ ВАЖНО: всегда требовать user_id для изоляции пользователей
            if not user_id:
                return {"status": "error", "message": "user_id is required"}
                
            query = {"user_id": user_id}
            
            # Update connection status to disconnected and clear session
            result = self.credentials.update_many(
                query,
                {
                    "$set": {
                        "status": IikoRmsConnectionStatus.DISCONNECTED,
                        "session_key": None,
                        "session_expires_at": None,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            logger.info(f"Disconnected {result.modified_count} RMS connections")
            
            return {
                "status": "disconnected",
                "connections_cleared": result.modified_count
            }
            
        except Exception as e:
            logger.error(f"Error disconnecting RMS: {str(e)}")
            raise IikoRmsAPIError(f"Failed to disconnect: {str(e)}")
    
    def restore_rms_connection(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Attempt to restore iiko RMS connection using stored credentials
        Used for sticky connection functionality
        """
        try:
            logger.info(f"🔍 DEBUG: Attempting to restore RMS connection for user: {user_id}")
            
            # КРИТИЧЕСКИ ВАЖНО: всегда требовать user_id для изоляции пользователей
            if not user_id:
                logger.warning("⚠️ DEBUG: No user_id provided for restore")
                return {"status": "no_stored_credentials"}
                
            # Find most recent connection for user
            query = {"user_id": user_id}
            credentials_record = self.credentials.find_one(
                query,
                sort=[("last_connection", DESCENDING)]
            )
            
            logger.info(f"🔍 DEBUG: Credentials found: {bool(credentials_record)}")
            if credentials_record:
                logger.info(f"🔍 DEBUG: Host: {credentials_record.get('host')}, Status: {credentials_record.get('status')}")
            
            if not credentials_record:
                logger.warning("⚠️ DEBUG: No credentials found in MongoDB")
                return {"status": "no_stored_credentials"}
            
            if credentials_record.get("status") == IikoRmsConnectionStatus.DISCONNECTED:
                return {"status": "manually_disconnected"}
            
            # Try to restore connection using stored credentials
            try:
                rms_client = IikoRmsClient(
                    credentials_record["host"],
                    credentials_record["login"], 
                    credentials_record["password"]
                )
                
                # Test connection by authenticating
                session_key = rms_client.authenticate()
                
                # Get organizations to verify connection is fully working
                organizations = rms_client.get_organizations()
                
                # Update credentials with new session
                self.credentials.update_one(
                    {"_id": credentials_record["_id"]},
                    {
                        "$set": {
                            "status": IikoRmsConnectionStatus.CONNECTED,
                            "session_key": session_key,
                            "session_expires_at": datetime.now(timezone.utc) + timedelta(hours=2),
                            "last_connection": datetime.now(timezone.utc),
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                
                logger.info("✅ RMS connection restored successfully")
                
                # CRITICAL FIX: Get sync status and products count
                org_id = credentials_record.get("organization_id", "default")
                sync_status_record = self.sync_status.find_one(
                    {"organization_id": org_id},
                    sort=[("started_at", DESCENDING)]
                )
                
                products_count = self.products.count_documents({"organization_id": org_id})
                
                return {
                    "status": "restored",
                    "host": credentials_record["host"],
                    "login": credentials_record["login"][:3] + "***",
                    "organization_id": org_id,
                    "organization_name": credentials_record.get("organization_name"),
                    "organizations": organizations,
                    "session_expires_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
                    "products_count": products_count,
                    "sync_status": sync_status_record["status"] if sync_status_record else "never_synced",
                    "last_sync": sync_status_record["completed_at"].isoformat() if sync_status_record and sync_status_record.get("completed_at") else None,
                    "last_connection": credentials_record.get("last_connection").isoformat() if credentials_record.get("last_connection") else None
                }
                
            except IikoRmsAPIError as api_error:
                # Handle specific API errors (401, 403, etc.)
                if "401" in str(api_error) or "403" in str(api_error):
                    # Mark as needs reconnection
                    self.credentials.update_one(
                        {"_id": credentials_record["_id"]},
                        {
                            "$set": {
                                "status": IikoRmsConnectionStatus.NEEDS_RECONNECTION,
                                "updated_at": datetime.now(timezone.utc)
                            }
                        }
                    )
                    
                    return {
                        "status": "needs_reconnection",
                        "error": "Authentication expired. Please reconnect.",
                        "host": credentials_record["host"],
                        "login": credentials_record["login"][:3] + "***"
                    }
                else:
                    # Other API errors
                    self.credentials.update_one(
                        {"_id": credentials_record["_id"]},
                        {
                            "$set": {
                                "status": IikoRmsConnectionStatus.ERROR,
                                "updated_at": datetime.now(timezone.utc)
                            }
                        }
                    )
                    
                    return {
                        "status": "connection_error",
                        "error": str(api_error),
                        "host": credentials_record["host"],
                        "login": credentials_record["login"][:3] + "***"
                    }
                    
        except Exception as e:
            logger.error(f"Error restoring RMS connection: {str(e)}")
            return {
                "status": "restore_error",
                "error": str(e)
            }
    
    def mask_credentials_in_logs(self, message: str) -> str:
        """
        Mask sensitive credentials in log messages
        Prevents password/session key exposure in logs
        """
        import re
        
        # Mask patterns for common credentials
        patterns = [
            (r'password["\s]*[:=]["\s]*([^"\s,}]+)', r'password": "***"'),
            (r'pass["\s]*[:=]["\s]*([^"\s,}]+)', r'pass": "***"'),
            (r'session_key["\s]*[:=]["\s]*([^"\s,}]+)', r'session_key": "***"'),
            (r'key["\s]*[:=]["\s]*([a-zA-Z0-9]{20,})', r'key": "***"'),
            # Mask long alphanumeric strings that might be tokens
            (r'([a-zA-Z0-9]{30,})', lambda m: m.group(1)[:6] + "***" + m.group(1)[-4:] if len(m.group(1)) > 10 else "***")
        ]
        
        masked_message = message
        for pattern, replacement in patterns:
            if callable(replacement):
                masked_message = re.sub(pattern, replacement, masked_message)
            else:
                masked_message = re.sub(pattern, replacement, masked_message)
        
        return masked_message
    
    def get_rms_connection_status(self, user_id: Optional[str] = None, auto_restore: bool = True) -> Dict[str, Any]:
        """
        Get RMS connection status with optional auto-restore
        Implements sticky connection functionality
        """
        try:
            # КРИТИЧЕСКИ ВАЖНО: всегда требовать user_id для изоляции пользователей
            if not user_id:
                return {"status": "not_connected"}
            
            # КРИТИЧЕСКИ ВАЖНО: полная изоляция для demo пользователей
            if user_id == 'demo_user' or (user_id and user_id.startswith('demo')):
                return {
                    "status": "demo_mode",
                    "host": None,
                    "login": None,
                    "organization_id": None,
                    "organization_name": None,
                    "last_connection": None,
                    "session_expires_at": None,
                    "demo": True
                }
                
            query = {"user_id": user_id}
            credentials_record = self.credentials.find_one(
                query,
                sort=[("last_connection", DESCENDING)]
            )
            
            if not credentials_record:
                return {"status": "not_connected"}
            
            # Check if we need to attempt auto-restore
            if auto_restore and credentials_record.get("status") in [
                IikoRmsConnectionStatus.CONNECTED, 
                IikoRmsConnectionStatus.NEEDS_RECONNECTION
            ]:
                # Check if session might be expired
                session_expires_at = credentials_record.get("session_expires_at")
                if session_expires_at and not session_expires_at.tzinfo:
                    # Make session_expires_at timezone-aware if it's naive
                    session_expires_at = session_expires_at.replace(tzinfo=timezone.utc)
                
                if (not session_expires_at or 
                    datetime.now(timezone.utc) >= session_expires_at - timedelta(minutes=5)):
                    
                    logger.info("Session expired or about to expire, attempting restore...")
                    restore_result = self.restore_rms_connection(user_id)
                    
                    if restore_result["status"] == "restored":
                        # Refresh credentials_record after successful restore
                        credentials_record = self.credentials.find_one(
                            query,
                            sort=[("last_connection", DESCENDING)]
                        )
            
            # Mask password in response
            masked_login = credentials_record["login"][:3] + "***" if len(credentials_record["login"]) > 3 else "***"
            
            return {
                "status": credentials_record["status"],
                "host": credentials_record["host"],
                "login": masked_login,
                "organization_id": credentials_record.get("organization_id"),
                "organization_name": credentials_record.get("organization_name"),
                "last_connection": credentials_record.get("last_connection"),
                "session_expires_at": credentials_record.get("session_expires_at"),
                "is_session_valid": (
                    credentials_record.get("session_expires_at") and 
                    datetime.now(timezone.utc) < (
                        credentials_record["session_expires_at"].replace(tzinfo=timezone.utc) 
                        if credentials_record["session_expires_at"] and not credentials_record["session_expires_at"].tzinfo 
                        else credentials_record["session_expires_at"]
                    )
                ) if credentials_record.get("session_expires_at") else False
            }
            
        except Exception as e:
            logger.error(f"Error getting RMS connection status: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def get_rms_sync_status(self, organization_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get latest RMS sync status for organization with user isolation"""
        try:
            # КРИТИЧЕСКИ ВАЖНО: фильтрация по user_id для изоляции данных
            query = {"organization_id": organization_id, "sync_type": "nomenclature"}
            
            # Если указан user_id, добавляем его в фильтр для изоляции
            if user_id and user_id != 'anonymous':
                # Проверяем что у пользователя есть права на эти данные
                connection_query = {"user_id": user_id}
                connection_record = self.credentials.find_one(connection_query)
                if not connection_record:
                    return {
                        "status": "no_access",
                        "message": "User has no access to organization sync data"
                    }
                
                # Добавляем user_id в query (если такое поле есть в sync records)
                # Примечание: sync records могут не иметь user_id, поэтому проверяем связь через credentials
                
            sync_record = self.sync_status.find_one(
                query,
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
    
    def sync_prices(self, organization_id: str = "default") -> Dict[str, Any]:
        """
        IK-03: Synchronize pricing data from iiko RMS
        Idempotent operation - can be called multiple times safely
        """
        try:
            logger.info(f"Starting price synchronization for organization: {organization_id}")
            
            # Get RMS client
            rms_client = self._get_rms_client_for_org(organization_id)
            
            # Fetch pricing data from RMS
            pricing_data = rms_client.fetch_prices(organization_id)
            prices = pricing_data.get("prices", [])
            
            if not prices:
                logger.warning("No pricing data received from iiko RMS")
                return {"status": "no_data", "message": "No pricing data available"}
            
            # Batch upsert pricing data
            batch_operations = []
            sync_timestamp = datetime.now(timezone.utc)
            
            for price_item in prices:
                try:
                    # Create price document
                    price_doc = IikoRmsPrice(
                        skuId=price_item["skuId"],
                        name=price_item["name"],
                        article=price_item.get("article"),
                        unit=price_item["unit"],
                        original_unit=price_item["original_unit"],
                        price_per_unit=float(price_item["price_per_unit"]),
                        currency=price_item.get("currency", "RUB"),
                        vat_pct=float(price_item.get("vat_pct", 0.0)),
                        source="iiko",
                        active=price_item.get("active", True),
                        organization_id=organization_id,
                        as_of=sync_timestamp,
                        updated_at=sync_timestamp
                    )
                    
                    # Prepare upsert operation
                    filter_query = {
                        "skuId": price_doc.skuId,
                        "organization_id": organization_id
                    }
                    
                    update_doc = price_doc.model_dump(by_alias=True, exclude={"id"})
                    
                    batch_operations.append({
                        "replaceOne": {
                            "filter": filter_query,
                            "replacement": update_doc,
                            "upsert": True
                        }
                    })
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid price data for {price_item.get('name', 'unknown')}: {str(e)}")
                    continue
            
            # Execute batch operations
            if batch_operations:
                result = self.prices.bulk_write(batch_operations)
                
                # Update sync status
                sync_status = IikoRmsSyncStatus(
                    organization_id=organization_id,
                    sync_type="prices",
                    status="completed",
                    last_sync=sync_timestamp,
                    items_processed=len(prices),
                    items_created=result.upserted_count,
                    items_updated=result.modified_count,
                    errors=[]
                )
                
                self.sync_status.replace_one(
                    {"organization_id": organization_id, "sync_type": "prices"},
                    sync_status.model_dump(by_alias=True, exclude={"id"}),
                    upsert=True
                )
                
                logger.info(f"✅ Price sync completed: {result.upserted_count} new, {result.modified_count} updated")
                
                return {
                    "status": "success",
                    "organization_id": organization_id,
                    "items_processed": len(prices),
                    "items_created": result.upserted_count,
                    "items_updated": result.modified_count,
                    "sync_timestamp": sync_timestamp.isoformat(),
                    "message": f"Successfully synced {len(prices)} price records"
                }
            else:
                logger.warning("No valid price records to sync")
                return {"status": "no_valid_data", "message": "No valid price records to sync"}
                
        except IikoRmsAPIError as e:
            logger.error(f"RMS API error during price sync: {str(e)}")
            return {"status": "api_error", "error": str(e)}
        except Exception as e:
            logger.error(f"Error during price synchronization: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def get_prices(self, skuId: Optional[str] = None, organization_id: str = "default", 
                  active_only: bool = True) -> List[Dict[str, Any]]:
        """
        IK-03: Get pricing data from local cache
        Used by PriceProvider for cost calculations
        """
        try:
            # Build query
            query = {"organization_id": organization_id}
            
            if skuId:
                query["skuId"] = skuId
                
            if active_only:
                query["active"] = True
            
            # Get prices sorted by freshness
            prices_cursor = self.prices.find(query).sort("as_of", DESCENDING)
            
            prices = []
            for price_doc in prices_cursor:
                # Convert MongoDB document to dict and clean up
                price = dict(price_doc)
                if "_id" in price:
                    del price["_id"]  # Remove MongoDB ObjectId
                prices.append(price)
            
            return prices
            
        except Exception as e:
            logger.error(f"Error retrieving prices: {str(e)}")
            return []

# Global RMS service instance
_iiko_rms_service: Optional[IikoRmsService] = None

def get_iiko_rms_service() -> IikoRmsService:
    """Get or create global IikoRmsService instance"""
    global _iiko_rms_service
    
    if _iiko_rms_service is None:
        _iiko_rms_service = IikoRmsService()
    
    return _iiko_rms_service