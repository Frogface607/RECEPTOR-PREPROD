import React, { useState, useEffect } from 'react';
import { Save, ArrowLeft, Loader2, CheckCircle, FileText } from 'lucide-react';
import axios from 'axios';
import ResearchResults from './ResearchResults';
import { API_URL } from '../config';

// Справочники
const VENUE_TYPES = {
  restaurant: "Ресторан",
  cafe: "Кафе",
  bar: "Бар",
  fastfood: "Фастфуд",
  canteen: "Столовая",
  catering: "Кейтеринг",
  coffeeshop: "Кофейня",
  bakery: "Пекарня",
  pizzeria: "Пиццерия",
};

const CUISINE_TYPES = {
  russian: "Русская",
  european: "Европейская",
  italian: "Итальянская",
  asian: "Азиатская",
  japanese: "Японская",
  chinese: "Китайская",
  georgian: "Грузинская",
  uzbek: "Узбекская",
  american: "Американская",
  french: "Французская",
  mediterranean: "Средиземноморская",
  fusion: "Фьюжн",
  pan_asian: "Паназиатская",
};

const SKILL_LEVELS = {
  novice: "Начинающий",
  medium: "Средний",
  advanced: "Продвинутый",
  expert: "Эксперт",
};

const REGIONS = {
  moskva: "Москва",
  spb: "Санкт-Петербург",
  krasnodar: "Краснодар",
  sochi: "Сочи",
  kazan: "Казань",
  novosibirsk: "Новосибирск",
  ekaterinburg: "Екатеринбург",
  other: "Другой регион",
};

