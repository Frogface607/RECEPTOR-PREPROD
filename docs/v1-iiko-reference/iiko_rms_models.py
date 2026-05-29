"""
MongoDB models for iiko RMS integration
Handles storage of RMS nomenclature, credentials, and synchronization data
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field
from enum import Enum

class IikoRmsConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    NEEDS_RECONNECTION = "needs_reconnection" 
    ERROR = "error"

class IikoRmsCredentials(BaseModel):
    """Model for storing encrypted iiko RMS credentials"""
    id: str = Field(default_factory=lambda: str(uuid4()), alias="_id")
    user_id: Optional[str] = Field(None, description="User who created the connection")
    host: str = Field(description="iiko RMS server host")
    login: str = Field(description="RMS login")
    password: str = Field(description="Encrypted password")  # Should be encrypted in production
    organization_id: Optional[str] = Field(None, description="Selected organization ID")
    organization_name: Optional[str] = Field(None, description="Selected organization name")
    status: IikoRmsConnectionStatus = Field(default=IikoRmsConnectionStatus.DISCONNECTED)
    last_connection: Optional[datetime] = Field(None, description="Last successful connection")
    session_key: Optional[str] = Field(None, description="Current session key")
    session_expires_at: Optional[datetime] = Field(None, description="Session expiration time")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True

class IikoRmsProduct(BaseModel):
    """Model for storing iiko RMS nomenclature products"""
    id: str = Field(alias="_id", description="Product ID from iiko RMS")
    organization_id: str = Field(description="Organization this product belongs to")
    name: str = Field(description="Product name")
    name_normalized: str = Field(description="Normalized name for search")
    article: Optional[str] = Field(None, description="Product article (номенклатурный код) from 'num' field - for TTK export")
    quick_dial_code: Optional[str] = Field(None, description="Quick dial code (код быстрого набора) from 'code' field - NOT for TTK")
    group_id: Optional[str] = Field(None, description="Product group ID")
    group_name: Optional[str] = Field(None, description="Product group name")
    unit: str = Field(description="Normalized unit (g/ml/pcs)")
    unit_coefficient: float = Field(default=1.0, description="Coefficient to convert to normalized unit")
    price: Optional[float] = Field(None, description="Original price")
    price_per_unit: Optional[float] = Field(None, description="Price per normalized unit")
    active: bool = Field(default=True, description="Product status in iiko")
    description: Optional[str] = Field(None, description="Product description")
    barcode: Optional[str] = Field(None, description="Product barcode")
    product_type: str = Field(default="product", description="Product type (product, dish, modifier)")
    
    # Source tracking
    source: str = Field(default="iiko_rms", description="Data source identifier")
    
    # Sync information
    synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True

class IikoRmsGroup(BaseModel):
    """Model for storing iiko RMS product groups/categories"""
    id: str = Field(alias="_id", description="Group ID from iiko RMS")
    organization_id: str = Field(description="Organization this group belongs to")
    name: str = Field(description="Group name")
    parent_id: Optional[str] = Field(None, description="Parent group ID")
    active: bool = Field(default=True, description="Group status")
    
    # Sync information
    synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True

class IikoRmsPrice(BaseModel):
    """
    IK-03: Model for storing iiko RMS pricing data 
    Separate collection for pricing to enable efficient price lookups
    """
    id: str = Field(default_factory=lambda: str(uuid4()), alias="_id")
    skuId: str = Field(description="Product SKU/ID from iiko RMS")
    name: str = Field(description="Product name")
    article: Optional[str] = Field(None, description="Product article/code")
    unit: str = Field(description="Normalized unit (g/ml/pcs)")
    original_unit: str = Field(description="Original unit from iiko RMS")
    price_per_unit: float = Field(description="Purchase price per normalized unit") 
    currency: str = Field(default="RUB", description="Price currency")
    vat_pct: float = Field(default=0.0, description="VAT rate percentage")
    source: str = Field(default="iiko", description="Price source")
    active: bool = Field(default=True, description="Product active status")
    organization_id: str = Field(default="default", description="Organization this price belongs to")
    as_of: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Price fetch timestamp")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True

class IikoRmsSyncStatus(BaseModel):
    """Model for tracking RMS synchronization operations"""
    id: str = Field(default_factory=lambda: str(uuid4()), alias="_id")
    organization_id: str = Field(description="Organization ID")
    sync_type: str = Field(description="Type of sync (nomenclature, groups, etc.)")
    status: str = Field(description="Sync status (running, completed, failed)")
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Statistics
    products_processed: int = Field(default=0)
    products_created: int = Field(default=0)
    products_updated: int = Field(default=0)
    products_deleted: int = Field(default=0)
    groups_processed: int = Field(default=0)
    groups_created: int = Field(default=0)
    groups_updated: int = Field(default=0)
    
    # Connection info
    host: Optional[str] = Field(None, description="RMS host used")
    session_info: Optional[Dict[str, Any]] = Field(None, description="Session information")
    
    class Config:
        populate_by_name = True

class IikoRmsMapping(BaseModel):
    """Model for storing ingredient to RMS product mappings"""
    id: str = Field(default_factory=lambda: str(uuid4()), alias="_id")
    ingredient_name: str = Field(description="Ingredient name from TechCard")
    ingredient_name_normalized: str = Field(description="Normalized ingredient name")
    rms_product_id: str = Field(description="Mapped RMS product ID")
    rms_product_name: str = Field(description="RMS product name")
    rms_article: Optional[str] = Field(None, description="RMS product article")
    mapping_type: str = Field(description="Mapping type (auto, manual)")
    match_score: float = Field(description="Matching confidence score (0-1)")
    
    # Mapping metadata
    created_by: Optional[str] = Field(None, description="User who created the mapping")
    approved: bool = Field(default=False, description="Manual approval status")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True

# Database collection names
IIKO_RMS_CREDENTIALS_COLLECTION = "iiko_rms_credentials"
IIKO_RMS_PRODUCTS_COLLECTION = "iiko_rms_products"
IIKO_RMS_GROUPS_COLLECTION = "iiko_rms_groups"
IIKO_RMS_SYNC_STATUS_COLLECTION = "iiko_rms_sync_status"
IIKO_RMS_MAPPINGS_COLLECTION = "iiko_rms_mappings"
IIKO_RMS_PRICES_COLLECTION = "iiko_prices"  # IK-03: New collection for pricing data

# MongoDB indexes for performance
IIKO_RMS_PRODUCTS_INDEXES = [
    {"keys": [("organization_id", 1)], "name": "organization_id_1"},
    {"keys": [("name_normalized", "text")], "name": "name_search"},
    {"keys": [("article", 1)], "name": "article_1"},
    {"keys": [("active", 1)], "name": "active_1"},
    {"keys": [("synced_at", -1)], "name": "synced_at_-1"},
    {"keys": [("organization_id", 1), ("active", 1)], "name": "org_active_products"},
    {"keys": [("source", 1)], "name": "source_1"},
    {"keys": [("group_id", 1)], "name": "group_id_1"}
]

IIKO_RMS_GROUPS_INDEXES = [
    {"keys": [("organization_id", 1)], "name": "organization_id_1"},
    {"keys": [("parent_id", 1)], "name": "parent_id_1"},
    {"keys": [("active", 1)], "name": "active_1"},
    {"keys": [("name", 1)], "name": "name_1"}
]

IIKO_RMS_CREDENTIALS_INDEXES = [
    {"keys": [("user_id", 1)], "name": "user_id_1"},
    {"keys": [("host", 1)], "name": "host_1"},
    {"keys": [("organization_id", 1)], "name": "organization_id_1"},
    {"keys": [("status", 1)], "name": "status_1"},
    {"keys": [("session_expires_at", 1)], "name": "session_expires_at_1"}
]

IIKO_RMS_SYNC_STATUS_INDEXES = [
    {"keys": [("organization_id", 1)], "name": "organization_id_1"},
    {"keys": [("sync_type", 1)], "name": "sync_type_1"},
    {"keys": [("status", 1)], "name": "status_1"},
    {"keys": [("started_at", -1)], "name": "started_at_-1"}
]

IIKO_RMS_MAPPINGS_INDEXES = [
    {"keys": [("ingredient_name_normalized", "text")], "name": "ingredient_search"},
    {"keys": [("rms_product_id", 1)], "name": "rms_product_id_1"},
    {"keys": [("mapping_type", 1)], "name": "mapping_type_1"},
    {"keys": [("match_score", -1)], "name": "match_score_-1"},
    {"keys": [("approved", 1)], "name": "approved_1"},
    {"keys": [("created_by", 1)], "name": "created_by_1"}
]

# IK-03: Indexes for pricing data collection
IIKO_RMS_PRICES_INDEXES = [
    {"keys": [("skuId", 1)], "name": "skuId_1"},  # Primary lookup by SKU
    {"keys": [("organization_id", 1), ("skuId", 1)], "name": "org_sku_compound"},  # Organization-scoped lookup
    {"keys": [("name", "text")], "name": "name_search"},  # Text search by product name
    {"keys": [("as_of", -1)], "name": "as_of_-1"},  # Sort by freshness
    {"keys": [("active", 1), ("as_of", -1)], "name": "active_freshness"}  # Active products by freshness
]