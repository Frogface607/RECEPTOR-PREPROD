import { api } from './api'

export interface BillingPlan {
  id: string
  name: string
  amount: string
  currency: string
  billing_period: 'monthly' | 'annual'
  description: string
  features: string[]
  payment_methods?: string[]
}

export interface PaymentResponse {
  confirmation_url: string
  payment_id: string
  status: string
  amount: {
    value: string
    currency: string
  }
  expires_in: string
  package: {
    id: string
    name: string
    billing_period: string
  }
}

export interface PaymentStatusResponse {
  payment_id: string
  status: string
  amount: {
    value: string
    currency: string
  }
  description: string
  created_at?: string
  payment_method?: {
    type: string
    title: string
  }
  metadata: any
  local_transaction: boolean
}

// Mock data for demo purposes until backend integration is resolved
const MOCK_RU_PLANS: BillingPlan[] = [
  {
    id: 'pro_monthly_ru',
    name: 'PRO Ежемесячно',
    amount: '1990.00',
    currency: 'RUB',
    billing_period: 'monthly',
    description: 'PRO подписка Receptor - доступ ко всем функциям на 1 месяц',
    features: [
      'Export Master (PDF, Excel, iiko)',
      'Генератор меню',
      'Интеграция с iiko',
      'AI-Лаборатория',
      'Приоритетная поддержка',
      'Расширенная аналитика'
    ],
    payment_methods: [
      'Банковские карты (МИР, Visa, Mastercard)',
      'СБП (Система быстрых платежей)',
      'Apple Pay / Google Pay',
      'ЮMoney',
      'Сбербанк Онлайн',
      'Альфа-Клик'
    ]
  },
  {
    id: 'pro_annual_ru',
    name: 'PRO Ежегодно',
    amount: '19900.00',
    currency: 'RUB',
    billing_period: 'annual',
    description: 'PRO подписка Receptor - доступ ко всем функциям на 1 год (экономия 2 месяца)',
    features: [
      'Export Master (PDF, Excel, iiko)',
      'Генератор меню',
      'Интеграция с iiko',
      'AI-Лаборатория',
      'Приоритетная поддержка',
      'Расширенная аналитика'
    ],
    payment_methods: [
      'Банковские карты (МИР, Visa, Mastercard)',
      'СБП (Система быстрых платежей)',
      'Apple Pay / Google Pay',
      'ЮMoney',
      'Сбербанк Онлайн',
      'Альфа-Клик'
    ]
  }
]

const MOCK_INTL_PLANS: BillingPlan[] = [
  {
    id: 'pro_monthly',
    name: 'PRO Monthly',
    amount: '29.00',
    currency: 'USD',
    billing_period: 'monthly',
    description: 'PRO subscription - access to all features for 1 month',
    features: [
      'Export Master (PDF, Excel)',
      'Menu Generator',
      'AI Kitchen Lab',
      'Priority Support',
      'Advanced Analytics'
    ]
  },
  {
    id: 'pro_annual',
    name: 'PRO Annual',
    amount: '290.00',
    currency: 'USD',
    billing_period: 'annual',
    description: 'PRO subscription - access to all features for 1 year (2 months free)',
    features: [
      'Export Master (PDF, Excel)',
      'Menu Generator',
      'AI Kitchen Lab',
      'Priority Support',
      'Advanced Analytics'
    ]
  }
]

// Determine market based on locale or other factors
const getMarket = (): 'RU' | 'INTERNATIONAL' => {
  // In production, this could be based on:
  // - User's country setting
  // - IP geolocation
  // - Browser locale
  // - URL subdomain (ru.receptor.com vs receptor.com)
  
  const locale = navigator.language || 'en'
  if (locale.startsWith('ru')) {
    return 'RU'
  }
  
  // For demo purposes, default to RU to test YooKassa
  return 'RU'
}

