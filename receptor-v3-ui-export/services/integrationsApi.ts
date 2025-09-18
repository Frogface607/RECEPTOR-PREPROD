import { api } from './api'

// iiko Integration Types
export interface IikoIntegrationConfig {
  baseUrl: string
  token: string
  organizationId?: string
}

export interface IikoStatus {
  connected: boolean
  baseUrl?: string
  organizationId?: string
  updatedAt?: string
  message?: string
}

export interface IikoTestResult {
  ok: boolean
  message?: string
  details?: any
}

class IntegrationsApiService {
  /**
   * Test iiko connection
   */
  async testIikoConnection(config: IikoIntegrationConfig): Promise<IikoTestResult> {
    try {
      console.log('🔌 Testing iiko connection:', config.baseUrl)

      const response = await api.post<IikoTestResult>(
        '/api/integrations/iiko/test',
        {
          baseUrl: config.baseUrl,
          token: config.token,
          organizationId: config.organizationId
        },
        {
          timeout: 30000 // 30 seconds for connection test
        }
      )

      console.log('✅ iiko connection test completed:', response.data)
      
      return response.data
    } catch (error) {
      console.error('🚨 iiko connection test failed:', error)
      throw error
    }
  }

  /**
   * Save iiko integration settings (PRO only)
   */
  async saveIikoIntegration(config: IikoIntegrationConfig): Promise<{ success: boolean; message?: string }> {
    try {
      console.log('💾 Saving iiko integration settings')

      const response = await api.post<{ success: boolean; message?: string }>(
        '/api/integrations/iiko/save',
        {
          baseUrl: config.baseUrl,
          token: config.token,
          organizationId: config.organizationId
        }
      )

      console.log('✅ iiko integration settings saved')
      
      return response.data
    } catch (error) {
      console.error('🚨 Failed to save iiko integration settings:', error)
      throw error
    }
  }

  /**
   * Get current iiko integration status
   */
  async getIikoStatus(): Promise<IikoStatus> {
    try {
      console.log('📊 Loading iiko integration status')

      const response = await api.get<IikoStatus>(
        '/api/integrations/iiko/status'
      )

      console.log('✅ iiko status loaded:', response.data)
      
      return response.data
    } catch (error) {
      console.error('🚨 Failed to load iiko status:', error)
      
      // Graceful fallback for 404 or network errors
      if ((error as any)?.response?.status === 404) {
        console.log('📝 No iiko integration configured, returning disconnected status')
        return {
          connected: false,
          message: 'Интеграция не настроена'
        }
      }
      
      throw error
    }
  }

  /**
   * Disconnect iiko integration
   */
  async disconnectIiko(): Promise<{ success: boolean }> {
    try {
      console.log('🔌 Disconnecting iiko integration')

      const response = await api.delete<{ success: boolean }>(
        '/api/integrations/iiko/disconnect'
      )

      console.log('✅ iiko integration disconnected')
      
      return response.data
    } catch (error) {
      console.error('🚨 Failed to disconnect iiko integration:', error)
      throw error
    }
  }

  /**
   * Validate iiko configuration before testing
   */
  validateConfig(config: Partial<IikoIntegrationConfig>): { isValid: boolean; error?: string } {
    if (!config.baseUrl?.trim()) {
      return { isValid: false, error: 'Base URL обязателен' }
    }
    
    if (!config.token?.trim()) {
      return { isValid: false, error: 'API Token обязателен' }
    }
    
    try {
      new URL(config.baseUrl)
    } catch {
      return { isValid: false, error: 'Некорректный формат Base URL' }
    }
    
    return { isValid: true }
  }
}

// Export singleton instance
export const integrationsApi = new IntegrationsApiService()
export default integrationsApi