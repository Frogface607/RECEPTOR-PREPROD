import React, { useState } from 'react'
import { TechCardV2, normalizeYield } from '../../types/techcard-v2'
import { useFeatureFlags } from '../../utils/featureFlags'
import { getUserPlan } from '../../utils/featureFlags'
import InfoCard from './InfoCard'
import IngredientsTable from './IngredientsTable'
import ProcessSteps from './ProcessSteps'
import NutritionCard from './NutritionCard'
import CostCard from './CostCard'
import AIEditor from './AIEditor'
import SaveButton from './SaveButton'
import ExportMaster from './ExportMaster'
import UpgradeModal from '../ui/UpgradeModal'

interface TechCardViewProps {
  techCard: TechCardV2
  onEditStart?: () => void
  onEditSuccess?: (updatedTechCard: TechCardV2) => void
  onEditError?: (error: string) => void
  onSaveStart?: () => void
  onSaveSuccess?: (savedData: { id: string; saved_at: string }) => void
  onSaveError?: (error: { id: string; saved_at: string; message: string }) => void
  showSaveButton?: boolean
}

const TechCardView: React.FC<TechCardViewProps> = ({ 
  techCard, 
  onEditStart,
  onEditSuccess,
  onEditError,
  onSaveStart,
  onSaveSuccess,
  onSaveError,
  showSaveButton = true
}) => {
  const { isEnabled } = useFeatureFlags()
  const yieldData = normalizeYield(techCard)
  const userPlan = getUserPlan()
  
  // Export modal state
  const [isExportModalOpen, setIsExportModalOpen] = useState(false)
  const [isUpgradeModalOpen, setIsUpgradeModalOpen] = useState(false)
  
  const formatDate = (dateString?: string) => {
    if (!dateString) return ''
    return new Date(dateString).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-display-sm text-gray-900 mb-2">
              {techCard.title}
            </h1>
            {techCard.description && (
              <p className="text-body-lg text-gray-600 mb-3">
                {techCard.description}
              </p>
            )}
            <div className="flex items-center space-x-4 text-body-sm text-gray-500">
              {techCard.category && (
                <span className="px-2 py-1 bg-gray-100 rounded-full">
                  {techCard.category}
                </span>
              )}
              {techCard.created_at && (
                <span>Создано: {formatDate(techCard.created_at)}</span>
              )}
              {techCard.status && (
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  techCard.status === 'READY' 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {techCard.status}
                </span>
              )}
            </div>
          </div>
          
          {/* Action Buttons */}
          <div className="flex items-center space-x-3">
            {/* Export Button */}
            {isEnabled('export_master') && (
              <button
                onClick={() => setIsExportModalOpen(true)}
                className="btn-secondary"
                title="Экспорт техкарты в различные форматы"
              >
                <span className="flex items-center space-x-2">
                  <div className="w-4 h-4 border border-current rounded-sm flex items-center justify-center">
                    <div className="w-2 h-2 border border-current"></div>
                  </div>
                  <span>Экспорт</span>
                </span>
              </button>
            )}
            
            {/* Save Button */}
            {showSaveButton && isEnabled('inline_editing') && onSaveStart && onSaveSuccess && onSaveError && (
              <SaveButton
                techCard={techCard}
                onSaveStart={onSaveStart}
                onSaveSuccess={onSaveSuccess}
                onSaveError={onSaveError}
              />
            )}
          </div>
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <InfoCard
          title="Количество порций"
          value={techCard.portions}
          unit="шт"
          variant="primary"
        />
        <InfoCard
          title="Выход на порцию"
          value={yieldData.per_portion}
          unit={yieldData.unit}
          variant="secondary"
        />
        <InfoCard
          title="Общий выход"
          value={yieldData.total}
          unit={yieldData.unit}
          subtitle={`${techCard.portions} порций`}
        />
      </div>

      {/* Ingredients */}
      <IngredientsTable ingredients={techCard.ingredients} />

      {/* Process Steps */}
      <ProcessSteps steps={techCard.process_steps} />

      {/* Bottom Cards - Nutrition & Cost */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {techCard.nutrition ? (
          <NutritionCard nutrition={techCard.nutrition} />
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="text-center text-gray-500">
              <div className="text-4xl mb-2">📊</div>
              <h3 className="text-heading-lg text-gray-900 mb-2">Пищевая ценность</h3>
              <p className="text-body-sm">Данные о пищевой ценности недоступны</p>
            </div>
          </div>
        )}
        <CostCard cost={techCard.cost} portions={techCard.portions} />
      </div>

      {/* Footer */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between text-body-xs text-gray-500">
          <span>
            Техкарта ID: {techCard.id}
          </span>
          {techCard.updated_at && (
            <span>
              Обновлено: {formatDate(techCard.updated_at)}
            </span>
          )}
        </div>
      </div>

      {/* AI Editor (conditional) */}
      {isEnabled('ai_editing') && onEditStart && onEditSuccess && onEditError && (
        <AIEditor
          techCardId={techCard.id}
          onEditStart={onEditStart}
          onEditSuccess={onEditSuccess}
          onEditError={onEditError}
        />
      )}

      {/* Export Master Modal */}
      <ExportMaster
        techCard={techCard}
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
      />

      {/* Upgrade Modal */}
      <UpgradeModal
        isOpen={isUpgradeModalOpen}
        onClose={() => setIsUpgradeModalOpen(false)}
        feature="расширенные форматы экспорта"
        onUpgrade={() => {
          setIsUpgradeModalOpen(false)
          // In real app, redirect to upgrade page
          console.log('🚀 Upgrade flow initiated')
        }}
      />
    </div>
  )
}

export default TechCardView