import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [showRegistration, setShowRegistration] = useState(false);
  const [cities, setCities] = useState([]);
  const [selectedCity, setSelectedCity] = useState('');
  const [dishName, setDishName] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingType, setLoadingType] = useState(''); // 'techcard', 'sales', 'pairing', 'photo'
  const [techCard, setTechCard] = useState(null);
  const [userTechCards, setUserTechCards] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editInstruction, setEditInstruction] = useState('');
  const [isEditingAI, setIsEditingAI] = useState(false);
  const [currentTechCardId, setCurrentTechCardId] = useState(null);
  const [ingredients, setIngredients] = useState([]);

  // Subscription states
  const [subscriptionPlans, setSubscriptionPlans] = useState({});
  const [userSubscription, setUserSubscription] = useState(null);
  const [kitchenEquipment, setKitchenEquipment] = useState({});
  const [userEquipment, setUserEquipment] = useState([]);
  const [showPricingModal, setShowPricingModal] = useState(false);
  const [showEquipmentModal, setShowEquipmentModal] = useState(false);
  const [isUpgrading, setIsUpgrading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [userHistory, setUserHistory] = useState([]);
  const [showPriceModal, setShowPriceModal] = useState(false);
  const [userPrices, setUserPrices] = useState([]);
  const [uploadingPrices, setUploadingPrices] = useState(false);
  const [editableIngredients, setEditableIngredients] = useState([]);
  const [isEditingIngredients, setIsEditingIngredients] = useState(false);
  const [editableSteps, setEditableSteps] = useState([]);
  const [isEditingSteps, setIsEditingSteps] = useState(false);

  // Instructions state
  const [showInstructions, setShowInstructions] = useState(false);

  // Interactive ingredients state
  const [currentIngredients, setCurrentIngredients] = useState([]);

  // PRO AI features state
  const [showProAIModal, setShowProAIModal] = useState(false);
  const [proAIResult, setProAIResult] = useState('');
  const [proAITitle, setProAITitle] = useState('');
  
  // Separate states for PRO AI modals
  const [showSalesScriptModal, setShowSalesScriptModal] = useState(false);
  const [salesScriptResult, setSalesScriptResult] = useState('');
  const [showFoodPairingModal, setShowFoodPairingModal] = useState(false);
  const [foodPairingResult, setFoodPairingResult] = useState('');
  const [showPhotoTipsModal, setShowPhotoTipsModal] = useState(false);
  const [photoTipsResult, setPhotoTipsResult] = useState('');
  const [showInspirationModal, setShowInspirationModal] = useState(false);
  const [inspirationResult, setInspirationResult] = useState('');
  const [inspirationPrompt, setInspirationPrompt] = useState('');
  
  // Finances modal state
  const [showFinancesModal, setShowFinancesModal] = useState(false);
  const [financesResult, setFinancesResult] = useState(null);
  const [isAnalyzingFinances, setIsAnalyzingFinances] = useState(false);

  // Inline editing states
  const [isInlineEditing, setIsInlineEditing] = useState(false);
  const [editingField, setEditingField] = useState(null);
  const [editingValue, setEditingValue] = useState('');

  // Voice recognition states
  const [isListening, setIsListening] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState('');
  const [showVoiceModal, setShowVoiceModal] = useState(false);
  const [recognition, setRecognition] = useState(null);
  const [showRegistrationModal, setShowRegistrationModal] = useState(false);

  // Login states
  const [showLogin, setShowLogin] = useState(false);
  const [loginEmail, setLoginEmail] = useState('');

  // Registration form state
  const [registrationData, setRegistrationData] = useState({
    email: '',
    name: '',
    city: ''
  });

  // Typing animation states
  const [displayedText, setDisplayedText] = useState('');
  const [typingIndex, setTypingIndex] = useState(0);
  const fullText = "От идеи до техкарты за 60 секунд";

  // Typing animation effect
  useEffect(() => {
    if (typingIndex < fullText.length) {
      const timeout = setTimeout(() => {
        setDisplayedText(fullText.slice(0, typingIndex + 1));
        setTypingIndex(typingIndex + 1);
      }, 100);
      return () => clearTimeout(timeout);
    }
  }, [typingIndex, fullText]);

  // Animated loading messages
  const getLoadingMessages = (type) => {
    const messages = {
      techcard: [
        "🛒 Иду на виртуальный рынок за продуктами...",
        "⚖️ Взвешиваю ингредиенты на точных весах...",
        "👨‍🍳 Консультируюсь с нейрошефом...",
        "🧮 Считаю себестоимость и прибыль...",
        "📋 Пишу пошаговый рецепт...",
        "🔥 Рассчитываю время приготовления...",
        "🎨 Добавляю последние штрихи...",
        "✨ Техкарта почти готова!"
      ],
      sales: [
        "🎭 Изучаю психологию клиента...",
        "💬 Придумываю убойные фразы...",
        "🎯 Настраиваю скрипт на целевую аудиторию...",
        "🔥 Добавляю эмоциональные триггеры...",
        "💡 Готовлю ответы на возражения...",
        "✨ Скрипт продаж готов!"
      ],
      pairing: [
        "🍷 Дегустирую вина в виртуальном погребе...",
        "🧀 Подбираю идеальные сочетания...",
        "📚 Консультируюсь с сомелье...",
        "🎨 Создаю баланс вкусов...",
        "⚗️ Анализирую химию вкуса...",
        "✨ Фудпейринг готов!"
      ],
      photo: [
        "📸 Настраиваю виртуальную камеру...",
        "💡 Выбираю идеальное освещение...",
        "🎨 Подбираю лучший ракурс...",
        "🍽️ Создаю композицию кадра...",
        "✨ Советы по фото готовы!"
      ],
      inspiration: [
        "🎨 Ищу креативные идеи по всему миру...",
        "🧠 Активирую творческие нейроны...",
        "🌍 Изучаю международные кухни...",
        "⚡ Генерирую неожиданные сочетания...",
        "🔮 Создаю магию вкуса...",
        "🌟 Придумываю гениальный твист...",
        "✨ Вдохновение готово!"
      ]
    };
    return messages[type] || messages.techcard;
  };

  const simulateProgress = (type, duration = 15000) => {
    const messages = getLoadingMessages(type);
    const totalSteps = messages.length;
    const stepDuration = duration / totalSteps;
    
    setLoadingProgress(0);
    setLoadingMessage(messages[0]);
    
    let currentStep = 0;
    const interval = setInterval(() => {
      currentStep++;
      const progress = (currentStep / totalSteps) * 100;
      setLoadingProgress(progress);
      
      if (currentStep < totalSteps) {
        setLoadingMessage(messages[currentStep]);
      } else {
        clearInterval(interval);
      }
    }, stepDuration);
    
    return interval;
  };
  
  // Format PRO AI content for better display
  const formatProAIContent = (content) => {
    if (!content) return '';
    
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold text
      .replace(/\*(.*?)\*/g, '<em>$1</em>')              // Italic text
      .replace(/#{1,6}\s*(.*)/g, '<h3 class="text-lg font-bold text-purple-300 mt-4 mb-2">$1</h3>')  // Headers
      .replace(/^\s*-\s+(.*)/gm, '<li class="ml-4 mb-1">• $1</li>')  // List items
      .replace(/^\s*\d+\.\s+(.*)/gm, '<li class="ml-4 mb-1">$1</li>')  // Numbered lists
      .replace(/\n\n/g, '<br><br>')  // Double line breaks
      .replace(/\n/g, '<br>');       // Single line breaks
  };
  // Inline editing functions
  const startInlineEdit = (field, value) => {
    setEditingField(field);
    setEditingValue(value);
    setIsInlineEditing(true);
  };

  const saveInlineEdit = () => {
    if (!editingField || !techCard) return;
    
    let updatedTechCard = techCard;
    
    // Обновляем соответствующее поле в техкарте
    if (editingField.startsWith('ingredient_')) {
      // Обновляем ингредиент
      const ingredientIndex = parseInt(editingField.split('_')[1]);
      const newIngredients = [...currentIngredients];
      if (newIngredients[ingredientIndex]) {
        newIngredients[ingredientIndex].name = editingValue;
        setCurrentIngredients(newIngredients);
      }
    } else if (editingField.startsWith('step_')) {
      // Обновляем шаг рецепта
      const stepPattern = new RegExp(`(\\d+\\. )(.*)`, 'g');
      updatedTechCard = updatedTechCard.replace(stepPattern, (match, num, text) => {
        if (num.trim() === editingField.replace('step_', '') + '.') {
          return num + editingValue;
        }
        return match;
      });
    } else {
      // Обновляем другие поля
      const fieldPatterns = {
        'title': /(\*\*Название:\*\*\s*)(.*?)(?=\n|\*\*|$)/,
        'description': /(\*\*Описание:\*\*\s*)(.*?)(?=\n\*\*|$)/,
        'time': /(\*\*Время:\*\*\s*)(.*?)(?=\n|\*\*|$)/,
        'yield': /(\*\*Выход:\*\*\s*)(.*?)(?=\n|\*\*|$)/,
        'cost': /(\*\*💸 Себестоимость:\*\*\s*)(.*?)(?=\n|\*\*|$)/,
        'kbju': /(\*\*КБЖУ на 1 порцию:\*\*\s*)(.*?)(?=\n|\*\*|$)/,
        'allergens': /(\*\*Аллергены:\*\*\s*)(.*?)(?=\n|\*\*|$)/,
        'storage': /(\*\*Заготовки и хранение:\*\*\s*)(.*?)(?=\n\*\*|$)/s
      };
      
      const pattern = fieldPatterns[editingField];
      if (pattern) {
        updatedTechCard = updatedTechCard.replace(pattern, `$1${editingValue}`);
      }
    }
    
    setTechCard(updatedTechCard);
    setIsInlineEditing(false);
    setEditingField(null);
    setEditingValue('');
  };

  const cancelInlineEdit = () => {
    setIsInlineEditing(false);
    setEditingField(null);
    setEditingValue('');
  };

  // Компонент для редактируемого текста
  const EditableText = ({ field, value, className = "", multiline = false }) => {
    const isEditing = editingField === field;
    
    if (isEditing) {
      return multiline ? (
        <div className="inline-block w-full">
          <textarea
            value={editingValue}
            onChange={(e) => setEditingValue(e.target.value)}
            className="w-full bg-gray-700 text-white px-2 py-1 rounded border border-purple-400 focus:outline-none resize-none"
            rows={3}
            onBlur={saveInlineEdit}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.ctrlKey) {
                saveInlineEdit();
              } else if (e.key === 'Escape') {
                cancelInlineEdit();
              }
            }}
            autoFocus
          />
        </div>
      ) : (
        <input
          value={editingValue}
          onChange={(e) => setEditingValue(e.target.value)}
          className="inline-block bg-gray-700 text-white px-2 py-1 rounded border border-purple-400 focus:outline-none"
          onBlur={saveInlineEdit}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              saveInlineEdit();
            } else if (e.key === 'Escape') {
              cancelInlineEdit();
            }
          }}
          autoFocus
        />
      );
    }
    
    return (
      <span
        className={`${className} cursor-pointer hover:bg-gray-700/50 px-1 py-0.5 rounded transition-colors`}
        onClick={() => startInlineEdit(field, value)}
        title="Кликните для редактирования"
      >
        {value}
      </span>
    );
  };

  const formatTechCard = (content) => {
    if (!content) return null;

    // Извлекаем основные секции с помощью regex
    const extractSection = (pattern) => {
      const match = content.match(pattern);
      return match ? match[1].trim() : '';
    };

    const title = extractSection(/\*\*Название:\*\*\s*(.*?)(?=\n|$)/);
    const category = extractSection(/\*\*Категория:\*\*\s*(.*?)(?=\n|$)/);
    const description = extractSection(/\*\*Описание:\*\*\s*(.*?)(?=\n\n|\*\*)/s);
    const ingredients = extractSection(/\*\*Ингредиенты:\*\*.*?\n\n(.*?)(?=\n\n|\*\*)/s);
    const recipe = extractSection(/\*\*Пошаговый рецепт:\*\*\s*(.*?)(?=\n\n|\*\*)/s);
    const time = extractSection(/\*\*Время:\*\*\s*(.*?)(?=\n|$)/);
    const yieldAmount = extractSection(/\*\*Выход:\*\*\s*(.*?)(?=\n|$)/);
    const portion = extractSection(/\*\*Порция:\*\*\s*(.*?)(?=\n|$)/);
    const cost = extractSection(/\*\*Себестоимость:\*\*\s*(.*?)(?=\n\n|\*\*)/s);
    const kbzhu1 = extractSection(/\*\*КБЖУ на 1 порцию:\*\*\s*(.*?)(?=\n|$)/);
    const kbzhu100 = extractSection(/\*\*КБЖУ на 100 г:\*\*\s*(.*?)(?=\n|$)/);
    const allergens = extractSection(/\*\*Аллергены:\*\*\s*(.*?)(?=\n|$)/);
    const storage = extractSection(/\*\*Заготовки и хранение:\*\*\s*(.*?)(?=\n\n|\*\*)/s);
    const tips = extractSection(/\*\*Особенности и советы от шефа:\*\*\s*(.*?)(?=\n\n|\*\*)/s);
    const serving = extractSection(/\*\*Рекомендация подачи:\*\*\s*(.*?)(?=\n|$)/);

    return (
      <div className="space-y-6">
        {/* НАЗВАНИЕ */}
        {title && (
          <div className="text-center">
            <h1 className="text-3xl font-bold text-purple-300 mb-2">
              <EditableText field="title" value={title} className="text-3xl font-bold text-purple-300" />
            </h1>
            {category && (
              <p className="text-gray-400 text-lg">
                <EditableText field="category" value={category} className="text-gray-400 text-lg" />
              </p>
            )}
          </div>
        )}

        {/* ОПИСАНИЕ */}
        {description && (
          <div className="bg-gray-800/30 rounded-lg p-4">
            <h3 className="text-lg font-bold text-purple-400 mb-3 uppercase tracking-wide">ОПИСАНИЕ</h3>
            <div className="text-gray-300 leading-relaxed">
              <EditableText field="description" value={description} className="text-gray-300 leading-relaxed" multiline={true} />
            </div>
          </div>
        )}

        {/* ИНГРЕДИЕНТЫ */}
        {ingredients && renderIngredientsSection(content)}

        {/* ВРЕМЯ И ВЫХОД */}
        {(time || yieldAmount) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {time && (
              <div className="bg-blue-900/20 rounded-lg p-4 text-center">
                <h4 className="text-blue-300 font-bold mb-2">ВРЕМЯ</h4>
                <p className="text-gray-300">
                  <EditableText field="time" value={time} className="text-gray-300" />
                </p>
              </div>
            )}
            {yieldAmount && (
              <div className="bg-green-900/20 rounded-lg p-4 text-center">
                <h4 className="text-green-300 font-bold mb-2">ВЫХОД</h4>
                <p className="text-gray-300">
                  <EditableText field="yield" value={yieldAmount} className="text-gray-300" />
                </p>
              </div>
            )}
          </div>
        )}

        {/* СЕБЕСТОИМОСТЬ */}
        {cost && (
          <div className="bg-green-900/20 rounded-lg p-4">
            <h3 className="text-xl font-bold text-green-300 mb-4">СЕБЕСТОИМОСТЬ</h3>
            <div className="space-y-1">
              <EditableText field="cost" value={cost} className="text-gray-300" multiline={true} />
            </div>
          </div>
        )}

        {/* ПОШАГОВЫЙ РЕЦЕПТ */}
        {recipe && (
          <div className="bg-gray-800/30 rounded-lg p-4">
            <h3 className="text-xl font-bold text-purple-300 mb-4">ПОШАГОВЫЙ РЕЦЕПТ</h3>
            <div className="space-y-3">
              {recipe.split('\n').filter(line => line.trim()).map((line, idx) => (
                <div key={idx} className="flex items-start space-x-3">
                  <span className="text-purple-400 font-bold min-w-[2rem]">
                    {line.match(/^\d+\./) ? line.match(/^\d+/)[0] : '•'}
                  </span>
                  <div className="text-gray-300 flex-1">
                    <EditableText 
                      field={`step_${idx}`} 
                      value={line.replace(/^\d+\.\s*/, '')} 
                      className="text-gray-300" 
                      multiline={true}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* КБЖУ */}
        {(kbzhu1 || kbzhu100) && (
          <div className="bg-yellow-900/20 rounded-lg p-4">
            <h3 className="text-xl font-bold text-yellow-300 mb-4">КБЖУ</h3>
            <div className="space-y-2">
              {kbzhu1 && (
                <p className="text-gray-300">
                  <strong>На 1 порцию:</strong> <EditableText field="kbju" value={kbzhu1} className="text-gray-300" />
                </p>
              )}
              {kbzhu100 && (
                <p className="text-gray-300">
                  <strong>На 100 г:</strong> {kbzhu100}
                </p>
              )}
            </div>
          </div>
        )}

        {/* АЛЛЕРГЕНЫ */}
        {allergens && (
          <div className="bg-red-900/20 rounded-lg p-4">
            <h3 className="text-xl font-bold text-red-300 mb-2">АЛЛЕРГЕНЫ</h3>
            <p className="text-gray-300">
              <EditableText field="allergens" value={allergens} className="text-gray-300" />
            </p>
          </div>
        )}

        {/* ЗАГОТОВКИ И ХРАНЕНИЕ */}
        {storage && (
          <div className="bg-gray-800/30 rounded-lg p-4">
            <h3 className="text-xl font-bold text-purple-300 mb-4">ЗАГОТОВКИ И ХРАНЕНИЕ</h3>
            <div className="space-y-2">
              <EditableText field="storage" value={storage} className="text-gray-300" multiline={true} />
            </div>
          </div>
        )}

        {/* СОВЕТЫ ОТ ШЕФА */}
        {tips && (
          <div className="bg-gradient-to-r from-orange-900/20 to-red-900/20 rounded-lg p-4">
            <h3 className="text-xl font-bold text-orange-300 mb-4">СОВЕТЫ ОТ ШЕФА</h3>
            <div className="space-y-2">
              <EditableText field="tips" value={tips} className="text-gray-300" multiline={true} />
            </div>
          </div>
        )}

        {/* РЕКОМЕНДАЦИЯ ПОДАЧИ */}
        {serving && (
          <div className="bg-pink-900/20 rounded-lg p-4">
            <h3 className="text-xl font-bold text-pink-300 mb-2">ПОДАЧА</h3>
            <p className="text-gray-300">
              <EditableText field="serving" value={serving} className="text-gray-300" />
            </p>
          </div>
        )}
      </div>
    );
  };

  // Basic functions
  const fetchCities = async () => {
    try {
      const response = await axios.get(`${API}/cities`);
      setCities(response.data);
    } catch (error) {
      console.error('Error fetching cities:', error);
    }
  };

  const fetchSubscriptionPlans = async () => {
    try {
      const response = await axios.get(`${API}/subscription-plans`);
      setSubscriptionPlans(response.data);
    } catch (error) {
      console.error('Error fetching subscription plans:', error);
    }
  };

  const fetchKitchenEquipment = async () => {
    try {
      const response = await axios.get(`${API}/kitchen-equipment`);
      setKitchenEquipment(response.data);
    } catch (error) {
      console.error('Error fetching kitchen equipment:', error);
    }
  };

  const fetchUserSubscription = async () => {
    // В Beta версии все пользователи имеют PRO подписку
    if (!currentUser?.id) return;
    
    setUserSubscription({
      subscription_plan: 'pro',
      subscription_status: 'active',
      monthly_tech_cards_used: 0,
      kitchen_equipment: []
    });
    setUserEquipment([]);
  };

  const fetchUserPrices = async () => {
    if (!currentUser?.id) return;
    try {
      const response = await axios.get(`${API}/user-prices/${currentUser.id}`);
      setUserPrices(response.data.prices || []);
    } catch (error) {
      console.error('Error fetching user prices:', error);
    }
  };

  const updateKitchenEquipment = async (equipmentIds) => {
    if (!currentUser?.id) return;
    try {
      await axios.post(`${API}/update-kitchen-equipment/${currentUser.id}`, {
        equipment_ids: equipmentIds
      });
      setUserEquipment(equipmentIds);
      setShowEquipmentModal(false);
      alert('Кухонное оборудование обновлено успешно!');
    } catch (error) {
      console.error('Error updating kitchen equipment:', error);
      alert('Ошибка при обновлении оборудования: ' + (error.response?.data?.detail || error.message));
    }
  };

  const parseIngredientsFromTechCard = (techCardContent) => {
    if (!techCardContent) return [];
    
    const ingredientsMatch = techCardContent.match(/\*\*Ингредиенты:\*\*(.*?)(?=\*\*[^*]+:\*\*|$)/s);
    if (!ingredientsMatch) return [];
    
    const ingredientsText = ingredientsMatch[1];
    const ingredientLines = ingredientsText
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.startsWith('-') && line.length > 5);
    
    const parsedIngredients = ingredientLines.map((line, index) => {
      const cleanLine = line.replace(/^-\s*/, '').trim();
      let name = '', quantity = '', unit = 'г', price = '', totalPrice = '0';
      
      // Парсим по формату: "Продукт — количество — ~цена"
      if (cleanLine.includes(' — ')) {
        const parts = cleanLine.split(' — ');
        name = parts[0] || '';
        
        // Парсим количество и единицу
        if (parts[1]) {
          const qtyMatch = parts[1].match(/(\d+(?:\.\d+)?)\s*([а-яёА-ЯЁ]+|г|кг|мл|л|шт|штук?)?/);
          if (qtyMatch) {
            quantity = qtyMatch[1];
            unit = qtyMatch[2] || 'г';
          }
        }
        
        // Парсим цену
        if (parts[2]) {
          const priceMatch = parts[2].match(/~?(\d+(?:\.\d+)?)/);
          if (priceMatch) {
            totalPrice = priceMatch[1];
            price = priceMatch[1];
          }
        }
      } else {
        name = cleanLine;
      }
      
      return {
        id: index + 1,
        name: name.trim(),
        quantity: quantity,
        unit: unit,
        price: price,
        totalPrice: totalPrice,
        originalQuantity: quantity,
        originalPrice: price
      };
    });
    
    return parsedIngredients;
  };

  // Заменим статический список на интерактивную таблицу
  const renderIngredientsSection = (content) => {
    if (!content) return null;
    
    const ingredientsMatch = content.match(/\*\*Ингредиенты:\*\*(.*?)(?=\*\*[^*]+:\*\*|$)/s);
    if (!ingredientsMatch) return null;
    
    return (
      <div className="bg-gradient-to-r from-purple-600/10 to-pink-600/10 border border-purple-400/20 rounded-lg p-4">
        <h3 className="text-xl font-bold text-purple-300 mb-4">ИНГРЕДИЕНТЫ</h3>
        
        {/* Отображаем интерактивный редактор */}
        {currentIngredients.length > 0 ? (
          <div className="space-y-3">
            {/* Заголовки таблицы */}
            <div className="hidden sm:grid grid-cols-12 gap-3 text-sm font-bold text-purple-300 border-b border-purple-400/30 pb-2">
              <span className="col-span-1">#</span>
              <span className="col-span-6">ИНГРЕДИЕНТ</span>
              <span className="col-span-3">КОЛИЧЕСТВО</span>
              <span className="col-span-2">ЦЕНА</span>
            </div>
            
            {/* Строки ингредиентов */}
            {currentIngredients.map((ingredient, index) => (
              <div key={ingredient.id || index} className="grid grid-cols-1 sm:grid-cols-12 gap-2 sm:gap-3 bg-gray-800/50 rounded-lg p-3">
                <span className="hidden sm:flex col-span-1 text-purple-400 font-bold items-center justify-center">
                  {index + 1}.
                </span>
                <input
                  type="text"
                  value={ingredient.name}
                  onChange={(e) => updateIngredient(ingredient.id, 'name', e.target.value)}
                  className="col-span-6 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-gray-200 focus:border-purple-400 focus:outline-none"
                  placeholder="Название ингредиента"
                />
                <input
                  type="text"
                  value={`${ingredient.quantity || ''} ${ingredient.unit || 'г'}`}
                  onChange={(e) => {
                    const value = e.target.value;
                    const match = value.match(/(\d+(?:\.\d+)?)\s*([а-яёА-ЯЁ]+|г|кг|мл|л|шт|штук?)?/);
                    if (match) {
                      const newQty = match[1];
                      const newUnit = match[2] || ingredient.unit || 'г';
                      
                      // Обновляем количество и единицу одновременно
                      setCurrentIngredients(prev => prev.map(ing => {
                        if (ing.id === ingredient.id) {
                          const updatedIng = { ...ing, quantity: newQty, unit: newUnit };
                          
                          // Пересчитываем цену пропорционально
                          if (ing.originalQuantity && ing.originalPrice) {
                            const originalQty = parseFloat(ing.originalQuantity) || 1;
                            const originalPrice = parseFloat(ing.originalPrice) || 0;
                            const newQtyFloat = parseFloat(newQty) || 0;
                            
                            const newPrice = (newQtyFloat / originalQty) * originalPrice;
                            updatedIng.totalPrice = newPrice.toFixed(1);
                            updatedIng.price = newPrice.toFixed(1);
                          }
                          
                          return updatedIng;
                        }
                        return ing;
                      }));
                    }
                  }}
                  className="col-span-3 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-gray-200 focus:border-purple-400 focus:outline-none"
                  placeholder="250 г"
                />
                <div className="col-span-2 flex items-center space-x-2">
                  <span className="text-green-400 font-bold text-sm">
                    {Math.round(parseFloat(ingredient.totalPrice) || 0)} ₽
                  </span>
                  <button 
                    onClick={() => removeIngredient(ingredient.id)}
                    className="text-red-400 hover:text-red-300 text-sm"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
            
            {/* Кнопки управления */}
            <div className="flex gap-3 mt-4">
              <button
                onClick={addNewIngredient}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm"
              >
                + ДОБАВИТЬ ИНГРЕДИЕНТ
              </button>
              <button
                onClick={saveIngredientsToTechCard}
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm"
              >
                💾 СОХРАНИТЬ ИЗМЕНЕНИЯ
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center py-6 text-gray-400">
            <p>Ингредиенты не найдены</p>
          </div>
        )}
      </div>
    );
  };
  const updateIngredient = (id, field, value) => {
    setCurrentIngredients(prev => prev.map(ing => {
      if (ing.id === id) {
        const updatedIng = { ...ing, [field]: value };
        
        // Если изменилось количество, пересчитаем цену
        if (field === 'quantity' && ing.originalQuantity && ing.originalPrice) {
          const originalQty = parseFloat(ing.originalQuantity) || 1;
          const originalPrice = parseFloat(ing.originalPrice) || 0;
          const newQty = parseFloat(value) || 0;
          
          // Пропорциональный пересчет цены
          const newPrice = (newQty / originalQty) * originalPrice;
          updatedIng.totalPrice = newPrice.toFixed(1);
          updatedIng.price = newPrice.toFixed(1);
        }
        
        return updatedIng;
      }
      return ing;
    }));
  };

  const removeIngredient = (id) => {
    setCurrentIngredients(prev => prev.filter(ing => ing.id !== id));
  };

  const addNewIngredient = () => {
    const newId = Math.max(...currentIngredients.map(ing => ing.id), 0) + 1;
    setCurrentIngredients(prev => [...prev, {
      id: newId,
      name: 'Новый ингредиент',
      quantity: '100',
      unit: 'г',
      price: '10',
      totalPrice: '10',
      originalQuantity: '100',
      originalPrice: '10'
    }]);
  };

  const saveIngredientsToTechCard = () => {
    // Обновляем техкарту с новыми ингредиентами
    const newIngredientsText = currentIngredients.map(ing => 
      `- ${ing.name} — ${ing.quantity} ${ing.unit} — ~${Math.round(parseFloat(ing.totalPrice) || 0)} ₽`
    ).join('\n');
    
    const updatedTechCard = techCard.replace(
      /(\*\*Ингредиенты:\*\*)(.*?)(?=\*\*[^*]+:\*\*|$)/s,
      `$1\n\n${newIngredientsText}\n\n`
    );
    
    setTechCard(updatedTechCard);
    alert('Ингредиенты обновлены!');
  };

  // ПРО AI ФУНКЦИИ
  const generateSalesScript = async () => {
    if (!techCard || !currentUser?.id) return;
    
    setIsGenerating(true);
    setLoadingType('sales');
    const progressInterval = simulateProgress('sales', 12000);
    
    try {
      const response = await axios.post(`${API}/generate-sales-script`, {
        tech_card: techCard,
        user_id: currentUser.id
      });
      
      setSalesScriptResult(response.data.script);
      
      // Завершаем анимацию
      clearInterval(progressInterval);
      setLoadingProgress(100);
      setLoadingMessage('✨ Скрипт продаж готов!');
      
      setTimeout(() => {
        setIsGenerating(false);
        setLoadingProgress(0);
        setLoadingMessage('');
        setLoadingType('');
        setShowSalesScriptModal(true);
      }, 2000);
      
    } catch (error) {
      console.error('Error generating sales script:', error);
      clearInterval(progressInterval);
      setIsGenerating(false);
      setLoadingProgress(0);
      setLoadingMessage('');
      setLoadingType('');
      alert('Ошибка при генерации скрипта продаж');
    }
  };

  const generateFoodPairing = async () => {
    if (!techCard || !currentUser?.id) return;
    
    setIsGenerating(true);
    setLoadingType('pairing');
    const progressInterval = simulateProgress('pairing', 12000);
    
    try {
      const response = await axios.post(`${API}/generate-food-pairing`, {
        tech_card: techCard,
        user_id: currentUser.id
      });
      
      setFoodPairingResult(response.data.pairing);
      
      // Завершаем анимацию
      clearInterval(progressInterval);
      setLoadingProgress(100);
      setLoadingMessage('✨ Фудпейринг готов!');
      
      setTimeout(() => {
        setIsGenerating(false);
        setLoadingProgress(0);
        setLoadingMessage('');
        setLoadingType('');
        setShowFoodPairingModal(true);
      }, 2000);
      
    } catch (error) {
      console.error('Error generating food pairing:', error);
      clearInterval(progressInterval);
      setIsGenerating(false);
      setLoadingProgress(0);
      setLoadingMessage('');
      setLoadingType('');
      alert('Ошибка при генерации фудпейринга');
    }
  };

  const generatePhotoTips = async () => {
    if (!techCard || !currentUser?.id) return;
    
    setIsGenerating(true);
    setLoadingType('photo');
    const progressInterval = simulateProgress('photo', 10000);
    
    try {
      const response = await axios.post(`${API}/generate-photo-tips`, {
        user_id: currentUser.id,
        tech_card: techCard
      });
      
      clearInterval(progressInterval);
      setIsGenerating(false);
      setLoadingProgress(0);
      setLoadingMessage('');
      setLoadingType('');
      
      setPhotoTipsResult(response.data.tips);
      
      // Показываем модальное окно с небольшой задержкой
      setTimeout(() => {
        setShowPhotoTipsModal(true);
      }, 2000);
      
    } catch (error) {
      console.error('Error generating photo tips:', error);
      clearInterval(progressInterval);
      setIsGenerating(false);
      setLoadingProgress(0);
      setLoadingMessage('');
      setLoadingType('');
      alert('Ошибка при генерации советов по фото');
    }
  };

  const generateInspiration = async () => {
    if (!techCard || !currentUser?.id) return;
    
    setIsGenerating(true);
    setLoadingType('inspiration');
    const progressInterval = simulateProgress('inspiration', 15000);
    
    try {
      const response = await axios.post(`${API}/generate-inspiration`, {
        user_id: currentUser.id,
        tech_card: techCard,
        inspiration_prompt: inspirationPrompt || 'Создай креативный и жизнеспособный твист на это блюдо'
      });
      
      clearInterval(progressInterval);
      setIsGenerating(false);
      setLoadingProgress(0);
      setLoadingMessage('');
      setLoadingType('');
      
      setInspirationResult(response.data.inspiration);
      
      // Показываем модальное окно с небольшой задержкой
      setTimeout(() => {
        setShowInspirationModal(true);
      }, 2000);
      
    } catch (error) {
      console.error('Error generating inspiration:', error);
      clearInterval(progressInterval);
      setIsGenerating(false);
      setLoadingProgress(0);
      setLoadingMessage('');
      setLoadingType('');
      alert('Ошибка при генерации вдохновения');
    }
  };

  const analyzeFinances = async () => {
    if (!techCard || !currentUser?.id) return;
    
    setIsAnalyzingFinances(true);
    
    try {
      const response = await axios.post(`${API}/analyze-finances`, {
        user_id: currentUser.id,
        tech_card: techCard
      });
      
      setFinancesResult(response.data.analysis);
      setShowFinancesModal(true);
      
    } catch (error) {
      console.error('Error analyzing finances:', error);
      alert('Ошибка при анализе финансов: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsAnalyzingFinances(false);
    }
  };

  // РЕВОЛЮЦИОННОЕ РЕШЕНИЕ: ИНТЕРАКТИВНАЯ ТАБЛИЦА ИНГРЕДИЕНТОВ
  const renderIngredientsTable = (content) => {
    console.log('=== INGREDIENTS TABLE DEBUG ===');
    console.log('Content received:', !!content);
    
    if (!content) {
      console.log('No content provided');
      return null;
    }
    
    // Извлекаем ингредиенты из техкарты 
    const ingredientsMatch = content.match(/\*\*Ингредиенты:\*\*(.*?)(?=\*\*[^*]+:\*\*|$)/s);
    console.log('Ingredients match found:', !!ingredientsMatch);
    
    if (ingredientsMatch) {
      const ingredientsText = ingredientsMatch[1];
      console.log('Ingredients text:', ingredientsText);
      
      const ingredientLines = ingredientsText
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.startsWith('-') && line.length > 5);
      
      console.log('Parsed ingredient lines:', ingredientLines);
      
      if (ingredientLines.length > 0) {
        // Парсим ингредиенты в структурированный формат
        const parsedIngredients = ingredientLines.map((line, index) => {
          const cleanLine = line.replace(/^-\s*/, '').trim();
          let name = '', quantity = '', price = '';
          
          // Парсим по формату: "Продукт — количество — ~цена"
          if (cleanLine.includes(' — ')) {
            const parts = cleanLine.split(' — ');
            name = parts[0] || '';
            quantity = parts[1] || '';
            price = parts[2] || '';
          } else if (cleanLine.includes(' - ')) {
            const parts = cleanLine.split(' - ');
            name = parts[0] || '';
            quantity = parts[1] || '';
            price = parts[2] || '';
          } else {
            name = cleanLine;
          }
          
          // Извлекаем числовую цену для расчетов
          const priceMatch = price.match(/(\d+(?:[.,]\d+)?)/);
          const numericPrice = priceMatch ? parseFloat(priceMatch[1].replace(',', '.')) : 0;
          
          return {
            id: index,
            name: name.trim(),
            quantity: quantity.trim(),
            price: price.trim(),
            numericPrice: numericPrice
          };
        });
        
        console.log('Parsed ingredients:', parsedIngredients);
        
        // Используем parsedIngredients напрямую вместо состояния
        const displayIngredients = parsedIngredients;
        
        // Рассчитываем общую стоимость
        const totalCost = displayIngredients.reduce((sum, ing) => sum + (ing.numericPrice || 0), 0);
        
        console.log('Total cost calculated:', totalCost);
        
        return (
          <div key="ingredients-table" className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 border border-purple-400/30 rounded-lg p-6 mb-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-purple-300">ИНГРЕДИЕНТЫ</h3>
              <div className="text-sm text-purple-400">
                Всего позиций: {displayIngredients.length}
              </div>
            </div>
            
            {/* ИНТЕРАКТИВНАЯ ТАБЛИЦА */}
            <div className="overflow-x-auto bg-gray-800/50 rounded-lg">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gradient-to-r from-purple-600 to-purple-700">
                    <th className="text-left py-3 px-4 text-white font-bold text-sm">ИНГРЕДИЕНТ</th>
                    <th className="text-center py-3 px-4 text-white font-bold text-sm">КОЛИЧЕСТВО</th>
                    <th className="text-right py-3 px-4 text-white font-bold text-sm">ЦЕНА</th>
                    <th className="text-center py-3 px-4 text-white font-bold text-sm">ДЕЙСТВИЯ</th>
                  </tr>
                </thead>
                <tbody>
                  {displayIngredients.map((ingredient, index) => (
                    <tr key={ingredient.id} className={index % 2 === 0 ? 'bg-gray-700/30' : 'bg-gray-600/30'}>
                      <td className="py-3 px-4 text-gray-200 border-r border-gray-600">
                        <input
                          type="text"
                          value={ingredient.name}
                          onChange={(e) => {
                            const newIngredients = [...displayIngredients];
                            newIngredients[index] = { ...newIngredients[index], name: e.target.value };
                            setCurrentIngredients(newIngredients);
                          }}
                          className="w-full bg-transparent border-none outline-none text-gray-200 hover:bg-gray-700/50 rounded px-2 py-1"
                        />
                      </td>
                      <td className="py-3 px-4 text-center border-r border-gray-600">
                        <input
                          type="text"
                          value={ingredient.quantity}
                          onChange={(e) => {
                            const newIngredients = [...displayIngredients];
                            newIngredients[index] = { ...newIngredients[index], quantity: e.target.value };
                            setCurrentIngredients(newIngredients);
                          }}
                          className="w-full bg-transparent border-none outline-none text-gray-200 text-center hover:bg-gray-700/50 rounded px-2 py-1"
                        />
                      </td>
                      <td className="py-3 px-4 text-right border-r border-gray-600">
                        <input
                          type="text"
                          value={ingredient.price}
                          onChange={(e) => {
                            const newIngredients = [...displayIngredients];
                            const priceMatch = e.target.value.match(/(\d+(?:[.,]\d+)?)/);
                            const numericPrice = priceMatch ? parseFloat(priceMatch[1].replace(',', '.')) : 0;
                            newIngredients[index] = { 
                              ...newIngredients[index], 
                              price: e.target.value,
                              numericPrice: numericPrice
                            };
                            setCurrentIngredients(newIngredients);
                          }}
                          className="w-full bg-transparent border-none outline-none text-gray-200 text-right hover:bg-gray-700/50 rounded px-2 py-1"
                        />
                      </td>
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => {
                            const newIngredients = displayIngredients.filter((_, i) => i !== index);
                            setCurrentIngredients(newIngredients);
                          }}
                          className="text-red-400 hover:text-red-300 text-sm"
                        >
                          ✕
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* БЛОК С ОБЩЕЙ СТОИМОСТЬЮ */}
            <div className="mt-4 bg-gray-800/70 rounded-lg p-4">
              <div className="flex justify-between items-center">
                <span className="text-lg font-bold text-purple-300">Приблизительная себестоимость:</span>
                <span className="text-xl font-bold text-green-400">{Math.round(totalCost)} ₽</span>
              </div>
              <div className="mt-1 text-sm text-gray-400">
                *Рассчитывается из среднерыночных цен
              </div>
            </div>
            
            {/* КНОПКИ УПРАВЛЕНИЯ */}
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => {
                  const newId = Math.max(...displayIngredients.map(ing => ing.id), 0) + 1;
                  const newIngredients = [...displayIngredients, {
                    id: newId,
                    name: 'Новый ингредиент',
                    quantity: '100 г',
                    price: '~10 ₽',
                    numericPrice: 10
                  }];
                  setCurrentIngredients(newIngredients);
                }}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm"
              >
                + ДОБАВИТЬ ИНГРЕДИЕНТ
              </button>
              <button
                onClick={() => {
                  // Обновляем техкарту с новыми ингредиентами
                  const newIngredientsText = displayIngredients.map(ing => 
                    `- ${ing.name} — ${ing.quantity} — ${ing.price}`
                  ).join('\n');
                  
                  const updatedTechCard = techCard.replace(
                    /(\*\*Ингредиенты:\*\*)(.*?)(?=\*\*[^*]+:\*\*|$)/s,
                    `$1\n\n${newIngredientsText}\n\n`
                  );
                  
                  setTechCard(updatedTechCard);
                  alert('Ингредиенты обновлены!');
                }}
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm"
              >
                СОХРАНИТЬ ИЗМЕНЕНИЯ
              </button>
            </div>
          </div>
        );
      } else {
        console.log('No ingredient lines found');
      }
    } else {
      console.log('No ingredients section found');
    }
    
    // Если ингредиенты не найдены
    return (
      <div key="ingredients-error" className="bg-gradient-to-r from-red-600/20 to-orange-600/20 border border-red-400/30 rounded-lg p-6 mb-6">
        <h3 className="text-xl font-bold text-red-300 mb-4">ИНГРЕДИЕНТЫ</h3>
        <p className="text-red-300">Ингредиенты не найдены в техкарте. Попробуйте сгенерировать заново.</p>
      </div>
    );
  };

  const handleEditTechCard = async () => {
    if (!editInstruction.trim() || !currentTechCardId) return;

    setIsEditingAI(true);
    try {
      const response = await axios.post(`${API}/edit-tech-card`, {
        tech_card_id: currentTechCardId,
        edit_instruction: editInstruction,
        user_id: currentUser.id
      });
      
      setTechCard(response.data.tech_card);
      setCurrentIngredients(parseIngredientsFromTechCard(response.data.tech_card));
      setEditInstruction('');
      
      // Re-parse ingredients and steps for editing
      const lines = response.data.tech_card.split('\n');
      const ingredients = [];
      const steps = [];
      
      lines.forEach(line => {
        // Parse ingredients
        if (line.startsWith('- ') && line.includes('₽')) {
          const parts = line.replace('- ', '').split(' — ');
          if (parts.length >= 3) {
            ingredients.push({
              name: parts[0].trim(),
              quantity: parts[1].trim(),
              price: parts[2].trim()
            });
          }
        }
        
        // Parse numbered steps
        if (line.match(/^\d+\./)) {
          steps.push(line);
        }
      });
      
      setEditableIngredients(ingredients);
      setEditableSteps(steps);
      
    } catch (error) {
      console.error('Error editing tech card:', error);
      alert('Ошибка при редактировании техкарты');
    } finally {
      setIsEditingAI(false);
    }
  };

  const saveIngredientsChanges = () => {
    // Rebuild tech card with new ingredients
    const lines = techCard.split('\n');
    const newLines = [];
    let inIngredientsSection = false;
    let ingredientIndex = 0;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      if (line.includes('**Ингредиенты:**')) {
        inIngredientsSection = true;
        newLines.push(line);
        
        // Add updated ingredients
        editableIngredients.forEach(ing => {
          newLines.push(`- ${ing.name} — ${ing.quantity} — ${ing.price}`);
        });
        
        // Skip original ingredients
        continue;
      }
      
      if (inIngredientsSection && line.startsWith('- ') && line.includes('₽')) {
        // Skip original ingredient lines
        continue;
      }
      
      if (inIngredientsSection && line.startsWith('**') && line !== '**Ингредиенты:**') {
        inIngredientsSection = false;
      }
      
      newLines.push(line);
    }
    
    setTechCard(newLines.join('\n'));
    setIsEditingIngredients(false);
  };

  const saveStepsChanges = () => {
    // Rebuild tech card with new steps
    const lines = techCard.split('\n');
    const newLines = [];
    let inStepsSection = false;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      if (line.includes('**Пошаговый рецепт:**')) {
        inStepsSection = true;
        newLines.push(line);
        newLines.push('');
        
        // Add updated steps
        editableSteps.forEach((step, index) => {
          newLines.push(`${index + 1}. ${step}`);
        });
        
        continue;
      }
      
      if (inStepsSection && line.match(/^\d+\./)) {
        // Skip original step lines
        continue;
      }
      
      if (inStepsSection && line.startsWith('**') && !line.includes('Пошаговый рецепт')) {
        inStepsSection = false;
      }
      
      newLines.push(line);
    }
    
    setTechCard(newLines.join('\n'));
    setIsEditingSteps(false);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    
    if (!loginEmail) {
      alert('Введите email');
      return;
    }
    
    try {
      console.log('Attempting login with email:', loginEmail);
      const response = await axios.get(`${API}/user/${loginEmail}`);
      console.log('Login successful:', response.data);
      
      // Update state immediately
      setCurrentUser(response.data);
      localStorage.setItem('receptor_user', JSON.stringify(response.data));
      
      // Reset form
      setShowLogin(false);
      setLoginEmail('');
      
      console.log('User logged in:', response.data);
      
    } catch (error) {
      console.error('Login error:', error);
      if (error.response?.status === 404) {
        alert('Пользователь не найден. Попробуйте зарегистрироваться.');
      } else {
        alert('Ошибка входа. Попробуйте еще раз.');
      }
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    
    // Basic validation
    if (!registrationData.email || !registrationData.name || !registrationData.city) {
      alert('Пожалуйста, заполните все поля');
      return;
    }
    
    try {
      console.log('Attempting registration with data:', registrationData);
      const response = await axios.post(`${API}/register`, registrationData);
      console.log('Registration successful:', response.data);
      
      // Update state immediately
      setCurrentUser(response.data);
      localStorage.setItem('receptor_user', JSON.stringify(response.data));
      
      // Reset form
      setShowRegistration(false);
      setRegistrationData({ email: '', name: '', city: '' });
      
      // Force re-render by setting a flag
      console.log('User set to:', response.data);
      
    } catch (error) {
      console.error('Registration error:', error);
      if (error.response?.data?.detail) {
        alert(`Ошибка: ${error.response.data.detail}`);
      } else {
        alert('Ошибка регистрации. Попробуйте еще раз.');
      }
    }
  };

  const handleGenerateTechCard = async (e) => {
    e.preventDefault();
    console.log('Generate button clicked');
    console.log('Dish name:', dishName);
    console.log('Current user:', currentUser);
    
    if (!dishName.trim()) {
      alert('Пожалуйста, введите название блюда');
      return;
    }
    
    if (!currentUser?.id) {
      alert('Пожалуйста, войдите в систему');
      return;
    }
    
    // Запускаем анимированную загрузку
    setIsGenerating(true);
    setLoadingType('techcard');
    const progressInterval = simulateProgress('techcard', 15000);
    
    try {
      console.log('Sending request to:', `${API}/generate-tech-card`);
      const requestData = {
        dish_name: dishName,
        user_id: currentUser.id,
        city: currentUser.city || 'москва'
      };
      
      const response = await fetch(`${API}/generate-tech-card`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Tech card generation response:', data);
      
      setTechCard(data.tech_card);
      setCurrentIngredients(parseIngredientsFromTechCard(data.tech_card));
      
      // Парсим ингредиенты для редактора
      const ingredientsText = data.tech_card;
      const ingredientLines = ingredientsText.split('\n').filter(line => 
        line.trim().startsWith('- ') && line.includes('—') && line.includes('₽')
      );
      
      const parsedIngredients = ingredientLines.map((line, index) => {
        const parts = line.split('—').map(part => part.trim());
        if (parts.length >= 3) {
          const name = parts[0].replace(/^-\s*/, '').trim();
          const quantityPart = parts[1].trim();
          const pricePart = parts[2].replace(/[~₽]/g, '').trim();
          
          // Парсим количество и единицу
          const quantityMatch = quantityPart.match(/(\d+(?:\.\d+)?)\s*([а-яёА-ЯЁ]*|г|кг|мл|л|шт|штук)?/);
          const quantity = quantityMatch ? quantityMatch[1] : '100';
          const unit = quantityMatch ? (quantityMatch[2] || 'г') : 'г';
          
          const totalPrice = parseFloat(pricePart) || 0;
          const pricePerUnit = parseFloat(totalPrice) / parseFloat(quantity);
          
          return {
            id: index + 1,
            name,
            quantity,
            unit,
            unitPrice: pricePerUnit.toFixed(2),
            totalPrice: totalPrice.toFixed(1),
            originalQuantity: quantity,
            originalPrice: totalPrice.toFixed(1)
          };
        }
        return null;
      }).filter(Boolean);
      
      console.log('Parsed ingredients:', parsedIngredients);
      setCurrentIngredients(parsedIngredients);
      
      // Инициализируем редактируемые ингредиенты и этапы
      setEditableIngredients(parsedIngredients);
      
      // Парсим этапы для редактирования
      const stepsLines = data.tech_card.split('\n').filter(line => 
        line.trim().match(/^\d+\./)
      );
      setEditableSteps(stepsLines);
      
      // Добавляем в историю
      await fetchUserHistory();
      
      // Завершаем анимацию
      clearInterval(progressInterval);
      setLoadingProgress(100);
      setLoadingMessage('✨ Техкарта готова!');
      
      setTimeout(() => {
        setIsGenerating(false);
        setLoadingProgress(0);
        setLoadingMessage('');
        setLoadingType('');
      }, 2000);
      
    } catch (error) {
      console.error('Error generating tech card:', error);
      clearInterval(progressInterval);
      setIsGenerating(false);
      setLoadingProgress(0);
      setLoadingMessage('');
      setLoadingType('');
      alert('Ошибка при генерации техкарты. Попробуйте еще раз.');
    }
  };

  const handlePriceFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingPrices(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', currentUser.id);

    try {
      const response = await axios.post(`${API}/upload-prices`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      console.log('Upload response:', response.data);
      
      if (response.data.success) {
        alert(`Прайс-лист успешно загружен! Обработано ${response.data.count} позиций в ${response.data.categories_found} категориях`);
        setUserPrices(response.data.prices || []);
        setShowPriceModal(false);
      } else {
        alert('Ошибка при загрузке прайс-листа');
      }
    } catch (error) {
      console.error('Error uploading prices:', error);
      alert('Ошибка при загрузке файла: ' + (error.response?.data?.detail || error.message));
    } finally {
      setUploadingPrices(false);
    }
  };

  const fetchUserHistory = async () => {
    if (!currentUser?.id) {
      console.log('No user ID available for history fetch');
      return;
    }
    
    try {
      console.log('Fetching history for user:', currentUser.id);
      const response = await axios.get(`${API}/user-history/${currentUser.id}`);
      console.log('History response:', response.data);
      setUserHistory(response.data.history || []);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('receptor_user');
    setTechCard(null);
    setUserTechCards([]);
  };

  const handlePrintTechCard = () => {
    const dishName = techCard.split('\n').find(line => line.includes('Название'))?.replace(/\*\*/g, '').replace('Название:', '').trim() || 'Техкарта';
    const printWindow = window.open('', '_blank');
    
    // Process content to clean up formatting
    const cleanedContent = techCard.split('\n').map(line => {
      // Remove all ** formatting
      let cleanLine = line.replace(/\*\*/g, '');
      
      // Skip unwanted lines
      if (cleanLine.includes('Сгенерировано RECEPTOR AI') || 
          cleanLine.includes('экономьте') || 
          cleanLine.includes('стандартная ресторанная порция') ||
          cleanLine.toLowerCase().includes('указывай на одну порцию') ||
          cleanLine.toLowerCase().includes('указывай ингредиенты') ||
          cleanLine.toLowerCase().includes('ингредиенты указывай') ||
          cleanLine.trim() === '') {
        return '';
      }
      
      // Format headers
      if (line.startsWith('**') && line.endsWith('**')) {
        const title = cleanLine.replace(':', '').trim();
        if (title.includes('Название')) {
          const dishTitle = title.replace('Название', '').trim();
          return `<h1 style="color: #8B5CF6; font-size: 28px; font-weight: 900; text-align: center; margin-bottom: 30px; border-bottom: 3px solid #8B5CF6; padding-bottom: 15px;">${dishTitle}</h1>`;
        }
        return `<h2 style="color: #1A1B23; font-size: 18px; font-weight: 800; text-transform: uppercase; margin-top: 25px; margin-bottom: 15px; border-bottom: 2px solid #C084FC; padding-bottom: 8px;">${title}</h2>`;
      }
      
      // Format ingredients - remove all price information
      if (line.startsWith('- ') && (line.includes('₽') || line.includes('руб'))) {
        // Remove price information completely from ingredient lines
        const cleanIngredient = cleanLine.replace('- ', '').replace(/\s*—\s*~\d+(?:\.\d+)?\s*₽\s*$/, '').replace(/\s*—\s*\d+(?:\.\d+)?\s*₽\s*$/, '').trim();
        return `<p style="margin-left: 20px; margin-bottom: 8px;">• ${cleanIngredient}</p>`;
      }
      
      // Format numbered steps
      if (line.match(/^\d+\./)) {
        return `<div style="background: #F8FAFC; border-left: 4px solid #8B5CF6; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">${cleanLine}</div>`;
      }
      
      // Format list items
      if (line.startsWith('- ')) {
        return `<p style="margin-left: 20px; margin-bottom: 8px;">• ${cleanLine.replace('- ', '')}</p>`;
      }
      
      // Cost information - remove all cost sections from PDF
      if (line.includes('Себестоимость') || line.includes('Рекомендуемая цена') || line.includes('💸')) {
        return '';  // Skip cost information completely
      }
      
      // Regular paragraphs
      if (cleanLine.trim() && !cleanLine.startsWith('─')) {
        return `<p style="margin-bottom: 12px; line-height: 1.6;">${cleanLine}</p>`;
      }
      
      return '';
    }).filter(Boolean).join('');
    
    const techCardHtml = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Технологическая карта - ${dishName}</title>
          <meta charset="utf-8">
          <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
          <style>
            * { font-family: 'Montserrat', sans-serif !important; }
            body { 
              line-height: 1.6; 
              margin: 40px; 
              background: white; 
              color: #1A1B23; 
            }
            @media print {
              body { margin: 20px; }
            }
          </style>
        </head>
        <body>
          <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #8B5CF6; font-size: 32px; font-weight: 900; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px;">ТЕХНОЛОГИЧЕСКАЯ КАРТА</h1>
          </div>
          <div>${cleanedContent}</div>
          <div style="margin-top: 30px; text-align: center; font-size: 12px; color: #64748B; border-top: 1px solid #E5E7EB; padding-top: 20px;">
            <p><strong>Создано в RECEPTOR PRO Beta</strong></p>
            <p>Дата создания: ${new Date().toLocaleDateString('ru-RU')}</p>
            <p style="color: #F59E0B; font-size: 10px;">Тестовая версия - пожалуйста, проверяйте все расчеты</p>
          </div>
        </body>
      </html>
    `;
    
    printWindow.document.write(techCardHtml);
    printWindow.document.close();
    
    setTimeout(() => {
      printWindow.print();
    }, 500);
  };

  const startVoiceRecognition = () => {
    if (recognition) {
      recognition.start();
    } else {
      console.log('Speech recognition not initialized');
    }
  };

  const initVoiceRecognition = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = false;
      recognitionInstance.lang = 'ru-RU';
      
      recognitionInstance.onstart = () => {
        setIsListening(true);
        setVoiceStatus('Слушаю...');
        setShowVoiceModal(true);
      };
      
      recognitionInstance.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setDishName(transcript);
        setVoiceStatus('Распознано: ' + transcript);
        setTimeout(() => {
          setShowVoiceModal(false);
          setIsListening(false);
        }, 1500);
      };
      
      recognitionInstance.onerror = (event) => {
        setVoiceStatus('Ошибка распознавания');
        setIsListening(false);
        setTimeout(() => {
          setShowVoiceModal(false);
        }, 2000);
      };
      
      recognitionInstance.onend = () => {
        setIsListening(false);
        if (showVoiceModal) {
          setTimeout(() => {
            setShowVoiceModal(false);
          }, 1000);
        }
      };
      
      setRecognition(recognitionInstance);
    } else {
      console.log('Speech recognition not supported');
    }
  };

  useEffect(() => {
    fetchCities();
    fetchSubscriptionPlans();
    fetchKitchenEquipment();
    initVoiceRecognition();
    const savedUser = localStorage.getItem('receptor_user');
    console.log('Checking for saved user:', savedUser);
    if (savedUser) {
      const parsedUser = JSON.parse(savedUser);
      console.log('Setting currentUser from localStorage:', parsedUser);
      setCurrentUser(parsedUser);
      
      // Load user prices for PRO users
      if (parsedUser.subscription_plan === 'pro' || parsedUser.subscription_plan === 'business') {
        loadUserPrices(parsedUser.id);
      }
    }
  }, []);

  // Fetch subscription data when user changes
  useEffect(() => {
    if (currentUser?.id) {
      fetchUserSubscription();
      fetchUserHistory();
      fetchUserPrices();
    }
  }, [currentUser?.id]);

  const loadUserPrices = async (userId) => {
    try {
      const response = await axios.get(`${API}/user-prices/${userId}`);
      setUserPrices(response.data.prices || []);
    } catch (error) {
      console.error('Error loading user prices:', error);
    }
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black flex items-center justify-center p-4">
        <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-8 w-full max-w-md border border-gray-700">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-white mb-4">
              RECEPTOR <span className="text-purple-400">PRO</span> <span className="text-yellow-400 text-2xl">Beta</span>
            </h1>
            <p className="text-gray-300 text-lg mb-2">
              Нейросеть для создания техкарт для ресторанов
            </p>
            <p className="text-yellow-400 text-sm mb-8">
              🧪 Тестовая версия для получения обратной связи
            </p>
            
            <div className="mb-6">
              <label className="block text-purple-300 text-sm font-bold mb-2">
                ВЫБЕРИТЕ ВАШ ГОРОД
              </label>
              <select 
                value={selectedCity}
                onChange={(e) => setSelectedCity(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:border-purple-400 focus:outline-none"
              >
                <option value="">Выберите город</option>
                {cities.map(city => (
                  <option key={city.code} value={city.code}>{city.name}</option>
                ))}
              </select>
            </div>
            
            <button
              onClick={() => {
                if (!selectedCity) {
                  alert('Пожалуйста, выберите город');
                  return;
                }
                // Создаем тестового пользователя
                const testUser = {
                  id: 'test_user_' + Date.now(),
                  name: 'Тестовый пользователь',
                  email: 'test@example.com',
                  city: selectedCity.toLowerCase(),
                  subscription_plan: 'pro',
                  monthly_tech_cards_used: 0,
                  created_at: new Date().toISOString()
                };
                setCurrentUser(testUser);
                localStorage.setItem('receptor_user', JSON.stringify(testUser));
              }}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
            >
              НАЧАТЬ ТЕСТИРОВАНИЕ
            </button>
            
            <p className="text-gray-400 text-sm mt-4">
              🧪 RECEPTOR PRO Beta - тестируйте все функции бесплатно!
            </p>
          </div>

          {!showRegistration && !showLogin ? (
            <div className="space-y-6">
              <button
                onClick={() => setShowRegistration(true)}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
              >
                НАЧАТЬ РАБОТУ
              </button>
              <button
                onClick={() => setShowLogin(true)}
                className="w-full bg-gradient-to-r from-gray-600 to-gray-700 text-white font-bold py-3 px-6 rounded-lg hover:from-gray-700 hover:to-gray-800 transition-all"
              >
                ВОЙТИ
              </button>
            </div>
          ) : showLogin ? (
            <form onSubmit={handleLogin} className="space-y-6">
              <input
                type="email"
                placeholder="Email"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none"
                required
              />
              <button
                type="submit"
                className="w-full bg-gradient-to-r from-purple-600 to-purple-700 text-white font-bold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-purple-800 transition-all"
              >
                ВОЙТИ
              </button>
              <button
                type="button"
                onClick={() => setShowLogin(false)}
                className="w-full bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition-all"
              >
                НАЗАД
              </button>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-6">
              <input
                type="email"
                placeholder="Email"
                value={registrationData.email}
                onChange={(e) => setRegistrationData({...registrationData, email: e.target.value})}
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none"
                required
              />
              <input
                type="text"
                placeholder="Имя"
                value={registrationData.name}
                onChange={(e) => setRegistrationData({...registrationData, name: e.target.value})}
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none"
                required
              />
              <select
                value={registrationData.city}
                onChange={(e) => setRegistrationData({...registrationData, city: e.target.value})}
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none"
                required
              >
                <option value="">Выберите город</option>
                {cities.map(city => (
                  <option key={city.code} value={city.code}>{city.name}</option>
                ))}
              </select>
              <button
                type="submit"
                className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
              >
                ЗАРЕГИСТРИРОВАТЬСЯ
              </button>
              <button
                type="button"
                onClick={() => setShowRegistration(false)}
                className="w-full bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition-all"
              >
                НАЗАД
              </button>
            </form>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white font-['Montserrat']">
      {/* Hero Section */}
      {!currentUser && (
        <div className="hero-section">
          <div className="hero-particles">
            {[...Array(9)].map((_, i) => (
              <div key={i} className="particle"></div>
            ))}
          </div>
          
          <div className="hero-content">
            <h1 className="hero-title">
              {displayedText}
              <span className="typing-cursor"></span>
            </h1>
            
            <p className="hero-subtitle">
              ИИ создает профессиональные техкарты для ресторанов. 
              Быстро, удобно, прибыльно.
            </p>
            
            <button
              onClick={() => setShowRegistrationModal(true)}
              className="hero-cta"
            >
              Создать первую техкарту
            </button>
            
            <div className="hero-stats">
              <div className="hero-stat">
                <div className="hero-stat-number">1000+</div>
                <div className="hero-stat-label">Техкарт создано</div>
              </div>
              <div className="hero-stat">
                <div className="hero-stat-number">60</div>
                <div className="hero-stat-label">Секунд на создание</div>
              </div>
              <div className="hero-stat">
                <div className="hero-stat-number">95%</div>
                <div className="hero-stat-label">Довольных шефов</div>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* Header */}
      <header className="border-b border-purple-400/30 p-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-2 sm:space-y-0">
            <h1 className="text-2xl sm:text-3xl font-bold text-purple-300">
              RECEPTOR PRO <span className="text-yellow-400 text-lg sm:text-xl">Beta</span>
            </h1>
            
            {/* Subscription Info */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-4 w-full sm:w-auto">
              <div className="text-center sm:text-left">
                <div className="text-sm text-purple-300 font-bold">
                  {currentUser.subscription_plan?.toUpperCase() || 'FREE'}
                </div>
                {currentUser.subscription_plan === 'free' && (
                  <div className="text-xs text-gray-400">
                    {currentUser.monthly_tech_cards_used || 0}/3 техкарт
                  </div>
                )}
                {currentUser.subscription_plan === 'starter' && (
                  <div className="text-xs text-gray-400">
                    {currentUser.monthly_tech_cards_used || 0}/25 техкарт
                  </div>
                )}
                {(currentUser.subscription_plan === 'pro' || currentUser.subscription_plan === 'business') && (
                  <div className="text-xs text-gray-400">
                    {currentUser.monthly_tech_cards_used || 0} техкарт
                  </div>
                )}
              </div>
              
              <div className="flex items-center space-x-4 sm:space-x-6">
                <button
                  onClick={() => {
                    setShowHistory(!showHistory);
                    if (!showHistory) {
                      fetchUserHistory();
                    }
                  }}
                  className="text-purple-300 hover:text-purple-200 font-semibold text-sm sm:text-base"
                >
                  ИСТОРИЯ
                </button>
                <span className="text-purple-300 font-bold text-sm sm:text-base">{currentUser.name}</span>
                <button
                  onClick={handleLogout}
                  className="text-purple-300 hover:text-purple-200 font-semibold text-sm sm:text-base"
                >
                  ВЫЙТИ
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-10">
          {/* Left Panel */}
          <div className="lg:col-span-1">
            <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-4 sm:p-8 border border-gray-700 space-y-6 sm:space-y-8">
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-purple-300 mb-4 sm:mb-6">СОЗДАТЬ ТЕХКАРТУ</h2>
                
                {/* Beautiful Step-by-Step Instructions */}
                <div className="mb-4 sm:mb-6">
                  <div className="flex items-center space-x-2 mb-3 sm:mb-4 cursor-pointer" onClick={() => setShowInstructions(!showInstructions)}>
                    <span className="text-base sm:text-lg font-bold text-purple-300">КАК ПОЛЬЗОВАТЬСЯ</span>
                    <span className="text-purple-300 text-lg sm:text-xl">{showInstructions ? '▼' : '▶'}</span>
                  </div>
                  {showInstructions && (
                    <div className="bg-gradient-to-r from-purple-900/20 to-pink-900/20 rounded-xl p-4 sm:p-6 border border-purple-400/30 space-y-3 sm:space-y-4">
                      
                      <div className="grid grid-cols-1 gap-4 sm:gap-6">
                        <div>
                          <h4 className="text-purple-300 font-bold mb-3 text-sm sm:text-base">📝 ОПИСАНИЕ БЛЮДА</h4>
                          <div className="space-y-2 text-xs sm:text-sm text-gray-300">
                            <p>• <strong>Пишите максимально подробно</strong> - чем точнее опишете, тем лучше результат</p>
                            <p>• <strong>Укажите количество порций</strong> - например "на 4 порции"</p>
                            <p>• <strong>Добавьте особенности</strong> - "средней прожарки", "с хрустящей корочкой"</p>
                            <p className="text-purple-200">💡 <em>Пример: "Стейк из говядины на 4 порции, средней прожарки, общий выход 800г"</em></p>
                          </div>
                        </div>
                        
                        <div>
                          <h4 className="text-purple-300 font-bold mb-3 text-sm sm:text-base">🎯 СОВЕТЫ ПО ИСПОЛЬЗОВАНИЮ</h4>
                          <div className="space-y-2 text-xs sm:text-sm text-gray-300">
                            <p>• <strong>Редактируйте ингредиенты</strong> - можно менять количество и цены</p>
                            <p>• <strong>Используйте кнопку "РЕДАКТИРОВАТЬ"</strong> для ручной корректировки</p>
                            <p>• <strong>Сохраняйте в PDF</strong> - для печати в кухню</p>
                            <p>• <strong>PRO функции</strong> - скрипты продаж, фудпейринг, советы фото</p>
                          </div>
                        </div>
                      </div>
                      
                      <div className="mt-4 sm:mt-6 pt-3 sm:pt-4 border-t border-purple-400/30">
                        <h4 className="text-yellow-300 font-bold mb-2 text-sm sm:text-base">💰 О СЕБЕСТОИМОСТИ</h4>
                        <p className="text-xs sm:text-sm text-gray-300">
                          Себестоимость рассчитывается по среднерыночным ценам с учетом вашего региона. 
                          Нейросеть может ошибаться - всегда проверяйте расчеты! 
                          <strong className="text-purple-300"> Детальный калькулятор на основе прайсов ваших поставщиков в разработке.</strong>
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                    <form onSubmit={handleGenerateTechCard} className="space-y-4 sm:space-y-6">
                  <div>
                    <label className="block text-purple-300 text-sm font-bold mb-2 sm:mb-3 uppercase tracking-wide">
                      НАЗВАНИЕ БЛЮДА
                    </label>
                    <div className="relative">
                      <textarea
                        value={dishName}
                        onChange={(e) => setDishName(e.target.value)}
                        placeholder="Опишите блюдо подробно. Например: Стейк из говядины с картофельным пюре и грибным соусом"
                        className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none min-h-[120px] resize-none text-sm sm:text-base"
                        rows={5}
                        required
                      />
                      <button
                        type="button"
                        onClick={startVoiceRecognition}
                        disabled={isListening}
                        className={`absolute right-2 bottom-2 p-2 rounded-lg transition-colors ${
                          isListening 
                            ? 'bg-red-600 animate-pulse' 
                            : 'bg-purple-600 hover:bg-purple-700'
                        } text-white w-10 h-10 sm:w-12 sm:h-12 flex items-center justify-center`}
                        title="Голосовой ввод"
                      >
                        <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={!dishName.trim() || isGenerating}
                    className={`w-full ${isGenerating ? 'bg-gray-600 cursor-not-allowed' : 'btn-primary'} text-white font-bold py-3 sm:py-4 px-6 rounded-lg transition-colors flex items-center justify-center text-sm sm:text-base min-h-[48px] sm:min-h-[56px]`}
                  >
                    {isGenerating ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-3 h-4 w-4 sm:h-5 sm:w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        СОЗДАЮ ТЕХКАРТУ...
                      </>
                    ) : 'СОЗДАТЬ ТЕХКАРТУ'}
                  </button>
                </form>
                
                {/* PRO Price Management */}
                {(currentUser.subscription_plan === 'pro' || currentUser.subscription_plan === 'business') && (
                  <div className="border-t border-purple-400/30 pt-4 sm:pt-6">
                    <h3 className="text-base sm:text-lg font-bold text-purple-300 mb-3 sm:mb-4">PRO ФУНКЦИИ</h3>
                    
                    {/* Kitchen Equipment Button */}
                    <button
                      onClick={() => setShowEquipmentModal(true)}
                      className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 sm:py-4 px-4 sm:px-6 rounded-lg transition-colors mb-3 sm:mb-4 text-sm sm:text-base min-h-[48px]"
                    >
                      КУХОННОЕ ОБОРУДОВАНИЕ
                    </button>
                    {userEquipment.length > 0 && (
                      <div className="text-xs sm:text-sm text-purple-400 text-center mb-3 sm:mb-4">
                        Выбрано {userEquipment.length} единиц оборудования
                      </div>
                    )}
                    
                    {/* Price Management Button */}
                    <button
                      onClick={() => setShowPriceModal(true)}
                      className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 sm:py-4 px-4 sm:px-6 rounded-lg transition-colors mb-3 sm:mb-4 text-sm sm:text-base min-h-[48px]"
                    >
                      УПРАВЛЕНИЕ ПРАЙСАМИ
                    </button>
                    {userPrices.length > 0 && (
                      <div className="text-xs sm:text-sm text-green-400 text-center mb-3 sm:mb-4">
                        Загружено {userPrices.length} позиций
                      </div>
                    )}
                    <div className="text-xs sm:text-sm text-yellow-400 text-center mb-3 sm:mb-4 p-2 bg-yellow-900/20 rounded">
                      🔧 Функция в разработке
                    </div>
                    
                    {/* ПРО AI функции */}
                    <div className="border-t border-purple-400/20 pt-3 sm:pt-4">
                      <h4 className="text-sm sm:text-base font-bold text-purple-200 mb-3">AI ДОПОЛНЕНИЯ</h4>
                      
                      <div className="grid grid-cols-1 gap-2 sm:gap-3">
                        <button
                          onClick={() => generateSalesScript()}
                          disabled={isGenerating}
                          className={`w-full ${isGenerating ? 'bg-gray-600 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px]`}
                        >
                          СКРИПТ ПРОДАЖ
                        </button>
                        
                        <button
                          onClick={generateFoodPairing}
                          disabled={isGenerating}
                          className={`w-full ${isGenerating ? 'bg-gray-600 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px]`}
                        >
                          ФУДПЕЙРИНГ
                        </button>
                        
                        <button
                          onClick={generateInspiration}
                          disabled={isGenerating}
                          className={`w-full ${isGenerating ? 'bg-gray-600 cursor-not-allowed' : 'btn-inspiration'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px]`}
                        >
                          🌟 ВДОХНОВЕНИЕ
                        </button>
                        
                        <button
                          onClick={generatePhotoTips}
                          disabled={isGenerating}
                          className={`w-full ${isGenerating ? 'bg-gray-600 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px]`}
                        >
                          СОВЕТЫ ПО ФОТО
                        </button>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Upgrade prompt for Free users */}
                {currentUser.subscription_plan === 'free' && currentUser.monthly_tech_cards_used >= 3 && (
                  <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 border border-purple-400/30 rounded-lg p-4 mt-4">
                    <h3 className="text-base sm:text-lg font-bold text-purple-300 mb-2">ЛИМИТ ИСЧЕРПАН</h3>
                    <p className="text-gray-300 text-sm mb-3">
                      Вы использовали все 3 техкарты в месяце. Обновите подписку для неограниченного доступа!
                    </p>
                    <button
                      onClick={() => alert('Функция обновления подписки скоро будет доступна')}
                      className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-4 rounded-lg transition-colors text-sm sm:text-base min-h-[44px]"
                    >
                      ОБНОВИТЬ ПОДПИСКУ
                    </button>
                  </div>
                )}
              </div>

              {/* AI Editing */}
              {techCard && (
                <div className="border-t border-purple-400/30 pt-6 sm:pt-8">
                  <h3 className="text-lg sm:text-xl font-bold text-purple-300 mb-4 sm:mb-6">
                    РЕДАКТИРОВАТЬ ЧЕРЕЗ AI
                  </h3>
                  <div className="space-y-4">
                    <textarea
                      value={editInstruction}
                      onChange={(e) => setEditInstruction(e.target.value)}
                      placeholder="Детально опишите что изменить. Например: увеличить порцию в 2 раза, заменить картофель на рис"
                      className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none min-h-[100px] resize-none text-sm sm:text-base"
                      rows={4}
                    />
                    <button
                      onClick={handleEditTechCard}
                      disabled={!editInstruction.trim() || isEditingAI}
                      className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold py-3 sm:py-4 px-6 rounded-lg transition-colors flex items-center justify-center text-sm sm:text-base min-h-[48px] sm:min-h-[56px]"
                    >
                      {isEditingAI ? (
                        <>
                          <svg className="animate-spin -ml-1 mr-3 h-4 w-4 sm:h-5 sm:w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          ОБРАБАТЫВАЮ...
                        </>
                      ) : 'ИЗМЕНИТЬ ЧЕРЕЗ AI'}
                    </button>
                  </div>
                  
                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    className="w-full mt-4 bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 sm:py-4 px-6 rounded-lg transition-colors text-sm sm:text-base min-h-[48px] sm:min-h-[56px]"
                  >
                    {isEditing ? 'ЗАКРЫТЬ РЕДАКТОР' : 'РУЧНОЕ РЕДАКТИРОВАНИЕ'}
                  </button>
                </div>
              )}

              {/* Manual Editing */}
              {isEditing && techCard && (
                <div className="border-t border-purple-400/30 pt-6 sm:pt-8">
                  <h3 className="text-lg sm:text-xl font-bold text-purple-300 mb-4 sm:mb-6">
                    РУЧНОЕ РЕДАКТИРОВАНИЕ
                  </h3>
                  <div className="space-y-4">
                    <button
                      onClick={() => setIsEditingIngredients(true)}
                      className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                    >
                      РЕДАКТИРОВАТЬ ИНГРЕДИЕНТЫ
                    </button>
                    <button
                      onClick={() => setIsEditingSteps(true)}
                      className="w-full bg-yellow-600 hover:bg-yellow-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                    >
                      РЕДАКТИРОВАТЬ ЭТАПЫ
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Panel */}
          <div className="lg:col-span-2">
            {techCard ? (
              <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-4 sm:p-8 border border-gray-700">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 sm:mb-8 gap-4">
                  <div>
                    <h2 className="text-xl sm:text-2xl font-bold text-purple-300">ТЕХНОЛОГИЧЕСКАЯ КАРТА</h2>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">
                      💡 Кликните на любой текст для редактирования
                    </p>
                  </div>
                  <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4 w-full sm:w-auto">
                    <button 
                      onClick={() => navigator.clipboard.writeText(techCard)}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-bold transition-colors text-sm sm:text-base min-h-[44px] sm:min-h-[48px]"
                    >
                      КОПИРОВАТЬ
                    </button>
                    <button 
                      onClick={handlePrintTechCard}
                      className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-bold transition-colors text-sm sm:text-base min-h-[44px] sm:min-h-[48px]"
                    >
                      ЭКСПОРТ В PDF
                    </button>
                  </div>
                </div>
                <div className="prose prose-invert max-w-none">
                  {formatTechCard(techCard)}
                </div>
                
                {/* ВСТРОЕННЫЙ РЕДАКТОР ИНГРЕДИЕНТОВ */}
                <div className="mt-6 sm:mt-8 bg-gradient-to-r from-purple-600/20 to-pink-600/20 border border-purple-400/30 rounded-lg p-4 sm:p-6">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 sm:mb-6 gap-4">
                    <h3 className="text-lg sm:text-xl font-bold text-purple-300">РЕДАКТОР ИНГРЕДИЕНТОВ</h3>
                    <div className="flex space-x-2 sm:space-x-3 w-full sm:w-auto">
                      <button 
                        onClick={() => {
                          setCurrentIngredients([...currentIngredients, { 
                            name: '', 
                            quantity: '', 
                            price: '',
                            id: Date.now() 
                          }]);
                        }}
                        className="bg-green-600 hover:bg-green-700 text-white px-3 sm:px-4 py-2 rounded-lg font-bold transition-colors flex items-center space-x-1 sm:space-x-2 text-sm sm:text-base min-h-[40px] sm:min-h-[44px] flex-1 sm:flex-none justify-center"
                      >
                        <span>+</span>
                        <span>ДОБАВИТЬ</span>
                      </button>
                      <button 
                        onClick={() => {
                          // Логика сохранения изменений в техкарту
                          console.log('Сохраняем изменения ингредиентов:', currentIngredients);
                          
                          // Обновляем техкарту с новыми ингредиентами
                          const lines = techCard.split('\n');
                          const newLines = [];
                          let inIngredientsSection = false;
                          
                          for (let i = 0; i < lines.length; i++) {
                            const line = lines[i];
                            
                            if (line.includes('**Ингредиенты:**')) {
                              inIngredientsSection = true;
                              newLines.push(line);
                              newLines.push('');
                              
                              // Добавляем обновленные ингредиенты
                              currentIngredients.forEach(ing => {
                                newLines.push(`- ${ing.name} — ${ing.quantity} ${ing.unit} — ~${Math.round(parseFloat(ing.totalPrice) || 0)} ₽`);
                              });
                              continue;
                            }
                            
                            if (inIngredientsSection && line.startsWith('- ') && line.includes('₽')) {
                              // Пропускаем старые строки ингредиентов
                              continue;
                            }
                            
                            if (inIngredientsSection && line.startsWith('**') && !line.includes('Ингредиенты')) {
                              inIngredientsSection = false;
                            }
                            
                            newLines.push(line);
                          }
                          
                          setTechCard(newLines.join('\n'));
                          alert('Изменения ингредиентов сохранены!');
                        }}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 sm:px-4 py-2 rounded-lg font-bold transition-colors flex items-center space-x-1 sm:space-x-2 text-sm sm:text-base min-h-[40px] sm:min-h-[44px] flex-1 sm:flex-none justify-center"
                      >
                        <span>💾</span>
                        <span>СОХРАНИТЬ</span>
                      </button>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    {currentIngredients.length === 0 ? (
                      <div className="text-center py-6 sm:py-8 text-gray-400">
                        <p className="mb-4 text-sm sm:text-base">Ингредиенты из техкарты появятся здесь автоматически</p>
                      </div>
                    ) : (
                      <>
                        <div className="hidden sm:grid grid-cols-12 gap-3 text-sm font-bold text-purple-300 border-b border-purple-400/30 pb-2">
                          <span className="col-span-1">#</span>
                          <span className="col-span-6">ИНГРЕДИЕНТ</span>
                          <span className="col-span-3">КОЛИЧЕСТВО</span>
                          <span className="col-span-1">СТОИМОСТЬ</span>
                          <span className="col-span-1">✕</span>
                        </div>
                        {currentIngredients.map((ingredient, index) => (
                          <div key={ingredient.id || index} className="grid grid-cols-1 sm:grid-cols-12 gap-2 sm:gap-3 bg-gray-800/50 rounded-lg p-3 hover:bg-gray-800/70 transition-colors">
                            <div className="flex items-center sm:hidden mb-2">
                              <span className="text-purple-400 font-bold mr-2">#{index + 1}</span>
                              <span className="text-purple-300 font-bold">ИНГРЕДИЕНТ</span>
                            </div>
                            <span className="hidden sm:flex col-span-1 text-purple-400 font-bold items-center justify-center">
                              {index + 1}.
                            </span>
                            <input
                              type="text"
                              value={ingredient.name}
                              onChange={(e) => {
                                const newIngredients = [...currentIngredients];
                                newIngredients[index].name = e.target.value;
                                setCurrentIngredients(newIngredients);
                              }}
                              placeholder="Название ингредиента"
                              className="col-span-6 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-gray-200 focus:border-purple-400 focus:outline-none"
                            />
                            <input
                              type="text"
                              value={`${ingredient.quantity || ''} ${ingredient.unit || 'г'}`}
                              onChange={(e) => {
                                const newIngredients = [...currentIngredients];
                                const value = e.target.value;
                                // Парсим количество и единицу
                                const match = value.match(/(\d+(?:\.\d+)?)\s*([а-яёА-ЯЁ]+|г|кг|мл|л|шт|штук)?/);
                                if (match) {
                                  const newQty = parseFloat(match[1]) || 0;
                                  const newUnit = match[2] || ingredient.unit || 'г';
                                  
                                  newIngredients[index].quantity = newQty.toString();
                                  newIngredients[index].unit = newUnit;
                                  
                                  // Пересчитаем стоимость на основе изначальной цены за единицу
                                  const originalQty = parseFloat(ingredient.originalQuantity) || 1;
                                  const originalPrice = parseFloat(ingredient.originalPrice) || 0;
                                  
                                  // Пропорциональный пересчет: (новое количество / старое количество) * старая цена
                                  const newPrice = (newQty / originalQty) * originalPrice;
                                  newIngredients[index].totalPrice = newPrice.toFixed(1);
                                }
                                setCurrentIngredients(newIngredients);
                              }}
                              placeholder="250 г"
                              className="col-span-3 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-gray-200 focus:border-purple-400 focus:outline-none"
                            />
                            <div className="col-span-1 flex items-center justify-center">
                              <span className="text-green-400 font-bold text-sm">
                                {Math.round(parseFloat(ingredient.totalPrice) || 0)} ₽
                              </span>
                            </div>
                            <button 
                              onClick={() => {
                                const newIngredients = currentIngredients.filter((_, i) => i !== index);
                                setCurrentIngredients(newIngredients);
                              }}
                              className="col-span-1 text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded-lg transition-colors flex items-center justify-center text-lg"
                            >
                              ✕
                            </button>
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                  
                  {currentIngredients.length > 0 && (
                    <div className="mt-6 p-4 bg-gray-800/30 rounded-lg border border-green-400/30">
                      <div className="grid grid-cols-3 gap-6 text-center">
                        <div>
                          <div className="text-gray-400 text-sm mb-1">ВЫХОД ПОРЦИИ</div>
                          <div className="text-blue-400 font-bold text-xl">
                            {(() => {
                              // Пытаемся извлечь выход из техкарты
                              const yieldMatch = techCard?.match(/\*\*Выход:\*\*\s*(\d+)\s*г/);
                              if (yieldMatch) {
                                return yieldMatch[1] + ' г';
                              }
                              
                              // Если не найден, считаем по ингредиентам
                              const totalWeight = currentIngredients.reduce((total, ing) => {
                                return total + (parseFloat(ing.quantity) || 0);
                              }, 0);
                              
                              return totalWeight.toFixed(0) + ' г';
                            })()}
                          </div>
                        </div>
                        
                        <div>
                          <div className="text-gray-400 text-sm mb-1">СЕБЕСТОИМОСТЬ ПОРЦИИ</div>
                          <div className="text-green-400 font-bold text-xl">
                            {Math.round(currentIngredients.reduce((total, ing) => {
                              return total + (parseFloat(ing.totalPrice) || 0);
                            }, 0))} ₽
                          </div>
                          <div className="text-gray-500 text-xs mt-1">
                            *Примерная себестоимость
                          </div>
                        </div>
                        
                        <div>
                          <div className="text-gray-400 text-sm mb-1">РЕКОМЕНДУЕМАЯ ЦЕНА</div>
                          <div className="text-purple-400 font-bold text-xl">
                            {Math.round(currentIngredients.reduce((total, ing) => {
                              return total + (parseFloat(ing.totalPrice) || 0);
                            }, 0) * 3)} ₽
                          </div>
                          <div className="text-gray-500 text-xs mt-1">
                            Маржа 200%
                          </div>
                        </div>
                      </div>
                      
                      <div className="mt-4 text-xs text-gray-500 text-center">
                        Стоимость рассчитывается на основе рыночных цен + региональный коэффициент + инфляция
                      </div>
                    </div>
                  )}
                </div>

              </div>
            ) : (
              <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-12 border border-gray-700 text-center">
                <h3 className="text-2xl font-bold text-purple-300 mb-4">ТЕХКАРТА ПОЯВИТСЯ ЗДЕСЬ</h3>
                <p className="text-gray-400">Введите название блюда слева и нажмите "СОЗДАТЬ ТЕХКАРТУ"</p>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Voice Recognition Modal */}
      {showVoiceModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 text-center border border-purple-500/30">
            <div className="mb-6">
              {isListening ? (
                <div className="w-20 h-20 mx-auto bg-red-500 rounded-full flex items-center justify-center animate-pulse">
                  <svg className="w-10 h-10 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 715 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                  </svg>
                </div>
              ) : (
                <div className="w-20 h-20 mx-auto bg-green-500 rounded-full flex items-center justify-center">
                  <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              )}
            </div>
            <h3 className="text-xl font-bold text-purple-300 mb-4">
              {isListening ? 'СЛУШАЮ...' : 'ГОТОВО!'}
            </h3>
            <p className="text-gray-300">
              {voiceStatus}
            </p>
            {!isListening && (
              <button
                onClick={() => setShowVoiceModal(false)}
                className="mt-6 bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg"
              >
                ЗАКРЫТЬ
              </button>
            )}
          </div>
        </div>
      )}

      {/* Ingredients Editor Modal */}
      {isEditingIngredients && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-purple-500/30">
            <h3 className="text-2xl font-bold text-purple-300 mb-6">РЕДАКТОР ИНГРЕДИЕНТОВ</h3>
            
            {editableIngredients.map((ingredient, index) => (
              <div key={index} className="grid grid-cols-4 gap-4 mb-4">
                <input
                  type="text"
                  value={ingredient.name}
                  onChange={(e) => {
                    const newIngredients = [...editableIngredients];
                    newIngredients[index].name = e.target.value;
                    setEditableIngredients(newIngredients);
                  }}
                  className="col-span-2 bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:border-purple-500 outline-none"
                  placeholder="Ингредиент"
                />
                <input
                  type="text"
                  value={ingredient.quantity}
                  onChange={(e) => {
                    const newIngredients = [...editableIngredients];
                    newIngredients[index].quantity = e.target.value;
                    setEditableIngredients(newIngredients);
                  }}
                  className="bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:border-purple-500 outline-none"
                  placeholder="Количество"
                />
                <input
                  type="text"
                  value={ingredient.price}
                  onChange={(e) => {
                    const newIngredients = [...editableIngredients];
                    newIngredients[index].price = e.target.value;
                    setEditableIngredients(newIngredients);
                    
                    // Auto-recalculate total cost
                    const totalCost = newIngredients.reduce((sum, ing) => {
                      return sum + (parseFloat(ing.totalPrice) || 0);
                    }, 0);
                    console.log('New total cost:', totalCost);
                  }}
                  className="bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:border-purple-500 outline-none"
                  placeholder="Цена"
                />
              </div>
            ))}
            
            <div className="flex space-x-4 mt-6">
              <button
                onClick={() => {
                  setEditableIngredients([...editableIngredients, { name: '', quantity: '', price: '' }]);
                }}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
              >
                ДОБАВИТЬ
              </button>
              <button
                onClick={saveIngredientsChanges}
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg"
              >
                СОХРАНИТЬ
              </button>
              <button
                onClick={() => setIsEditingIngredients(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
              >
                ОТМЕНА
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Steps Editor Modal */}
      {isEditingSteps && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-purple-500/30">
            <h3 className="text-2xl font-bold text-purple-300 mb-6">РЕДАКТОР ЭТАПОВ</h3>
            
            {editableSteps.map((step, index) => (
              <div key={index} className="mb-4">
                <textarea
                  value={step}
                  onChange={(e) => {
                    const newSteps = [...editableSteps];
                    newSteps[index] = e.target.value;
                    setEditableSteps(newSteps);
                  }}
                  className="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:border-purple-500 outline-none"
                  placeholder={`Этап ${index + 1}`}
                  rows={3}
                />
              </div>
            ))}
            
            <div className="flex space-x-4 mt-6">
              <button
                onClick={() => {
                  setEditableSteps([...editableSteps, '']);
                }}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
              >
                ДОБАВИТЬ ЭТАП
              </button>
              <button
                onClick={saveStepsChanges}
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg"
              >
                СОХРАНИТЬ
              </button>
              <button
                onClick={() => setIsEditingSteps(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
              >
                ОТМЕНА
              </button>
            </div>
          </div>
        </div>
      )}

      {/* History Modal */}
      {showHistory && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-purple-500/30">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-purple-300">ИСТОРИЯ ТЕХКАРТ</h3>
              <button
                onClick={() => setShowHistory(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            {userHistory.length === 0 ? (
              <p className="text-gray-400 text-center py-8">История пуста</p>
            ) : (
              <div className="space-y-4">
                {userHistory.map((item, index) => (
                  <div key={index} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="text-lg font-bold text-purple-300">
                        {item.content.split('\n')[0].replace('**Название:**', '').trim()}
                      </h4>
                      <span className="text-sm text-gray-400">
                        {new Date(item.created_at).toLocaleDateString('ru-RU')}
                      </span>
                    </div>
                    <p className="text-gray-300 text-sm mb-3">
                      {item.content.split('\n').find(line => line.includes('**Описание:**'))?.replace('**Описание:**', '').trim() || 'Без описания'}
                    </p>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => {
                          setTechCard(item.content);
                          setCurrentIngredients(parseIngredientsFromTechCard(item.content));
                          setCurrentTechCardId(item.id);
                          setShowHistory(false);
                        }}
                        className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded text-sm"
                      >
                        ОТКРЫТЬ
                      </button>
                      <button
                        onClick={() => navigator.clipboard.writeText(item.content)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                      >
                        КОПИРОВАТЬ
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Price Management Modal - PRO only */}
      {showPriceModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-green-500/30">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-green-300">УПРАВЛЕНИЕ ПРАЙСАМИ</h3>
              <button
                onClick={() => setShowPriceModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            {/* File Upload */}
            <div className="mb-6">
              <h4 className="text-lg font-bold text-green-300 mb-3">ЗАГРУЗИТЬ ПРАЙС</h4>
              <div className="border-2 border-dashed border-green-500/30 rounded-lg p-6 text-center">
                <input
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={handlePriceFileUpload}
                  className="hidden"
                  id="price-file-upload"
                />
                <label
                  htmlFor="price-file-upload"
                  className="cursor-pointer flex flex-col items-center"
                >
                  <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center mb-3">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <span className="text-green-300 font-bold">
                    {uploadingPrices ? 'ЗАГРУЖАЮ...' : 'ЗАГРУЗИТЬ EXCEL/CSV'}
                  </span>
                  <span className="text-gray-400 text-sm mt-1">
                    Поддерживаются форматы: .xlsx, .xls, .csv
                  </span>
                </label>
              </div>
            </div>
            
            {/* Current Prices */}
            {userPrices.length > 0 && (
              <div className="mb-6">
                <h4 className="text-lg font-bold text-green-300 mb-3">ЗАГРУЖЕННЫЕ ПРАЙСЫ</h4>
                <div className="bg-gray-800/50 rounded-lg max-h-60 overflow-y-auto">
                  <table className="w-full">
                    <thead className="bg-green-600 text-white sticky top-0">
                      <tr>
                        <th className="px-4 py-2 text-left">Продукт</th>
                        <th className="px-4 py-2 text-center">Категория</th>
                        <th className="px-4 py-2 text-right">Цена</th>
                        <th className="px-4 py-2 text-center">Единица</th>
                      </tr>
                    </thead>
                    <tbody>
                      {userPrices.slice(0, 15).map((price, index) => (
                        <tr key={index} className="border-b border-gray-700">
                          <td className="px-4 py-2 text-gray-300">{price.name}</td>
                          <td className="px-4 py-2 text-center">
                            <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                              price.category === 'мясо' ? 'bg-red-600 text-white' :
                              price.category === 'овощи' ? 'bg-green-600 text-white' :
                              price.category === 'молочные' ? 'bg-blue-600 text-white' :
                              price.category === 'рыба' ? 'bg-cyan-600 text-white' :
                              'bg-gray-600 text-white'
                            }`}>
                              {price.category || 'прочее'}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-right text-green-400">{price.price}₽</td>
                          <td className="px-4 py-2 text-center text-gray-400">{price.unit}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {userPrices.length > 15 && (
                    <div className="text-center py-2 text-gray-400 text-sm">
                      ... и еще {userPrices.length - 15} позиций
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* Instructions */}
            <div className="bg-blue-600/20 rounded-lg p-4 mb-6">
              <h4 className="text-blue-300 font-bold mb-2">УМНАЯ ОБРАБОТКА:</h4>
              <ul className="text-blue-200 text-sm space-y-1">
                <li>• <strong>Автоочистка:</strong> удаляет спецсимволы, исправляет сокращения</li>
                <li>• <strong>Категоризация:</strong> автоматически сортирует по типам продуктов</li>
                <li>• <strong>Нормализация:</strong> приводит единицы к стандарту (кг, л, шт)</li>
                <li>• <strong>Формат файла:</strong> A-название, B-цена, C-единица</li>
                <li>• <strong>Точность:</strong> расчет себестоимости до копейки!</li>
              </ul>
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={() => setUserPrices([])}
                disabled={userPrices.length === 0}
                className="flex-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors"
              >
                ОЧИСТИТЬ ВСЕ
              </button>
              <button
                onClick={() => setShowPriceModal(false)}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                ГОТОВО
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Voice Recognition Modal */}
      {showVoiceModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-md w-full mx-4 border border-purple-500/30">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-red-600 rounded-full flex items-center justify-center animate-pulse">
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-purple-300 mb-4">ГОЛОСОВОЙ ВВОД</h3>
              <p className="text-gray-300 mb-6">
                {voiceStatus}
              </p>
              <button
                onClick={() => setShowVoiceModal(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg"
              >
                ОТМЕНА
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Kitchen Equipment Modal */}
      {showEquipmentModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-purple-500/30">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-purple-300">КУХОННОЕ ОБОРУДОВАНИЕ</h3>
              <button
                onClick={() => setShowEquipmentModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="mb-6">
              <p className="text-gray-300 text-sm mb-4">
                Выберите оборудование, которое есть на вашей кухне. AI будет адаптировать рецепты под доступное оборудование.
              </p>
            </div>
            
            {kitchenEquipment.cooking_methods && (
              <div className="mb-6">
                <h4 className="text-lg font-bold text-purple-300 mb-3">Способы приготовления</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {kitchenEquipment.cooking_methods.map(equipment => (
                    <label key={equipment.id} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={userEquipment.includes(equipment.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setUserEquipment([...userEquipment, equipment.id]);
                          } else {
                            setUserEquipment(userEquipment.filter(id => id !== equipment.id));
                          }
                        }}
                        className="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500"
                      />
                      <span className="text-gray-300 text-sm">{equipment.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
            
            {kitchenEquipment.prep_equipment && (
              <div className="mb-6">
                <h4 className="text-lg font-bold text-purple-300 mb-3">Подготовительное оборудование</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {kitchenEquipment.prep_equipment.map(equipment => (
                    <label key={equipment.id} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={userEquipment.includes(equipment.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setUserEquipment([...userEquipment, equipment.id]);
                          } else {
                            setUserEquipment(userEquipment.filter(id => id !== equipment.id));
                          }
                        }}
                        className="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500"
                      />
                      <span className="text-gray-300 text-sm">{equipment.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
            
            {kitchenEquipment.storage && (
              <div className="mb-6">
                <h4 className="text-lg font-bold text-purple-300 mb-3">Хранение</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {kitchenEquipment.storage.map(equipment => (
                    <label key={equipment.id} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={userEquipment.includes(equipment.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setUserEquipment([...userEquipment, equipment.id]);
                          } else {
                            setUserEquipment(userEquipment.filter(id => id !== equipment.id));
                          }
                        }}
                        className="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500"
                      />
                      <span className="text-gray-300 text-sm">{equipment.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
            
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => setShowEquipmentModal(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg"
              >
                ОТМЕНА
              </button>
              <button
                onClick={() => updateKitchenEquipment(userEquipment)}
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg"
              >
                СОХРАНИТЬ
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PRO AI Results Modal */}
      {showProAIModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-purple-500/30">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-purple-300">{proAITitle}</h3>
              <button
                onClick={() => setShowProAIModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="bg-gray-800/50 rounded-lg p-6">
              <div className="text-gray-200 whitespace-pre-line">{proAIResult}</div>
            </div>
            
            <div className="flex justify-end space-x-4 mt-6">
              <button
                onClick={() => navigator.clipboard.writeText(proAIResult)}
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg"
              >
                КОПИРОВАТЬ
              </button>
              <button
                onClick={() => setShowProAIModal(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg"
              >
                ЗАКРЫТЬ
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sales Script Modal */}
      {showSalesScriptModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-purple-500/30">
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-xl">🎭</span>
                </div>
                <h3 className="text-2xl font-bold bg-gradient-to-r from-purple-300 to-pink-300 bg-clip-text text-transparent">
                  СКРИПТ ПРОДАЖ ДЛЯ ОФИЦИАНТА
                </h3>
              </div>
              <button
                onClick={() => setShowSalesScriptModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="bg-gray-800/50 rounded-lg p-6">
              <div className="text-gray-200" dangerouslySetInnerHTML={{__html: formatProAIContent(salesScriptResult)}}></div>
            </div>
            
            <div className="flex justify-end space-x-4 mt-6">
              <button
                onClick={() => navigator.clipboard.writeText(salesScriptResult)}
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg"
              >
                КОПИРОВАТЬ
              </button>
              <button
                onClick={() => setShowSalesScriptModal(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg"
              >
                ЗАКРЫТЬ
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Food Pairing Modal */}
      {showFoodPairingModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-purple-500/30">
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-xl">🍷</span>
                </div>
                <h3 className="text-2xl font-bold bg-gradient-to-r from-purple-300 to-pink-300 bg-clip-text text-transparent">
                  ФУДПЕЙРИНГ И СОЧЕТАНИЯ
                </h3>
              </div>
              <button
                onClick={() => setShowFoodPairingModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="bg-gray-800/50 rounded-lg p-6">
              <div className="text-gray-200" dangerouslySetInnerHTML={{__html: formatProAIContent(foodPairingResult)}}></div>
            </div>
            
            <div className="flex justify-end space-x-4 mt-6">
              <button
                onClick={() => navigator.clipboard.writeText(foodPairingResult)}
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg"
              >
                КОПИРОВАТЬ
              </button>
              <button
                onClick={() => setShowFoodPairingModal(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg"
              >
                ЗАКРЫТЬ
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Photo Tips Modal */}
      {showPhotoTipsModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-purple-500/30">
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-xl">📸</span>
                </div>
                <h3 className="text-2xl font-bold bg-gradient-to-r from-purple-300 to-pink-300 bg-clip-text text-transparent">
                  СОВЕТЫ ПО ФОТОГРАФИИ БЛЮДА
                </h3>
              </div>
              <button
                onClick={() => setShowPhotoTipsModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="bg-gray-800/50 rounded-lg p-6">
              <div className="text-gray-200" dangerouslySetInnerHTML={{__html: formatProAIContent(photoTipsResult)}}></div>
            </div>
            
            <div className="flex justify-end space-x-4 mt-6">
              <button
                onClick={() => navigator.clipboard.writeText(photoTipsResult)}
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg"
              >
                КОПИРОВАТЬ
              </button>
              <button
                onClick={() => setShowPhotoTipsModal(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg"
              >
                ЗАКРЫТЬ
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Animated Loading Modal */}
      {isGenerating && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 rounded-3xl p-10 max-w-md w-full mx-4 border border-purple-500/30 shadow-2xl">
            <div className="text-center">
              {/* Animated Icon */}
              <div className="mb-6 relative">
                <div className="w-20 h-20 mx-auto">
                  <div className="w-full h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full animate-pulse"></div>
                  <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-purple-400 to-pink-400 rounded-full animate-ping opacity-75"></div>
                </div>
              </div>
              
              {/* Loading Message */}
              <div className="mb-8">
                <h3 className="text-xl font-bold text-white mb-2">
                  {loadingType === 'techcard' && 'Генерирую техкарту...'}
                  {loadingType === 'sales' && 'Создаю скрипт продаж...'}
                  {loadingType === 'pairing' && 'Подбираю сочетания...'}
                  {loadingType === 'photo' && 'Готовлю советы по фото...'}
                  {loadingType === 'inspiration' && 'Создаю вдохновение...'}
                </h3>
                <p className="text-purple-300 text-sm animate-pulse">
                  {loadingMessage}
                </p>
              </div>
              
              {/* Progress Bar */}
              <div className="mb-6">
                <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
                  <div 
                    className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all duration-300 ease-out"
                    style={{ width: `${loadingProgress}%` }}
                  ></div>
                </div>
                <div className="text-purple-300 text-sm">
                  {Math.round(loadingProgress)}%
                </div>
              </div>
              
              {/* Fun Animation */}
              <div className="flex justify-center space-x-1">
                {[...Array(3)].map((_, i) => (
                  <div
                    key={i}
                    className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 0.1}s` }}
                  ></div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Inspiration Modal */}
      {showInspirationModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-purple-500/30">
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-xl">🌟</span>
                </div>
                <h3 className="text-2xl font-bold bg-gradient-to-r from-purple-300 to-pink-300 bg-clip-text text-transparent">
                  ВДОХНОВЕНИЕ - ТВИСТ НА БЛЮДО
                </h3>
              </div>
              <button
                onClick={() => setShowInspirationModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-6">
              <div className="bg-gray-800/50 rounded-xl p-6">
                <div className="prose prose-invert max-w-none">
                  <div 
                    className="text-gray-300 leading-relaxed"
                    dangerouslySetInnerHTML={{ 
                      __html: formatProAIContent(inspirationResult)
                    }}
                  />
                </div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-4 mt-8">
              <button
                onClick={async () => {
                  // Создаем новую техкарту из вдохновения и СОХРАНЯЕМ в базу
                  try {
                    // Отправляем запрос на сохранение техкарты
                    const response = await axios.post(`${API}/save-tech-card`, {
                      user_id: currentUser.id,
                      content: inspirationResult,
                      dish_name: inspirationResult.split('\n')[0]?.replace(/\*\*/g, '').replace('Название:', '').trim() || 'Техкарта из вдохновения',
                      city: currentUser.city,
                      is_inspiration: true
                    });
                    
                    // Устанавливаем техкарту и её ID
                    setTechCard(inspirationResult);
                    setCurrentTechCardId(response.data.id);
                    setShowInspirationModal(false);
                    
                    // Парсим новые ингредиенты
                    const lines = inspirationResult.split('\n');
                    const ingredients = [];
                    
                    lines.forEach(line => {
                      if (line.startsWith('- ') && line.includes('₽')) {
                        const parts = line.replace('- ', '').split(' — ');
                        if (parts.length >= 2) {
                          const name = parts[0].trim();
                          const quantity = parts[1].trim();
                          const priceMatch = line.match(/~(\d+(?:\.\d+)?)\s*₽/);
                          const price = priceMatch ? priceMatch[1] : '10';
                          
                          ingredients.push({
                            id: Date.now() + Math.random(),
                            name: name,
                            quantity: quantity.replace(/\s*г.*/, ''),
                            unit: 'г',
                            totalPrice: price
                          });
                        }
                      }
                    });
                    
                    setCurrentIngredients(ingredients);
                    alert('Новая техкарта создана на основе вдохновения и сохранена в историю! 🌟');
                    
                  } catch (error) {
                    console.error('Error saving inspiration tech card:', error);
                    // Fallback - просто устанавливаем техкарту без сохранения
                    setTechCard(inspirationResult);
                    setShowInspirationModal(false);
                    
                    // Парсим ингредиенты
                    const lines = inspirationResult.split('\n');
                    const ingredients = [];
                    
                    lines.forEach(line => {
                      if (line.startsWith('- ') && line.includes('₽')) {
                        const parts = line.replace('- ', '').split(' — ');
                        if (parts.length >= 2) {
                          const name = parts[0].trim();
                          const quantity = parts[1].trim();
                          const priceMatch = line.match(/~(\d+(?:\.\d+)?)\s*₽/);
                          const price = priceMatch ? priceMatch[1] : '10';
                          
                          ingredients.push({
                            id: Date.now() + Math.random(),
                            name: name,
                            quantity: quantity.replace(/\s*г.*/, ''),
                            unit: 'г',
                            totalPrice: price
                          });
                        }
                      }
                    });
                    
                    setCurrentIngredients(ingredients);
                    alert('Новая техкарта создана на основе вдохновения! 🌟');
                  }
                }}
                className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-6 py-2 rounded-lg"
              >
                СОЗДАТЬ ТЕХКАРТУ
              </button>
              <button
                onClick={() => navigator.clipboard.writeText(inspirationResult)}
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg"
              >
                КОПИРОВАТЬ
              </button>
              <button
                onClick={() => setShowInspirationModal(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg"
              >
                ЗАКРЫТЬ
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Registration Modal */}
      {showRegistrationModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl p-8 max-w-md w-full mx-4 border border-purple-500/30">
            <div className="text-center mb-6">
              <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full flex items-center justify-center">
                <span className="text-2xl">🚀</span>
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">Добро пожаловать в Receptor Pro!</h3>
              <p className="text-gray-300">Начните создавать профессиональные техкарты прямо сейчас</p>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-purple-300 text-sm font-bold mb-2">Email</label>
                <input
                  type="email"
                  value={registrationData.email}
                  onChange={(e) => setRegistrationData({...registrationData, email: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:border-purple-500 focus:outline-none"
                  placeholder="chef@restaurant.com"
                />
              </div>
              
              <div>
                <label className="block text-purple-300 text-sm font-bold mb-2">Имя</label>
                <input
                  type="text"
                  value={registrationData.name}
                  onChange={(e) => setRegistrationData({...registrationData, name: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:border-purple-500 focus:outline-none"
                  placeholder="Ваше имя"
                />
              </div>
              
              <div>
                <label className="block text-purple-300 text-sm font-bold mb-2">Город</label>
                <select
                  value={registrationData.city}
                  onChange={(e) => setRegistrationData({...registrationData, city: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:border-purple-500 focus:outline-none"
                >
                  <option value="">Выберите город</option>
                  <option value="moskva">Москва</option>
                  <option value="spb">Санкт-Петербург</option>
                  <option value="novosibirsk">Новосибирск</option>
                  <option value="ekaterinburg">Екатеринбург</option>
                  <option value="kazan">Казань</option>
                </select>
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={async () => {
                  if (registrationData.email && registrationData.name && registrationData.city) {
                    try {
                      const response = await axios.post(`${API}/register`, registrationData);
                      localStorage.setItem('receptor_user', JSON.stringify(response.data));
                      setCurrentUser(response.data);
                      setShowRegistrationModal(false);
                    } catch (error) {
                      console.error('Registration error:', error);
                      alert('Ошибка регистрации');
                    }
                  }
                }}
                className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-6 py-3 rounded-lg font-bold transition-colors"
              >
                Начать создавать
              </button>
              <button
                onClick={() => setShowRegistrationModal(false)}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-bold transition-colors"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;