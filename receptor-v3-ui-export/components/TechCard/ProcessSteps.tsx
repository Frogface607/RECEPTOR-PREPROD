import React from 'react'
import { ProcessStep } from '../../types/techcard-v2'

interface ProcessStepsProps {
  steps: ProcessStep[]
}

const ProcessSteps: React.FC<ProcessStepsProps> = ({ steps }) => {
  // Add null guards for safety
  const safeSteps = steps || []
  
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-heading-lg text-gray-900">Технология приготовления</h3>
        <p className="text-body-sm text-gray-500">
          {safeSteps.length} этапов
        </p>
      </div>
      
      <div className="p-4">
        <div className="space-y-6">
          {safeSteps.map((step, index) => (
            <div key={index} className="flex space-x-4">
              {/* Step number */}
              <div className="flex-shrink-0">
                <div className="flex items-center justify-center w-8 h-8 bg-primary-100 text-primary-700 rounded-full text-body-sm font-semibold">
                  {index + 1}
                </div>
              </div>
              
              {/* Step content */}
              <div className="flex-1 min-w-0">
                <h4 className="text-heading-sm text-gray-900 mb-2">
                  {step.title}
                </h4>
                <p className="text-body-sm text-gray-600 mb-3 leading-relaxed">
                  {step.description}
                </p>
                
                {/* Step metadata */}
                {(step.duration_min || step.temperature_c || step.equipment) && (
                  <div className="flex flex-wrap gap-4 text-body-xs text-gray-500">
                    {step.duration_min && (
                      <div className="flex items-center space-x-1">
                        <div className="w-4 h-4 border border-current rounded-full flex items-center justify-center">
                          <div className="w-1 h-1 bg-current rounded-full"></div>
                        </div>
                        <span>{step.duration_min} мин</span>
                      </div>
                    )}
                    {step.temperature_c && (
                      <div className="flex items-center space-x-1">
                        <div className="w-4 h-4 border border-current rounded flex items-center justify-center">
                          <div className="w-1 h-2 bg-current rounded-full"></div>
                        </div>
                        <span>{step.temperature_c}°C</span>
                      </div>
                    )}
                    {step.equipment && (
                      <div className="flex items-center space-x-1">
                        <div className="w-4 h-4 border border-current rounded-sm flex items-center justify-center">
                          <div className="w-2 h-1 bg-current rounded-full"></div>
                        </div>
                        <span>{step.equipment}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default ProcessSteps