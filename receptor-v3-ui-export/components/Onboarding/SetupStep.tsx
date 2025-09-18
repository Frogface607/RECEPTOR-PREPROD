import React, { useState } from 'react'
import { UserRole } from '../../hooks/useOnboarding'

interface SetupStepProps {
  userRole?: UserRole
  onNext: () => void
  onBack: () => void
  onSkip: () => void
  onRoleSelect: (role: UserRole) => void
}

const SetupStep: React.FC<SetupStepProps> = ({ 
  userRole, 
  onNext, 
  onBack, 
  onSkip, 
  onRoleSelect 
}) => {
  const [selectedRole, setSelectedRole] = useState<UserRole | undefined>(userRole)

  const roles = [
    {
      id: 'chef' as const,
      title: 'Шеф-повар',
      description: 'Создаю рецепты и техкарты, контролирую качество блюд',
      icon: '👨‍🍳',
      tips: [
        'Быстрое создание техкарт с ИИ',
        'Расчет БЖУ и калорийности',
        'Контроль себестоимости блюд'
      ]
    },
    {
      id: 'owner' as const,
      title: 'Владелец/Ресторатор',
      description: 'Управляю рестораном, анализирую прибыльность',
      icon: '👔',
      tips: [
        'Экспорт техкарт в системы учета',
        'Анализ себестоимости меню',
        'Интеграция с iiko и POS'
      ]
    },
    {
      id: 'manager' as const,
      title: 'Менеджер кухни',
      description: 'Организую работу кухни, следую стандартам',
      icon: '📋',
      tips: [
        'Стандартизация процессов',
        'Библиотека готовых техкарт',
        'Обучение персонала'
      ]
    }
  ]

  const handleRoleSelect = (role: UserRole) => {
    setSelectedRole(role)
    onRoleSelect(role)
  }

  const handleNext = () => {
    if (selectedRole) {
      onNext()
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-display-sm text-gray-900 mb-4">
          Персонализируем ваш опыт
        </h2>
        <p className="text-body-lg text-gray-600">
          Выберите вашу роль, чтобы мы показали наиболее релевантные возможности
        </p>
      </div>

      {/* Role Selection Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {roles.map((role) => (
          <button
            key={role.id}
            onClick={() => handleRoleSelect(role.id)}
            className={`p-6 text-left border-2 rounded-lg transition-all duration-200 ${
              selectedRole === role.id
                ? 'border-primary-500 bg-primary-50 shadow-md'
                : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
            }`}
          >
            <div className="text-4xl mb-4">{role.icon}</div>
            
            <h3 className="text-heading-md text-gray-900 mb-2">
              {role.title}
            </h3>
            
            <p className="text-body-sm text-gray-600 mb-4">
              {role.description}
            </p>

            <div className="space-y-2">
              <p className="text-body-xs font-medium text-gray-700">
                Что будет полезно:
              </p>
              <ul className="space-y-1">
                {role.tips.map((tip, index) => (
                  <li key={index} className="text-body-xs text-gray-600 flex items-start">
                    <span className="text-primary-500 mr-2">•</span>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>

            {selectedRole === role.id && (
              <div className="mt-4 flex items-center text-primary-600">
                <div className="w-4 h-4 border-2 border-current rounded-full flex items-center justify-center mr-2">
                  <div className="w-2 h-2 bg-current rounded-full"></div>
                </div>
                <span className="text-body-sm font-medium">Выбрано</span>
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Selected Role Preview */}
      {selectedRole && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-8">
          <div className="flex items-start space-x-3">
            <div className="w-5 h-5 text-blue-600 mt-0.5">
              <div className="w-4 h-4 border-2 border-current rounded-full flex items-center justify-center">
                <div className="w-1 h-1 bg-current rounded-full"></div>
              </div>
            </div>
            <div>
              <h4 className="text-heading-sm text-blue-900 mb-1">
                Отлично! Мы настроим интерфейс под роль "{roles.find(r => r.id === selectedRole)?.title}"
              </h4>
              <p className="text-body-sm text-blue-700">
                В следующих шагах мы покажем функции, которые будут особенно полезны в вашей работе.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="btn-secondary"
        >
          Назад
        </button>

        <button
          onClick={onSkip}
          className="text-gray-600 hover:text-gray-800 transition-colors duration-200"
        >
          Пропустить настройку
        </button>

        <button
          onClick={handleNext}
          disabled={!selectedRole}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Продолжить
        </button>
      </div>
    </div>
  )
}

export default SetupStep