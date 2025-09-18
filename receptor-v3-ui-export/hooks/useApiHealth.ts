import { useState, useEffect, useCallback } from 'react'
import { checkAPIHealth } from '../services/api'

export type ApiHealthStatus = 'healthy' | 'degraded' | 'unhealthy' | 'checking'

export interface ApiHealthData {
  status: ApiHealthStatus
  message?: string
  lastChecked?: Date
  uptime?: number
  version?: string
}

const HEALTH_CHECK_INTERVAL = 30000 // 30 seconds

export function useApiHealth() {
  const [healthData, setHealthData] = useState<ApiHealthData>({
    status: 'checking'
  })

  const performHealthCheck = useCallback(async () => {
    try {
      const result = await checkAPIHealth()
      console.log('API Health Check Result:', result)
      setHealthData({
        status: result.status,
        message: result.data?.message,
        lastChecked: new Date(),
        uptime: result.data?.service?.uptime_minutes,
        version: result.data?.service?.version
      })
    } catch (error) {
      console.warn('Health check failed:', error)
      setHealthData(prev => ({
        ...prev,
        status: 'unhealthy',
        message: 'Не удается проверить состояние API',
        lastChecked: new Date()
      }))
    }
  }, [])

  // Perform initial check
  useEffect(() => {
    performHealthCheck()
  }, [performHealthCheck])

  // Set up periodic health checks
  useEffect(() => {
    const interval = setInterval(performHealthCheck, HEALTH_CHECK_INTERVAL)
    return () => clearInterval(interval)
  }, [performHealthCheck])

  // Manual refresh
  const refreshHealth = useCallback(() => {
    setHealthData(prev => ({ ...prev, status: 'checking' }))
    performHealthCheck()
  }, [performHealthCheck])

  // Get status display info
  const getStatusDisplay = useCallback(() => {
    switch (healthData.status) {
      case 'healthy':
        return {
          label: 'Online',
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          icon: '🟢'
        }
      case 'degraded':
        return {
          label: 'Degraded', 
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-100',
          icon: '🟡'
        }
      case 'unhealthy':
        return {
          label: 'Offline',
          color: 'text-red-600', 
          bgColor: 'bg-red-100',
          icon: '🔴'
        }
      case 'checking':
        return {
          label: 'Checking...',
          color: 'text-gray-600',
          bgColor: 'bg-gray-100', 
          icon: '⚪'
        }
    }
  }, [healthData.status])

  return {
    ...healthData,
    refreshHealth,
    statusDisplay: getStatusDisplay(),
    isOnline: healthData.status === 'healthy',
    isDegraded: healthData.status === 'degraded',
    isOffline: healthData.status === 'unhealthy'
  }
}