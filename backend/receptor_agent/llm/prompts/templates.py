DRAFT_PROMPT = """You are an expert culinary R&D technologist creating professional tech cards.
Goal: Generate a complete TechCardV2 JSON for the given dish profile.

CRITICAL MATHEMATICAL REQUIREMENTS:
1. EXACT BALANCE: sum of all ingredients.netto_g MUST EQUAL yield.perBatch_g (±5% max)
2. PRECISE FORMULA: each ingredient netto_g = brutto_g * (1 - loss_pct/100) 
3. BATCH CALCULATION: yield.perBatch_g = yield.perPortion_g * portions

EXAMPLE CALCULATION:
- If portions=4, perPortion_g=200 → perBatch_g=800
- Ingredients must sum to ~800g netto: [meat 400g + vegetables 300g + seasoning 100g = 800g total]

OTHER REQUIREMENTS:
- Output ONLY valid JSON matching TechCardV2 schema
- Use EXACT numbers only (no ranges like "5-7", no text like "по вкусу")
- Units: only "g", "ml", "pcs" 
- Process: minimum 3 steps, thermal steps need time_min OR temp_c
- nutrition and cost fields: set to null (will be calculated later)

STRUCTURE TEMPLATE:
{
  "meta": {"title": "Борщ украинский", "version": "2.0", "cuisine": "украинская", "tags": []},
  "portions": 4,
  "yield": {"perPortion_g": 200.0, "perBatch_g": 800.0},
  "ingredients": [
    {"name": "Говядина", "unit": "g", "brutto_g": 450.0, "loss_pct": 10.0, "netto_g": 405.0, "allergens": []},
    {"name": "Свекла", "unit": "g", "brutto_g": 200.0, "loss_pct": 15.0, "netto_g": 170.0, "allergens": []},
    {"name": "Морковь", "unit": "g", "brutto_g": 120.0, "loss_pct": 20.0, "netto_g": 96.0, "allergens": []},
    {"name": "Лук", "unit": "g", "brutto_g": 100.0, "loss_pct": 10.0, "netto_g": 90.0, "allergens": []},
    {"name": "Соль", "unit": "g", "brutto_g": 8.0, "loss_pct": 0.0, "netto_g": 8.0, "allergens": []}
  ],
  "process": [
    {"n": 1, "action": "Подготовка мяса и овощей", "time_min": 20.0, "temp_c": null},
    {"n": 2, "action": "Варка бульона из говядины", "time_min": 90.0, "temp_c": 95.0},
    {"n": 3, "action": "Добавление овощей и доведение до готовности", "time_min": 30.0, "temp_c": 85.0}
  ],
  "storage": {"conditions": "Холодильник 0...+4°C", "shelfLife_hours": 48.0, "servingTemp_c": 65.0},
  "nutrition": {"per100g": null, "perPortion": null},
  "cost": {"rawCost": null, "costPerPortion": null},
  "printNotes": []
}

VERIFY: Sum of netto_g (405+170+96+90+8 = 769g) ≈ perBatch_g (800g) ✓"""

NORMALIZE_PROMPT = """Normalize ingredient names and units to canonical dictionary.
Rules:
- Keep only g/ml/pcs; map synonyms to canonical names if obvious; else keep as-is and set needs_review=true.
- Do NOT invent new ingredients. Preserve quantities.
- Output JSON only, matching schema.
"""

QUANTIFY_PROMPT = """Quantify gross/net/loss for each ingredient with realistic bounds.
Rules:
- If thermal processing implied, use typical loss ranges (poultry 10–18%, meat 12–22%, fish 8–15%, veg 5–12%).
- Ensure yield balance: sum(net_g) == yield.total_net_g == portions * per_portion_g (±1% tolerance).
- Fix inconsistencies by scaling evenly.
- Output JSON only, matching schema.
"""

HACCP_PROMPT = """Generate HACCP blocks for the dish.
Rules:
- hazards: bio/chem/phys relevant to ingredients.
- ccp: temperature limits for core steps, cold storage, cross-contamination controls where applicable.
- Each CCP: name, limit (e.g. '≥75°C'), monitoring, corrective.
- Include storage policy.
- Output JSON only, matching schema.
"""

CRITIC_PROMPT = """Review the JSON for consistency and safety.
Return the same JSON with only minimal fixes applied if needed (no commentary).
"""