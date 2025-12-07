import React, { useState } from 'react';

const PricingPage = ({ currentUser, onUpgrade, onClose }) => {
  const [billingCycle, setBillingCycle] = useState('monthly'); // 'monthly' | 'yearly'

  const plans = [
    {
      id: 'free',
      name: 'START',
      price: 0,
      description: 'Идеально для знакомства с платформой',
      features: [
        '3 AI-генерации техкарт в месяц',
        'Базовая база знаний',
        'Хранение до 10 техкарт',
        'Экспорт в PDF (с водяным знаком)'
      ],
      tokens: 50,
      color: 'gray',
      buttonText: currentUser ? 'Ваш текущий план' : 'Попробовать бесплатно'
    },
    {
      id: 'pro',
      name: 'PRO CHEF',
      price: billingCycle === 'monthly' ? 2990 : 2490,
      description: 'Для шеф-поваров и су-шефов',
      features: [
        '1000 NeuroCoins ежемесячно (~100 техкарт)',
        'Безлимитное хранение',
        'Доступ к GPT-5 и o1-preview',
        'Экспорт без водяных знаков',
        'Приоритетная генерация'
      ],
      tokens: 1000,
      isPopular: true,
      color: 'purple',
      buttonText: 'Оформить подписку'
    },
    {
      id: 'business',
      name: 'BUSINESS',
      price: billingCycle === 'monthly' ? 5990 : 4990,
      description: 'Для владельцев и сетей',
      features: [
        '3000 NeuroCoins ежемесячно',
        'Все функции PRO',
        'Финансовый аудит меню',
        'API доступ (iiko/r_keeper)',
        'Приоритетная поддержка 24/7',
        'Мульти-аккаунт (до 3 сотрудников)'
      ],
      tokens: 3000,
      color: 'amber',
      buttonText: 'Выбрать Business'
    }
  ];

  const tokenPacks = [
    { coins: 100, price: 490, label: 'Starter Pack' },
    { coins: 500, price: 1990, label: 'Standard Pack', popular: true },
    { coins: 1000, price: 3490, label: 'Pro Pack', save: '20%' },
  ];

  const handleSubscribe = (planId) => {
    if (!currentUser) {
        alert('Пожалуйста, войдите или зарегистрируйтесь');
        return;
    }
    onUpgrade(planId, billingCycle);
  };

  const handleBuyTokens = (pack) => {
     if (!currentUser) {
        alert('Пожалуйста, войдите или зарегистрируйтесь');
        return;
    }
    // В будущем здесь будет вызов ЮКассы
    onUpgrade('token_pack', pack);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white py-20 px-4 sm:px-6 lg:px-8 relative">
      {/* Close Button (X) - Top Right */}
      {onClose && (
        <div className="fixed top-4 right-4 z-50">
          <button
            onClick={onClose}
            className="w-10 h-10 bg-gray-800/80 hover:bg-gray-700 rounded-full flex items-center justify-center text-gray-300 hover:text-white transition-all shadow-lg border border-gray-700/50"
            title="Закрыть"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}
      
      {/* Back Button */}
      {onClose && (
        <div className="max-w-7xl mx-auto mb-8">
          <button
            onClick={onClose}
            className="flex items-center space-x-2 text-purple-300 hover:text-purple-200 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span>Назад к главной</span>
          </button>
        </div>
      )}
      
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto mb-16">
        <h2 className="text-purple-400 font-semibold tracking-wide uppercase text-sm mb-2">Тарифные планы</h2>
        <h1 className="text-4xl sm:text-5xl font-bold mb-6 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
          Инвестируйте в эффективность кухни
        </h1>
        <p className="text-xl text-gray-400 mb-8">
          Экономьте до 40 часов работы в месяц с помощью AI. Окупается с первой оптимизированной техкарты.
        </p>

        {/* Billing Toggle */}
        <div className="flex justify-center items-center space-x-4 mb-8">
          <span className={`text-sm ${billingCycle === 'monthly' ? 'text-white font-bold' : 'text-gray-400'}`}>
            Ежемесячно
          </span>
          <button
            onClick={() => setBillingCycle(prev => prev === 'monthly' ? 'yearly' : 'monthly')}
            className="w-14 h-7 bg-purple-600 rounded-full p-1 transition-colors duration-200 ease-in-out relative"
          >
            <div 
              className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform duration-200 ${billingCycle === 'yearly' ? 'translate-x-7' : 'translate-x-0'}`} 
            />
          </button>
          <span className={`text-sm ${billingCycle === 'yearly' ? 'text-white font-bold' : 'text-gray-400'}`}>
            Ежегодно <span className="text-emerald-400 text-xs ml-1">(-20%)</span>
          </span>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">
        {plans.map((plan) => (
          <div 
            key={plan.id}
            className={`relative rounded-2xl p-8 border ${plan.isPopular ? 'border-purple-500 bg-gray-800/80' : 'border-gray-700 bg-gray-800/40'} backdrop-blur-xl flex flex-col transition-transform duration-300 hover:-translate-y-2`}
          >
            {plan.isPopular && (
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-1 rounded-full text-sm font-bold shadow-lg">
                ХИТ ПРОДАЖ
              </div>
            )}
            
            <div className="mb-6">
              <h3 className={`text-2xl font-bold text-${plan.color}-400 mb-2`}>{plan.name}</h3>
              <div className="flex items-baseline mb-2">
                <span className="text-4xl font-bold text-white">{plan.price === 0 ? 'Бесплатно' : `${plan.price}₽`}</span>
                {plan.price > 0 && <span className="text-gray-400 ml-2">/мес</span>}
              </div>
              <p className="text-gray-400 text-sm">{plan.description}</p>
            </div>

            <ul className="space-y-4 mb-8 flex-1">
              {plan.features.map((feature, idx) => (
                <li key={idx} className="flex items-start">
                  <svg className="w-5 h-5 text-emerald-400 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-gray-300 text-sm">{feature}</span>
                </li>
              ))}
            </ul>

            <button
              onClick={() => handleSubscribe(plan.id)}
              disabled={currentUser && currentUser.subscription_plan === plan.id}
              className={`w-full py-3 rounded-xl font-bold transition-all duration-200 ${
                plan.isPopular 
                  ? 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shadow-lg shadow-purple-500/25' 
                  : currentUser && currentUser.subscription_plan === plan.id
                    ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                    : 'bg-gray-700 hover:bg-gray-600 text-white'
              }`}
            >
              {plan.buttonText}
            </button>
          </div>
        ))}
      </div>

      {/* Token Packs Section */}
      <div className="max-w-5xl mx-auto bg-gray-800/30 rounded-3xl p-8 sm:p-12 border border-gray-700/50 backdrop-blur-md">
        <div className="flex flex-col md:flex-row items-center justify-between mb-8">
          <div>
            <h3 className="text-2xl font-bold text-white mb-2">⚡ Докупить NeuroCoins</h3>
            <p className="text-gray-400">Если закончился лимит подписки, докупите токены. Они не сгорают.</p>
          </div>
          <div className="mt-4 md:mt-0 px-4 py-2 bg-purple-900/30 border border-purple-500/30 rounded-lg">
            <span className="text-purple-200 text-sm font-mono">1 техкарта ≈ 10 монет</span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {tokenPacks.map((pack, idx) => (
            <div key={idx} className={`relative bg-gray-900/50 border border-gray-700 rounded-xl p-6 hover:border-purple-500/50 transition-colors ${pack.popular ? 'ring-2 ring-purple-500/30' : ''}`}>
              {pack.popular && <span className="absolute top-2 right-2 text-xs font-bold text-purple-400 bg-purple-400/10 px-2 py-0.5 rounded">POPULAR</span>}
              {pack.save && <span className="absolute top-2 right-2 text-xs font-bold text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded">SAVE {pack.save}</span>}
              
              <div className="text-3xl font-bold text-white mb-1">{pack.coins} <span className="text-sm text-gray-400 font-normal">NC</span></div>
              <div className="text-lg text-purple-300 font-medium mb-4">{pack.price}₽</div>
              <button 
                onClick={() => handleBuyTokens(pack)}
                className="w-full py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-semibold transition-colors"
              >
                Купить
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Trust & Footer Info (For YooKassa Compliance) */}
      <div className="mt-24 border-t border-gray-800 pt-12 text-center text-gray-500 text-sm">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12 max-w-4xl mx-auto">
            <div>
                <h4 className="font-bold text-gray-300 mb-4">Документы</h4>
                <ul className="space-y-2">
                    <li><a href="#" className="hover:text-purple-400">Публичная оферта</a></li>
                    <li><a href="#" className="hover:text-purple-400">Политика конфиденциальности</a></li>
                </ul>
            </div>
            <div>
                <h4 className="font-bold text-gray-300 mb-4">Оплата</h4>
                <ul className="space-y-2">
                    <li>Банковские карты</li>
                    <li>SberPay</li>
                    <li>СБП</li>
                </ul>
            </div>
             <div>
                <h4 className="font-bold text-gray-300 mb-4">Контакты</h4>
                <ul className="space-y-2">
                    <li>support@receptor.pro</li>
                    <li>Telegram Bot</li>
                </ul>
            </div>
            <div>
                 <h4 className="font-bold text-gray-300 mb-4">Реквизиты</h4>
                 <p className="text-xs">ИП Иванов И.И.<br/>ИНН 1234567890<br/>ОГРН 1234567890123</p>
            </div>
        </div>
        <p>© 2025 RECEPTOR PRO. All rights reserved.</p>
      </div>
    </div>
  );
};

export default PricingPage;
