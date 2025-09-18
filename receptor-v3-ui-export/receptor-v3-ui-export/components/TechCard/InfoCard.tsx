import React from 'react'

interface InfoCardProps {
  title: string
  value: string | number
  unit?: string
  subtitle?: string
  variant?: 'default' | 'primary' | 'secondary'
}

const InfoCard: React.FC<InfoCardProps> = ({ 
  title, 
  value, 
  unit, 
  subtitle,
  variant = 'default' 
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        return 'border-primary-200 bg-primary-50'
      case 'secondary':
        return 'border-blue-200 bg-blue-50'
      default:
        return 'border-gray-200 bg-white'
    }
  }

  return (
    <div className={`rounded-lg shadow-sm border p-4 ${getVariantStyles()}`}>
      <h3 className="text-heading-sm text-gray-700 mb-2">{title}</h3>
      <div className="flex items-baseline space-x-1">
        <span className="text-2xl font-semibold text-gray-900">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </span>
        {unit && (
          <span className="text-body-sm text-gray-500">{unit}</span>
        )}
      </div>
      {subtitle && (
        <p className="text-body-xs text-gray-500 mt-1">{subtitle}</p>
      )}
    </div>
  )
}

export default InfoCard