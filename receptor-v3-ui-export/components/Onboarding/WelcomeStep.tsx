import React from 'react'

interface WelcomeStepProps {
  onNext: () => void
  onSkip: () => void
}

const WelcomeStep: React.FC<WelcomeStepProps> = ({ onNext, onSkip }) => {
  return (
    <div className="text-center max-w-2xl mx-auto">
      {/* Hero Icon */}
      <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center">
        <div className="w-10 h-10 text-white">
          <div className="w-10 h-10 border-2 border-current rounded-lg flex items-center justify-center">
            <div className="w-6 h-6 border border-current rounded-sm flex items-center justify-center">
              <div className="w-3 h-3 border border-current rounded-sm"></div>
            </div>
          </div>
        </div>
      </div>

      {/* Welcome Message */}
      <h1 className="text-display-md text-gray-900 mb-4">
        Добро пожаловать в Receptor V3!
      </h1>
      
      <p className="text-body-lg text-gray-600 mb-8 leading-relaxed">
        Мы поможем вам освоить новую систему управления техкартами за 6 минут. 
        Вы узнаете как создавать профессиональные техкарты с помощью ИИ и 
        управлять библиотекой рецептов.
      </p>

      {/* Key Features Preview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
          <div className="w-8 h-8 mx-auto mb-3 text-primary-600">
            <div className="w-8 h-8 border-2 border-current rounded-full flex items-center justify-center">
              <div className="text-sm font-bold">AI</div>
            </div>
          </div>
          <h3 className="text-heading-sm text-gray-900 mb-2">ИИ-генерация</h3>
          <p className="text-body-xs text-gray-600">
            Создавайте техкарты автоматически по названию блюда
          </p>
        </div>

        <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
          <div className="w-8 h-8 mx-auto mb-3 text-green-600">
            <div className="w-8 h-8 border-2 border-current rounded-sm flex items-center justify-center">
              <div className="w-4 h-4 border border-current rounded-sm"></div>
            </div>
          </div>
          <h3 className="text-heading-sm text-gray-900 mb-2">Библиотека</h3>
          <p className="text-body-xs text-gray-600">
            Сохраняйте и организуйте все ваши рецепты в одном месте
          </p>
        </div>

        <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
          <div className="w-8 h-8 mx-auto mb-3">
            <div className="w-8 h-8 border-2 border-gray-400 rounded-sm flex items-center justify-center">
              <div className="text-xs font-bold text-gray-600">PDF</div>
            </div>
          </div>
          <h3 className="text-heading-sm text-gray-900 mb-2">Экспорт</h3>
          <p className="text-body-xs text-gray-600">
            Экспортируйте в PDF, Excel и интеграции с iiko
          </p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-center space-x-4">
        <button
          onClick={() => {
            console.log('Пропуск онбординга...')
            onSkip()
          }}
          className="px-6 py-2 text-lg font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors duration-200"
        >
          ✕ Закрыть онбординг
        </button>
        
        <button
          onClick={onNext}
          className="btn-primary px-8"
          autoFocus
        >
          Начать знакомство
        </button>
      </div>

      {/* Time estimate */}
      <p className="text-body-xs text-gray-500 mt-6">
        Примерное время прохождения: 6 минут
      </p>
    </div>
  )
}

export default WelcomeStep