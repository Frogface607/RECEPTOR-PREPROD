# Rebuild Export Wizard Test Summary

## Overall Statistics
- Total Tests: 7
- Passed: 3
- Failed: 4
- Success Rate: 42.9%

## Generated Tech Cards
- c2af1b0f-a9cd-4c71-8c76-b3a3fa9eba7d

## Test Results
- ❌ FAIL: Generate TechCard: Борщ украинский с говядиной (N/A) - Exception: 
- ✅ PASS: Generate TechCard: Стейк из говядины с картофельным пюре (15.101s) - ID: c2af1b0f-a9cd-4c71-8c76-b3a3fa9eba7d
- ✅ PASS: Preflight Check (0.145s) - TTK Date: 2025-08-26, Dish Skeletons: 1, Product Skeletons: 6
- ❌ FAIL: ZIP Export (0.057s) - HTTP 400: {"detail":{"error":"PRE_FLIGHT_REQUIRED","message":"Нельзя экспортировать ТК без создания блюд в iiko. Сначала импортируйте скелеты блюд.","missing_dishes":[{"id":"dish_Стейк_из_говядины_с_картофельны
- ❌ FAIL: Anti-Mock Scan (N/A) - Found 8 mock signatures
- ✅ PASS: Excel Invariants (N/A) - No articles found to validate
- ❌ FAIL: TTK↔Skeletons Reconcile (N/A) - Dish articles match: False, Product articles match: False, GENERATED_* count: 0

## Artifacts Generated
- gen_runs.json
- preflight.json
- mock_scan.json
- xlsx_checks.json
- reconcile.json
