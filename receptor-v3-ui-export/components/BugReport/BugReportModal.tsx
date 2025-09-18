import React, { useState, useRef, useEffect } from 'react'
import { submitBugReport, BugReport } from '../../services/bugReportApi'
import { useTokens, TOKEN_REWARDS } from '../../hooks/useTokens'
import Toast from '../ui/Toast'

interface BugReportModalProps {
  isVisible: boolean
  onClose: () => void
}

type FormData = Omit<BugReport, 'user_agent' | 'url' | 'timestamp'>

const BugReportModal: React.FC<BugReportModalProps> = ({ 
  isVisible, 
  onClose 
}) => {
  const modalRef = useRef<HTMLDivElement>(null)
  const { addTokens, getRewardForReportType } = useTokens()
  
  const [formData, setFormData] = useState<FormData>({
    type: 'bug',
    title: '',
    description: '',
    priority: 'medium',
    steps: ''
  })
  
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  // Handle ESC key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isVisible) {
        onClose()
      }
    }

    if (isVisible) {
      document.addEventListener('keydown', handleEsc)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEsc)
      document.body.style.overflow = 'unset'
    }
  }, [isVisible, onClose])

  // Focus management
  useEffect(() => {
    if (isVisible && modalRef.current) {
      const firstInput = modalRef.current.querySelector('input, select, textarea') as HTMLElement
      if (firstInput) {
        firstInput.focus()
      }
    }
  }, [isVisible])

  const reportTypes = [
    { 
      value: 'bug' as const, 
      label: '🐛 Баг/Ошибка', 
      description: 'Что-то работает неправильно',
      reward: '+5 токенов'
    },
    { 
      value: 'feature' as const, 
      label: '💡 Новая функция', 
      description: 'Предложение улучшения',
      reward: '+10 токенов'
    },
    { 
      value: 'ux' as const, 
      label: '🎨 UX/Дизайн', 
      description: 'Улучшение интерфейса',
      reward: '+10 токенов + бейдж'
    }
  ]

  const priorities = [
    { value: 'low' as const, label: 'Низкий', color: 'text-gray-600' },
    { value: 'medium' as const, label: 'Средний', color: 'text-yellow-600' },
    { value: 'high' as const, label: 'Высокий', color: 'text-orange-600' },
    { value: 'critical' as const, label: 'Критический', color: 'text-red-600' }
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.title.trim() || !formData.description.trim()) {
      setToast({ message: 'Заполните обязательные поля', type: 'error' })
      return
    }

    setIsSubmitting(true)
    
    try {
      const response = await submitBugReport(formData)
      
      // Начислить токены
      const reward = getRewardForReportType(formData.type, formData.priority)
      addTokens(reward)
      
      // Показать успешное уведомление
      const tokenMessage = formData.type === 'bug' && formData.priority === 'critical' 
        ? `+${reward.amount} токенов + неделя PRO!`
        : `+${reward.amount} токенов за ${reward.reason.toLowerCase()}!`
      
      setToast({ 
        message: `${response.message} ${tokenMessage}`, 
        type: 'success' 
      })
      
      // Очистить форму и закрыть модал
      setFormData({
        type: 'bug',
        title: '',
        description: '',
        priority: 'medium',
        steps: ''
      })
      
      setTimeout(() => {
        onClose()
      }, 2000)
      
    } catch (error: any) {
      setToast({ 
        message: error.message || 'Не удалось отправить репорт', 
        type: 'error' 
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  if (!isVisible) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-gray-900 bg-opacity-75 transition-opacity"
        onClick={handleOverlayClick}
      />
      
      {/* Modal */}
      <div className="flex min-h-screen items-center justify-center p-4">
        <div 
          ref={modalRef}
          className="relative w-full max-w-2xl transform transition-all"
          role="dialog"
          aria-modal="true"
          aria-labelledby="bug-report-title"
        >
          <div className="bg-white rounded-lg shadow-xl overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-primary-500 to-primary-600 px-6 py-4">
              <div className="flex items-center justify-between">
                <h2 id="bug-report-title" className="text-heading-lg text-white">
                  Сообщить об ошибке
                </h2>
                <button
                  onClick={onClose}
                  className="text-white hover:text-gray-200 transition-colors duration-200"
                  aria-label="Закрыть"
                >
                  <div className="w-6 h-6 relative">
                    <div className="absolute inset-0 w-0.5 h-6 bg-current transform rotate-45 left-1/2 -translate-x-1/2"></div>
                    <div className="absolute inset-0 w-0.5 h-6 bg-current transform -rotate-45 left-1/2 -translate-x-1/2"></div>
                  </div>
                </button>
              </div>
              
              <p className="text-primary-100 text-body-sm mt-2">
                Помогите нам улучшить Receptor V3 и получите токены за активность!
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              {/* Type Selection */}
              <div>
                <label className="block text-heading-sm text-gray-900 mb-3">
                  Тип обращения
                </label>
                <div className="grid grid-cols-1 gap-3">
                  {reportTypes.map((type) => (
                    <label
                      key={type.value}
                      className={`flex items-start p-4 border-2 rounded-lg cursor-pointer transition-colors duration-200 ${
                        formData.type === type.value
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name="type"
                        value={type.value}
                        checked={formData.type === type.value}
                        onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value as any }))}
                        className="sr-only"
                      />
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="text-heading-sm text-gray-900">{type.label}</span>
                          <span className="text-body-xs text-primary-600 font-medium">{type.reward}</span>
                        </div>
                        <p className="text-body-sm text-gray-600 mt-1">{type.description}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Title */}
              <div>
                <label htmlFor="title" className="block text-heading-sm text-gray-900 mb-2">
                  Заголовок <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="title"
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="Кратко опишите проблему или предложение"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                />
              </div>

              {/* Priority (only for bugs) */}
              {formData.type === 'bug' && (
                <div>
                  <label htmlFor="priority" className="block text-heading-sm text-gray-900 mb-2">
                    Приоритет
                  </label>
                  <select
                    id="priority"
                    value={formData.priority}
                    onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value as any }))}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    {priorities.map((priority) => (
                      <option key={priority.value} value={priority.value}>
                        {priority.label}
                        {priority.value === 'critical' && ' (+25 токенов + неделя PRO)'}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Description */}
              <div>
                <label htmlFor="description" className="block text-heading-sm text-gray-900 mb-2">
                  Описание <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Подробно опишите проблему или ваше предложение"
                  rows={4}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-vertical"
                  required
                />
              </div>

              {/* Steps (only for bugs) */}
              {formData.type === 'bug' && (
                <div>
                  <label htmlFor="steps" className="block text-heading-sm text-gray-900 mb-2">
                    Шаги воспроизведения
                  </label>
                  <textarea
                    id="steps"
                    value={formData.steps}
                    onChange={(e) => setFormData(prev => ({ ...prev, steps: e.target.value }))}
                    placeholder="1. Откройте страницу...&#10;2. Нажмите на кнопку...&#10;3. Увидите ошибку..."
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-vertical"
                  />
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={onClose}
                  className="btn-secondary"
                  disabled={isSubmitting}
                >
                  Отмена
                </button>
                
                <button
                  type="submit"
                  disabled={isSubmitting || !formData.title.trim() || !formData.description.trim()}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (
                    <span className="flex items-center space-x-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Отправляем...</span>
                    </span>
                  ) : (
                    'Отправить'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Toast notifications */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  )
}

export default BugReportModal