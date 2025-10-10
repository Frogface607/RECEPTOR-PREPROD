#!/usr/bin/env python3
"""
HOTFIX: Migrate existing techcards to add missing product_code fields
Pulls article from IIKO RMS using skuId

RUN THIS ONCE to fix existing techcards!
"""

import os
import sys
from pymongo import MongoClient
from datetime import datetime

def migrate_product_codes():
    """Add product_code to ingredients that have skuId but missing product_code"""
    
    # Get MongoDB connection
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
    db_name = os.getenv('DB_NAME', 'receptor_pro').strip('"')
    
    # Validate DB name
    if len(db_name) > 63:
        print(f"⚠️ DB name too long ({len(db_name)}), truncating to 63 chars")
        db_name = db_name[:63]
    
    client = MongoClient(mongo_url)
    db = client[db_name]
    
    print(f"\n🔧 Migrating product_codes for database: {db_name}")
    print("=" * 60)
    
    try:
        # Get all techcards
        techcards = list(db.techcards_v2.find({}))
        total_techcards = len(techcards)
        
        if total_techcards == 0:
            print("ℹ️ No techcards found in database")
            return
        
        print(f"\n📋 Found {total_techcards} techcards to analyze")
        
        migrated_count = 0
        ingredients_updated = 0
        
        for idx, techcard in enumerate(techcards, 1):
            techcard_id = techcard.get('_id')
            techcard_title = techcard.get('meta', {}).get('title', 'Unknown')
            ingredients = techcard.get('ingredients', [])
            
            if not ingredients:
                continue
            
            updated = False
            local_updates = 0
            
            print(f"\n[{idx}/{total_techcards}] Processing: {techcard_title} ({techcard_id})")
            
            for ingredient in ingredients:
                ingredient_name = ingredient.get('name', 'Unknown')
                
                # Check if product_code is missing but skuId exists
                if ingredient.get('skuId') and not ingredient.get('product_code'):
                    sku_id = ingredient['skuId']
                    
                    # Lookup product in IIKO RMS products
                    product = db.iiko_rms_products.find_one({"_id": sku_id})
                    
                    if product and product.get('article'):
                        # Add product_code from IIKO
                        ingredient['product_code'] = product['article']
                        updated = True
                        local_updates += 1
                        ingredients_updated += 1
                        
                        print(f"  ✅ {ingredient_name}: added product_code = {product['article']}")
                    else:
                        print(f"  ⚠️ {ingredient_name}: skuId={sku_id} не найден в IIKO RMS")
            
            if updated:
                # Update techcard in MongoDB
                result = db.techcards_v2.update_one(
                    {"_id": techcard_id},
                    {
                        "$set": {
                            "ingredients": ingredients,
                            "updated_at": datetime.now()
                        }
                    }
                )
                
                if result.modified_count > 0:
                    migrated_count += 1
                    print(f"  💾 Saved {local_updates} product_codes to MongoDB")
                else:
                    print(f"  ⚠️ MongoDB update failed")
            else:
                print(f"  ℹ️ No changes needed")
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"\n🎉 MIGRATION COMPLETE!")
        print(f"✅ Updated {migrated_count} techcards")
        print(f"✅ Fixed {ingredients_updated} ingredients")
        print(f"ℹ️ Analyzed {total_techcards} total techcards")
        
        if migrated_count > 0:
            print(f"\n💡 Now SKU mappings will persist in MongoDB!")
            print(f"📊 Coverage improvement: +{ingredients_updated} mapped ingredients")
        else:
            print(f"\nℹ️ All techcards already have product_code - no migration needed!")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        client.close()
        print("\n✅ MongoDB connection closed")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  RECEPTOR PRO - Product Code Migration (HOTFIX)")
    print("="*60)
    
    print("\n⚠️ This script will:")
    print("  1. Find all techcards with skuId but no product_code")
    print("  2. Lookup article from IIKO RMS")
    print("  3. Update ingredients with product_code")
    print("  4. Save to MongoDB")
    
    response = input("\n❓ Continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        migrate_product_codes()
        print("\n✨ Done! Your techcards now have persistent product_codes! ✨\n")
    else:
        print("\n❌ Migration cancelled\n")


