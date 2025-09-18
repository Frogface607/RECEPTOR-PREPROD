import React from 'react'
import { getFormatInfo } from '../../utils/download'

interface FormatCardProps {
  format: 'pdf' | 'xlsx' | 'iiko_csv' | 'iiko_xml'
  onSelect: (format: string) => void
  disabled?: boolean
  isExporting?: boolean
  userPlan: 'free' | 'pro' | 'enterprise'
}

const FormatCard: React.FC<FormatCardProps> = ({ 
  format, 
  onSelect, 
  disabled = false, 
  isExporting = false,
  userPlan
}) => {
  const formatInfo = getFormatInfo(format)
  const isProRequired = formatInfo.isPro && userPlan === 'free'
  const isDisabled = disabled || isExporting || (isProRequired && userPlan === 'free')

  const handleClick = () => {
    if (!isDisabled) {
      onSelect(format)
    }
  }

  const getIcon = () => {
    switch (format) {
      case 'pdf':
        return (
          <div className="w-8 h-8 border-2 border-current rounded-sm flex items-center justify-center">
            <div className="text-xs font-bold">PDF</div>
          </div>
        )
      case 'xlsx':
        return (
          <div className="w-8 h-8 border-2 border-current rounded-sm flex items-center justify-center bg-green-50">
            <div className="text-xs font-bold text-green-600">XLS</div>
          </div>
        )
      case 'iiko_csv':
        return (
          <div className="w-8 h-8 border-2 border-current rounded-sm flex items-center justify-center bg-blue-50">
            <div className="text-xs font-bold text-blue-600">CSV</div>
          </div>
        )
      case 'iiko_xml':
        return (
          <div className="w-8 h-8 border-2 border-current rounded-sm flex items-center justify-center bg-purple-50">
            <div className="text-xs font-bold text-purple-600">XML</div>
          </div>
        )
      default:
        return (
          <div className="w-8 h-8 border-2 border-current rounded-sm flex items-center justify-center">
            <div className="text-xs font-bold">?</div>
          </div>
        )
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={isDisabled}
      className={`w-full p-4 border-2 rounded-lg text-left transition-all duration-200 ${
        isDisabled
          ? 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
          : 'border-gray-200 bg-white hover:border-primary-300 hover:bg-primary-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500'
      }`}
    >
      <div className="flex items-start space-x-3">
        {/* Icon */}
        <div className={`flex-shrink-0 ${isDisabled ? 'text-gray-400' : 'text-gray-600'}`}>
          {getIcon()}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            <h3 className={`text-heading-sm ${isDisabled ? 'text-gray-400' : 'text-gray-900'}`}>
              {formatInfo.name}
            </h3>
            
            {formatInfo.isPro && (
              <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                userPlan === 'free' 
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'bg-blue-100 text-blue-700'
              }`}>
                PRO
              </span>
            )}
          </div>
          
          <p className={`text-body-sm ${isDisabled ? 'text-gray-400' : 'text-gray-600'}`}>
            {formatInfo.description}
          </p>

          {/* Pro required message */}
          {isProRequired && (
            <p className="text-body-xs text-yellow-600 mt-2">
              Требуется PRO подписка
            </p>
          )}

          {/* Extension info */}
          {!isProRequired && (
            <p className="text-body-xs text-gray-500 mt-2">
              Файл: .{formatInfo.extension}
            </p>
          )}
          
          {/* Loading state */}
          {isExporting && (
            <div className="flex items-center space-x-2 mt-2">
              <div className="w-3 h-3 border border-primary-600 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-body-xs text-primary-600">Экспортируется...</span>
            </div>
          )}
        </div>
      </div>
    </button>
  )
}

export default FormatCard