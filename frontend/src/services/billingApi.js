import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8002';
const API = `${BACKEND_URL}/api`;

// Subscription plans
const MOCK_RU_PLANS = [
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
];

// Determine market based on locale
const getMarket = () => {
  const locale = navigator.language || 'en';
  if (locale.startsWith('ru')) {
    return 'RU';
  }
  // Default to RU for Russian market
  return 'RU';
};

export const billingApi = {
  // Get available billing plans
  getPlans: async () => {
    const market = getMarket();
    
    try {
      if (market === 'RU') {
        console.log('🔵 Fetching plans from:', `${API}/yookassa/plans`);
        const response = await axios.get(`${API}/yookassa/plans`);
        console.log('🔵 Plans API response:', response.data);
        return response.data;
      }
    } catch (error) {
      console.warn('⚠️ API not available, using mock data:', error);
      console.warn('⚠️ Error details:', error.response?.data || error.message);
    }
    
    // Fallback to mock data
    if (market === 'RU') {
      console.log('🔵 Using fallback mock plans');
      return {
        plans: MOCK_RU_PLANS,
        currency: 'RUB',
        market: 'RU'
      };
    }
    
    // Default fallback
    return {
      plans: MOCK_RU_PLANS,
      currency: 'RUB',
      market: 'RU'
    };
  },

  // Create payment session
  createPayment: async (packageId, userId, userEmail) => {
    const market = getMarket();
    
    try {
      if (market === 'RU') {
        const response = await axios.post(`${API}/yookassa/checkout`, {
          package_id: packageId,
          user_id: userId,
          user_email: userEmail
        });
        
        return {
          confirmation_url: response.data.confirmation_url,
          payment_id: response.data.payment_id,
          status: response.data.status,
          amount: response.data.amount,
          expires_in: response.data.expires_in,
          package: response.data.package
        };
      }
    } catch (error) {
      console.warn('Payment API not available:', error);
      throw new Error('API недоступен. Демо режим.');
    }
  },

  // Confirm payment and activate PRO (fallback)
  confirmPayment: async (paymentId) => {
    try {
      console.log(`Confirming payment ${paymentId} via fallback endpoint`);
      
      const response = await axios.post(`${API}/yookassa/confirm?payment_id=${paymentId}`);
      
      console.log('✅ Payment confirmation response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Payment confirmation failed:', error);
      return {
        status: 'failed',
        message: 'Confirmation request failed'
      };
    }
  },

  // Get payment status
  getPaymentStatus: async (paymentId) => {
    const market = getMarket();
    
    try {
      if (market === 'RU') {
        const response = await axios.get(`${API}/yookassa/payment/${paymentId}`);
        return response.data;
      }
    } catch (error) {
      console.warn('Payment status API not available:', error);
      return {
        payment_id: paymentId,
        status: 'succeeded',
        amount: { value: '1990.00', currency: 'RUB' },
        description: 'Demo payment',
        metadata: {},
        local_transaction: false
      };
    }
  },

  // Market info
  getMarketInfo: () => {
    const market = getMarket();
    return {
      market,
      currency: market === 'RU' ? 'RUB' : 'USD',
      paymentProvider: market === 'RU' ? 'YooKassa' : 'Stripe'
    };
  }
};

