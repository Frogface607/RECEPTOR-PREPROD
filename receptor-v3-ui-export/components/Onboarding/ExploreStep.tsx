import React from 'react'
import { UserRole } from '../../hooks/useOnboarding'

interface ExploreStepProps {
  userRole?: UserRole
  onComplete: () => void
  onBack: () => void
}

const ExploreStep: React.FC<ExploreStepProps> = ({ 
  userRole, 
  onComplete, 
  onBack 
}) => {
  const getPersonalizedFeatures = () => {
    const baseFeatures = [
      {
        title: 'Библиотека техкарт',
        description: 'Сохраняйте и организуйте все ваши рецепты',
        icon: '📚',
        location: 'Раздел "Библиотека"'
      },
      {
        title: 'ИИ-редактор',
        description: 'Улучшайте техкарты с помощью искусственного интеллекта',
        icon: '🤖',
        location: 'Внизу каждой техкарты'
      }
    ]

    const roleFeatures = {
      chef: [
        {
          title: 'Расчет БЖУ',
          description: 'Автоматический расчет пищевой ценности',
          icon: '🍎',
          location: 'В каждой техкарте'
        },
        {
          title: 'Контроль качества',
          description: 'Стандартизация рецептов и процессов',
          icon: '⭐',
          location: 'Настройки техкарт'
        }
      ],
      owner: [
        {
          title: 'Экспорт и интеграции',
          description: 'PDF, Excel, интеграция с iiko',
          icon: '📤',
          location: 'Кнопка "Экспорт" в техкартах'
        },
        {
          title: 'Анализ себестоимости',
          description: 'Контроль прибыльности каждого блюда',
          icon: '💰',
          location: 'Карточка стоимости'
        }
      ],
      manager: [
        {
          title: 'Стандарты процессов',
          description: 'Четкие инструкции для команды',
          icon: '📋',
          location: 'Шаги приготовления'
        },
        {
          title: 'Обучение персонала',
          description: 'Готовые материалы для обучения',
          icon: '🎓',
          location: 'Экспорт в PDF'
        }
      ]
    }

    return [
      ...baseFeatures,
      ...(roleFeatures[userRole || 'chef'] || roleFeatures.chef)
    ]
  }

  const features = getPersonalizedFeatures()

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-display-sm text-gray-900 mb-4">
          Изучите возможности Receptor V3
        </h2>
        <p className="text-body-lg text-gray-600">
          Вот ключевые функции, которые помогут вам в работе
        </p>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {features.map((feature, index) => (
          <div
            key={index}
            className="p-4 rounded-lg border border-gray-200 bg-white transition-all"
          >
            <div className="flex items-start space-x-4">
              <div className="text-3xl">{feature.icon}</div>
              <div className="flex-1">
                <h3 className="text-heading-md text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-body-sm text-gray-600 mb-3">
                  {feature.description}
                </p>
                <div className="flex items-center text-body-xs text-gray-500">
                  <div className="w-3 h-3 border border-current rounded-full mr-2 flex items-center justify-center">
                    <div className="w-1 h-1 bg-current rounded-full"></div>
                  </div>
                  {feature.location}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Navigation Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
        <h3 className="text-heading-md text-blue-900 mb-4">
          Как начать работу:
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-start space-x-3">
            <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
              1
            </div>
            <div>
              <h4 className="text-heading-sm text-blue-900">Создайте техкарту</h4>
              <p className="text-body-sm text-blue-700">
                Введите название блюда на главной странице
              </p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
              2
            </div>
            <div>
              <h4 className="text-heading-sm text-blue-900">Сохраните в библиотеку</h4>
              <p className="text-body-sm text-blue-700">
                Используйте кнопку "Сохранить в библиотеку"
              </p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
              3
            </div>
            <div>
              <h4 className="text-heading-sm text-blue-900">Улучшите с ИИ</h4>
              <p className="text-body-sm text-blue-700">
                Используйте ИИ-редактор для доработки
              </p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
              4
            </div>
            <div>
              <h4 className="text-heading-sm text-blue-900">Экспортируйте</h4>
              <p className="text-body-sm text-blue-700">
                Выгрузите в нужном формате для работы
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Help and Support */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 mb-8">
        <h3 className="text-heading-md text-gray-900 mb-4">
          Нужна помощь?
        </h3>
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center space-x-2 text-body-sm text-gray-600">
            <div className="w-4 h-4 border border-current rounded-sm"></div>
            <span>Документация в разделе Help</span>
          </div>
          <div className="flex items-center space-x-2 text-body-sm text-gray-600">
            <div className="w-4 h-4 border border-current rounded-sm"></div>
            <span>Горячие клавиши: Ctrl+H</span>
          </div>
          <div className="flex items-center space-x-2 text-body-sm text-gray-600">
            <div className="w-4 h-4 border border-current rounded-sm"></div>
            <span>Повторить онбординг: меню Помощь</span>
          </div>
        </div>
      </div>

      {/* Completion */}
      <div className="text-center">
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
          <div className="w-16 h-16 mx-auto mb-4 bg-green-500 rounded-full flex items-center justify-center">
            <span className="text-white text-2xl">🎉</span>
          </div>
          <h3 className="text-heading-lg text-green-900 mb-2">
            Поздравляем! Онбординг завершен
          </h3>
          <p className="text-body-md text-green-700">
            Теперь вы готовы эффективно работать с Receptor V3. 
            Начните создавать профессиональные техкарты уже сейчас!
          </p>
        </div>

        <div className="flex items-center justify-between">
          <button onClick={onBack} className="btn-secondary">
            Назад
          </button>

          <button
            onClick={onComplete}
            className="btn-primary text-lg px-8 py-3"
            autoFocus
          >
            Начать работу!
          </button>
        </div>
      </div>
    </div>
  )
}

export default ExploreStep