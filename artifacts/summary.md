# TechCard Generation Workflow Test Summary

## Test Specification
**Generate new TechCards → PF-02→EX-03: preflight→zip + XLSX @-format (credit-safe)**

Executed: 2025-08-25T20:36:31.805681

## Configuration
- **Dish Names**: Тест Блюдо 1, Тест Блюдо 2, Тест Блюдо 3
- **Portions**: 1
- **Operational Rounding**: True
- **Backend URL**: https://menu-designer-ai.preview.emergentagent.com

## Results Overview
- **Total Tests**: 9
- **Passed**: 9
- **Failed**: 0
- **Success Rate**: 100.0%

## Workflow Results
- **Tech Cards Generated**: 3/3
- **Generation Success Rate**: 100.0%

## Acceptance Criteria Status
- **All Generate Http 200**: ✅ PASS
- **Gx02 Validation Passes**: ✅ PASS
- **Preflight Correct**: ✅ PASS
- **Zip Contains Expected Files**: ✅ PASS
- **Xlsx Articles Text Format**: ✅ PASS
- **No Guid Code In Articles**: ⚠️ N/A

## Detailed Test Results
- **Generate TechCard: Тест Блюдо 1**: ✅ PASS
  - Details: Generated techcard ID: 7d6bfb27-64a7-4500-8231-16ef88118934, Status: draft
  - Response Time: 11.494s
- **Generate TechCard: Тест Блюдо 2**: ✅ PASS
  - Details: Generated techcard ID: e379d95e-3f5c-4ee9-8cd2-3480a739ef67, Status: draft
  - Response Time: 11.618s
- **Generate TechCard: Тест Блюдо 3**: ✅ PASS
  - Details: Generated techcard ID: bdd32562-f14e-4969-910b-8a8d219a3f03, Status: draft
  - Response Time: 11.422s
- **Validate TechCard: 7d6bfb27-64a7-4500-8231-16ef88118934**: ✅ PASS
  - Details: GX-02 validation: PASS, Score: 0, Issues: 0
  - Response Time: 0.011s
- **Validate TechCard: e379d95e-3f5c-4ee9-8cd2-3480a739ef67**: ✅ PASS
  - Details: GX-02 validation: PASS, Score: 0, Issues: 0
  - Response Time: 0.009s
- **Validate TechCard: bdd32562-f14e-4969-910b-8a8d219a3f03**: ✅ PASS
  - Details: GX-02 validation: PASS, Score: 0, Issues: 0
  - Response Time: 0.009s
- **Preflight Check**: ✅ PASS
  - Details: Counts: {'dishSkeletons': 0, 'productSkeletons': 0}, Missing: {'dishes': [], 'products': []}, TTK Date: 2025-08-25
  - Response Time: 0.098s
- **ZIP Export**: ✅ PASS
  - Details: ZIP exported successfully, size: 5143 bytes
  - Response Time: 0.056s
- **XLSX Format Validation**: ✅ PASS
  - Details: Files: 1, Issues: []
  - Response Time: 0.012s

## Artifacts Created
- `/app/artifacts/gen_runs.json`
- `/app/artifacts/validation.json`
- `/app/artifacts/preflight.json`
- `/app/artifacts/export.json`
- `/app/artifacts/xlsx_checks.json`
- `/app/artifacts/summary.md`
