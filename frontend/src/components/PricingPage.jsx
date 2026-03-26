import React, { useState, useEffect } from 'react';
import { Crown, Check, X, Zap, Gift, ArrowLeft } from 'lucide-react';
import axios from 'axios';
import { API_URL, USER_ID } from '../config';
import { toast } from './Toast';

const PLAN_FEATURES = [
  { name: 'AI-чат с контекстом заведения', free: '10 сообщений/день', pro: 'Безлимитно', enterprise: 'Безлимитно' },
  { name: 'Интеграция iiko (Cloud + RMS)', free: true, pro: true, enterprise: true },
  { name: 'Поиск по номенклатуре', free: true, pro: true, enterprise: true },
  { name: 'Профиль заведения', free: true, pro: true, enterprise: true },
  { name: 'Deep Research (конкурентный анализ)', free: false, pro: '5/месяц', enterprise: 'Безлимитно' },
  { name: 'BI Dashboard', free: true, pro: true, enterprise: true },
  { name: 'Экспорт данных (CSV)', free: false, pro: true, enterprise: true },
  { name: 'Приоритетная поддержка', free: false, pro: false, enterprise: true },
  { name: 'API доступ', free: false, pro: false, enterprise: true },
];

function PricingPage({ onBack, onSelectPlan }) {
  const [currentPlan, setCurrentPlan] = useState('free');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCurrentPlan();
  }, []);

  const loadCurrentPlan = async () => {
    try {
      const response = await axios.get(`${API_URL}/billing/plan/${USER_ID}`);
      setCurrentPlan(response.data.plan || 'free');
    } catch (error) {
      // fail silently
    } finally {
      setLoading(false);
    }
  };

  const renderFeatureValue = (value) => {
    if (value === true) return <Check size={18} className="text-emerald-400" />;
    if (value === false) return <X size={18} className="text-gray-600" />;
    return <span className="text-sm text-white">{value}</span>;
  };

  const plans = [
    {
      key: 'free',
      name: 'Starter',
      price: '0',
      period: '',
      description: 'Попробуйте RECEPTOR бесплатно',
      color: 'gray',
      gradient: 'from-gray-700 to-gray-800',
      badge: null,
    },
    {
      key: 'pro',
      name: 'Professional',
      price: '6 990',
      period: '₽/мес',
      description: 'Для активных рестораторов',
      color: 'emerald',
      gradient: 'from-emerald-600 to-emerald-700',
      badge: 'Популярный',
    },
    {
      key: 'enterprise',
      name: 'Enterprise',
      price: '14 990',
      period: '₽/мес',
      description: 'Для сетей и холдингов',
      color: 'purple',
      gradient: 'from-purple-600 to-purple-700',
      badge: null,
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={onBack}
            className="p-2 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-white">Тарифы</h1>
            <p className="text-gray-400 mt-1">Выберите план, который подходит вашему заведению</p>
          </div>
        </div>

        {/* Referral banner */}
        <div className="mb-8 bg-gradient-to-r from-emerald-900/30 to-emerald-800/30 border border-emerald-600/30 rounded-xl p-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Gift className="w-8 h-8 text-emerald-400" />
            <div>
              <p className="text-white font-semibold">Пригласите друга — получите 14 дней Pro бесплатно</p>
              <p className="text-sm text-gray-400">Бонус для вас и приглашённого</p>
            </div>
          </div>
          <button
            onClick={() => onSelectPlan('referral')}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Пригласить
          </button>
        </div>

        {/* Plan cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          {plans.map((plan) => (
            <div
              key={plan.key}
              className={`relative bg-gray-900 border rounded-2xl p-6 flex flex-col ${
                plan.key === 'pro'
                  ? 'border-emerald-500/50 shadow-lg shadow-emerald-500/10 scale-105'
                  : 'border-gray-700'
              }`}
            >
              {plan.badge && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-emerald-600 text-white text-xs font-bold rounded-full">
                  {plan.badge}
                </div>
              )}

              <h3 className="text-xl font-bold text-white mb-1">{plan.name}</h3>
              <p className="text-sm text-gray-400 mb-4">{plan.description}</p>

              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-bold text-white">{plan.price}</span>
                <span className="text-gray-400">{plan.period}</span>
              </div>

              <button
                onClick={() => {
                  if (plan.key === currentPlan) return;
                  if (plan.key === 'free') return;
                  toast('Оплата скоро будет доступна. Пока используйте реферальную программу!', 'info');
                }}
                disabled={plan.key === currentPlan}
                className={`w-full py-3 rounded-xl font-semibold text-sm transition-all mb-6 ${
                  plan.key === currentPlan
                    ? 'bg-gray-800 text-gray-500 cursor-default'
                    : plan.key === 'pro'
                      ? 'bg-gradient-to-r from-emerald-600 to-emerald-700 text-white hover:from-emerald-500 hover:to-emerald-600 shadow-lg shadow-emerald-500/20'
                      : 'bg-gray-800 text-white hover:bg-gray-700 border border-gray-700'
                }`}
              >
                {plan.key === currentPlan ? 'Текущий план' : plan.key === 'free' ? 'Бесплатно' : 'Выбрать'}
              </button>

              {/* Feature list for this plan */}
              <div className="space-y-3 flex-1">
                {PLAN_FEATURES.map((feature, i) => {
                  const value = feature[plan.key];
                  return (
                    <div key={i} className="flex items-center justify-between gap-2">
                      <span className={`text-sm ${value ? 'text-gray-300' : 'text-gray-600'}`}>
                        {feature.name}
                      </span>
                      {renderFeatureValue(value)}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* FAQ */}
        <div className="text-center text-sm text-gray-500 pb-8">
          <p>Все тарифы включают интеграцию с iiko. Оплата ежемесячная, отмена в любой момент.</p>
          <p className="mt-1">Вопросы? Напишите нам в чат — RECEPTOR поможет выбрать тариф.</p>
        </div>
      </div>
    </div>
  );
}

export default PricingPage;
