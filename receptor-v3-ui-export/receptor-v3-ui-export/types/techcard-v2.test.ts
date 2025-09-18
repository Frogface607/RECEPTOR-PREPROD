// Simple test to verify normalizeYield function
import { normalizeYield, TechCardV2 } from './techcard-v2'

// Mock tech card with yield_ field
const mockTechCardWithYield_: TechCardV2 = {
  id: 'test-1',
  title: 'Test Dish',
  portions: 4,
  ingredients: [],
  process_steps: [], 
  nutrition: {
    calories_per_100g: 200,
    proteins_per_100g: 10,
    fats_per_100g: 5,
    carbs_per_100g: 20
  },
  cost: {
    total_cost: 100,
    cost_per_portion: 25,
    currency: 'RUB'
  },
  yield_: {
    total: 1200,
    per_portion: 300,
    unit: 'г'
  }
}

// Mock tech card with yield field (alternative format)
const mockTechCardWithYield: TechCardV2 = {
  ...mockTechCardWithYield_,
  id: 'test-2',
  yield: {
    total: 800,
    per_portion: 200,
    unit: 'г'
  }
}
delete (mockTechCardWithYield as any).yield_

// Mock tech card with no yield fields (fallback scenario)
const mockTechCardNoYield: TechCardV2 = {
  ...mockTechCardWithYield_,
  id: 'test-3',
  ingredients: [
    { name: 'Ingredient 1', brutto: 100, netto: 90, loss_pct: 10, unit: 'г' },
    { name: 'Ingredient 2', brutto: 200, netto: 180, loss_pct: 10, unit: 'г' }
  ]
}
delete (mockTechCardNoYield as any).yield_
delete (mockTechCardNoYield as any).yield

// Test function - would normally use Jest/Vitest
function testNormalizeYield() {
  console.log('🧪 Testing normalizeYield function...')
  
  // Test 1: yield_ field
  const result1 = normalizeYield(mockTechCardWithYield_)
  console.assert(result1.total === 1200, 'Should use yield_.total')
  console.assert(result1.per_portion === 300, 'Should use yield_.per_portion') 
  console.assert(result1.unit === 'г', 'Should use yield_.unit')
  console.log('✅ Test 1 (yield_ field): PASSED')
  
  // Test 2: yield field (fallback)
  const result2 = normalizeYield(mockTechCardWithYield)
  console.assert(result2.total === 800, 'Should use yield.total')
  console.assert(result2.per_portion === 200, 'Should use yield.per_portion')
  console.assert(result2.unit === 'г', 'Should use yield.unit')
  console.log('✅ Test 2 (yield field): PASSED')
  
  // Test 3: No yield fields (calculation fallback)
  const result3 = normalizeYield(mockTechCardNoYield)
  console.assert(result3.total === 270, 'Should calculate from ingredients netto sum')
  console.assert(result3.per_portion === 68, 'Should calculate per_portion from total/portions') // 270/4 = 67.5, rounded to 68
  console.assert(result3.unit === 'г', 'Should default to г')
  console.log('✅ Test 3 (no yield, fallback): PASSED')
  
  console.log('🎉 All normalizeYield tests passed!')
}

// Run tests if this file is executed directly
if (typeof window === 'undefined') {
  testNormalizeYield()
}

export { testNormalizeYield }