import { createGenerationRequest, cancelRequest, api } from './api'
import { TechCardV2 } from '../types/techcard-v2'
import { generateSmartDemoTechCard } from '../utils/demoData_smart'

const API_BASE = '/api'

// Request ID for generation requests (for cancellation)
let currentGenerationRequestId = 'techcard-generation'

// Import feature flags directly 
import { DEFAULT_FLAGS } from '../utils/featureFlags'

// Check if demo fallback should be used
const shouldUseDemoFallback = (): boolean => {
  // CRITICAL FIX: Use actual feature flags instead of localStorage
  console.log('🎛️ Demo fallback setting:', DEFAULT_FLAGS.demo_fallback)
  return DEFAULT_FLAGS.demo_fallback
}

// Simulate generation delay for demo
const simulateGenerationDelay = (ms: number = 3000): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export const techCardApi = {
  // Generate tech card with REAL API (no more demo fallback by default)
  generate: async (dishName: string): Promise<TechCardV2> => {
    try {
      console.log(`🎯 Generating REAL tech card for: ${dishName}`)
      
      // Use correct V2 API endpoint
      const payload = {
        name: dishName.trim(),
        cuisine: "русская",
        equipment: [],
        budget: null,
        dietary: []
      }

      const response = await createGenerationRequest(
        `${API_BASE}/v1/techcards.v2/generate`,
        payload,
        currentGenerationRequestId
      )
      
      console.log(`✅ Tech card V2 API response received`, response.data)
      
      // Extract tech card from V2 API response
      const cardData = response.data.card
      
      if (!cardData) {
        throw new Error('No card data returned from API')
      }
      
      console.log('🎯 REAL tech card data received:', cardData)
      
      // Return the actual tech card data from API
      return cardData as TechCardV2
      
    } catch (error: any) {
      console.error('TechCard generation failed:', error.message)
      
      // Check if demo fallback is enabled and should be used
      if (shouldUseDemoFallback()) {
        console.log('🎭 Demo fallback is ENABLED, using demo data')
        // Simulate generation time for better UX
        await simulateGenerationDelay(2000)
        
        console.log('🎭 Using SMART demo data for:', dishName)
        const smartDemoCard = generateSmartDemoTechCard(dishName)
        
        // Add smart demo marker
        return {
          ...smartDemoCard,
          title: `${smartDemoCard.title} (УМНЫЕ ДЕМО-ДАННЫЕ)`,
          meta: {
            ...smartDemoCard.meta,
            isDemoData: true,
            demoReason: 'LLM недоступен из-за бюджетных ограничений - показаны умные демо-данные на основе названия блюда'
          }
        }
      }
      
      console.log('🚫 Demo fallback is DISABLED, throwing error')
      // If no demo fallback, throw the original error
      throw error
    }
  },

  // Save tech card to library
  save: async (techCard: TechCardV2, userId: string = 'anonymous'): Promise<{ success: boolean; id?: string }> => {
    try {
      console.log(`💾 Saving tech card to library: ${techCard.title}`)
      
      const response = await api.post(`${API_BASE}/v1/techcards.v2/save`, {
        techcard: techCard,
        user_id: userId,
        library_name: 'My Library'
      })
      
      console.log('✅ Tech card saved successfully:', response.data)
      
      return {
        success: true,
        id: response.data.id
      }
    } catch (error: any) {
      console.error('Failed to save tech card:', error)
      return {
        success: false
      }
    }
  },

  // Get user's tech cards list
  getUserTechCards: async (userId: string = 'anonymous'): Promise<TechCardV2[]> => {
    try {
      console.log(`📚 Loading user tech cards for: ${userId}`)
      
      const response = await api.get(`${API_BASE}/v1/techcards.v2/list/${userId}`)
      
      console.log('✅ User tech cards loaded:', response.data)
      
      return response.data.techcards || []
    } catch (error: any) {
      console.error('Failed to load user tech cards:', error)
      return []
    }
  },

  // Get tech card by ID
  getTechCardById: async (techCardId: string): Promise<TechCardV2 | null> => {
    try {
      console.log(`🔍 Loading tech card by ID: ${techCardId}`)
      
      const response = await api.get(`${API_BASE}/v1/techcards.v2/${techCardId}`)
      
      console.log('✅ Tech card loaded by ID:', response.data)
      
      return response.data.techcard
    } catch (error: any) {
      console.error('Failed to load tech card by ID:', error)
      return null
    }
  },

  // Cancel current generation
  cancelGeneration: () => {
    console.log('🛑 Cancelling tech card generation')
    cancelRequest(currentGenerationRequestId)
  },

  // Legacy methods for compatibility
  validateDishName: async (dishName: string) => {
    return { valid: dishName.trim().length > 0, message: dishName.trim().length > 0 ? 'OK' : 'Dish name required' }
  },

  validateEditPrompt: async (prompt: string) => {
    return { valid: prompt.trim().length > 0, message: prompt.trim().length > 0 ? 'OK' : 'Edit prompt required' }
  },

  edit: async (techCard: TechCardV2, editPrompt: string) => {
    // TODO: Implement AI editing
    console.warn('AI editing not implemented yet')
    return techCard
  },

  export: async (techCard: TechCardV2, format: string = 'pdf') => {
    try {
      console.log(`📄 Exporting tech card as ${format}:`, techCard.title)
      
      const response = await api.post(`${API_BASE}/export`, {
        techcard: techCard,
        format: format
      })
      
      console.log('✅ Export successful:', response.data)
      return response.data
    } catch (error: any) {
      console.error('Export failed:', error)
      throw error
    }
  },

  list: async (userId: string = 'anonymous') => {
    return techCardApi.getUserTechCards(userId)
  },

  getById: async (techCardId: string) => {
    return techCardApi.getTechCardById(techCardId)
  }
}