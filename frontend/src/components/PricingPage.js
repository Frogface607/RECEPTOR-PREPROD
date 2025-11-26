import React, { useState, useEffect } from 'react';
import { billingApi } from '../services/billingApi';

const PricingPage = ({ currentUser, onClose, onSubscriptionUpdated }) => {
  const [isAnnual, setIsAnnual] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [plans, setPlans] = useState([]);
  const [marketInfo, setMarketInfo] = useState(null);

  // Handle return from payment
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const status = params.get('status');
    const paymentId = params.get('payment_id') || params.get('session_id');

    if (status === 'success' && paymentId) {
      setToast({
        message: '🎉 Оплата прошла успешно! PRO активируется...',
        type: 'success'
      });
      pollPaymentStatus(paymentId);
    } else if (status === 'cancel') {
      setToast({
        message: 'Оплата отменена. Попробуйте еще раз.',
        type: 'error'
      });
    }
  }, []);

  // Load plans and market info
  useEffect(() => {
    loadPlansAndMarketInfo();
  }, []);

  const loadPlansAndMarketInfo = async () => {
    try {
      console.log('🔵 Loading plans and market info...');
      const [plansData, marketData] = await Promise.all([
        billingApi.getPlans(),
        Promise.resolve(billingApi.getMarketInfo())
      ]);
      
      console.log('🔵 Plans data:', plansData);
      console.log('🔵 Market data:', marketData);
      
      setPlans(plansData?.plans || []);
      setMarketInfo(marketData);
      
      if (!plansData?.plans || plansData.plans.length === 0) {
        console.warn('⚠️ No plans loaded, using fallback');
        // Fallback to mock plans if API fails
        setPlans([
          {
            id: 'pro_monthly_ru',
            name: 'PRO Ежемесячно',
            amount: '1990.00',
            currency: 'RUB',
            billing_period: 'monthly',
            features: [
              'Export Master (PDF, Excel, iiko)',
              'Генератор меню',
              'Интеграция с iiko',
              'AI-Лаборатория',
              'Приоритетная поддержка',
              'Расширенная аналитика'
            ]
          },
          {
            id: 'pro_annual_ru',
            name: 'PRO Ежегодно',
            amount: '19900.00',
            currency: 'RUB',
            billing_period: 'annual',
            features: [
              'Export Master (PDF, Excel, iiko)',
              'Генератор меню',
              'Интеграция с iiko',
              'AI-Лаборатория',
              'Приоритетная поддержка',
              'Расширенная аналитика'
            ]
          }
        ]);
        setMarketInfo({ market: 'RU', currency: 'RUB', paymentProvider: 'YooKassa' });
      }
    } catch (error) {
      console.error('❌ Failed to load plans:', error);
      setToast({
        message: 'Не удалось загрузить тарифы. Используются базовые тарифы.',
        type: 'error'
      });
      // Fallback to mock plans
      setPlans([
        {
          id: 'pro_monthly_ru',
          name: 'PRO Ежемесячно',
          amount: '1990.00',
          currency: 'RUB',
          billing_period: 'monthly',
          features: [
            'Export Master (PDF, Excel, iiko)',
            'Генератор меню',
            'Интеграция с iiko',
            'AI-Лаборатория',
            'Приоритетная поддержка',
            'Расширенная аналитика'
          ]
        },
        {
          id: 'pro_annual_ru',
          name: 'PRO Ежегодно',
          amount: '19900.00',
          currency: 'RUB',
          billing_period: 'annual',
          features: [
            'Export Master (PDF, Excel, iiko)',
            'Генератор меню',
            'Интеграция с iiko',
            'AI-Лаборатория',
            'Приоритетная поддержка',
            'Расширенная аналитика'
          ]
        }
      ]);
      setMarketInfo({ market: 'RU', currency: 'RUB', paymentProvider: 'YooKassa' });
    }
  };

  const pollPaymentStatus = async (paymentId, attempts = 0) => {
    const maxAttempts = 15;
    
    if (attempts >= maxAttempts) {
      setToast({
        message: 'Проверка статуса платежа превысила время ожидания. Попробуйте обновить страницу.',
        type: 'error'
      });
      return;
    }

    try {
      const confirmResponse = await billingApi.confirmPayment(paymentId);
      
      if (confirmResponse.status === 'success' && confirmResponse.action === 'pro_activated') {
        setToast({
          message: '✅ PRO подписка активирована! Добро пожаловать в PRO!',
          type: 'success'
        });
        
        // Update user subscription
        if (onSubscriptionUpdated) {
          onSubscriptionUpdated();
        }
        
        // Reload user data
        if (currentUser) {
          const savedUser = JSON.parse(localStorage.getItem('receptor_user') || '{}');
          savedUser.subscription_plan = 'pro';
          localStorage.setItem('receptor_user', JSON.stringify(savedUser));
        }
        
        return;
      }
      
      if (confirmResponse.status === 'pending') {
        setTimeout(() => pollPaymentStatus(paymentId, attempts + 1), 10000);
      } else if (confirmResponse.status === 'failed') {
        setToast({
          message: 'Платеж не был завершен. Обратитесь в поддержку если деньги были списаны.',
          type: 'error'
        });
      }
    } catch (error) {
      console.error('Error during payment status polling:', error);
      if (attempts < maxAttempts - 2) {
        setTimeout(() => pollPaymentStatus(paymentId, attempts + 1), 15000);
      } else {
        setToast({
          message: 'Ошибка проверки статуса платежа. Обновите страницу или обратитесь в поддержку.',
          type: 'error'
        });
      }
    }
  };

  const handleUpgrade = async (packageId) => {
    if (!currentUser) {
      setToast({
        message: 'Необходимо войти в систему для оплаты',
        type: 'error'
      });
      return;
    }

    setIsLoading(true);
    
    try {
      const paymentResponse = await billingApi.createPayment(
        packageId,
        currentUser.id,
        currentUser.email
      );
      
      if (paymentResponse.confirmation_url) {
        window.location.href = paymentResponse.confirmation_url;
      } else {
        throw new Error('No payment URL received');
      }
    } catch (error) {
      setToast({
        message: error.message || 'Не удалось создать сессию оплаты',
        type: 'error'
      });
      setIsLoading(false);
    }
  };

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
  };

  const getProPlan = () => {
    const monthlyPlan = plans.find(p => p.billing_period === 'monthly');
    const annualPlan = plans.find(p => p.billing_period === 'annual');
    
    if (isAnnual && annualPlan) {
      const monthlyAmount = monthlyPlan?.amount ? parseFloat(monthlyPlan.amount) : 0;
      const annualAmount = parseFloat(annualPlan.amount);
      const monthlyPrice = Math.round(annualAmount / 12);
      
      return {
        id: annualPlan.id,
        name: 'PRO',
        price: monthlyPrice,
        originalPrice: annualAmount,
        period: marketInfo?.currency === 'RUB' ? 'мес' : 'mo',
        billedPeriod: marketInfo?.currency === 'RUB' ? 'год' : 'year',
        savings: monthlyAmount ? `Экономия ${Math.round((monthlyAmount * 12) - annualAmount)}${marketInfo?.currency === 'RUB' ? '₽' : '$'}` : '',
        features: annualPlan.features || [],
        cta: 'Upgrade to PRO',
        disabled: false
      };
    } else if (monthlyPlan) {
      return {
        id: monthlyPlan.id,
        name: 'PRO',
        price: parseFloat(monthlyPlan.amount),
        period: marketInfo?.currency === 'RUB' ? 'мес' : 'mo',
        billedPeriod: marketInfo?.currency === 'RUB' ? 'месяц' : 'month',
        features: monthlyPlan.features || [],
        cta: 'Upgrade to PRO',
        disabled: false
      };
    }
    
    return null;
  };

  const proPlan = getProPlan();
  const userPlan = currentUser?.subscription_plan || 'free';

  // Show loading state if plans are not loaded yet
  if (plans.length === 0 && !marketInfo) {
    return (
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-gray-900 border border-gray-700 rounded-2xl p-8 w-full max-w-md">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-white">Загрузка тарифов...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-8 w-full max-w-4xl my-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-3xl font-bold text-white mb-2">Выберите свой план</h2>
            <p className="text-gray-400">Начните бесплатно. Переходите на PRO для полного доступа.</p>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* Billing Toggle */}
        <div className="flex items-center justify-center space-x-4 mb-8">
          <span className={`text-sm ${!isAnnual ? 'text-white font-medium' : 'text-gray-400'}`}>
            Ежемесячно
          </span>
          <button
            onClick={() => setIsAnnual(!isAnnual)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              isAnnual ? 'bg-blue-600' : 'bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                isAnnual ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
          <span className={`text-sm ${isAnnual ? 'text-white font-medium' : 'text-gray-400'}`}>
            Ежегодно
            <span className="ml-1 text-xs text-green-400 font-medium">-17%</span>
          </span>
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          {/* Free Plan */}
          <div className={`bg-gray-800 rounded-lg p-6 border-2 ${
            userPlan === 'free' ? 'border-blue-500' : 'border-gray-700'
          }`}>
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-white mb-2">{freePlan.name}</h3>
              <div className="mb-4">
                <span className="text-4xl font-bold text-white">{freePlan.price}</span>
                <span className="text-gray-400 ml-2">{freePlan.period}</span>
              </div>
            </div>
            
            <ul className="space-y-3 mb-8">
              {freePlan.features.map((feature, index) => (
                <li key={index} className="flex items-center">
                  <div className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center mr-3 flex-shrink-0">
                    <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="text-gray-300">{feature}</span>
                </li>
              ))}
            </ul>
            
            <button
              disabled={freePlan.disabled}
              className="w-full py-3 px-4 bg-gray-700 text-gray-400 font-medium rounded-lg cursor-not-allowed"
            >
              {userPlan === 'free' ? 'Текущий план' : freePlan.cta}
            </button>
          </div>

          {/* PRO Plan */}
          {proPlan && (
            <div className={`bg-gray-800 rounded-lg p-6 border-2 relative ${
              userPlan === 'pro' ? 'border-blue-500' : 'border-blue-600'
            }`}>
              {userPlan !== 'pro' && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-blue-600 text-white px-4 py-1 text-sm font-medium rounded-full">
                    Популярный
                  </span>
                </div>
              )}
              
              <div className="text-center mb-6">
                <h3 className="text-2xl font-bold text-white mb-2">{proPlan.name}</h3>
                <div className="mb-4">
                  <span className="text-4xl font-bold text-white">
                    {marketInfo?.currency === 'RUB' ? '₽' : '$'}{proPlan.price}
                  </span>
                  <span className="text-gray-400 ml-2">/{proPlan.period}</span>
                  {proPlan.billedPeriod && (
                    <div className="text-sm text-gray-400 mt-1">
                      выставляется за {proPlan.billedPeriod}
                    </div>
                  )}
                  {proPlan.savings && (
                    <div className="text-sm text-green-400 font-medium mt-1">
                      {proPlan.savings}
                    </div>
                  )}
                </div>
              </div>
              
              <ul className="space-y-3 mb-8">
                {proPlan.features.map((feature, index) => (
                  <li key={index} className="flex items-center">
                    <div className="w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center mr-3 flex-shrink-0">
                      <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <span className="text-gray-300">{feature}</span>
                  </li>
                ))}
              </ul>
              
              <button
                onClick={() => handleUpgrade(proPlan.id)}
                disabled={isLoading || userPlan === 'pro'}
                className={`w-full py-3 px-4 font-medium rounded-lg transition-colors ${
                  userPlan === 'pro'
                    ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white'
                }`}
              >
                {isLoading ? 'Загрузка...' : userPlan === 'pro' ? 'Текущий план' : proPlan.cta}
              </button>
            </div>
          )}
        </div>

        {/* Toast */}
        {toast && (
          <div className={`fixed bottom-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'
          } text-white`}>
            {toast.message}
            <button
              onClick={() => setToast(null)}
              className="ml-4 text-white hover:text-gray-200"
            >
              ✕
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PricingPage;

