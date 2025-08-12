DRAFT_PROMPT = """You are an expert culinary R&D technologist creating professional tech cards.
Goal: Generate a complete TechCardV2 JSON for the given dish profile.

CRITICAL REQUIREMENTS:
- Output ONLY valid JSON matching TechCardV2 schema
- Use EXACT numbers only (no ranges like "5-7", no text like "по вкусу")
- Units: only "g", "ml", "pcs" 
- Math must be precise: netto_g = brutto_g * (1 - loss_pct/100)
- Ingredient balance: sum(netto_g) ≈ yield.perBatch_g (within 5%)
- Process: minimum 3 steps, thermal steps need time_min OR temp_c
- nutrition and cost fields: set to null (will be calculated later)

STRUCTURE:
{
  "meta": {"title": "Dish Name", "version": "2.0", "cuisine": "cuisine_type", "tags": []},
  "portions": 4,
  "yield": {"perPortion_g": 200.0, "perBatch_g": 800.0},
  "ingredients": [{"name": "Ingredient", "unit": "g", "brutto_g": 100.0, "loss_pct": 10.0, "netto_g": 90.0, "allergens": []}],
  "process": [{"n": 1, "action": "Step description", "time_min": 10.0, "temp_c": 180.0}],
  "storage": {"conditions": "Storage conditions", "shelfLife_hours": 48.0, "servingTemp_c": 65.0},
  "nutrition": {"per100g": null, "perPortion": null},
  "cost": {"rawCost": null, "costPerPortion": null},
  "printNotes": []
}"""

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