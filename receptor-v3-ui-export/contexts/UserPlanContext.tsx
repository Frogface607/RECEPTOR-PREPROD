import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'

export type UserPlan = 'free' | 'pro' | 'enterprise'

export interface UserPlanState {
  plan: UserPlan
  loading: boolean
  error: string | null
  subscriptionId?: string
  expiresAt?: string
  paymentSystem?: 'yookassa' | 'stripe'
  billingPeriod?: 'monthly' | 'annual'
}

export interface UserPlanContextType extends UserPlanState {
  refreshPlan: () => Promise<void>
  canUse: (feature: string) => boolean
  isPro: boolean
  isFree: boolean
  planDisplayName: string
}

const UserPlanContext = createContext<UserPlanContextType | undefined>(undefined)

// Feature to plan mapping
const FEATURE_PLAN_MAPPING: Record<string, UserPlan[]> = {
  // Free features (available to all)
  'techcard_generation': ['free', 'pro', 'enterprise'],
  'library_basic': ['free', 'pro', 'enterprise'],
  'pdf_export': ['free', 'pro', 'enterprise'],
  
  // PRO features
  'excel_export': ['pro', 'enterprise'],
  'iiko_export': ['pro', 'enterprise'],
  'zip_export': ['pro', 'enterprise'],
  'menu_generator': ['pro', 'enterprise'],
  'iiko_integration': ['pro', 'enterprise'],
  'ai_kitchen': ['pro', 'enterprise'],
  'analytics_pro': ['pro', 'enterprise'],
  'priority_support': ['pro', 'enterprise'],
  'bulk_operations': ['pro', 'enterprise'],
  'cascade_generation': ['pro', 'enterprise'],
  
  // Enterprise features (future)
  'team_management': ['enterprise'],
  'custom_integrations': ['enterprise'],
  'white_label': ['enterprise']
}

export const UserPlanProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<UserPlanState>({
    plan: 'free',
    loading: true,
    error: null
  })

  const fetchUserPlan = useCallback(async (): Promise<UserPlanState> => {
    try {
      // Try to get user profile from backend
      const response = await api.get('/api/user-profile/info')
      const userData = response.data

      if (userData && userData.plan) {
        return {
          plan: userData.plan as UserPlan,
          loading: false,
          error: null,
          subscriptionId: userData.subscription_id,
          expiresAt: userData.expires_at,
          paymentSystem: userData.payment_system,
          billingPeriod: userData.billing_period
        }
      }

      // Fallback to localStorage for now (development)
      const localPlan = localStorage.getItem('user_plan') as UserPlan
      if (localPlan && ['free', 'pro', 'enterprise'].includes(localPlan)) {
        return {
          plan: localPlan,
          loading: false,
          error: null
        }
      }

      // Default to free plan
      return {
        plan: 'free',
        loading: false,
        error: null
      }
    } catch (error: any) {
      console.warn('Failed to fetch user plan, using free plan:', error)
      
      // Fallback to localStorage on API error
      const localPlan = localStorage.getItem('user_plan') as UserPlan
      if (localPlan && ['free', 'pro', 'enterprise'].includes(localPlan)) {
        return {
          plan: localPlan,
          loading: false,
          error: null
        }
      }

      // Always fallback to free - never crash
      return {
        plan: 'free',
        loading: false,
        error: null // Don't show errors to users
      }
    }
  }, [])

  const refreshPlan = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true }))
    const newState = await fetchUserPlan()
    setState(newState)
    
    // Cache in localStorage for offline use
    localStorage.setItem('user_plan', newState.plan)
  }, [fetchUserPlan])

  // Initialize plan on mount
  useEffect(() => {
    refreshPlan()
  }, [refreshPlan])

  // Check if user can use a specific feature
  const canUse = useCallback((feature: string): boolean => {
    const requiredPlans = FEATURE_PLAN_MAPPING[feature]
    if (!requiredPlans) {
      // If feature is not defined, assume it's free
      return true
    }
    return requiredPlans.includes(state.plan)
  }, [state.plan])

  // Convenience properties
  const isPro = state.plan === 'pro' || state.plan === 'enterprise'
  const isFree = state.plan === 'free'
  
  const planDisplayName = {
    'free': 'Free',
    'pro': 'PRO',
    'enterprise': 'Enterprise'
  }[state.plan]

  const contextValue: UserPlanContextType = {
    ...state,
    refreshPlan,
    canUse,
    isPro,
    isFree,
    planDisplayName
  }

  return (
    <UserPlanContext.Provider value={contextValue}>
      {children}
    </UserPlanContext.Provider>
  )
}

export const useUserPlan = (): UserPlanContextType => {
  const context = useContext(UserPlanContext)
  if (context === undefined) {
    throw new Error('useUserPlan must be used within a UserPlanProvider')
  }
  return context
}

// Helper hook for PRO gating
export const usePROGating = () => {
  const { canUse, isPro, refreshPlan } = useUserPlan()
  
  const requiresPRO = useCallback((feature: string): boolean => {
    const requiredPlans = FEATURE_PLAN_MAPPING[feature]
    return requiredPlans ? !requiredPlans.includes('free') : false
  }, [])

  const checkFeatureAccess = useCallback((feature: string): {
    hasAccess: boolean
    requiresUpgrade: boolean
    requiredPlan: UserPlan
  } => {
    const hasAccess = canUse(feature)
    const requiredPlans = FEATURE_PLAN_MAPPING[feature] || ['free']
    const requiredPlan = requiredPlans.includes('free') ? 'free' : 'pro'
    
    return {
      hasAccess,
      requiresUpgrade: !hasAccess,
      requiredPlan
    }
  }, [canUse])

  return {
    canUse,
    isPro,
    requiresPRO,
    checkFeatureAccess,
    refreshPlan
  }
}