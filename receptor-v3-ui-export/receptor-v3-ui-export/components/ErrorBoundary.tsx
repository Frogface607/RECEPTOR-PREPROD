import React from 'react'

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
  errorInfo?: React.ErrorInfo
  retryCount: number
}

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
  maxRetries?: number
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private retryTimeout?: number

  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { 
      hasError: false,
      retryCount: 0
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('🚨 CRITICAL ERROR caught by ErrorBoundary:', error, errorInfo)
    
    this.setState({
      error,
      errorInfo
    })
    
    // Auto-retry for certain types of errors
    if (this.shouldAutoRetry(error) && this.state.retryCount < (this.props.maxRetries || 3)) {
      console.log(`🔄 Auto-retrying error (attempt ${this.state.retryCount + 1})...`)
      
      this.retryTimeout = setTimeout(() => {
        this.setState(prevState => ({
          hasError: false,
          error: undefined,
          errorInfo: undefined,
          retryCount: prevState.retryCount + 1
        }))
      }, 2000)
    }
  }

  componentWillUnmount() {
    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout)
    }
  }

  shouldAutoRetry(error: Error): boolean {
    // Auto-retry for network errors, chunk loading errors, etc.
    const retryableErrors = [
      'ChunkLoadError',
      'Loading chunk',
      'Loading CSS chunk',
      'Network error',
      'Failed to fetch'
    ]
    
    return retryableErrors.some(errorType => 
      error.message?.includes(errorType) || error.name?.includes(errorType)
    )
  }

  handleManualRetry = () => {
    console.log('🔄 Manual retry triggered by user')
    this.setState({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      retryCount: 0
    })
  }

  handleReload = () => {
    console.log('🔄 Full page reload triggered by user')
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="bg-white p-8 rounded-lg shadow-lg max-w-2xl w-full mx-4">
            <div className="text-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-red-600 text-2xl">⚠️</span>
              </div>
              
              <h1 className="text-xl font-semibold text-gray-900 mb-2">
                Произошла критическая ошибка
              </h1>
              
              <p className="text-gray-600 mb-6">
                Приложение временно недоступно из-за технической ошибки. 
                Мы автоматически пытаемся восстановить работу.
              </p>

              {/* Error details (for debugging) */}
              {import.meta.env?.DEV && this.state.error && (
                <details className="text-left mb-6 p-4 bg-gray-100 rounded border">
                  <summary className="cursor-pointer font-medium text-gray-700 mb-2">
                    Техническая информация (для разработки)
                  </summary>
                  <div className="text-sm text-gray-600 font-mono">
                    <p className="mb-2"><strong>Ошибка:</strong> {this.state.error.message}</p>
                    <p className="mb-2"><strong>Стек:</strong></p>
                    <pre className="text-xs overflow-x-auto whitespace-pre-wrap bg-white p-2 rounded border">
                      {this.state.error.stack}
                    </pre>
                    {this.state.errorInfo && (
                      <>
                        <p className="mb-2 mt-4"><strong>Компонент стек:</strong></p>
                        <pre className="text-xs overflow-x-auto whitespace-pre-wrap bg-white p-2 rounded border">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </>
                    )}
                  </div>
                </details>
              )}

              {/* Retry information */}
              {this.state.retryCount > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-6">
                  <p className="text-sm text-blue-800">
                    Попытка восстановления #{this.state.retryCount} из {this.props.maxRetries || 3}
                  </p>
                </div>
              )}

              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={this.handleManualRetry}
                  className="px-6 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
                >
                  Попробовать снова
                </button>
                
                <button
                  onClick={this.handleReload}
                  className="px-6 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
                >
                  Перезагрузить страницу
                </button>
              </div>

              <div className="mt-6 text-xs text-gray-500">
                <p>
                  Если проблема повторяется, обратитесь в техническую поддержку.
                </p>
                <p className="mt-1">
                  Код ошибки: ERR_{this.state.error?.name || 'UNKNOWN'}_{Date.now().toString().slice(-6)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary