import React, { useState, useEffect } from 'react';

/**
 * 🎯 Универсальная система туров для RECEPTOR PRO
 * 
 * Использование:
 * <TourSystem 
 *   tourId="create-techcard"
 *   steps={tourSteps}
 *   onComplete={() => {}}
 * />
 */

const TourSystem = ({ tourId, steps, onComplete, onSkip, autoStart = false, isActive = false }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [hasCompleted, setHasCompleted] = useState(false);

  const step = steps[currentStep];
  const progress = ((currentStep + 1) / steps.length) * 100;

  // Check if tour was already completed
  useEffect(() => {
    const completedTours = JSON.parse(localStorage.getItem('completedTours') || '[]');
    const wasCompleted = completedTours.includes(tourId);
    setHasCompleted(wasCompleted);
    
    if (autoStart && !wasCompleted) {
      setTimeout(() => setIsVisible(true), 500);
    }
  }, [tourId, autoStart]);

  // Listen to isActive prop changes
  useEffect(() => {
    if (isActive) {
      setCurrentStep(0);
      setIsVisible(true);
    }
  }, [isActive]);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    setIsVisible(false);
    const skippedTours = JSON.parse(localStorage.getItem('skippedTours') || '[]');
    if (!skippedTours.includes(tourId)) {
      skippedTours.push(tourId);
      localStorage.setItem('skippedTours', JSON.stringify(skippedTours));
    }
    setTimeout(() => {
      if (onSkip) onSkip();
    }, 300);
  };

  const handleComplete = () => {
    setIsVisible(false);
    setHasCompleted(true);
    
    const completedTours = JSON.parse(localStorage.getItem('completedTours') || '[]');
    if (!completedTours.includes(tourId)) {
      completedTours.push(tourId);
      localStorage.setItem('completedTours', JSON.stringify(completedTours));
    }
    
    setTimeout(() => {
      if (onComplete) onComplete();
    }, 300);
  };

  const handleRestart = () => {
    setCurrentStep(0);
    setIsVisible(true);
  };

  // Keyboard navigation
  useEffect(() => {
    if (!isVisible) return;
    
    const handleKeyPress = (e) => {
      if (e.key === 'Enter') handleNext();
      else if (e.key === 'Backspace' && currentStep > 0) {
        e.preventDefault();
        handleBack();
      }
      else if (e.key === 'Escape') handleSkip();
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [currentStep, isVisible]);

  // Public API для запуска тура извне
  useEffect(() => {
    window[`startTour_${tourId}`] = () => {
      setCurrentStep(0);
      setIsVisible(true);
    };
    
    return () => {
      delete window[`startTour_${tourId}`];
    };
  }, [tourId]);

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/70 backdrop-blur-sm animate-fadeIn">
      {/* Highlight Element (если указан selector) */}
      {step.highlightSelector && (
        <div className="absolute inset-0 pointer-events-none">
          <style>{`
            ${step.highlightSelector} {
              position: relative !important;
              z-index: 10000 !important;
              box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.7), 0 0 20px rgba(168, 85, 247, 0.8) !important;
              border-radius: 8px !important;
            }
          `}</style>
        </div>
      )}

      {/* Tour Modal */}
      <div 
        className={`relative w-full max-w-2xl mx-4 transform transition-all duration-500 ${
          isVisible ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
        }`}
        style={{
          marginTop: step.position === 'top' ? '-200px' : '0',
          marginBottom: step.position === 'bottom' ? '-200px' : '0'
        }}
      >
        <div className={`bg-gradient-to-br ${step.gradient || 'from-purple-600 to-blue-600'} p-[2px] rounded-2xl shadow-2xl`}>
          <div className="bg-gray-900 rounded-2xl p-6">
            
            {/* Progress */}
            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-400">
                  {step.section && <span className="text-purple-400 font-medium">{step.section} • </span>}
                  Шаг {currentStep + 1} из {steps.length}
                </span>
                <button
                  onClick={handleSkip}
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                >
                  Пропустить ✕
                </button>
              </div>
              <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full bg-gradient-to-r ${step.gradient || 'from-purple-500 to-blue-500'} transition-all duration-500`}
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            {/* Icon & Title */}
            <div className="mb-6">
              {step.icon && (
                <div className="text-5xl mb-3 text-center">
                  {step.icon}
                </div>
              )}
              <h3 className="text-2xl font-bold text-white mb-2 text-center">
                {step.title}
              </h3>
              {step.subtitle && (
                <p className="text-lg text-purple-300 text-center">
                  {step.subtitle}
                </p>
              )}
            </div>

            {/* Description */}
            {step.description && (
              <p className="text-gray-300 mb-6 text-center leading-relaxed">
                {step.description}
              </p>
            )}

            {/* Features List */}
            {step.features && (
              <div className="mb-6 space-y-2">
                {step.features.map((feature, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 p-3 bg-gray-800/50 rounded-lg"
                  >
                    <span className="text-green-400 text-lg flex-shrink-0">✓</span>
                    <span className="text-white">{feature}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Steps List (пошаговая инструкция) */}
            {step.stepsList && (
              <div className="mb-6 space-y-3">
                {step.stepsList.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 p-4 bg-gray-800/50 rounded-lg border-l-4 border-purple-500/50"
                  >
                    <span className="text-purple-400 font-bold text-lg flex-shrink-0">
                      {idx + 1}.
                    </span>
                    <div>
                      <div className="text-white font-medium mb-1">{item.title}</div>
                      {item.desc && (
                        <div className="text-sm text-gray-400">{item.desc}</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Example */}
            {step.example && (
              <div className="mb-6 p-4 bg-gray-800/50 rounded-lg border border-purple-500/30">
                <div className="text-sm text-gray-400 mb-2">💡 Пример:</div>
                <div className="text-white">
                  {typeof step.example === 'string' ? (
                    step.example
                  ) : (
                    <div className="space-y-2">
                      <div><span className="text-gray-400">Ввод:</span> {step.example.input}</div>
                      <div className="text-purple-400">→ {step.example.output}</div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Tip */}
            {step.tip && (
              <div className="mb-6 p-4 bg-blue-900/20 border-l-4 border-blue-500 rounded-r-lg">
                <p className="text-blue-200 text-sm">{step.tip}</p>
              </div>
            )}

            {/* Warning/Note */}
            {step.note && (
              <div className={`mb-6 p-4 ${
                step.noteType === 'warning' 
                  ? 'bg-yellow-900/20 border-l-4 border-yellow-500' 
                  : 'bg-purple-900/20 border-l-4 border-purple-500'
              } rounded-r-lg`}>
                <p className={`text-sm ${
                  step.noteType === 'warning' ? 'text-yellow-200' : 'text-purple-200'
                }`}>
                  {step.note}
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              {currentStep > 0 && (
                <button
                  onClick={handleBack}
                  className="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-xl font-medium transition-all"
                >
                  ← Назад
                </button>
              )}
              <button
                onClick={handleNext}
                className={`flex-1 px-6 py-3 bg-gradient-to-r ${step.gradient || 'from-purple-600 to-blue-600'} hover:opacity-90 text-white rounded-xl font-bold transition-all ${
                  step.final ? 'text-lg' : ''
                }`}
              >
                {step.action || 'Далее →'}
              </button>
            </div>

            {/* Footer */}
            <div className="mt-4 text-center text-xs text-gray-500">
              {step.footer || 'Enter — дальше • Backspace — назад • Esc — пропустить'}
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        .animate-fadeIn {
          animation: fadeIn 0.4s ease-out;
        }
      `}</style>
    </div>
  );
};

// Helper component для кнопки запуска тура
export const TourButton = ({ tourId, label = "❓", className = "" }) => {
  const handleClick = () => {
    if (window[`startTour_${tourId}`]) {
      window[`startTour_${tourId}`]();
    }
  };

  return (
    <button
      onClick={handleClick}
      className={className || "text-blue-400 hover:text-blue-300 transition-colors"}
      title={`Показать тур: ${label}`}
    >
      {label}
    </button>
  );
};

export default TourSystem;


