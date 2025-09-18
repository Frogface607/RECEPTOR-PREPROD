import { api } from './api'

export interface BugReport {
  type: 'bug' | 'feature' | 'ux'
  title: string
  description: string
  priority: 'low' | 'medium' | 'high' | 'critical'
  steps?: string
  user_agent?: string
  url?: string
  timestamp?: string
}

export interface BugReportResponse {
  success: boolean
  id?: string
  message?: string
  tokens_earned?: number
}

const OFFLINE_REPORTS_KEY = 'offline_bug_reports'

// Получение User Agent и текущего URL
const getBrowserInfo = (): Pick<BugReport, 'user_agent' | 'url'> => ({
  user_agent: navigator.userAgent,
  url: window.location.href
})

// Сохранение репорта для offline отправки
const saveOfflineReport = (report: BugReport) => {
  try {
    const existing = JSON.parse(localStorage.getItem(OFFLINE_REPORTS_KEY) || '[]')
    const reportWithTimestamp = {
      ...report,
      timestamp: new Date().toISOString()
    }
    existing.push(reportWithTimestamp)
    localStorage.setItem(OFFLINE_REPORTS_KEY, JSON.stringify(existing))
    console.log('Bug report saved offline:', reportWithTimestamp)
  } catch (error) {
    console.warn('Failed to save offline bug report:', error)
  }
}

// Получение сохраненных offline репортов
const getOfflineReports = (): BugReport[] => {
  try {
    return JSON.parse(localStorage.getItem(OFFLINE_REPORTS_KEY) || '[]')
  } catch (error) {
    console.warn('Failed to load offline bug reports:', error)
    return []
  }
}

// Очистка offline репортов после успешной отправки
const clearOfflineReports = () => {
  try {
    localStorage.removeItem(OFFLINE_REPORTS_KEY)
  } catch (error) {
    console.warn('Failed to clear offline bug reports:', error)
  }
}

// Отправка баг-репорта
export const submitBugReport = async (report: Omit<BugReport, 'user_agent' | 'url'>): Promise<BugReportResponse> => {
  const fullReport: BugReport = {
    ...report,
    ...getBrowserInfo(),
    timestamp: new Date().toISOString()
  }

  try {
    const response = await api.post('/api/bug-reports', fullReport)
    
    return {
      success: true,
      id: response.data.id,
      message: response.data.message || 'Баг-репорт успешно отправлен!',
      tokens_earned: response.data.tokens_earned
    }
  } catch (error: any) {
    // При ошибке сети или 404/500 сохраняем offline
    if (!error.response || error.response.status >= 500 || error.response.status === 404) {
      saveOfflineReport(fullReport)
      
      return {
        success: true,
        message: 'Баг-репорт сохранен и будет отправлен при восстановлении соединения',
        tokens_earned: getTokensForReportType(report.type, report.priority)
      }
    }
    
    // Другие ошибки (400, 401, etc)
    throw new Error(error.response?.data?.message || 'Не удалось отправить баг-репорт')
  }
}

// Повторная отправка offline репортов
export const syncOfflineReports = async (): Promise<{ sent: number; failed: number }> => {
  const offlineReports = getOfflineReports()
  
  if (offlineReports.length === 0) {
    return { sent: 0, failed: 0 }
  }

  let sent = 0
  let failed = 0

  for (const report of offlineReports) {
    try {
      await api.post('/api/bug-reports', report)
      sent++
    } catch (error) {
      failed++
      console.warn('Failed to sync offline report:', error)
    }
  }

  // Если все отправлены успешно, очищаем offline storage
  if (failed === 0) {
    clearOfflineReports()
  }

  return { sent, failed }
}

// Подсчет токенов за тип репорта (для offline режима)
const getTokensForReportType = (type: BugReport['type'], priority?: BugReport['priority']): number => {
  if (type === 'bug' && priority === 'critical') {
    return 25 // Критический баг
  }
  
  const tokens = {
    bug: 5,
    feature: 10,
    ux: 10
  }
  
  return tokens[type] || 5
}

// Проверка наличия offline репортов
export const hasOfflineReports = (): boolean => {
  return getOfflineReports().length > 0
}

// Получение количества offline репортов
export const getOfflineReportsCount = (): number => {
  return getOfflineReports().length
}