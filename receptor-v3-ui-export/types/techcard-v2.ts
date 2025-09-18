// TechCard V2 TypeScript definitions

export interface Ingredient {
  name: string
  brutto: number
  netto: number
  loss_pct: number
  unit: string
  article?: string
  product_code?: string
  sku_id?: string
}

export interface ProcessStep {
  title: string
  description: string
  duration_min?: number
  temperature_c?: number
  equipment?: string
}

export interface Nutrition {
  calories_per_100g: number
  proteins_per_100g: number
  fats_per_100g: number
  carbs_per_100g: number
  total_calories?: number
  total_proteins?: number
  total_fats?: number
  total_carbs?: number
}

export interface Cost {
  total_cost: number
  cost_per_portion: number
  currency: string
}

export interface Yield {
  total: number
  per_portion: number
  unit: string
}

export interface TechCardV2 {
  id: string
  title: string
  portions: number
  ingredients: Ingredient[]
  process_steps: ProcessStep[]
  nutrition: Nutrition
  cost: Cost
  // Handle both yield_ and yield fields from API
  yield_?: Yield
  yield?: Yield
  // Metadata
  meta?: {
    [key: string]: any
    raw_content?: string
    isDemoData?: boolean
    demoReason?: string
  }
  created_at?: string
  updated_at?: string
  status?: string
  category?: string
  description?: string
}

export interface GenerateTechCardRequest {
  dish_name: string
}

export interface GenerateTechCardResponse {
  techcard: TechCardV2
  generation_time_ms: number
  status: string
}

// Utility function to normalize yield field
export function normalizeYield(techcard: TechCardV2): Yield {
  const yieldData = techcard.yield_ || techcard.yield
  
  if (!yieldData) {
    // Fallback yield calculation
    const totalWeight = techcard.ingredients.reduce((sum, ing) => sum + ing.netto, 0)
    return {
      total: totalWeight,
      per_portion: Math.round(totalWeight / techcard.portions),
      unit: 'г'
    }
  }
  
  return {
    total: yieldData.total || 0,
    per_portion: yieldData.per_portion || Math.round((yieldData.total || 0) / techcard.portions),
    unit: yieldData.unit || 'г'
  }
}

// API Error types
export interface ApiError {
  message: string
  code?: string
  status?: number
}

export class TechCardApiError extends Error implements ApiError {
  code?: string
  status?: number
  
  constructor(message: string, code?: string, status?: number) {
    super(message)
    this.name = 'TechCardApiError'
    this.code = code
    this.status = status
  }
}