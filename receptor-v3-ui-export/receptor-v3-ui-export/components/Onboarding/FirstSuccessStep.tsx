import React, { useState, useEffect } from 'react'
import { UserRole } from '../../hooks/useOnboarding'
import LoadingSkeleton from '../TechCard/LoadingSkeleton'

interface FirstSuccessStepProps {
  userRole?: UserRole
  onNext: () => void
  onBack: () => void
  onSkip: () => void
  onCreateOwn?: () => void
}

type DemoState = 'intro' | 'generating' | 'success'

const FirstSuccessStep: React.FC<FirstSuccessStepProps> = ({ 
  userRole, 
  onNext, 
  onBack, 
  onSkip,
  onCreateOwn 
}) => {
  const [demoState, setDemoState] = useState<DemoState>('intro')

  // Demo tech card data
  const demoTechCard = {
    title: 'Паста Карбонара',
    portions: 4,
    ingredients: [
      { name: 'Спагетти', brutto: 400, netto: 400, unit: 'г' },
      { name: 'Бекон', brutto: 150, netto: 150, unit: 'г' },
      { name: 'Яйца куриные', brutto: 120, netto: 120, unit: 'г' },
      { name: 'Сыр Пармезан', brutto: 80, netto: 80, unit: 'г' },
      { name: 'Чеснок', brutto: 20, netto: 18, unit: 'г' },
      { name: 'Оливковое масло', brutto: 30, netto: 30, unit: 'мл' }
    ],
    totalWeight: 798,
    costPerPortion: 185,
    calories: 520,
    cookingTime: 25
  }

  const handleStartDemo = () => {
    setDemoState('generating')
    
    // Simulate generation process
    setTimeout(() => {
      setDemoState('success')
    }, 4000) // 4 seconds loading
  }

  const handleCreateOwn = () => {
    onCreateOwn?.()
    onNext()
  }

  const getRoleSpecificMessage = () => {
    switch (userRole) {
      case 'chef':
        return 'Как шеф-повар, вы можете быстро создавать стандартизированные рецепты с точными пропорциями и пищевой ценностью.'
      case 'owner':
        return 'Как владелец, вы получите полный контроль над себестоимостью блюд и сможете оптимизировать прибыльность меню.'
      case 'manager':
        return 'Как менеджер кухни, вы обеспечите единые стандарты приготовления и упростите обучение персонала.'
      default:
        return 'Создавайте профессиональные техкарты за считанные секунды с помощью искусственного интеллекта.'
    }
  }

  if (demoState === 'intro') {
    return (
      <div className="max-w-3xl mx-auto text-center">
        <h2 className="text-display-sm text-gray-900 mb-4">
          Время для первого успеха!
        </h2>
        
        <p className="text-body-lg text-gray-600 mb-6">
          {getRoleSpecificMessage()}
        </p>

        <div className="bg-gradient-to-r from-primary-50 to-blue-50 border border-primary-200 rounded-lg p-6 mb-8">
          <h3 className="text-heading-lg text-gray-900 mb-4">
            Давайте создадим вашу первую техкарту
          </h3>
          
          <div className="bg-white rounded-lg p-4 mb-4 border border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                <span className="text-2xl">🍝</span>
              </div>
              <div className="text-left">
                <h4 className="text-heading-md text-gray-900">Паста Карбонара</h4>
                <p className="text-body-sm text-gray-600">Классическое итальянское блюдо</p>
              </div>
            </div>
          </div>

          <button
            onClick={handleStartDemo}
            className="btn-primary text-lg px-8 py-3"
            autoFocus
          >
            Создать демо-техкарту
          </button>
        </div>

        <div className="flex items-center justify-between">
          <button onClick={onBack} className="btn-secondary">
            Назад
          </button>
          
          <button
            onClick={onSkip}
            className="text-gray-600 hover:text-gray-800 transition-colors duration-200"
          >
            Пропустить демо
          </button>
          
          <button onClick={onNext} className="btn-secondary">
            Пропустить к обзору
          </button>
        </div>
      </div>
    )
  }

  if (demoState === 'generating') {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto mb-4 bg-primary-500 rounded-full flex items-center justify-center">
            <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          </div>
          
          <h2 className="text-display-sm text-gray-900 mb-2">
            Создаем вашу техкарту...
          </h2>
          
          <p className="text-body-md text-gray-600">
            ИИ анализирует рецепт и рассчитывает все необходимые параметры
          </p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <LoadingSkeleton />
        </div>

        <div className="text-center mt-6">
          <p className="text-body-sm text-gray-500">
            Обычно создание техкарты занимает 10-30 секунд
          </p>
        </div>
      </div>
    )
  }

  // Success state
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <div className="w-16 h-16 mx-auto mb-4 bg-green-500 rounded-full flex items-center justify-center">
          <span className="text-white text-2xl">✓</span>
        </div>
        
        <h2 className="text-display-sm text-gray-900 mb-2">
          Техкарта готова!
        </h2>
        
        <p className="text-body-md text-gray-600">
          Посмотрите, как ИИ автоматически рассчитал все параметры блюда
        </p>
      </div>

      {/* Demo Tech Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">🍝</span>
            </div>
            <div>
              <h3 className="text-heading-lg text-gray-900">{demoTechCard.title}</h3>
              <p className="text-body-sm text-gray-600">Создано только что с помощью ИИ</p>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-6">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-primary-600 mb-1">
              {demoTechCard.portions}
            </div>
            <div className="text-body-sm text-gray-600">порции</div>
          </div>
          
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600 mb-1">
              {demoTechCard.totalWeight}г
            </div>
            <div className="text-body-sm text-gray-600">общий выход</div>
          </div>
          
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600 mb-1">
              {demoTechCard.costPerPortion}₽
            </div>
            <div className="text-body-sm text-gray-600">за порцию</div>
          </div>
          
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600 mb-1">
              {demoTechCard.calories}
            </div>
            <div className="text-body-sm text-gray-600">ккал/100г</div>
          </div>
        </div>

        {/* Ingredients Preview */}
        <div className="px-6 pb-6">
          <h4 className="text-heading-sm text-gray-900 mb-3">
            Ингредиенты ({demoTechCard.ingredients.length} позиций)
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-body-sm">
            {demoTechCard.ingredients.map((ingredient, index) => (
              <div key={index} className="flex justify-between py-1">
                <span className="text-gray-700">{ingredient.name}</span>
                <span className="text-gray-500">{ingredient.netto} {ingredient.unit}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Success Actions */}
      <div className="text-center space-y-6">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h4 className="text-heading-sm text-green-900 mb-2">
            🎉 Поздравляем с первой техкартой!
          </h4>
          <p className="text-body-sm text-green-700">
            ИИ автоматически рассчитал пропорции, себестоимость, БЖУ и время приготовления
          </p>
        </div>

        <button
          onClick={handleCreateOwn}
          className="btn-primary text-lg px-8 py-3"
        >
          Создать свою техкарту
        </button>

        <div className="flex items-center justify-between">
          <button onClick={onBack} className="btn-secondary">
            Назад
          </button>
          
          <button onClick={onNext} className="btn-primary">
            Изучить возможности
          </button>
        </div>
      </div>
    </div>
  )
}

export default FirstSuccessStep