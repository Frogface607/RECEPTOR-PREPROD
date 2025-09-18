/**
 * Validation utilities for form inputs
 */

export interface ValidationResult {
  isValid: boolean
  error?: string
}

/**
 * Validate URL format
 */
export function validateUrl(url: string): ValidationResult {
  const trimmed = url.trim()
  
  if (!trimmed) {
    return { isValid: false, error: 'URL не может быть пустым' }
  }
  
  try {
    new URL(trimmed)
    return { isValid: true }
  } catch {
    return { isValid: false, error: 'Некорректный формат URL' }
  }
}

/**
 * Validate API token format
 */
export function validateApiToken(token: string): ValidationResult {
  const trimmed = token.trim()
  
  if (!trimmed) {
    return { isValid: false, error: 'API токен обязателен' }
  }
  
  if (trimmed.length < 10) {
    return { isValid: false, error: 'API токен слишком короткий (минимум 10 символов)' }
  }
  
  if (trimmed.length > 500) {
    return { isValid: false, error: 'API токен слишком длинный (максимум 500 символов)' }
  }
  
  // Check for suspicious characters that might indicate copy-paste errors
  if (trimmed.includes(' ') || trimmed.includes('\n') || trimmed.includes('\t')) {
    return { isValid: false, error: 'API токен содержит пробелы или переносы строк' }
  }
  
  return { isValid: true }
}

/**
 * Validate organization ID (optional field)
 */
export function validateOrganizationId(orgId: string): ValidationResult {
  const trimmed = orgId.trim()
  
  // Organization ID is optional
  if (!trimmed) {
    return { isValid: true }
  }
  
  // UUID format validation (iiko typically uses UUIDs)
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
  
  if (!uuidRegex.test(trimmed)) {
    return { isValid: false, error: 'Organization ID должен быть в формате UUID' }
  }
  
  return { isValid: true }
}

/**
 * Validate all iiko integration fields
 */
export function validateIikoIntegration(data: {
  baseUrl: string
  token: string
  organizationId?: string
}): ValidationResult {
  // Validate base URL
  const urlValidation = validateUrl(data.baseUrl)
  if (!urlValidation.isValid) {
    return { isValid: false, error: `Base URL: ${urlValidation.error}` }
  }
  
  // Validate token
  const tokenValidation = validateApiToken(data.token)
  if (!tokenValidation.isValid) {
    return { isValid: false, error: `API Token: ${tokenValidation.error}` }
  }
  
  // Validate organization ID if provided
  if (data.organizationId) {
    const orgValidation = validateOrganizationId(data.organizationId)
    if (!orgValidation.isValid) {
      return { isValid: false, error: `Organization ID: ${orgValidation.error}` }
    }
  }
  
  return { isValid: true }
}

/**
 * Clean and normalize input values
 */
export function normalizeInputs(data: {
  baseUrl: string
  token: string
  organizationId?: string
}) {
  return {
    baseUrl: data.baseUrl.trim().replace(/\/$/, ''), // Remove trailing slash
    token: data.token.trim(),
    organizationId: data.organizationId?.trim() || undefined
  }
}