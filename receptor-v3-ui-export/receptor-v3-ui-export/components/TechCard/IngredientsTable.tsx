import React from 'react'
import { Ingredient } from '../../types/techcard-v2'

interface IngredientsTableProps {
  ingredients: Ingredient[]
}

const IngredientsTable: React.FC<IngredientsTableProps> = ({ ingredients }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-heading-lg text-gray-900">Ингредиенты</h3>
        <p className="text-body-sm text-gray-500">
          {ingredients.length} позиций
        </p>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-body-sm font-medium text-gray-500 uppercase tracking-wider">
                Наименование
              </th>
              <th className="px-4 py-3 text-right text-body-sm font-medium text-gray-500 uppercase tracking-wider">
                Брутто
              </th>
              <th className="px-4 py-3 text-right text-body-sm font-medium text-gray-500 uppercase tracking-wider">
                Нетто
              </th>
              <th className="px-4 py-3 text-center text-body-sm font-medium text-gray-500 uppercase tracking-wider">
                Ед.
              </th>
              <th className="px-4 py-3 text-center text-body-sm font-medium text-gray-500 uppercase tracking-wider">
                Потери %
              </th>
              {ingredients.some(ing => ing.article || ing.product_code) && (
                <th className="px-4 py-3 text-center text-body-sm font-medium text-gray-500 uppercase tracking-wider">
                  Артикул
                </th>
              )}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {ingredients.map((ingredient, index) => (
              <tr key={index} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-body-sm text-gray-900">
                  {ingredient.name}
                </td>
                <td className="px-4 py-3 text-body-sm text-gray-900 text-right">
                  {(ingredient.brutto || 0).toLocaleString()}
                </td>
                <td className="px-4 py-3 text-body-sm text-gray-900 text-right font-medium">
                  {(ingredient.netto || 0).toLocaleString()}
                </td>
                <td className="px-4 py-3 text-body-sm text-gray-500 text-center">
                  {ingredient.unit}
                </td>
                <td className="px-4 py-3 text-body-sm text-gray-500 text-center">
                  {(ingredient.loss_pct || 0).toFixed(1)}%
                </td>
                {ingredients.some(ing => ing.article || ing.product_code) && (
                  <td className="px-4 py-3 text-body-xs text-gray-500 text-center">
                    {ingredient.article || ingredient.product_code || '-'}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Summary row */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
        <div className="flex justify-between items-center text-body-sm">
          <span className="font-medium text-gray-900">Итого нетто:</span>
          <span className="font-semibold text-gray-900">
            {ingredients.reduce((sum, ing) => sum + (ing.netto || 0), 0).toLocaleString()} г
          </span>
        </div>
      </div>
    </div>
  )
}

export default IngredientsTable