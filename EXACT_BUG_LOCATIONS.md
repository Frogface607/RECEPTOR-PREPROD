# 🎯 ТОЧНЫЕ ЛОКАЦИИ БАГОВ - READY TO FIX!

**Дата:** 2025-10-09  
**Статус:** Найдены КОНКРЕТНЫЕ строки кода с проблемами!

---

## 🔥 BUG #1 + #3: SKU MAPPINGS - ПОЛНАЯ КАРТИНА ПРОБЛЕМЫ!

### **ЧТО ПРОИСХОДИТ (FULL FLOW):**

```
User clicks "Автомаппинг"
    ↓
startEnhancedAutoMapping() (Line 4689)
    ↓ API call
Backend: enhanced_auto_mapping() (backend)
    ↓ Returns suggestions
Frontend: Shows modal (Line 4823)
    ↓
User clicks "Принять ≥90%"
    ↓
acceptAllHighConfidence() (Line 5304)
    ↓
Updates autoMappingResults state (Line 5371-5378)
    ❌ BUT NOT tcV2!
    ↓
User clicks "Применить выбранное"
    ↓
applyAutoMappingChanges() (Line 5039-5135)
    ↓
setTcV2(updatedTcV2) (Line 5115) ✅ Updates state in memory
performRecalculation() (Line 5118) ✅ Recalculates
    ❌ BUT NO API CALL TO SAVE TO MONGODB!
    ↓
User reloads page
    ↓
Loads from MongoDB → OLD DATA WITHOUT MAPPINGS! ❌
```

### **ПРОБЛЕМА #1: Backend не сохраняет (но этот endpoint не используется!)**

**File:** `backend/receptor_agent/routes/techcards_v2.py`  
**Lines:** 947-995  
**Function:** `apply_mapping_changes()`

**Статус:** ⚠️ Этот endpoint НЕ ВЫЗЫВАЕТСЯ из frontend!  
Frontend делает все локально!

---

### **ПРОБЛЕМА #2: Frontend не вызывает API для сохранения!**

**File:** `frontend/src/App.js`  
**Lines:** 5039-5135  
**Function:** `applyAutoMappingChanges()`

**КОД ПРОБЛЕМЫ:**

```javascript
// Line 5039-5135
const applyAutoMappingChanges = async () => {
  const acceptedResults = autoMappingResults.filter(r => 
    r.status === 'accepted' || r.status === 'auto_accept'
  );
  
  // ... validation ...
  
  // Update tcV2 with new SKUs
  const updatedTcV2 = { ...tcV2 };
  let changesCount = 0;
  
  for (const result of acceptedResults) {
    if (result.suggestion && result.index >= 0) {
      // ✅ Обновляет ingredients в памяти
      updatedTcV2.ingredients[result.index] = {
        ...updatedTcV2.ingredients[result.index],
        skuId: suggestion.sku_id,
        product_code: productCode,  // Line 5099
        source: 'rms'
      };
      changesCount++;
    }
  }
  
  // ✅ Updates state
  setTcV2(updatedTcV2);  // Line 5115
  
  // ✅ Recalculates
  await performRecalculation(updatedTcV2);  // Line 5118
  
  // ❌❌❌ ПРОБЛЕМА ЗДЕСЬ! ❌❌❌
  // НЕТ API CALL ДЛЯ СОХРАНЕНИЯ В MongoDB!
  // НЕТ: await axios.post('/api/v1/techcards.v2/save', updatedTcV2)
  
  setAutoMappingMessage({ 
    type: 'success', 
    text: `✅ Применено ${changesCount} изменений` 
  });
  
  setShowAutoMappingModal(false);
  setAutoMappingResults([]);
};
```

### **THE FIX:**

**ВАРИАНТ 1: Frontend - Добавить API call для сохранения (РЕКОМЕНДУЮ!)**

**File:** `frontend/src/App.js`  
**Location:** Line 5039-5135, функция `applyAutoMappingChanges()`

**AFTER Line 5118 (`await performRecalculation(updatedTcV2);`), ADD:**

```javascript
  // ✅✅✅ КРИТИЧНО: Сохраняем в MongoDB! ✅✅✅
  try {
    const techcardId = updatedTcV2.id || updatedTcV2._id || updatedTcV2.meta?.id;
    
    if (techcardId) {
      console.log(`💾 Saving ${changesCount} SKU mappings to MongoDB for techcard ${techcardId}`);
      
      const saveResponse = await axios.put(
        `${API}/v1/techcards.v2/${techcardId}`,
        updatedTcV2
      );
      
      if (saveResponse.data.status === 'success') {
        console.log(`✅ SKU mappings persisted to MongoDB!`);
      }
    } else {
      console.warn('⚠️ No techcard ID - mappings not persisted to DB');
    }
  } catch (saveError) {
    console.error('MongoDB save error:', saveError);
    // Don't block UX, но показываем warning
    setAutoMappingMessage({ 
      type: 'warning', 
      text: `⚠️ Изменения применены, но не сохранены в БД: ${saveError.message}` 
    });
  }
```

