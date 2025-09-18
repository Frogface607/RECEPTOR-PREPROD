import React, { useState } from 'react'
import { techCardApi } from '../../services/techCardApi'
import { TechCardV2 } from '../../types/techcard-v2'
import { useUserPlan } from '../../contexts/UserPlanContext'
import { downloadBlob, generateFallbackFilename, validateBlobResponse, getFormatInfo } from '../../utils/download'
import Modal from '../ui/Modal'
import FormatCard from './FormatCard'
import { FileProgress } from '../ui/Progress'
import Alert from '../ui/Alert'

interface ExportMasterProps {
  techCard: TechCardV2
  isOpen: boolean
  onClose: () => void
}

type ExportStatus = 'idle' | 'preparing' | 'downloading' | 'complete' | 'error'

const ExportMaster: React.FC<ExportMasterProps> = ({
  techCard,
  isOpen,
  onClose
}) => {
  const { canUse, planDisplayName, isFree } = useUserPlan()
  const [exportingFormat, setExportingFormat] = useState<string | null>(null)
  const [exportStatus, setExportStatus] = useState<ExportStatus>('idle')
  const [error, setError] = useState<string | null>(null)
  const [currentFilename, setCurrentFilename] = useState<string>('')

  const formats: Array<'pdf' | 'xlsx' | 'iiko_csv' | 'iiko_xml'> = [
    'pdf', 'xlsx', 'iiko_csv', 'iiko_xml'
  ]

  const handleFormatSelect = async (format: string) => {
    // Check feature access using new gating system
    const featureKey = format === 'pdf' ? 'pdf_export' : 
                      format === 'xlsx' ? 'excel_export' : 
                      'iiko_export'
    
    if (!canUse(featureKey)) {
      // This will be handled by FeatureGate component
      return
    }

    setExportingFormat(format)
    setExportStatus('preparing')
    setError(null)
    setCurrentFilename('')

    try {
      console.log(`📤 Starting export for format: ${format}`)
      
      // Generate fallback filename
      const fallbackFilename = generateFallbackFilename(techCard.title, format)
      setCurrentFilename(fallbackFilename)
      
      // Call export API
      setExportStatus('downloading')
      const { blob, contentDisposition } = await techCardApi.export(techCard.id, format as any)
      
      // Validate response
      await validateBlobResponse(blob)
      
      // Download file
      downloadBlob(blob, contentDisposition, {
        fallbackName: fallbackFilename
      })
      
      setExportStatus('complete')
      
      // Show success briefly, then reset
      setTimeout(() => {
        setExportStatus('idle')
        setExportingFormat(null)
        setCurrentFilename('')
      }, 2000)
      
      console.log(`✅ Export completed successfully: ${format}`)
      
    } catch (err) {
      console.error('❌ Export failed:', err)
      
      const errorMessage = err instanceof Error ? err.message : 'Произошла ошибка при экспорте'
      setError(errorMessage)
      setExportStatus('error')
    }
  }

  const handleRetry = () => {
    if (exportingFormat) {
      handleFormatSelect(exportingFormat)
    }
  }

  const handleReset = () => {
    setExportingFormat(null)
    setExportStatus('idle')
    setError(null)
    setCurrentFilename('')
  }

  const handleClose = () => {
    if (exportStatus === 'preparing' || exportStatus === 'downloading') {
      // Don't allow closing during active export
      return
    }
    handleReset()
    onClose()
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Экспорт техкарты"
      size="lg"
      closeOnOverlay={exportStatus === 'idle'}
    >
      <div className="space-y-6">
        {/* Tech card info */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-heading-sm text-gray-900 mb-1">{techCard.title}</h3>
          <div className="flex items-center space-x-4 text-body-sm text-gray-600">
            <span>{techCard.portions} порций</span>
            <span>{techCard.ingredients.length} ингредиентов</span>
            <span>ID: {techCard.id.slice(-8)}</span>
          </div>
        </div>

        {/* Export status */}
        {exportStatus !== 'idle' && (
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <FileProgress
              filename={currentFilename}
              status={exportStatus}
              error={error || undefined}
            />
            
            {exportStatus === 'error' && (
              <div className="mt-4 flex space-x-3">
                <button
                  onClick={handleRetry}
                  className="btn-primary"
                >
                  Повторить
                </button>
                <button
                  onClick={handleReset}
                  className="btn-secondary"
                >
                  Выбрать другой формат
                </button>
              </div>
            )}
          </div>
        )}

        {/* Error alert */}
        {error && exportStatus === 'idle' && (
          <Alert variant="error" onClose={() => setError(null)}>
            <strong>Ошибка экспорта:</strong> {error}
          </Alert>
        )}

        {/* Format selection */}
        {exportStatus === 'idle' && (
          <>
            <div>
              <h4 className="text-heading-md text-gray-900 mb-2">Выберите формат экспорта</h4>
              <p className="text-body-sm text-gray-600 mb-4">
                Экспортируйте техкарту в удобном для вас формате. 
                PDF доступен бесплатно, остальные форматы требуют PRO подписку.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {formats.map((format) => (
                <FormatCard
                  key={format}
                  format={format}
                  onSelect={handleFormatSelect}
                  disabled={exportingFormat !== null}
                  isExporting={exportingFormat === format}
                  userPlan={isFree ? 'free' : 'pro'}
                />
              ))}
            </div>

            {/* Plan info */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <div className="w-5 h-5 text-blue-600 mt-0.5">
                  <div className="w-4 h-4 border-2 border-current rounded-full flex items-center justify-center">
                    <div className="w-1 h-1 bg-current rounded-full"></div>
                  </div>
                </div>
                <div>
                  <h5 className="text-heading-sm text-blue-900 mb-1">
                    Текущий план: {planDisplayName}
                  </h5>
                  <ul className="text-body-xs text-blue-700 space-y-1">
                    <li>• PDF экспорт доступен на всех планах</li>
                    {isFree ? (
                      <li>• Excel и iiko форматы доступны с PRO подпиской</li>
                    ) : (
                      <li>• Все форматы экспорта доступны на вашем плане</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Actions */}
        {exportStatus === 'idle' && (
          <div className="flex justify-end">
            <button
              onClick={handleClose}
              className="btn-secondary"
            >
              Закрыть
            </button>
          </div>
        )}
        
        {exportStatus === 'complete' && (
          <div className="text-center">
            <button
              onClick={handleClose}
              className="btn-primary"
            >
              Готово
            </button>
          </div>
        )}
      </div>
    </Modal>
  )
}

export default ExportMaster