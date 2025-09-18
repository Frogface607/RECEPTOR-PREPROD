import React, { useState } from 'react'
import { techCardApi } from '../../services/techCardApi'

interface AIEditorProps {
  techCardId: string
  onEditStart: () => void
  onEditSuccess: (updatedTechCard: any) => void
  onEditError: (error: string) => void
  disabled?: boolean
}

const QUICK_PROMPTS = [
  'Увеличить порцию в 2 раза',
  'Заменить масло на оливковое', 
  'Снизить калорийность на 15%',
  'Добавить специи по вкусу'
]

const AIEditor: React.FC<AIEditorProps> = ({
  techCardId,
  onEditStart,
  onEditSuccess,
  onEditError,
  disabled = false
}) => {
  const [prompt, setPrompt] = useState('')
  const [isEditing, setIsEditing] = useState(false)

  const handleEdit = async () => {
    // Validate prompt
    const validation = techCardApi.validateEditPrompt(prompt)
    if (!validation.isValid) {
      onEditError(validation.error || 'Неверное описание изменений')
      return
    }

    setIsEditing(true)
    onEditStart()

    try {
      console.log('🎯 Starting optimistic AI edit:', prompt)
      const updatedTechCard = await techCardApi.edit(techCardId, prompt)
      
      console.log('✅ AI edit completed successfully')
      onEditSuccess(updatedTechCard)
      setPrompt('') // Clear prompt on success
      
    } catch (error) {
      console.error('❌ AI edit failed:', error)
      const errorMessage = error instanceof Error ? error.message : 'Произошла ошибка при редактировании'
      onEditError(errorMessage)
    } finally {
      setIsEditing(false)
    }
  }

  const handleQuickPrompt = (quickPrompt: string) => {
    setPrompt(quickPrompt)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && !isEditing) {
      e.preventDefault()
      handleEdit()
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-heading-lg text-gray-900 mb-1">Редактировать через ИИ</h3>
        <p className="text-body-sm text-gray-500">
          Опишите, что хотите изменить в техкарте, и ИИ применит изменения автоматически
        </p>
      </div>
      
      <div className="p-4 space-y-4">
        {/* Quick prompts */}
        <div>
          <label className="block text-heading-sm text-gray-700 mb-2">
            Быстрые команды
          </label>
          <div className="flex flex-wrap gap-2">
            {QUICK_PROMPTS.map((quickPrompt, index) => (
              <button
                key={index}
                onClick={() => handleQuickPrompt(quickPrompt)}
                disabled={disabled || isEditing}
                className="px-3 py-1 text-body-sm bg-gray-100 text-gray-700 rounded-full border border-gray-200 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
              >
                {quickPrompt}
              </button>
            ))}
          </div>
        </div>

        {/* Prompt input */}
        <div>
          <label htmlFor="ai-prompt" className="block text-heading-sm text-gray-700 mb-2">
            Описание изменений
          </label>
          <textarea
            id="ai-prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Например: Замени говядину на курицу и уменьши количество соли..."
            disabled={disabled || isEditing}
            rows={3}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-body-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-50 disabled:text-gray-500 resize-none"
          />
          <div className="flex items-center justify-between mt-2">
            <p className="text-body-xs text-gray-500">
              Ctrl+Enter для быстрого применения
            </p>
            <p className="text-body-xs text-gray-500">
              {prompt.length}/500
            </p>
          </div>
        </div>

        {/* Action button */}
        <div className="flex items-center justify-end">
          <button
            onClick={handleEdit}
            disabled={disabled || isEditing || !prompt.trim()}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isEditing ? (
              <span className="flex items-center space-x-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Применяю изменения...</span>
              </span>
            ) : (
              'Применить изменения'
            )}
          </button>
        </div>
      </div>

      {/* Help text */}
      <div className="px-4 pb-4">
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start space-x-2">
            <div className="w-4 h-4 text-blue-600 mt-0.5">
              <div className="w-4 h-4 border-2 border-current rounded-full flex items-center justify-center">
                <div className="w-1 h-1 bg-current rounded-full"></div>
              </div>
            </div>
            <div>
              <p className="text-body-xs text-blue-700">
                <strong>Совет:</strong> Чем подробнее описание, тем точнее будут изменения. 
                Укажите конкретные ингредиенты, количества или процессы для лучшего результата.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AIEditor