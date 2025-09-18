import React from 'react'
import { Cost } from '../../types/techcard-v2'

interface CostCardProps {
  cost: Cost
  portions: number
}

const CostCard: React.FC<CostCardProps> = ({ cost, portions }) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: cost.currency || 'RUB',
      minimumFractionDigits: 2
    }).format(amount)
  }

  const profitMargins = [
    { label: '100%', multiplier: 2 },
    { label: '200%', multiplier: 3 },
    { label: '300%', multiplier: 4 }
  ]

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-heading-lg text-gray-900">Себестоимость</h3>
        <p className="text-body-sm text-gray-500">Расчет стоимости и наценки</p>
      </div>
      
      <div className="p-4">
        {/* Main cost info */}
        <div className="space-y-4 mb-6">
          <div className="flex items-center justify-between py-2">
            <span className="text-body-sm text-gray-700">Общая себестоимость:</span>
            <span className="text-heading-md text-gray-900 font-semibold">
              {formatCurrency(cost.total_cost)}
            </span>
          </div>
          
          <div className="flex items-center justify-between py-2">
            <span className="text-body-sm text-gray-700">На 1 порцию:</span>
            <span className="text-heading-sm text-primary-600 font-semibold">
              {formatCurrency(cost.cost_per_portion)}
            </span>
          </div>
          
          <div className="flex items-center justify-between py-2 text-body-xs text-gray-500">
            <span>Количество порций:</span>
            <span>{portions} шт</span>
          </div>
        </div>
        
        {/* Profit margins */}
        <div className="pt-4 border-t border-gray-200">
          <h4 className="text-heading-sm text-gray-900 mb-3">Рекомендуемые цены</h4>
          <div className="space-y-2">
            {profitMargins.map((margin, index) => {
              const sellingPrice = cost.cost_per_portion * margin.multiplier
              return (
                <div key={index} className="flex items-center justify-between py-1">
                  <span className="text-body-sm text-gray-600">
                    Наценка {margin.label}:
                  </span>
                  <span className="text-body-sm font-medium text-gray-900">
                    {formatCurrency(sellingPrice)}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
        
        {/* Cost breakdown hint */}
        <div className="mt-6 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start space-x-2">
            <div className="w-4 h-4 text-blue-600 mt-0.5">
              <div className="w-4 h-4 border-2 border-current rounded-full flex items-center justify-center">
                <div className="w-1 h-1 bg-current rounded-full"></div>
              </div>
            </div>
            <div>
              <p className="text-body-xs text-blue-700">
                Расчет включает только стоимость ингредиентов. 
                Учтите дополнительные расходы: труд, аренда, коммунальные услуги.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CostCard