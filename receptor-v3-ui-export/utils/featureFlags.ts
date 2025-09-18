import { useState, useEffect } from 'react'
import axios from 'axios'

export interface FeatureFlags {
  inline_editing: boolean        // инлайн правки ТТК
  ai_editing: boolean            // AI-поле снизу ТТК
  export_master: boolean         // мастер экспорта (PRO)
  menu_generator: boolean        // «Мои меню» (PRO)
  iiko_setup: boolean            // мастер интеграции iiko
  lab_ai_advisor: boolean        // AI-советчик (чат)
  lab_food_pairing: boolean      // Food Pairing
  lab_sales_scripts: boolean     // Скрипты продаж
  lab_batch_ops: boolean         // Массовые операции
  lab_cascade_v2: boolean        // Каскадная генерация
  analytics_pro: boolean         // Расширенная аналитика
  bug_report_ui: boolean         // форма баг-репорта
  tokens_system: boolean         // токены/очки вдохновения
  onboarding: boolean            // система онбординга
  demo_fallback: boolean         // demo-fallback при недоступном API
  enable_pro_rollout: boolean    // канареечный rollout PRO функций
}

export const DEFAULT_FLAGS: FeatureFlags = {
  inline_editing: true,        // инлайн правки ТТК
  ai_editing: true,            // AI-поле снизу ТТК
  export_master: getCanaryFlag('export_master', 10),  // мастер экспорта (PRO) - 10% пользователей
  menu_generator: false,       // «Мои меню» (PRO) - отключено в MVP
  iiko_setup: true,            // мастер интеграции iiko
  lab_ai_advisor: false,       // AI-советчик (чат) - будущая фича
  lab_food_pairing: false,     // Food Pairing - будущая фича
  lab_sales_scripts: false,    // Скрипты продаж - будущая фича
  lab_batch_ops: false,        // Массовые операции - будущая фича
  lab_cascade_v2: false,       // Каскадная генерация - будущая фича
  analytics_pro: getCanaryFlag('analytics_pro', 5),    // Расширенная аналитика - 5% пользователей
  bug_report_ui: true,         // форма баг-репорта
  tokens_system: false,        // токены/очки вдохновения - будущая фича
  onboarding: true,            // система онбординга
  demo_fallback: false,         // demo-fallback ОТКЛЮЧЕН - используем новый OpenAI ключ!
  enable_pro_rollout: true      // канареечный rollout PRO функций
}

// User plan types for PRO gating
export type UserPlan = 'free' | 'pro' | 'enterprise'

// Canary rollout function - gradually enables features for percentage of users
function getCanaryFlag(featureName: string, percentage: number): boolean {
  if (percentage <= 0) return false
  if (percentage >= 100) return true
  
  // Use user session or device fingerprint for consistent behavior
  const userHash = hashString(getUserId() + featureName)
  return (userHash % 100) < percentage
}

// Simple hash function for consistent user bucketing
function hashString(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32-bit integer
  }
  return Math.abs(hash)
}

// Get consistent user ID (in real app this would be actual user ID)
function getUserId(): string {
  let userId = localStorage.getItem('canary_user_id')
  if (!userId) {
    userId = 'user_' + Math.random().toString(36).substr(2, 9)
    localStorage.setItem('canary_user_id', userId)
  }
  return userId
}

// Mock user plan - in real app this would come from API/context
export const getUserPlan = (): UserPlan => {
  // This would typically come from user context, API, or localStorage
  return 'free' // Default to free for demo
}

interface UseFeatureFlagsReturn {
  flags: FeatureFlags
  isEnabled: (flagName: keyof FeatureFlags) => boolean
  loading: boolean
  error: string | null
}

export function useFeatureFlags(): UseFeatureFlagsReturn {
  const [flags, setFlags] = useState<FeatureFlags>(DEFAULT_FLAGS)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadFeatureFlags = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // For now, use local defaults (server endpoint not implemented yet)
        console.log('Using local feature flags configuration')
        setFlags(DEFAULT_FLAGS)
        
        // TODO: Implement server-side feature flags endpoint
        // const response = await axios.get('/api/feature-flags', {
        //   timeout: 5000
        // })
        // 
        // if (response.data && typeof response.data === 'object') {
        //   const serverFlags = { ...DEFAULT_FLAGS, ...response.data }
        //   setFlags(serverFlags)
        // } else {
        //   setFlags(DEFAULT_FLAGS)
        // }
      } catch (err) {
        console.warn('Failed to load feature flags from server, using defaults:', err)
        setError('Failed to load feature flags from server')
        setFlags(DEFAULT_FLAGS)
      } finally {
        setLoading(false)
      }
    }

    loadFeatureFlags()
  }, [])

  const isEnabled = (flagName: keyof FeatureFlags): boolean => {
    return Boolean(flags[flagName])
  }

  return {
    flags,
    isEnabled,
    loading,
    error
  }
}