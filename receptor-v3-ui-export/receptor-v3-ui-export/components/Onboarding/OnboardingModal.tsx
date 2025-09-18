import React, { useEffect, useRef, useCallback } from 'react'
import { useOnboarding } from '../../hooks/useOnboarding'
import { useAnalytics } from '../../hooks/useAnalytics'
import { useFeatureFlags } from '../../utils/featureFlags'
import ProgressBar from './ProgressBar'
import WelcomeStep from './WelcomeStep'
import SetupStep from './SetupStep'
import FirstSuccessStep from './FirstSuccessStep'
import ExploreStep from './ExploreStep'

interface OnboardingModalProps {
  isVisible: boolean
  onClose?: () => void
}

const OnboardingModal: React.FC<OnboardingModalProps> = ({ 
  isVisible, 
  onClose 
}) => {
  const {
    currentStep,
    userRole,
    nextStep,
    prevStep,
    skipOnboarding,
    completeOnboarding,
    setUserRole,
    hideOnboarding,
    getCurrentStepInfo,
    canGoBack
  } = useOnboarding()

  const { isEnabled } = useFeatureFlags()
  const { 
    trackOnboardingStart,
    trackOnboardingStep,
    trackOnboardingComplete,
    trackOnboardingSkip
  } = useAnalytics()

  const modalRef = useRef<HTMLDivElement>(null)
  const stepInfo = getCurrentStepInfo()
  const analyticsEnabled = isEnabled('analytics_pro')

  // Define handlers first
  const handleClose = useCallback(() => {
    console.log('OnboardingModal: Закрытие онбординга...')
    if (analyticsEnabled) {
      const elapsedTime = stepInfo.elapsedTime * 1000
      trackOnboardingSkip(currentStep, elapsedTime)
    }
    skipOnboarding()
    onClose?.()
  }, [analyticsEnabled, stepInfo.elapsedTime, currentStep, trackOnboardingSkip, skipOnboarding, onClose])

  const handleSkip = useCallback(() => {
    console.log('OnboardingModal: Пропуск онбординга...')
    handleClose()
  }, [handleClose])

  const handleCreateOwn = useCallback(() => {
    // Close onboarding and trigger create flow
    if (analyticsEnabled) {
      const elapsedTime = stepInfo.elapsedTime * 1000
      trackOnboardingComplete(elapsedTime)
    }
    completeOnboarding()
    onClose?.()
  }, [analyticsEnabled, stepInfo.elapsedTime, trackOnboardingComplete, completeOnboarding, onClose])

  const handleComplete = useCallback(() => {
    if (analyticsEnabled) {
      const elapsedTime = stepInfo.elapsedTime * 1000
      trackOnboardingComplete(elapsedTime)
    }
    completeOnboarding()
  }, [analyticsEnabled, stepInfo.elapsedTime, trackOnboardingComplete, completeOnboarding])

  // Handle overlay click
  const handleOverlayClick = useCallback((e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      handleClose()
    }
  }, [handleClose])

  // Track onboarding start
  useEffect(() => {
    if (isVisible && analyticsEnabled) {
      trackOnboardingStart()
    }
  }, [isVisible, analyticsEnabled, trackOnboardingStart])

  // Track step changes
  useEffect(() => {
    if (isVisible && analyticsEnabled) {
      const elapsedTime = stepInfo.elapsedTime * 1000 // Convert to ms
      trackOnboardingStep(currentStep, userRole, elapsedTime)
    }
  }, [currentStep, userRole, stepInfo.elapsedTime, isVisible, analyticsEnabled, trackOnboardingStep])

  // Handle ESC key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isVisible) {
        handleClose()
      }
    }

    if (isVisible) {
      document.addEventListener('keydown', handleEsc)
      document.body.style.overflow = 'hidden' // Prevent background scroll
    }

    return () => {
      document.removeEventListener('keydown', handleEsc)
      document.body.style.overflow = 'unset'
    }
  }, [isVisible, handleClose])

  // Focus management
  useEffect(() => {
    if (isVisible && modalRef.current) {
      const focusableElements = modalRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )
      const firstElement = focusableElements[0] as HTMLElement
      if (firstElement) {
        firstElement.focus()
      }
    }
  }, [isVisible, currentStep])

  if (!isVisible) return null

  const renderStep = () => {
    switch (currentStep) {
      case 'welcome':
        return (
          <WelcomeStep
            onNext={nextStep}
            onSkip={handleSkip}
          />
        )
      
      case 'setup':
        return (
          <SetupStep
            userRole={userRole}
            onNext={nextStep}
            onBack={prevStep}
            onSkip={handleSkip}
            onRoleSelect={setUserRole}
          />
        )
      
      case 'first-success':
        return (
          <FirstSuccessStep
            userRole={userRole}
            onNext={nextStep}
            onBack={prevStep}
            onSkip={handleSkip}
            onCreateOwn={handleCreateOwn}
          />
        )
      
      case 'explore':
        return (
          <ExploreStep
            userRole={userRole}
            onComplete={handleComplete}
            onBack={prevStep}
          />
        )
      
      default:
        return null
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-gray-900 bg-opacity-75 transition-opacity"
        onClick={handleOverlayClick}
      />
      
      {/* Modal */}
      <div className="flex min-h-screen items-center justify-center p-4">
        <div 
          ref={modalRef}
          className="relative w-full max-w-6xl transform transition-all"
          role="dialog"
          aria-modal="true"
          aria-labelledby="onboarding-title"
        >
          <div className="bg-white rounded-lg shadow-xl overflow-hidden">
            {/* Progress Bar */}
            <ProgressBar
              currentStep={stepInfo.stepNumber}
              totalSteps={stepInfo.totalSteps}
              progress={stepInfo.progress}
              elapsedTime={stepInfo.elapsedTime}
              totalEstimatedTime={stepInfo.totalEstimatedTime}
            />
            
            {/* Close Button */}
            <button
              onClick={handleClose}
              className="absolute top-4 right-4 z-10 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded-full p-2 bg-white shadow-lg"
              title="Закрыть онбординг (ESC)"
              aria-label="Закрыть онбординг"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            
            {/* Step Content */}
            <div className="p-8 min-h-[600px] flex items-center">
              <div className="w-full">
                <div id="onboarding-title" className="sr-only">
                  Онбординг Receptor V3 - Шаг {stepInfo.stepNumber} из {stepInfo.totalSteps}
                </div>
                {renderStep()}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default OnboardingModal