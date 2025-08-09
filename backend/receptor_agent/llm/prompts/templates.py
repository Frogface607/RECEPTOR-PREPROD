DRAFT_PROMPT = """You are an expert culinary R&D technologist for a pro kitchen.
Goal: propose a dish skeleton for the given venue profile.
Rules:
- Output JSON only (no text), matching the schema.
- Provide: name, category, cuisine; initial yield (portions/per_portion/total_net); a short process (2–4 steps).
- Ingredients must be realistic for the cuisine and equipment; put rough net/gross estimates (they will be normalized later).
- Units: use g/ml/pcs only.
"""

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