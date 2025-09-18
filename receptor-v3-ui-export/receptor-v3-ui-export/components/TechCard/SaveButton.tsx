import React, { useState } from 'react'
import { techCardApi } from '../../services/techCardApi'
import { TechCardV2 } from '../../types/techcard-v2'

interface SaveButtonProps {
  techCard: TechCardV2
  onSaveStart?: () => void
  onSaveSuccess?: (savedData: { id: string; saved_at: string }) => void
  onSaveError?: (error: { id: string; saved_at: string; message: string }) => void
  disabled?: boolean
}

const SaveButton: React.FC<SaveButtonProps> = ({
  techCard,
  onSaveStart,
  onSaveSuccess,
  onSaveError,
  disabled = false
}) => {
  const [isSaving, setIsSaving] = useState(false)

  const handleSave = async () => {
    setIsSaving(true)
    onSaveStart?.()

    try {
      console.log('💾 Starting tech card save:', techCard.title)
      const savedData = await techCardApi.save(techCard)
      
      console.log('✅ Tech card saved successfully:', savedData)
      onSaveSuccess?.({
        id: savedData.id || 'unknown',
        saved_at: new Date().toISOString()
      })
      
    } catch (error) {
      console.error('❌ Tech card save failed:', error)
      onSaveError?.({
        id: techCard.id,
        saved_at: new Date().toISOString(),
        message: error instanceof Error ? error.message : 'Произошла ошибка при сохранении'
      })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <button
      onClick={handleSave}
      disabled={disabled || isSaving}
      className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
      title="Сохранить техкарту в библиотеку для повторного использования"
    >
      {isSaving ? (
        <span className="flex items-center space-x-2">
          <div className="w-4 h-4 border-2 border-gray-600 border-t-transparent rounded-full animate-spin"></div>
          <span>Сохраняю...</span>
        </span>
      ) : (
        <span className="flex items-center space-x-2">
          <div className="w-4 h-4 border border-current rounded-sm flex items-center justify-center">
            <div className="w-2 h-2 border border-current rounded-sm"></div>
          </div>
          <span>Сохранить в библиотеку</span>
        </span>
      )}
    </button>
  )
}

export default SaveButton