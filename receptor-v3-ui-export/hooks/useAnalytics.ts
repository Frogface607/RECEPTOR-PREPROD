import { useCallback } from 'react'
import { api } from '../services/api'

// Session management
const getSessionId = (): string => {
  let sessionId = sessionStorage.getItem('analytics_session_id')
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    sessionStorage.setItem('analytics_session_id', sessionId)
  }
  return sessionId
}

// User ID management (could be extended with proper auth)
const getUserId = (): string | null => {
  return localStorage.getItem('user_id') || null
}

export interface AnalyticsEvent {
  event_type: string
  user_id?: string | null
  session_id?: string
  properties?: Record<string, any>
  timestamp?: Date
}

export interface OnboardingEvent {
  event_type: 'onboarding_start' | 'onboarding_step' | 'onboarding_complete' | 'onboarding_skip'
  step?: 'welcome' | 'setup' | 'first-success' | 'explore'
  user_role?: 'chef' | 'owner' | 'manager'
  elapsed_time_ms?: number
  user_id?: string | null
  session_id?: string
}

export interface TTFVEvent {
  event_type: 'ttfv_start' | 'ttfv_success' | 'ttfv_demo_success'
  ttfv_seconds?: number
  generation_type?: 'real' | 'demo'
  dish_name?: string
  user_id?: string | null
  session_id?: string
}

export interface TechCardEvent {
  event_type: 'tc_generate_start' | 'tc_generate_success' | 'tc_generate_error' | 'tc_save_success'
  techcard_id?: string
  dish_name?: string
  generation_time_ms?: number
  error_message?: string
  user_id?: string | null
  session_id?: string
}

export interface ExportEvent {
  event_type: 'export_success' | 'export_error'
  export_type?: 'pdf' | 'excel' | 'iiko' | 'zip'
  techcard_count?: number
  file_size_bytes?: number
  error_message?: string
  user_id?: string | null
  session_id?: string
}

export interface BillingEvent {
  event_type: 'billing_success' | 'billing_cancel' | 'billing_upgrade_attempt'
  plan_id?: 'pro_monthly_ru' | 'pro_annual_ru'
  amount?: string
  currency?: string
  payment_system?: 'yookassa' | 'stripe'
  user_id?: string | null
  session_id?: string
}

