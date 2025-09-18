import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import Toast from '../../components/ui/Toast'
import { billingApi, BillingPlan } from '../../services/billingApi'
import { useUserPlan } from '../../contexts/UserPlanContext'

const PricingPage: React.FC = () => {
  const [searchParams] = useSearchParams()
  const [isAnnual, setIsAnnual] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)
  const [plans, setPlans] = useState<BillingPlan[]>([])
  const [marketInfo, setMarketInfo] = useState<{ market: string; currency: string; paymentProvider: string }>()
  const { refreshPlan, plan } = useUserPlan()

  // Handle return from payment
  useEffect(() => {
    const status = searchParams.get('status')
    const paymentId = searchParams.get('payment_id') || searchParams.get('session_id')

    if (status === 'success' && paymentId) {
      setToast({
        message: '🎉 Оплата прошла успешно! PRO активируется...',
        type: 'success'
      })
      // Poll payment status to confirm PRO activation
      pollPaymentStatus(paymentId)
    } else if (status === 'cancel') {
      setToast({
        message: 'Оплата отменена. Попробуйте еще раз.',
        type: 'error'
      })
    }
  }, [searchParams])

  // Load plans and market info on component mount
  useEffect(() => {
    loadPlansAndMarketInfo()
  }, [])

  const loadPlansAndMarketInfo = async () => {
    try {
      const [plansData, marketData] = await Promise.all([
        billingApi.getPlans(),
        Promise.resolve(billingApi.getMarketInfo())
      ])
      
      setPlans(plansData.plans)
      setMarketInfo(marketData)
    } catch (error) {
      console.error('Failed to load plans:', error)
      setToast({
        message: 'Не удалось загрузить тарифы',
        type: 'error'
      })
    }
  }

  const pollPaymentStatus = async (paymentId: string, attempts: number = 0) => {
    const maxAttempts = 15 // 15 attempts with 10-15 sec intervals = ~3 minutes max
    
    if (attempts >= maxAttempts) {
      setToast({
        message: 'Проверка статуса платежа превысила время ожидания. Попробуйте обновить страницу.',
        type: 'error'
      })
      return
    }

    try {
      console.log(`Polling payment status attempt ${attempts + 1}/${maxAttempts} for payment ${paymentId}`)
      
      // First, refresh user plan from server (no cache)
      await refreshPlan()
      
      // Check if plan is already PRO (webhook worked)
      if (plan === 'pro') {
        setToast({
          message: '🎉 PRO подписка активирована! Добро пожаловать в PRO!',
          type: 'success'
        })
        console.log('✅ Plan refreshed to PRO - webhook activation successful')
        return
      }
      
      // Fallback: check payment status via confirm endpoint
      const confirmResponse = await billingApi.confirmPayment(paymentId)
      
      if (confirmResponse.status === 'success' && confirmResponse.action === 'pro_activated') {
        setToast({
          message: '✅ PRO подписка активирована через подтверждение! Добро пожаловать в PRO!',
          type: 'success'
        })
        console.log('✅ PRO activated via confirm endpoint')
        
        // Refresh plan one more time to reflect the change
        await refreshPlan()
        return
      }
      
      // Continue polling if payment is still processing
      if (confirmResponse.status === 'pending') {
        console.log(`Payment still pending, will retry in 10 seconds (attempt ${attempts + 1})`)
        setTimeout(() => pollPaymentStatus(paymentId, attempts + 1), 10000) // 10 sec intervals
      } else if (confirmResponse.status === 'failed') {
        setToast({
          message: 'Платеж не был завершен. Обратитесь в поддержку если деньги были списаны.',
          type: 'error'
        })
      }

    } catch (error) {
      console.error('Error during payment status polling:', error)
      
      // Continue polling for temporary errors, but with longer intervals
      if (attempts < maxAttempts - 2) { // Give up earlier on errors
        console.log(`Error occurred, retrying in 15 seconds (attempt ${attempts + 1})`)
        setTimeout(() => pollPaymentStatus(paymentId, attempts + 1), 15000) // 15 sec on errors
      } else {
        setToast({
          message: 'Ошибка проверки статуса платежа. Обновите страницу или обратитесь в поддержку.',
          type: 'error'
        })
      }
    }
  }

  const handleUpgrade = async (packageId: string) => {
    setIsLoading(true)
    
    try {
      // Create payment with current billing API
      const paymentResponse = await billingApi.createPayment(
        packageId,
        'demo_user_id', // In production, get from user context
        'user@example.com' // In production, get from user context
      )
      
      // Redirect to payment page (YooKassa Hosted Page or Stripe Checkout)
      if (paymentResponse.confirmation_url) {
        window.location.href = paymentResponse.confirmation_url
      } else {
        throw new Error('No payment URL received')
      }
      
    } catch (error: any) {
      setToast({
        message: error.message || 'Не удалось создать сессию оплаты',
        type: 'error'
      })
    } finally {
      setIsLoading(false)
    }
  }

  const freePlan = {
    name: 'Free',
    price: 0,
    period: 'навсегда',
    features: [
      'Базовая генерация техкарт',
      'Экспорт в PDF',
      'До 10 техкарт в библиотеке',
      'Стандартная поддержка'
    ],
    cta: 'Текущий план',
    disabled: true
  }

  const getProPlan = () => {
    const monthlyPlan = plans.find(p => p.billing_period === 'monthly')
    const annualPlan = plans.find(p => p.billing_period === 'annual')
    
    if (isAnnual && annualPlan) {
      const monthlyAmount = monthlyPlan?.amount ? parseFloat(monthlyPlan.amount) : 0
      const annualAmount = parseFloat(annualPlan.amount)
      const monthlyPrice = Math.round(annualAmount / 12)
      
      return {
        id: annualPlan.id,
        name: 'PRO',
        price: monthlyPrice,
        originalPrice: annualAmount,
        period: marketInfo?.currency === 'RUB' ? 'мес' : 'mo',
        billedPeriod: marketInfo?.currency === 'RUB' ? 'год' : 'year',
        savings: monthlyAmount ? `Экономия ${Math.round((monthlyAmount * 12) - annualAmount)}${marketInfo?.currency === 'RUB' ? '₽' : '$'}` : '',
        features: annualPlan.features,
        cta: 'Upgrade to PRO',
        disabled: false
      }
    } else if (monthlyPlan) {
      return {
        id: monthlyPlan.id,
        name: 'PRO',
        price: parseFloat(monthlyPlan.amount),
        period: marketInfo?.currency === 'RUB' ? 'мес' : 'mo',
        billedPeriod: marketInfo?.currency === 'RUB' ? 'месяц' : 'month',
        features: monthlyPlan.features,
        cta: 'Upgrade to PRO',
        disabled: false
      }
    }
    
    return null
  }

  const proPlan = getProPlan()

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Выберите свой план
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Начните бесплатно. Переходите на PRO для полного доступа к функциям.
          </p>
          
          {/* Billing Toggle */}
          <div className="flex items-center justify-center space-x-4 mb-8">
            <span className={`text-sm ${!isAnnual ? 'text-gray-900 font-medium' : 'text-gray-500'}`}>
              Ежемесячно
            </span>
            <button
              onClick={() => setIsAnnual(!isAnnual)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                isAnnual ? 'bg-primary-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  isAnnual ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`text-sm ${isAnnual ? 'text-gray-900 font-medium' : 'text-gray-500'}`}>
              Ежегодно
              <span className="ml-1 text-xs text-green-600 font-medium">-17%</span>
            </span>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {/* Free Plan */}
          <div className="bg-white rounded-lg shadow-lg p-8 border-2 border-gray-200">
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">{freePlan.name}</h3>
              <div className="mb-4">
                <span className="text-4xl font-bold text-gray-900">${freePlan.price}</span>
                <span className="text-gray-600 ml-2">{freePlan.period}</span>
              </div>
            </div>
            
            <ul className="space-y-3 mb-8">
              {freePlan.features.map((feature, index) => (
                <li key={index} className="flex items-center">
                  <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center mr-3">
                    <div className="w-2 h-2 bg-green-600 rounded-full" />
                  </div>
                  <span className="text-gray-700">{feature}</span>
                </li>
              ))}
            </ul>
            
            <button
              disabled={freePlan.disabled}
              className="w-full py-3 px-4 bg-gray-100 text-gray-500 font-medium rounded-lg cursor-not-allowed"
            >
              {freePlan.cta}
            </button>
          </div>

          {/* PRO Plan */}
          {proPlan && (
            <div className="bg-white rounded-lg shadow-lg p-8 border-2 border-primary-500 relative">
              {/* Popular Badge */}
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                <span className="bg-primary-500 text-white px-4 py-1 text-sm font-medium rounded-full">
                  Популярный
                </span>
              </div>
              
              <div className="text-center mb-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{proPlan.name}</h3>
                <div className="mb-4">
                  <span className="text-4xl font-bold text-gray-900">
                    {marketInfo?.currency === 'RUB' ? '₽' : '$'}{proPlan.price}
                  </span>
                  <span className="text-gray-600 ml-2">/{proPlan.period}</span>
                  {proPlan.billedPeriod && (
                    <div className="text-sm text-gray-500 mt-1">
                      выставляется за {proPlan.billedPeriod}
                    </div>
                  )}
                  {proPlan.savings && (
                    <div className="text-sm text-green-600 font-medium mt-1">
                      {proPlan.savings}
                    </div>
                  )}
                </div>
              </div>
              
              <ul className="space-y-3 mb-8">
                {proPlan.features.map((feature, index) => (
                  <li key={index} className="flex items-center">
                    <div className="w-5 h-5 rounded-full bg-primary-100 flex items-center justify-center mr-3">
                      <div className="w-2 h-2 bg-primary-600 rounded-full" />
                    </div>
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>
              
              <button
                onClick={() => handleUpgrade(proPlan.id)}
                disabled={isLoading}
                className="w-full py-3 px-4 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors duration-200"
              >
                {isLoading ? 'Перенаправление...' : proPlan.cta}
              </button>
            </div>
          )}
        </div>

        {/* FAQ Section */}
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Часто задаваемые вопросы</h2>
          <div className="grid md:grid-cols-2 gap-6 text-left mb-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="font-semibold text-gray-900 mb-3">Можно ли отменить подписку?</h3>
              <p className="text-gray-600">Да, вы можете отменить подписку в любое время. Доступ к PRO функциям сохранится до конца оплаченного периода.</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="font-semibold text-gray-900 mb-3">Есть ли пробный период?</h3>
              <p className="text-gray-600">Бесплатный план позволяет протестировать основные функции. PRO подписка активируется сразу после оплаты.</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="font-semibold text-gray-900 mb-3">Какие способы оплаты доступны?</h3>
              <p className="text-gray-600">
                Банковские карты (МИР, Visa, Mastercard), СБП, Apple Pay, Google Pay, 
                ЮMoney, Сбербанк Онлайн, Альфа-Клик
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="font-semibold text-gray-900 mb-3">Безопасность платежей</h3>
              <p className="text-gray-600">Все платежи обрабатываются через защищенную систему ЮKassa с соблюдением стандартов PCI DSS.</p>
            </div>
          </div>
          
          {/* Payment Methods */}
          <div className="bg-gray-50 p-6 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Способы оплаты</h3>
            <div className="flex flex-wrap justify-center items-center space-x-4 space-y-2">
              <span className="bg-white px-3 py-2 rounded text-sm font-medium text-gray-700">🏦 МИР</span>
              <span className="bg-white px-3 py-2 rounded text-sm font-medium text-gray-700">💳 Visa</span>
              <span className="bg-white px-3 py-2 rounded text-sm font-medium text-gray-700">💳 Mastercard</span>
              <span className="bg-white px-3 py-2 rounded text-sm font-medium text-gray-700">⚡ СБП</span>
              <span className="bg-white px-3 py-2 rounded text-sm font-medium text-gray-700">📱 Apple Pay</span>
              <span className="bg-white px-3 py-2 rounded text-sm font-medium text-gray-700">📱 Google Pay</span>
              <span className="bg-white px-3 py-2 rounded text-sm font-medium text-gray-700">💰 ЮMoney</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Toast notifications */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  )
}

export default PricingPage