**UPDATED FUNCTION (Lines 5039-5135):**

```javascript
const applyAutoMappingChanges = async () => {
  const acceptedResults = autoMappingResults.filter(r => r.status === 'accepted' || r.status === 'auto_accept');
  
  if (acceptedResults.length === 0) {
    setAutoMappingMessage({ type: 'error', text: 'Нет изменений для применения' });
    return;
  }

  setAutoMappingMessage({ type: 'info', text: '🔄 Применение изменений...' });
  
  try {
    // Validate tcV2
    if (!tcV2 || !tcV2.ingredients || !Array.isArray(tcV2.ingredients)) {
      throw new Error('Техкарта не найдена или повреждена');
    }
    
    // Update tcV2 with new SKUs
    const updatedTcV2 = { ...tcV2 };
    let changesCount = 0;
    
    for (const result of acceptedResults) {
      if (result.suggestion && result.index >= 0 && result.index < updatedTcV2.ingredients.length) {
        const suggestion = result.suggestion;
        let productCode = null;
        
        // Extract article
        if (suggestion.article) {
          productCode = String(suggestion.article).padStart(5, '0');
        }
        
        // Apply mapping
        updatedTcV2.ingredients[result.index] = {
          ...updatedTcV2.ingredients[result.index],
          skuId: suggestion.sku_id,
          product_code: productCode,
          source: 'rms'
        };
        changesCount++;
      }
    }
    
    if (changesCount === 0) {
      throw new Error('Не удалось применить изменения');
    }
    
    // ✅ Update state
    setTcV2(updatedTcV2);
    
    // ✅ Recalculate
    await performRecalculation(updatedTcV2);
    
    // ✅✅✅ КРИТИЧНО: СОХРАНЯЕМ В MongoDB! ✅✅✅
    try {
      const techcardId = updatedTcV2.id || updatedTcV2._id || updatedTcV2.meta?.id;
      
      if (techcardId) {
        console.log(`💾 Saving ${changesCount} SKU mappings to MongoDB for techcard ${techcardId}`);
        
        const saveResponse = await axios.put(
          `${API}/v1/techcards.v2/${techcardId}`,
          updatedTcV2
        );
        
        if (saveResponse.data.status === 'success') {
          console.log(`✅ SKU mappings persisted to MongoDB!`);
          
          setAutoMappingMessage({ 
            type: 'success', 
            text: `✅ Применено и СОХРАНЕНО ${changesCount} изменений! Данные не потеряются при перезагрузке.` 
          });
        }
      } else {
        console.warn('⚠️ No techcard ID - mappings not persisted to DB');
        
        setAutoMappingMessage({ 
          type: 'warning', 
          text: `⚠️ Применено ${changesCount} изменений, но без сохранения в БД (нет ID)` 
        });
      }
    } catch (saveError) {
      console.error('MongoDB save error:', saveError);
      
      setAutoMappingMessage({ 
        type: 'warning', 
        text: `⚠️ Изменения применены локально, но не сохранены: ${saveError.message}` 
      });
    }
    
  } catch (error) {
    console.error('Apply auto-mapping changes error:', error);
    setAutoMappingMessage({ 
      type: 'error', 
      text: `❌ Ошибка применения изменений: ${error.message}` 
    });
  }
  
  setShowAutoMappingModal(false);
  setAutoMappingResults([]);
};
```

---

### **BACKEND ENDPOINT НУЖНО СОЗДАТЬ:**

**File:** `backend/receptor_agent/routes/techcards_v2.py`

**ПРОБЛЕМА:** Нет PUT endpoint для update техкарты!

**ADD NEW ENDPOINT (добавь после Line 995, после `apply_mapping_changes`):**

```python
@router.put("/techcards.v2/{techcard_id}")
async def update_techcard_v2(techcard_id: str, request: Request):
    """
    Update existing TechCard V2 in MongoDB
    Used for persisting SKU mappings, edits, and other changes
    """
    try:
        body = await request.json()
        
        if not techcard_id:
            raise HTTPException(400, "techcard_id required")
        
        # Get MongoDB connection
        import os
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
        client = AsyncIOMotorClient(mongo_url)
        db_name = os.environ.get('DB_NAME', 'receptor_pro').strip('"')
        
        # Validate DB name length (MongoDB fix)
        if len(db_name) > 63:
            logger.warning(f"DB name too long ({len(db_name)}), truncating to 63 chars")
            db_name = db_name[:63]
        
        db = client[db_name]
        
        # Update техкарты в MongoDB
        # Remove _id from body if present (can't update _id field)
        if '_id' in body:
            del body['_id']
        if 'id' in body:
            del body['id']
        
        # Add updated_at timestamp
        from datetime import datetime
        body['updated_at'] = datetime.now()
        
        result = await db.techcards_v2.update_one(
            {"_id": techcard_id},
            {"$set": body}
        )
        
        client.close()
        
        if result.matched_count == 0:
            raise HTTPException(404, f"Techcard {techcard_id} not found")
        
        logger.info(f"✅ Updated techcard {techcard_id} in MongoDB (modified: {result.modified_count})")
        
        return {
            "status": "success",
            "techcard_id": techcard_id,
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "message": "Techcard updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update techcard error: {e}")
        raise HTTPException(500, f"Update failed: {str(e)}")
```