export const useAnalytics = () => {
  const trackEvent = useCallback(async (event: AnalyticsEvent) => {
    try {
      const sessionId = getSessionId()
      const userId = getUserId()
      
      const eventData = {
        ...event,
        user_id: event.user_id || userId,
        session_id: event.session_id || sessionId,
        timestamp: event.timestamp || new Date()
      }
      
      await api.post('/api/analytics/events', eventData)
    } catch (error) {
      console.warn('Failed to track analytics event:', error)
    }
  }, [])

  const trackOnboarding = useCallback(async (event: OnboardingEvent) => {
    try {
      const sessionId = getSessionId()
      const userId = getUserId()
      
      const eventData = {
        ...event,
        user_id: event.user_id || userId,
        session_id: event.session_id || sessionId
      }
      
      await api.post('/api/analytics/onboarding', eventData)
    } catch (error) {
      console.warn('Failed to track onboarding event:', error)
    }
  }, [])

  const trackTTFV = useCallback(async (event: TTFVEvent) => {
    try {
      const sessionId = getSessionId()
      const userId = getUserId()
      
      const eventData = {
        ...event,
        user_id: event.user_id || userId,
        session_id: event.session_id || sessionId
      }
      
      await api.post('/api/analytics/ttfv', eventData)
    } catch (error) {
      console.warn('Failed to track TTFV event:', error)
    }
  }, [])

  const trackTechCard = useCallback(async (event: TechCardEvent) => {
    try {
      const sessionId = getSessionId()
      const userId = getUserId()
      
      const eventData = {
        ...event,
        user_id: event.user_id || userId,
        session_id: event.session_id || sessionId
      }
      
      await api.post('/api/analytics/techcard', eventData)
    } catch (error) {
      console.warn('Failed to track tech card event:', error)
    }
  }, [])

  const trackExport = useCallback(async (event: ExportEvent) => {
    try {
      const sessionId = getSessionId()
      const userId = getUserId()
      
      const eventData = {
        ...event,
        user_id: event.user_id || userId,
        session_id: event.session_id || sessionId
      }
      
      await api.post('/api/analytics/export', eventData)
    } catch (error) {
      console.warn('Failed to track export event:', error)
    }
  }, [])

  const trackBilling = useCallback(async (event: BillingEvent) => {
    try {
      const sessionId = getSessionId()
      const userId = getUserId()
      
      const eventData = {
        ...event,
        user_id: event.user_id || userId,
        session_id: event.session_id || sessionId
      }
      
      await api.post('/api/analytics/billing', eventData)
    } catch (error) {
      console.warn('Failed to track billing event:', error)
    }
  }, [])

  // Helper methods with common patterns
  const trackOnboardingStart = useCallback(() => {
    trackOnboarding({ event_type: 'onboarding_start' })
  }, [trackOnboarding])

  const trackOnboardingStep = useCallback((step: OnboardingEvent['step'], userRole?: OnboardingEvent['user_role'], elapsedTimeMs?: number) => {
    trackOnboarding({ 
      event_type: 'onboarding_step', 
      step, 
      user_role: userRole,
      elapsed_time_ms: elapsedTimeMs 
    })
  }, [trackOnboarding])

  const trackOnboardingComplete = useCallback((elapsedTimeMs?: number) => {
    trackOnboarding({ 
      event_type: 'onboarding_complete',
      elapsed_time_ms: elapsedTimeMs
    })
  }, [trackOnboarding])

  const trackOnboardingSkip = useCallback((step?: OnboardingEvent['step'], elapsedTimeMs?: number) => {
    trackOnboarding({ 
      event_type: 'onboarding_skip', 
      step,
      elapsed_time_ms: elapsedTimeMs
    })
  }, [trackOnboarding])

  const trackTTFVStart = useCallback(() => {
    trackTTFV({ event_type: 'ttfv_start' })
  }, [trackTTFV])

  const trackTTFVSuccess = useCallback((options: {
    ttfvSeconds: number
    generationType: 'real' | 'demo'
    dishName?: string
  }) => {
    trackTTFV({ 
      event_type: 'ttfv_success',
      ttfv_seconds: options.ttfvSeconds,
      generation_type: options.generationType,
      dish_name: options.dishName
    })
  }, [trackTTFV])

  const trackTechCardGeneration = useCallback((dishName: string) => {
    trackTechCard({ 
      event_type: 'tc_generate_start',
      dish_name: dishName
    })
  }, [trackTechCard])

  const trackTechCardSuccess = useCallback((options: {
    techcardId: string
    dishName: string
    generationTimeMs: number
  }) => {
    trackTechCard({ 
      event_type: 'tc_generate_success',
      techcard_id: options.techcardId,
      dish_name: options.dishName,
      generation_time_ms: options.generationTimeMs
    })
  }, [trackTechCard])

  const trackTechCardSave = useCallback((options: {
    techcardId: string
    dishName: string
  }) => {
    trackTechCard({ 
      event_type: 'tc_save_success',
      techcard_id: options.techcardId,
      dish_name: options.dishName
    })
  }, [trackTechCard])

  const trackExportSuccess = useCallback((options: {
    exportType: ExportEvent['export_type']
    techcardCount: number
    fileSizeBytes?: number
  }) => {
    trackExport({ 
      event_type: 'export_success',
      export_type: options.exportType,
      techcard_count: options.techcardCount,
      file_size_bytes: options.fileSizeBytes
    })
  }, [trackExport])

  const trackBillingUpgradeAttempt = useCallback((options: {
    planId: BillingEvent['plan_id']
    amount: string
    currency: string
    paymentSystem: BillingEvent['payment_system']
  }) => {
    trackBilling({ 
      event_type: 'billing_upgrade_attempt',
      plan_id: options.planId,
      amount: options.amount,
      currency: options.currency,
      payment_system: options.paymentSystem
    })
  }, [trackBilling])

  const trackBillingSuccess = useCallback((options: {
    planId: BillingEvent['plan_id']
    amount: string
    currency: string
    paymentSystem: BillingEvent['payment_system']
  }) => {
    trackBilling({ 
      event_type: 'billing_success',
      plan_id: options.planId,
      amount: options.amount,
      currency: options.currency,
      payment_system: options.paymentSystem
    })
  }, [trackBilling])

  return {
    // Generic tracking
    trackEvent,
    trackOnboarding,
    trackTTFV,
    trackTechCard,
    trackExport,
    trackBilling,
    
    // Helper methods
    trackOnboardingStart,
    trackOnboardingStep,
    trackOnboardingComplete,
    trackOnboardingSkip,
    trackTTFVStart,
    trackTTFVSuccess,
    trackTechCardGeneration,
    trackTechCardSuccess,
    trackTechCardSave,
    trackExportSuccess,
    trackBillingUpgradeAttempt,
    trackBillingSuccess,
    
    // Utilities
    getSessionId,
    getUserId
  }
}