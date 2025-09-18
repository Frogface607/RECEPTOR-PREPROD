import { useState, useEffect, useCallback } from 'react'

export type OnboardingStep = 'welcome' | 'setup' | 'first-success' | 'explore'
export type UserRole = 'chef' | 'owner' | 'manager'

export interface OnboardingState {
  currentStep: OnboardingStep
  isCompleted: boolean
  isVisible: boolean
  userRole?: UserRole
  startTime?: number
}

const STORAGE_KEY = 'onboarding_completed'
const PROGRESS_KEY = 'onboarding_progress'

const STEP_ORDER: OnboardingStep[] = ['welcome', 'setup', 'first-success', 'explore']

const STEP_DURATIONS = {
  welcome: 30,      // 30 seconds
  setup: 60,        // 1 minute  
  'first-success': 180, // 3 minutes
  explore: 90       // 1.5 minutes
} // Total: 6 minutes

export function useOnboarding() {
  const [state, setState] = useState<OnboardingState>({
    currentStep: 'welcome',
    isCompleted: false, // Allow onboarding to show for new users
    isVisible: false
  })

  // Initialize onboarding state
  useEffect(() => {
    const isCompleted = localStorage.getItem(STORAGE_KEY) === 'true'
    const savedProgress = localStorage.getItem(PROGRESS_KEY)
    
    let currentStep: OnboardingStep = 'welcome'
    let userRole: UserRole | undefined
    
    if (savedProgress) {
      try {
        const progress = JSON.parse(savedProgress)
        currentStep = progress.currentStep || 'welcome'
        userRole = progress.userRole
      } catch (e) {
        console.warn('Failed to parse onboarding progress:', e)
      }
    }

    setState({
      currentStep,
      isCompleted,
      isVisible: !isCompleted,
      userRole,
      startTime: isCompleted ? undefined : Date.now()
    })
  }, [])

  // Save progress to localStorage
  const saveProgress = useCallback((newState: Partial<OnboardingState>) => {
    const progress = {
      currentStep: newState.currentStep || state.currentStep,
      userRole: newState.userRole || state.userRole,
      timestamp: Date.now()
    }
    localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress))
  }, [state.currentStep, state.userRole])

  // Complete onboarding
  const completeOnboarding = useCallback(() => {
    localStorage.setItem(STORAGE_KEY, 'true')
    localStorage.removeItem(PROGRESS_KEY)
    
    setState(prev => ({
      ...prev,
      isCompleted: true,
      isVisible: false
    }))
  }, [])

  // Start onboarding (for manual restart)
  const startOnboarding = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(PROGRESS_KEY)
    
    setState({
      currentStep: 'welcome',
      isCompleted: false,
      isVisible: true,
      startTime: Date.now()
    })
  }, [])

  // Navigate to next step
  const nextStep = useCallback(() => {
    const currentIndex = STEP_ORDER.indexOf(state.currentStep)
    
    if (currentIndex < STEP_ORDER.length - 1) {
      const nextStep = STEP_ORDER[currentIndex + 1]
      const newState = { ...state, currentStep: nextStep }
      
      setState(newState)
      saveProgress(newState)
    } else {
      // Last step completed
      completeOnboarding()
    }
  }, [state, saveProgress, completeOnboarding])

  // Navigate to previous step
  const prevStep = useCallback(() => {
    const currentIndex = STEP_ORDER.indexOf(state.currentStep)
    
    if (currentIndex > 0) {
      const prevStep = STEP_ORDER[currentIndex - 1]
      const newState = { ...state, currentStep: prevStep }
      
      setState(newState)
      saveProgress(newState)
    }
  }, [state, saveProgress])

  // Skip onboarding
  const skipOnboarding = useCallback(() => {
    console.log('Skipping onboarding - setting completed = true')
    localStorage.setItem(STORAGE_KEY, 'true')
    localStorage.removeItem(PROGRESS_KEY)
    
    setState(prev => ({
      ...prev,
      isCompleted: true,
      isVisible: false
    }))
    
    // Force reload if needed
    setTimeout(() => {
      if (window.location.href.includes('emergentagent.com')) {
        console.log('Force reloading to close onboarding')
        window.location.reload()
      }
    }, 500)
  }, [])

  // Set user role (used in setup step)
  const setUserRole = useCallback((role: UserRole) => {
    const newState = { ...state, userRole: role }
    setState(newState)
    saveProgress(newState)
  }, [state, saveProgress])

  // Hide onboarding without completing
  const hideOnboarding = useCallback(() => {
    setState(prev => ({ ...prev, isVisible: false }))
  }, [])

  // Get current step info
  const getCurrentStepInfo = useCallback(() => {
    const currentIndex = STEP_ORDER.indexOf(state.currentStep)
    const progress = ((currentIndex + 1) / STEP_ORDER.length) * 100
    const estimatedDuration = STEP_DURATIONS[state.currentStep]
    
    // Calculate total elapsed time
    const elapsedTime = state.startTime ? Math.floor((Date.now() - state.startTime) / 1000) : 0
    const totalEstimatedTime = Object.values(STEP_DURATIONS).reduce((sum, duration) => sum + duration, 0)
    
    return {
      stepNumber: currentIndex + 1,
      totalSteps: STEP_ORDER.length,
      progress,
      estimatedDuration,
      elapsedTime,
      totalEstimatedTime,
      isFirstStep: currentIndex === 0,
      isLastStep: currentIndex === STEP_ORDER.length - 1
    }
  }, [state.currentStep, state.startTime])

  return {
    ...state,
    nextStep,
    prevStep,
    skipOnboarding,
    startOnboarding,
    completeOnboarding,
    setUserRole,
    hideOnboarding,
    getCurrentStepInfo,
    // Computed properties
    canGoBack: STEP_ORDER.indexOf(state.currentStep) > 0,
    canGoNext: STEP_ORDER.indexOf(state.currentStep) < STEP_ORDER.length - 1
  }
}