import React from 'react'

interface ProgressBarProps {
  currentStep: number
  totalSteps: number
  progress: number
  elapsedTime: number
  totalEstimatedTime: number
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  currentStep,
  totalSteps,
  progress,
  elapsedTime,
  totalEstimatedTime
}) => {
  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    
    if (minutes > 0) {
      return `${minutes}м ${remainingSeconds}с`
    }
    return `${remainingSeconds}с`
  }

  const estimatedRemaining = Math.max(0, totalEstimatedTime - elapsedTime)

  return (
    <div className="w-full bg-white border-b border-gray-200 p-4">
      <div className="max-w-2xl mx-auto">
        {/* Step indicators */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            {Array.from({ length: totalSteps }, (_, index) => {
              const stepNumber = index + 1
              const isActive = stepNumber === currentStep
              const isCompleted = stepNumber < currentStep
              
              return (
                <div key={index} className="flex items-center">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors duration-200 ${
                      isCompleted
                        ? 'bg-green-500 text-white'
                        : isActive
                        ? 'bg-primary-500 text-white'
                        : 'bg-gray-200 text-gray-500'
                    }`}
                  >
                    {isCompleted ? '✓' : stepNumber}
                  </div>
                  {index < totalSteps - 1 && (
                    <div
                      className={`w-8 h-0.5 mx-2 transition-colors duration-200 ${
                        isCompleted ? 'bg-green-500' : 'bg-gray-200'
                      }`}
                    />
                  )}
                </div>
              )
            })}
          </div>

          {/* Time info */}
          <div className="text-right text-body-xs text-gray-500">
            <div>Прошло: {formatTime(elapsedTime)}</div>
            <div>Осталось: ~{formatTime(estimatedRemaining)}</div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary-500 to-primary-600 transition-all duration-500 ease-out"
            style={{ width: `${Math.max(5, progress)}%` }}
          />
        </div>

        {/* Progress text */}
        <div className="flex items-center justify-between mt-2 text-body-xs text-gray-600">
          <span>Шаг {currentStep} из {totalSteps}</span>
          <span>{Math.round(progress)}% завершено</span>
        </div>
      </div>
    </div>
  )
}

export default ProgressBar