function VenueProfile({ userId, onBack }) {
  const [profile, setProfile] = useState({
    venue_name: '',
    venue_type: '',
    venue_concept: '',
    cuisine_focus: [],
    average_check: '',
    city: '',
    region: 'moskva',
    seating_capacity: '',
    staff_count: '',
    staff_skill_level: 'medium',
    special_requirements: [],
    venue_description: '',
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [researching, setResearching] = useState(false);
  const [researchDone, setResearchDone] = useState(false);
  const [researchError, setResearchError] = useState('');
  const [researchData, setResearchData] = useState(null);
  const [showResearchResults, setShowResearchResults] = useState(false);

  useEffect(() => {
    loadProfile();
    checkResearchStatus();
  }, [userId]);

  const loadProfile = async () => {
    try {
      const response = await axios.get(`${API_URL}/venue/${userId}`);
      setProfile(prev => ({
        ...prev,
        ...response.data,
        average_check: response.data.average_check || '',
        seating_capacity: response.data.seating_capacity || '',
        staff_count: response.data.staff_count || '',
      }));
    } catch (error) {
      console.error('Error loading profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkResearchStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/venue/research/status/${userId}`);
      if (response.data.status === 'completed') {
        setResearchData(response.data);
        setResearchDone(true);
      }
    } catch (error) {
      console.log('No research data yet');
    }
  };

  const startDeepResearch = async () => {
    if (!profile.venue_name || !profile.city) {
      setResearchError('Укажите название заведения и город');
      return;
    }

    setResearching(true);
    setResearchDone(false);
    setResearchError('');

    try {
      await axios.post(`${API_URL}/venue/research/start`, {
        venue_name: profile.venue_name,
        city: profile.city,
        user_id: userId
      });

      // Polling: проверяем каждые 10 секунд, максимум 3 минуты
      const maxAttempts = 18;
      let attempt = 0;

      const pollInterval = setInterval(async () => {
        attempt++;
        try {
          const checkResponse = await axios.get(`${API_URL}/venue/research/status/${userId}`);
          if (checkResponse.data.status === 'completed') {
            clearInterval(pollInterval);
            setResearchDone(true);
            setResearchData(checkResponse.data);
            setResearching(false);
          } else if (checkResponse.data.status === 'failed') {
            clearInterval(pollInterval);
            setResearchError('Исследование завершилось с ошибкой. Попробуйте ещё раз.');
            setResearching(false);
          } else if (attempt >= maxAttempts) {
            clearInterval(pollInterval);
            setResearchError('Исследование занимает слишком много времени. Обновите страницу позже.');
            setResearching(false);
          }
        } catch (err) {
          if (attempt >= maxAttempts) {
            clearInterval(pollInterval);
            setResearchError('Не удалось проверить статус исследования');
            setResearching(false);
          }
        }
      }, 10000);

    } catch (error) {
      console.error('Deep research error:', error);
      setResearchError('Ошибка при запуске исследования');
      setResearching(false);
    }
  };

  const saveProfile = async () => {
    setSaving(true);
    setSaved(false);
    try {
      const dataToSave = {
        ...profile,
        average_check: profile.average_check ? parseInt(profile.average_check) : null,
        seating_capacity: profile.seating_capacity ? parseInt(profile.seating_capacity) : null,
        staff_count: profile.staff_count ? parseInt(profile.staff_count) : null,
      };
      
      await axios.post(`${API_URL}/venue/${userId}`, dataToSave);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (error) {
      console.error('Error saving profile:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field, value) => {
    setProfile(prev => ({ ...prev, [field]: value }));
  };

  const toggleCuisine = (cuisine) => {
    setProfile(prev => ({
      ...prev,
      cuisine_focus: prev.cuisine_focus.includes(cuisine)
        ? prev.cuisine_focus.filter(c => c !== cuisine)
        : [...prev.cuisine_focus, cuisine]
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-emerald-500" size={32} />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <button 
              onClick={onBack}
              className="p-2 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-white">Профиль заведения</h1>
              <p className="text-gray-400 text-sm">Эта информация поможет ассистенту давать более релевантные ответы</p>
            </div>
          </div>
          
          <div className="flex gap-3">
            {/* Deep Research Button */}
            <button
              onClick={startDeepResearch}
              disabled={researching || !profile.venue_name || !profile.city}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-500 disabled:opacity-50 transition-colors"
              title="AI исследует ваше заведение в интернете: отзывы, конкурентов, соцсети"
            >
              {researching ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  Исследую...
                </>
              ) : researchDone ? (
                <>
                  <CheckCircle size={18} />
                  Готово!
                </>
              ) : (
                <>
                  🔬
                  Исследовать
                </>
              )}
            </button>

            {/* View Results Button */}
            {researchDone && researchData && (
              <button
                onClick={() => setShowResearchResults(true)}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 transition-colors"
                title="Посмотреть результаты исследования"
              >
                <FileText size={18} />
                Результаты
              </button>
            )}

            {/* Save Button */}
            <button
              onClick={saveProfile}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-500 disabled:opacity-50 transition-colors"
            >
              {saving ? (
                <Loader2 className="animate-spin" size={18} />
              ) : saved ? (
                <CheckCircle size={18} />
              ) : (
                <Save size={18} />
              )}
              {saved ? 'Сохранено!' : 'Сохранить'}
            </button>
          </div>

          {/* Research Status/Error */}
          {researchError && (
            <div className="text-red-400 text-sm">
              {researchError}
            </div>
          )}
          {researching && (
            <div className="text-purple-400 text-sm">
              🔬 Исследую заведение в интернете... Это займёт 1-2 минуты. 
              AI ищет отзывы, конкурентов и соцсети.
            </div>
          )}
          {researchDone && (
            <div className="text-emerald-400 text-sm">
              ✅ Исследование завершено! Теперь RECEPTOR знает всё о вашем заведении.
            </div>
          )}
        </div>

        {/* Form */}
        <div className="space-y-6">
          {/* Основная информация */}
          <section className="bg-gray-800/50 border border-gray-700 rounded-xl p-6 space-y-4">
            <h2 className="text-lg font-semibold text-white mb-4">Основная информация</h2>
            
            <div>
              <label className="block text-sm text-gray-400 mb-2">Название заведения</label>
              <input
                type="text"
                value={profile.venue_name || ''}
                onChange={(e) => handleChange('venue_name', e.target.value)}
                placeholder="Например: Ресторан 'Высота'"
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Тип заведения</label>
                <select
                  value={profile.venue_type || ''}
                  onChange={(e) => handleChange('venue_type', e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="">Выберите тип</option>
                  {Object.entries(VENUE_TYPES).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Средний чек (₽)</label>
                <input
                  type="number"
                  value={profile.average_check || ''}
                  onChange={(e) => handleChange('average_check', e.target.value)}
                  placeholder="1500"
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Концепция</label>
              <input
                type="text"
                value={profile.venue_concept || ''}
                onChange={(e) => handleChange('venue_concept', e.target.value)}
                placeholder="Например: Современная русская кухня с авторской подачей"
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </section>

          {/* Кухня */}
          <section className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Направления кухни</h2>
            <div className="flex flex-wrap gap-2">
              {Object.entries(CUISINE_TYPES).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => toggleCuisine(key)}
                  className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                    profile.cuisine_focus?.includes(key)
                      ? 'bg-emerald-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </section>

          {/* Локация */}
          <section className="bg-gray-800/50 border border-gray-700 rounded-xl p-6 space-y-4">
            <h2 className="text-lg font-semibold text-white mb-4">Локация</h2>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Город</label>
                <input
                  type="text"
                  value={profile.city || ''}
                  onChange={(e) => handleChange('city', e.target.value)}
                  placeholder="Москва"
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Регион</label>
                <select
                  value={profile.region || 'moskva'}
                  onChange={(e) => handleChange('region', e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-emerald-500"
                >
                  {Object.entries(REGIONS).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>
            </div>
          </section>

          {/* Персонал и мощности */}
          <section className="bg-gray-800/50 border border-gray-700 rounded-xl p-6 space-y-4">
            <h2 className="text-lg font-semibold text-white mb-4">Персонал и мощности</h2>
            
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Посадочных мест</label>
                <input
                  type="number"
                  value={profile.seating_capacity || ''}
                  onChange={(e) => handleChange('seating_capacity', e.target.value)}
                  placeholder="50"
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Сотрудников</label>
                <input
                  type="number"
                  value={profile.staff_count || ''}
                  onChange={(e) => handleChange('staff_count', e.target.value)}
                  placeholder="15"
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Уровень персонала</label>
                <select
                  value={profile.staff_skill_level || 'medium'}
                  onChange={(e) => handleChange('staff_skill_level', e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-emerald-500"
                >
                  {Object.entries(SKILL_LEVELS).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>
            </div>
          </section>

          {/* Описание */}
          <section className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Дополнительно</h2>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Описание заведения</label>
              <textarea
                value={profile.venue_description || ''}
                onChange={(e) => handleChange('venue_description', e.target.value)}
                placeholder="Расскажите о своём заведении: особенности, история, уникальные предложения..."
                rows={4}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 resize-none"
              />
            </div>
          </section>
        </div>
      </div>

      {/* Research Results Modal */}
      {showResearchResults && researchData && (
        <ResearchResults
          research={researchData}
          venueName={profile.venue_name}
          onClose={() => setShowResearchResults(false)}
        />
      )}
    </div>
  );
}

export default VenueProfile;

