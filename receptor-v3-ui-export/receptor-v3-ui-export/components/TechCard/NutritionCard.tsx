import React from 'react'
import { Nutrition } from '../../types/techcard-v2'

interface NutritionCardProps {
  nutrition: Nutrition
}

const NutritionCard: React.FC<NutritionCardProps> = ({ nutrition }) => {
  // Add comprehensive null guards and safe defaults
  const safeNutrition = nutrition ? {
    calories_per_100g: nutrition.calories_per_100g || 0,
    proteins_per_100g: nutrition.proteins_per_100g || 0,
    fats_per_100g: nutrition.fats_per_100g || 0,
    carbs_per_100g: nutrition.carbs_per_100g || 0,
    total_calories: nutrition.total_calories || 0,
    total_proteins: nutrition.total_proteins || 0,
    total_fats: nutrition.total_fats || 0,
    total_carbs: nutrition.total_carbs || 0
  } : {
    calories_per_100g: 0,
    proteins_per_100g: 0,
    fats_per_100g: 0,
    carbs_per_100g: 0,
    total_calories: 0,
    total_proteins: 0,
    total_fats: 0,
    total_carbs: 0
  }
  
  const nutritionItems = [
    {
      label: 'Калорийность',
      value: safeNutrition.calories_per_100g || 0,
      unit: 'ккал/100г',
      total: safeNutrition.total_calories,
      color: 'text-orange-600'
    },
    {
      label: 'Белки',
      value: safeNutrition.proteins_per_100g || 0,
      unit: 'г/100г',
      total: safeNutrition.total_proteins,
      color: 'text-blue-600'
    },
    {
      label: 'Жиры',
      value: safeNutrition.fats_per_100g || 0,
      unit: 'г/100г',
      total: safeNutrition.total_fats,
      color: 'text-yellow-600'
    },
    {
      label: 'Углеводы',
      value: safeNutrition.carbs_per_100g || 0,
      unit: 'г/100г',
      total: safeNutrition.total_carbs,
      color: 'text-green-600'
    }
  ]

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-heading-lg text-gray-900">Пищевая ценность</h3>
        <p className="text-body-sm text-gray-500">БЖУ и калорийность</p>
      </div>
      
      <div className="p-4">
        <div className="space-y-4">
          {nutritionItems.map((item, index) => (
            <div key={index} className="flex items-center justify-between py-2">
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${item.color.replace('text-', 'bg-')}`}></div>
                <span className="text-body-sm text-gray-700">{item.label}</span>
              </div>
              
              <div className="text-right">
                <div className={`text-body-sm font-medium ${item.color}`}>
                  {(item.value || 0).toLocaleString()} {(item.unit || '').split('/')[1] || 'г'}
                </div>
                {item.total && typeof item.total === 'number' && (
                  <div className="text-body-xs text-gray-500">
                    всего: {(item.total || 0).toLocaleString()} {(item.unit || '').split('/')[1] || 'г'}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
        
        {/* Energy distribution */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <h4 className="text-heading-sm text-gray-900 mb-3">Энергетическая ценность</h4>
          <div className="space-y-2">
            <div className="flex justify-between text-body-sm">
              <span className="text-gray-600">На 100г продукта:</span>
              <span className="font-medium text-gray-900">
                {(safeNutrition.calories_per_100g || 0).toLocaleString()} ккал
              </span>
            </div>
            {safeNutrition.total_calories && typeof safeNutrition.total_calories === 'number' && (
              <div className="flex justify-between text-body-sm">
                <span className="text-gray-600">Общая калорийность:</span>
                <span className="font-medium text-gray-900">
                  {(safeNutrition.total_calories || 0).toLocaleString()} ккал
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default NutritionCard