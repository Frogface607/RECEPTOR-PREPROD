/**
 * Utility functions for downloading files from blob responses
 */

export interface DownloadOptions {
  filename?: string
  fallbackName?: string
}

/**
 * Extract filename from Content-Disposition header
 */
export function extractFilenameFromHeader(contentDisposition?: string): string | null {
  if (!contentDisposition) return null

  // Try to match filename="..." or filename*=UTF-8''...
  const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/i)
  if (filenameMatch && filenameMatch[1]) {
    let filename = filenameMatch[1].replace(/['"]/g, '')
    
    // Handle UTF-8 encoded filenames
    if (filename.startsWith('UTF-8\'\'')) {
      filename = decodeURIComponent(filename.substring(7))
    }
    
    return filename
  }

  // Try to match filename*= format (RFC 5987)
  const extendedMatch = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (extendedMatch && extendedMatch[1]) {
    return decodeURIComponent(extendedMatch[1])
  }

  return null
}

/**
 * Generate fallback filename based on title and format
 */
export function generateFallbackFilename(title: string, format: string): string {
  // Clean title for filename
  const cleanTitle = title
    .replace(/[<>:"/\\|?*]/g, '') // Remove invalid filename characters
    .replace(/\s+/g, '_') // Replace spaces with underscores
    .substring(0, 50) // Limit length

  const extensions: Record<string, string> = {
    pdf: 'pdf',
    xlsx: 'xlsx',
    iiko_csv: 'csv',
    iiko_xml: 'xml'
  }

  const extension = extensions[format] || 'txt'
  return `${cleanTitle}.${extension}`
}

/**
 * Download blob as file
 */
export function downloadBlob(
  blob: Blob, 
  contentDisposition?: string,
  options: DownloadOptions = {}
): void {
  try {
    // Extract filename from header or use provided/fallback name
    let filename = extractFilenameFromHeader(contentDisposition)
    
    if (!filename) {
      filename = options.filename || options.fallbackName || 'download'
    }

    console.log(`📥 Downloading file: ${filename} (${blob.size} bytes)`)

    // Create blob URL
    const url = window.URL.createObjectURL(blob)

    // Create temporary download link
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.style.display = 'none'

    // Add to DOM, click, and remove
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    // Clean up blob URL
    setTimeout(() => {
      window.URL.revokeObjectURL(url)
    }, 100)

    console.log(`✅ File download initiated: ${filename}`)
    
  } catch (error) {
    console.error('❌ Download failed:', error)
    throw new Error('Не удалось скачать файл. Попробуйте еще раз.')
  }
}

/**
 * Check if blob contains error response (JSON instead of file)
 */
export async function validateBlobResponse(blob: Blob): Promise<void> {
  // If blob is very small and content-type suggests JSON, it might be an error
  if (blob.size < 1000 && blob.type.includes('application/json')) {
    try {
      const text = await blob.text()
      const errorData = JSON.parse(text)
      
      if (errorData.error || errorData.message) {
        throw new Error(errorData.message || errorData.error || 'Ошибка экспорта')
      }
    } catch (parseError) {
      // If it's not JSON, assume it's a valid small file
      console.log('Blob validation passed - not a JSON error response')
    }
  }
}

/**
 * Validate export format
 */
export function validateExportFormat(format: string): boolean {
  const validFormats = ['pdf', 'xlsx', 'iiko_csv', 'iiko_xml']
  return validFormats.includes(format)
}

/**
 * Get format display info
 */
export function getFormatInfo(format: string): {
  name: string
  extension: string
  description: string
  isPro: boolean
} {
  const formats: Record<string, any> = {
    pdf: {
      name: 'PDF',
      extension: 'pdf',
      description: 'Готовый к печати документ с полным оформлением',
      isPro: false
    },
    xlsx: {
      name: 'Excel',
      extension: 'xlsx',
      description: 'Таблица Excel для редактирования и анализа',
      isPro: true
    },
    iiko_csv: {
      name: 'iiko CSV',
      extension: 'csv',
      description: 'CSV файл для импорта в систему iiko',
      isPro: true
    },
    iiko_xml: {
      name: 'iiko XML',
      extension: 'xml',
      description: 'XML файл для импорта техкарт в iiko',
      isPro: true
    }
  }

  return formats[format] || {
    name: format.toUpperCase(),
    extension: 'txt',
    description: 'Неизвестный формат',
    isPro: false
  }
}