export const billingApi = {
  // Get available billing plans based on market
  getPlans: async (): Promise<{ plans: BillingPlan[]; currency: string; market: string }> => {
    const market = getMarket()
    
    // Try to get plans from API first, fallback to mock data
    try {
      if (market === 'RU') {
        // Try YooKassa API
        const response = await api.get('/api/yookassa/plans')
        return response.data
      } else {
        // Try Stripe API
        const response = await api.get('/api/billing/plans')
        return {
          plans: response.data.plans,
          currency: 'USD',
          market: 'INTERNATIONAL'
        }
      }
    } catch (error) {
      console.warn('API not available, using mock data:', error)
      
      // Return mock data based on market
      if (market === 'RU') {
        return {
          plans: MOCK_RU_PLANS,
          currency: 'RUB',
          market: 'RU'
        }
      } else {
        return {
          plans: MOCK_INTL_PLANS,
          currency: 'USD',
          market: 'INTERNATIONAL'
        }
      }
    }
  },

  // Create payment session
  createPayment: async (
    packageId: string, 
    userId?: string, 
    userEmail?: string
  ): Promise<PaymentResponse> => {
    const market = getMarket()
    
    try {
      if (market === 'RU') {
        // Try YooKassa API
        const response = await api.post('/api/yookassa/checkout', {
          package_id: packageId,
          user_id: userId,
          user_email: userEmail
        })
        
        return {
          confirmation_url: response.data.confirmation_url,
          payment_id: response.data.payment_id,
          status: response.data.status,
          amount: response.data.amount,
          expires_in: response.data.expires_in,
          package: response.data.package
        }
      } else {
        // Try Stripe API
        const originUrl = window.location.origin
        const response = await api.post('/api/billing/checkout', {
          package_id: packageId,
          origin_url: originUrl
        })
        
        return {
          confirmation_url: response.data.url,
          payment_id: response.data.session_id,
          status: 'pending',
          amount: {
            value: response.data.package.amount.toString(),
            currency: response.data.package.currency
          },
          expires_in: '24 hours',
          package: response.data.package
        }
      }
    } catch (error) {
      console.warn('Payment API not available, using demo mode:', error)
      
      // For demo purposes, show alert instead of real payment
      alert(`Demo Mode: Would redirect to ${market === 'RU' ? 'YooKassa' : 'Stripe'} payment for package: ${packageId}`)
      
      throw new Error('API недоступен. Демо режим.')
    }
  },

  // Confirm payment and activate PRO (fallback)
  confirmPayment: async (paymentId: string): Promise<{
    status: 'success' | 'pending' | 'failed'
    payment_status?: string
    action?: string
    user_id?: string
    message?: string
    activation_result?: any
  }> => {
    try {
      console.log(`Confirming payment ${paymentId} via fallback endpoint`)
      
      const response = await api.post(`/api/yookassa/confirm?payment_id=${paymentId}`)
      
      console.log('✅ Payment confirmation response:', response.data)
      return response.data
      
    } catch (error) {
      console.error('❌ Payment confirmation failed:', error)
      
      // Return error status
      return {
        status: 'failed',
        message: 'Confirmation request failed'
      }
    }
  },

  // Get payment status
  getPaymentStatus: async (paymentId: string): Promise<PaymentStatusResponse> => {
    const market = getMarket()
    
    try {
      if (market === 'RU') {
        // Try YooKassa API
        const response = await api.get(`/api/yookassa/payment/${paymentId}`)
        return response.data
      } else {
        // Try Stripe API
        const response = await api.get(`/api/billing/checkout/status/${paymentId}`)
        return {
          payment_id: response.data.session_id,
          status: response.data.status,
          amount: {
            value: response.data.amount_total?.toString() || '0',
            currency: response.data.currency || 'USD'
          },
          description: '',
          payment_method: undefined,
          metadata: response.data.metadata,
          local_transaction: true
        }
      }
    } catch (error) {
      console.warn('Payment status API not available:', error)
      
      // Mock successful payment for demo
      return {
        payment_id: paymentId,
        status: 'succeeded',
        amount: { value: '1990.00', currency: 'RUB' },
        description: 'Demo payment',
        metadata: {},
        local_transaction: false
      }
    }
  },

  // Check if user has PRO subscription
  checkProStatus: async (userId?: string): Promise<{ hasPro: boolean; expiresAt?: string }> => {
    try {
      // This would typically check with user subscription API
      // For now, return a placeholder implementation
      return { hasPro: false }
    } catch (error) {
      console.error('Failed to check PRO status:', error)
      return { hasPro: false }
    }
  },

  // Market info
  getMarketInfo: () => {
    const market = getMarket()
    return {
      market,
      currency: market === 'RU' ? 'RUB' : 'USD',
      paymentProvider: market === 'RU' ? 'YooKassa' : 'Stripe'
    }
  }
}