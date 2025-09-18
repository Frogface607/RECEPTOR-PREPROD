import { useState, useEffect, useCallback } from 'react'

export interface TokensState {
  total: number
  earned_today: number
  last_earned_date: string
}

export interface TokenReward {
  amount: number
  reason: string
  type: 'bug' | 'feature' | 'ux'
  bonus?: string
}

export type UserLevel = 'Начинающий' | 'Активный' | 'Эксперт'

const STORAGE_KEY = 'user_tokens'
const DEFAULT_STATE: TokensState = {
  total: 0,
  earned_today: 0,
  last_earned_date: new Date().toDateString()
}

// Награды за разные типы репортов
export const TOKEN_REWARDS = {
  bug: { amount: 5, reason: 'Обнаружение бага' },
  critical_bug: { amount: 25, reason: 'Критический баг', bonus: 'Неделя PRO' },
  feature: { amount: 10, reason: 'Предложение функции' },
  ux: { amount: 10, reason: 'UX предложение', bonus: 'Бейдж "Дизайнер"' }
} as const

// Уровни пользователей
export const USER_LEVELS = {
  beginner: { name: 'Начинающий' as UserLevel, min: 0, max: 100 },
  active: { name: 'Активный' as UserLevel, min: 100, max: 500 },
  expert: { name: 'Эксперт' as UserLevel, min: 500, max: Infinity }
}

export function useTokens() {
  const [tokensState, setTokensState] = useState<TokensState>(DEFAULT_STATE)
  const [animationQueue, setAnimationQueue] = useState<TokenReward[]>([])

  // Загрузка состояния из localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        const today = new Date().toDateString()
        
        // Сброс daily счетчика если новый день
        if (parsed.last_earned_date !== today) {
          parsed.earned_today = 0
          parsed.last_earned_date = today
        }
        
        setTokensState(parsed)
      }
    } catch (error) {
      console.warn('Failed to load tokens from localStorage:', error)
    }
  }, [])

  // Сохранение в localStorage при изменении
  const saveTokensState = useCallback((newState: TokensState) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newState))
      setTokensState(newState)
    } catch (error) {
      console.warn('Failed to save tokens to localStorage:', error)
    }
  }, [])

  // Получение текущего уровня пользователя
  const getCurrentLevel = useCallback((): UserLevel => {
    const { total } = tokensState
    
    if (total >= USER_LEVELS.expert.min) return USER_LEVELS.expert.name
    if (total >= USER_LEVELS.active.min) return USER_LEVELS.active.name
    return USER_LEVELS.beginner.name
  }, [tokensState.total])

  // Прогресс до следующего уровня
  const getLevelProgress = useCallback(() => {
    const { total } = tokensState
    
    if (total >= USER_LEVELS.expert.min) {
      return { current: total, max: USER_LEVELS.expert.max, progress: 100 }
    }
    
    if (total >= USER_LEVELS.active.min) {
      return {
        current: total - USER_LEVELS.active.min,
        max: USER_LEVELS.expert.min - USER_LEVELS.active.min,
        progress: ((total - USER_LEVELS.active.min) / (USER_LEVELS.expert.min - USER_LEVELS.active.min)) * 100
      }
    }
    
    return {
      current: total,
      max: USER_LEVELS.active.min,
      progress: (total / USER_LEVELS.active.min) * 100
    }
  }, [tokensState.total])

  // Добавление токенов
  const addTokens = useCallback((reward: TokenReward) => {
    const today = new Date().toDateString()
    const newState: TokensState = {
      total: tokensState.total + reward.amount,
      earned_today: tokensState.last_earned_date === today 
        ? tokensState.earned_today + reward.amount 
        : reward.amount,
      last_earned_date: today
    }
    
    saveTokensState(newState)
    
    // Добавить анимацию в очередь
    setAnimationQueue(prev => [...prev, reward])
  }, [tokensState, saveTokensState])

  // Очистка очереди анимаций
  const clearAnimationQueue = useCallback(() => {
    setAnimationQueue([])
  }, [])

  // Получение награды по типу баг-репорта
  const getRewardForReportType = useCallback((type: 'bug' | 'feature' | 'ux', priority?: string): TokenReward => {
    if (type === 'bug' && priority === 'critical') {
      return { ...TOKEN_REWARDS.critical_bug, type: 'bug' }
    }
    
    return { 
      ...TOKEN_REWARDS[type], 
      type 
    }
  }, [])

  return {
    // Состояние
    ...tokensState,
    animationQueue,
    
    // Методы
    addTokens,
    clearAnimationQueue,
    getCurrentLevel,
    getLevelProgress,
    getRewardForReportType,
    
    // Computed properties
    level: getCurrentLevel(),
    levelProgress: getLevelProgress()
  }
}