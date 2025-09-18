import React, { useEffect, useState } from 'react'
import { useTokens, TokenReward } from '../../hooks/useTokens'

interface TokensDisplayProps {
  showLevel?: boolean
  className?: string
}

const TokensDisplay: React.FC<TokensDisplayProps> = ({ 
  showLevel = false, 
  className = '' 
}) => {
  const { total, level, levelProgress, animationQueue, clearAnimationQueue } = useTokens()
  const [animatingReward, setAnimatingReward] = useState<TokenReward | null>(null)
  const [showConfetti, setShowConfetti] = useState(false)

  // Обработка анимаций из очереди
  useEffect(() => {
    if (animationQueue.length > 0 && !animatingReward) {
      const nextReward = animationQueue[0]
      setAnimatingReward(nextReward)
      setShowConfetti(true)
      
      // Убираем анимацию через 3 секунды
      setTimeout(() => {
        setAnimatingReward(null)
        setShowConfetti(false)
        clearAnimationQueue()
      }, 3000)
    }
  }, [animationQueue, animatingReward, clearAnimationQueue])

  const getTokenIcon = () => {
    return (
      <div className="w-5 h-5 bg-gradient-to-br from-yellow-400 to-yellow-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
        ⭐
      </div>
    )
  }

  const getLevelColor = () => {
    switch (level) {
      case 'Эксперт':
        return 'text-purple-600'
      case 'Активный':
        return 'text-blue-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <div className={`relative ${className}`}>
      {/* Основной счетчик */}
      <div className="flex items-center space-x-2">
        {getTokenIcon()}
        
        <div className="flex flex-col">
          <div className="flex items-center space-x-1">
            <span className="text-heading-sm font-bold text-gray-900">
              {total.toLocaleString()}
            </span>
            {showLevel && (
              <span className={`text-body-xs ${getLevelColor()}`}>
                {level}
              </span>
            )}
          </div>
          
          {showLevel && (
            <div className="w-16">
              <div className="w-full bg-gray-200 rounded-full h-1">
                <div 
                  className="bg-gradient-to-r from-yellow-400 to-yellow-600 h-1 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(levelProgress.progress, 100)}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Анимация начисления токенов */}
      {animatingReward && (
        <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 z-50">
          <div className="animate-bounce bg-green-500 text-white px-3 py-1 rounded-full text-body-xs font-bold shadow-lg">
            +{animatingReward.amount} 🎉
          </div>
        </div>
      )}

      {/* Эффект конфетти */}
      {showConfetti && (
        <div className="absolute inset-0 pointer-events-none">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="absolute animate-ping"
              style={{
                left: `${20 + i * 15}%`,
                top: `${10 + (i % 2) * 20}%`,
                animationDelay: `${i * 0.1}s`,
                animationDuration: '1s'
              }}
            >
              <div className={`w-2 h-2 ${
                i % 3 === 0 ? 'bg-yellow-400' : 
                i % 3 === 1 ? 'bg-blue-400' : 'bg-green-400'
              } rounded-full`} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default TokensDisplay