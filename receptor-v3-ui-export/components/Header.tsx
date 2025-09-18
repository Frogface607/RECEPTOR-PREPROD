import React, { useState } from 'react'
import { useFeatureFlags } from '../../utils/featureFlags'
import { useOnboarding } from '../../hooks/useOnboarding'
import { useApiHealth } from '../../hooks/useApiHealth'
import TokensDisplay from '../BugReport/TokensDisplay'
import BugReportModal from '../BugReport/BugReportModal'

const Header: React.FC = () => {
  const { isEnabled } = useFeatureFlags()
  const { startOnboarding, isCompleted } = useOnboarding()
  const { status, statusDisplay, refreshHealth, lastChecked } = useApiHealth()
  const [isBugReportOpen, setIsBugReportOpen] = useState(false)

  const showQuickStartButton = isEnabled('onboarding') && isCompleted
  const showBugReportButton = isEnabled('bug_report_ui')
  const showApiStatus = true // Always show API status

  // Event handlers
  const handleBugReport = () => {
    setIsBugReportOpen(true)
  }

  const handleQuickStart = () => {
    startOnboarding()
  }

  console.log('Header API Status:', { status, statusDisplay, showApiStatus })
  console.log('DEBUG: handleBugReport function exists:', typeof handleBugReport)

  return (
    <>
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">R</span>
            </div>
            <h1 className="text-heading-lg text-gray-900">🚀 FIXED VERSION - Receptor V3</h1>
            
            {/* API Status */}
            {showApiStatus && (
              <div className="flex items-center space-x-2">
                <button
                  onClick={refreshHealth}
                  className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs transition-colors duration-200 ${statusDisplay.bgColor} ${statusDisplay.color} hover:opacity-80`}
                  title={`API Status: ${statusDisplay.label}${lastChecked ? ` (Last checked: ${lastChecked.toLocaleTimeString()})` : ''}`}
                >
                  <span className="text-xs">{statusDisplay.icon}</span>
                  <span className="font-medium">{statusDisplay.label}</span>
                </button>
              </div>
            )}
          </div>

          {/* Right Side - Tokens + Bug Report + Quick Start + Profile */}
          <div className="flex items-center space-x-4">
            {/* Tokens Display */}
            {showBugReportButton && (
              <TokensDisplay showLevel={true} />
            )}

            {/* Bug Report Button */}
            {showBugReportButton && (
              <button
                onClick={handleBugReport}
                className="flex items-center space-x-2 px-3 py-2 text-body-sm text-gray-600 hover:text-primary-600 hover:bg-gray-50 rounded-md transition-colors duration-200"
                title="Сообщить об ошибке"
              >
                <div className="w-4 h-4">
                  <div className="w-4 h-4 border-2 border-current rounded-sm flex items-center justify-center">
                    <div className="text-xs">🐛</div>
                  </div>
                </div>
                <span>Баг-репорт</span>
              </button>
            )}

            {/* Quick Start Button */}
            {showQuickStartButton && (
              <button
                onClick={handleQuickStart}
                className="flex items-center space-x-2 px-3 py-2 text-body-sm text-primary-600 hover:text-primary-700 hover:bg-primary-50 rounded-md transition-colors duration-200"
                title="Повторить онбординг"
              >
                <div className="w-4 h-4">
                  <div className="w-4 h-4 border-2 border-current rounded-full flex items-center justify-center">
                    <div className="text-xs font-bold">?</div>
                  </div>
                </div>
                <span>Быстрый старт</span>
              </button>
            )}

            {/* Mini Profile */}
            <div className="flex items-center space-x-3">
              <div className="text-right">
                <p className="text-body-sm text-gray-900">Пользователь</p>
                <p className="text-body-xs text-gray-500">V3 Preview</p>
              </div>
              <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                <span className="text-gray-600 font-medium text-sm">П</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Bug Report Modal */}
      <BugReportModal
        isVisible={isBugReportOpen}
        onClose={() => setIsBugReportOpen(false)}
      />
    </>
  )
}

export default Header