**ВАЖНО:** Также нужен GET endpoint для загрузки техкарты по ID!

**ADD ТАКЖЕ (если его нет):**

```python
@router.get("/techcards.v2/{techcard_id}")
async def get_techcard_v2(techcard_id: str, user_id: Optional[str] = Query(None)):
    """
    Get TechCard V2 by ID from MongoDB
    With user isolation for security
    """
    try:
        import os
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
        client = AsyncIOMotorClient(mongo_url)
        db_name = os.environ.get('DB_NAME', 'receptor_pro').strip('"')
        
        if len(db_name) > 63:
            db_name = db_name[:63]
        
        db = client[db_name]
        
        # Query with user_id for isolation
        query = {"_id": techcard_id}
        if user_id and user_id != 'demo_user':
            query["user_id"] = user_id
        
        techcard = await db.techcards_v2.find_one(query)
        
        client.close()
        
        if not techcard:
            raise HTTPException(404, f"Techcard {techcard_id} not found")
        
        # Convert ObjectId to string for JSON
        if '_id' in techcard:
            techcard['_id'] = str(techcard['_id'])
        
        return techcard
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get techcard error: {e}")
        raise HTTPException(500, f"Get failed: {str(e)}")
```

```python
        # ✅✅✅ КРИТИЧНО: СОХРАНЯЕМ В MongoDB! ✅✅✅
        if applied_count > 0:
            import os
            from motor.motor_asyncio import AsyncIOMotorClient
            
            # Get techcard ID
            techcard_id = techcard_data.get('id') or techcard_data.get('_id')
            
            if not techcard_id:
                logger.warning("No techcard ID - cannot persist mappings!")
            else:
                # MongoDB connection
                mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/receptor_pro')
                client = AsyncIOMotorClient(mongo_url)
                db_name = os.environ.get('DB_NAME', 'receptor_pro').strip('"')
                
                # Validate DB name length
                if len(db_name) > 63:
                    logger.warning(f"DB name too long ({len(db_name)}), truncating to 63 chars")
                    db_name = db_name[:63]
                
                db = client[db_name]
                
                # Update техкарты в MongoDB
                update_result = await db.techcards_v2.update_one(
                    {"_id": techcard_id},
                    {"$set": {
                        "ingredients": ingredients,
                        "updated_at": datetime.now()
                    }}
                )
                
                client.close()
                
                if update_result.modified_count > 0:
                    logger.info(f"✅ PERSISTED {applied_count} SKU mappings to MongoDB for techcard {techcard_id}")
                else:
                    logger.warning(f"⚠️ MongoDB update matched but not modified for {techcard_id}")
        
        # Save user decisions for future learning
        organization_id = body.get('organization_id', 'default')
        logger.info(f"Applied {applied_count} mapping changes for organization {organization_id}")
        
        return {
            "status": "success",
            "updated_techcard": updated_card,
            "applied_count": applied_count,
            "persisted": applied_count > 0,  # ✅ Indicator
            "message": f"Применено и СОХРАНЕНО {applied_count} изменений маппинга"
        }
```

**Import to add at top of file:**
```python
from datetime import datetime  # If not already imported
```

---

## 🐛 BUG #3: AUTO-MAPPING UI NOT UPDATING

### **EXACT LOCATION:**

**File:** `frontend/src/App.js`  
**Lines:** 4689-4872  
**Function:** `startEnhancedAutoMapping()`

### **ПРОБЛЕМА В КОДЕ:**

```javascript
// Line 4689-4872
const startEnhancedAutoMapping = async () => {
  // ... validation ...
  
  try {
    // ✅ Call backend
    const response = await fetch(`${BACKEND_URL}/api/v1/techcards.v2/mapping/enhanced`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        techcard: tcV2,
        organization_id: 'default',
        auto_apply: false
      })
    });

    const result = await response.json();
    
    if (result.status === 'success' && result.mapping_results) {
      // ✅ Shows results in modal
      setAutoMappingResults(sanitizedResults);
      setShowAutoMappingModal(true);  // Line 4823
      
      // ❌❌❌ ПРОБЛЕМА! ❌❌❌
      // Modal показан, но изменения НЕ ПРИМЕНЕНЫ к tcV2!
      // User видит modal с suggestions, но actual mapping happens ТОЛЬКО когда он жмет кнопку!
    }
    
  } catch (error) {
    console.error('Enhanced auto-mapping error:', error);
  } finally {
    setIsAutoMapping(false);
  }
};
```

### **ГДЕ ПРОИСХОДИТ ACTUAL APPLY:**

**Нужно найти handler кнопки "Принять все" в Auto-Mapping Modal!**

Ищем дальше...

<function_calls>
<invoke name="grep">
<parameter name="pattern">Принять все|acceptAllMappings|applyAllMappings
