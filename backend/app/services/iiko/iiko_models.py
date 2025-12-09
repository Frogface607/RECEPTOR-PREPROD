"""
MongoDB models for iikoCloud API integration
Handles storage of tokens, products, and synchronization data
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field
from enum import Enum

class IikoTokenStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"

class IikoToken(BaseModel):
    """Model for storing iikoCloud API tokens"""
    id: str = Field(default_factory=lambda: str(uuid4()), alias="_id")
    user_id: Optional[str] = Field(None, description="User who created the token")
    api_login: str = Field(description="iikoCloud API login")
    access_token: str = Field(description="Encrypted access token")
    expires_at: datetime = Field(description="Token expiration timestamp")
    organization_id: Optional[str] = Field(None, description="Selected organization ID")
    organization_name: Optional[str] = Field(None, description="Selected organization name")
    status: IikoTokenStatus = Field(default=IikoTokenStatus.ACTIVE, description="Token status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True

class IikoProductSizePrice(BaseModel):
    """Model for product size pricing information"""
    size_id: Optional[str] = Field(None, description="Size identifier")
    price: float = Field(description="Price for this size")
    currency: str = Field(default="RUB", description="Price currency")

class IikoProduct(BaseModel):
    """Model for storing iikoCloud products"""
    id: str = Field(alias="_id", description="Product ID from iiko")
    organization_id: str = Field(description="Organization this product belongs to")
    name: str = Field(description="Product name")
    name_normalized: str = Field(description="Normalized name for search")
    description: Optional[str] = Field(None, description="Product description")
    group_id: Optional[str] = Field(None, description="Product group ID")
    group_name: Optional[str] = Field(None, description="Product group name")
    size_prices: List[IikoProductSizePrice] = Field(default_factory=list, description="Size and price information")
    tags: List[str] = Field(default_factory=list, description="Product tags")
    is_deleted: bool = Field(default=False, description="Deletion status")
    unit: str = Field(default="pcs", description="Normalized unit (g/ml/pcs)")
    unit_coefficient: float = Field(default=1.0, description="Coefficient to convert to normalized unit")
    article: Optional[str] = Field(None, description="Product article/SKU")
    
    # Price information for cost calculation
    price_per_unit: Optional[float] = Field(None, description="Price per normalized unit")
    currency: str = Field(default="RUB", description="Price currency")
    
    # Sync information
    synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True

class IikoProductGroup(BaseModel):
    """Model for storing iikoCloud product groups"""
    id: str = Field(alias="_id", description="Group ID from iiko")
    organization_id: str = Field(description="Organization this group belongs to")
    name: str = Field(description="Group name")
    parent_group: Optional[str] = Field(None, description="Parent group ID")
    is_deleted: bool = Field(default=False, description="Deletion status")
    
    # Sync information
    synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True

class IikoSyncStatus(BaseModel):
    """Model for tracking synchronization status"""
    id: str = Field(default_factory=lambda: str(uuid4()), alias="_id")
    organization_id: str = Field(description="Organization ID")
    sync_type: str = Field(description="Type of sync (nomenclature, prices, etc.)")
    status: str = Field(description="Sync status (running, completed, failed)")
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Statistics
    products_processed: int = Field(default=0, description="Number of products processed")
    products_created: int = Field(default=0, description="Number of products created")
    products_updated: int = Field(default=0, description="Number of products updated")
    products_deleted: int = Field(default=0, description="Number of products marked as deleted")
    
    class Config:
        populate_by_name = True

# Database collection names
IIKO_TOKENS_COLLECTION = "iiko_tokens"
IIKO_PRODUCTS_COLLECTION = "iiko_products"
IIKO_GROUPS_COLLECTION = "iiko_groups"
IIKO_SYNC_STATUS_COLLECTION = "iiko_sync_status"

# MongoDB indexes for performance
IIKO_PRODUCTS_INDEXES = [
    {"keys": [("organization_id", 1)], "name": "organization_id_1"},
    {"keys": [("name_normalized", "text")], "name": "name_search"},
    {"keys": [("article", 1)], "name": "article_1"},
    {"keys": [("is_deleted", 1)], "name": "is_deleted_1"},
    {"keys": [("synced_at", -1)], "name": "synced_at_-1"},
    {"keys": [("organization_id", 1), ("is_deleted", 1)], "name": "org_active_products"}
]

IIKO_GROUPS_INDEXES = [
    {"keys": [("organization_id", 1)], "name": "organization_id_1"},
    {"keys": [("parent_group", 1)], "name": "parent_group_1"},
    {"keys": [("is_deleted", 1)], "name": "is_deleted_1"}
]

IIKO_TOKENS_INDEXES = [
    {"keys": [("user_id", 1)], "name": "user_id_1"},
    {"keys": [("organization_id", 1)], "name": "organization_id_1"},
    {"keys": [("status", 1)], "name": "status_1"},
    {"keys": [("expires_at", 1)], "name": "expires_at_1"}
]

IIKO_SYNC_STATUS_INDEXES = [
    {"keys": [("organization_id", 1)], "name": "organization_id_1"},
    {"keys": [("sync_type", 1)], "name": "sync_type_1"},
    {"keys": [("started_at", -1)], "name": "started_at_-1"}
]