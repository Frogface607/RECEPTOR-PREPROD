import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;  // Backend routes already include /api prefix

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
  
  // Improve dish modal state
  const [showImproveDishModal, setShowImproveDishModal] = useState(false);
  const [improveDishResult, setImproveDishResult] = useState('');
  const [isImprovingDish, setIsImprovingDish] = useState(false);
  
  // Laboratory modal state
  const [showLaboratoryModal, setShowLaboratoryModal] = useState(false);
  const [laboratoryResult, setLaboratoryResult] = useState(null);
  const [isExperimenting, setIsExperimenting] = useState(false);
  const [experimentType, setExperimentType] = useState('random');
  
  // Venue Profile states
  const [showVenueProfileModal, setShowVenueProfileModal] = useState(false);
  const [venueProfile, setVenueProfile] = useState({});
  const [venueTypes, setVenueTypes] = useState({});
  const [cuisineTypes, setCuisineTypes] = useState({});
  const [averageCheckCategories, setAverageCheckCategories] = useState({});
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);
  const [profileStep, setProfileStep] = useState(1); // For wizard steps

  // Dashboard states
  const [currentView, setCurrentView] = useState('create'); // 'dashboard', 'create', 'menu-generator', 'my-venue'
  const [dashboardStats, setDashboardStats] = useState({
    totalTechCards: 0,
    totalMenus: 0,
    tokensUsed: 0,
    thisMonthCards: 0
  });

  // Menu Generator states
  const [showMenuWizard, setShowMenuWizard] = useState(false);
  const [menuType, setMenuType] = useState('');
  const [generatedMenu, setGeneratedMenu] = useState(null);
  const [menuWizardStep, setMenuWizardStep] = useState(1);
  const [menuProfile, setMenuProfile] = useState({
    // Basic Info (Step 1)
    menuType: '',
    dishCount: 12,
    averageCheckMin: 500,
    averageCheckMax: 1500,
    region: 'moskva',
    
    // Menu Constructor - NEW!
    useConstructor: false,
    categories: {
      salads: 2,
      appetizers: 3,
      soups: 2,
      main_dishes: 4,
      desserts: 2,
      beverages: 1
    },
    
    // Cuisine & Style (Step 2)
    cuisineStyle: '',
    cuisineInfluences: [],
    menuStyle: 'classic', // classic, modern, fusion, street
    
    // Business Details (Step 3)
    // Enhanced audience profiling (Step 3)
    audienceAges: {
      '18-25': 0,
      '26-35': 50,
      '36-50': 30,
      '50+': 20
    },
    audienceOccupations: [],
    regionDetails: {
      type: 'capital', // capital, province, resort
      geography: 'plains', // plains, sea, mountains
      climate: 'temperate'
    },
    menuGoals: [],
    specialRequirements: [],
    dietaryOptions: [],
    
    // Technical Details (Step 4)
    kitchenCapabilities: [],
    staffSkillLevel: 'medium',
    preparationTime: 'medium',
    ingredientBudget: 'medium',
    
    // Free Form (Step 5)
    menuDescription: '',
    expectations: '',
    additionalNotes: ''
  });

  // Mass Tech Card Generation states
  const [isGeneratingMassCards, setIsGeneratingMassCards] = useState(false);
  const [massGenerationProgress, setMassGenerationProgress] = useState({
    total: 0,
    completed: 0,
    current: '',
    results: []
  });
  const [showMassGenerationModal, setShowMassGenerationModal] = useState(false);

  // Menu Generation Modal states (Simplified!)
  const [showMenuGenerationModal, setShowMenuGenerationModal] = useState(false);
  const [menuGenerationProgress, setMenuGenerationProgress] = useState(0);

  // Simplified Menu Creation states - NEW APPROACH!
  const [showSimpleMenuModal, setShowSimpleMenuModal] = useState(false);
  const [simpleMenuData, setSimpleMenuData] = useState({
    menuType: '', // full, seasonal, business_lunch, event
    expectations: '', // Free-form user input
    dishCount: 0, // Will be set from venue profile default
    customCategories: null, // Optional override
    projectId: null // Link to menu project
  });
  const [isGeneratingSimpleMenu, setIsGeneratingSimpleMenu] = useState(false);

  // Menu Projects System states
  const [showProjectsModal, setShowProjectsModal] = useState(false);
  const [menuProjects, setMenuProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [showCreateProjectModal, setShowCreateProjectModal] = useState(false);
  const [newProjectData, setNewProjectData] = useState({
    projectName: '',
    description: '',
    projectType: '',
    venueType: null
  });
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [isLoadingProjects, setIsLoadingProjects] = useState(false);

  // Enhanced tech card context for menu dishes
  const [dishContext, setDishContext] = useState(null);

  // Menu Tech Cards View states
  const [showMenuTechCards, setShowMenuTechCards] = useState(false);
  const [menuTechCards, setMenuTechCards] = useState(null);
  const [isLoadingMenuTechCards, setIsLoadingMenuTechCards] = useState(false);
  
  // Replace Dish states
  const [showReplaceDishModal, setShowReplaceDishModal] = useState(false);
  const [replacingDishData, setReplacingDishData] = useState(null); // {dish_name, category, menu_id}
  const [replacementPrompt, setReplacementPrompt] = useState('');
  const [isReplacingDish, setIsReplacingDish] = useState(false);

  // Menu View Mode states
  const [menuViewMode, setMenuViewMode] = useState('customer'); // 'customer' or 'business'

  // Tips and lifehacks for mass generation loading
  const [currentTipIndex, setCurrentTipIndex] = useState(0);
  const receptionTips = [
    {
      title: "💡 Редактирование техкарт",
      text: "После создания вы можете отредактировать любую техкарту - изменить ингредиенты, порции или способ приготовления",
      icon: "✏️"
    },
    {
      title: "📊 Анализ себестоимости", 
      text: "Техкарты автоматически рассчитывают себестоимость. Используйте эти данные для установки правильных цен",
      icon: "💰"
    },
    {
      title: "🔄 Обновление цен",
      text: "Регулярно обновляйте прайс-листы ингредиентов в настройках для точности расчетов",
      icon: "📈"
    },
    {
      title: "🏢 Профиль заведения",
      text: "Настройте профиль заведения для более точных техкарт - тип кухни, средний чек, целевая аудитория",
      icon: "⚙️"
    },
    {
      title: "📋 Экспорт в PDF",
      text: "Все техкарты можно экспортировать в PDF без цен - идеально для передачи персоналу",
      icon: "📄"
    },
    {
      title: "🔍 Поиск по истории",
      text: "Используйте поиск в разделе 'История' чтобы быстро найти нужные техкарты",
      icon: "🔎"
    },
    {
      title: "⚡ Горячие клавиши",
      text: "Ctrl+Enter для быстрой генерации, Ctrl+S для сохранения изменений",
      icon: "⌨️"
    },
    {
      title: "🎯 Сезонные меню",
      text: "Создавайте отдельные техкарты для сезонных блюд - это поможет контролировать ротацию меню",
      icon: "🍂"
    }
  ];

  // Tips for menu generation (NEW!)
  const [currentMenuTipIndex, setCurrentMenuTipIndex] = useState(0);
  const menuGenerationTips = [
    {
      title: "🎯 Конструктор меню",
      text: "Используйте конструктор для точного контроля количества блюд в каждой категории - 10 горячих, 5 салатов, 3 десерта",
      icon: "🛠️"
    },
    {
      title: "🍽️ Баланс категорий",
      text: "Оптимальное соотношение: 30% горячие блюда, 25% закуски, 20% салаты, 15% супы, 10% десерты",
      icon: "⚖️"
    },
    {
      title: "💰 Ценовая стратегия",
      text: "Блюда с высокой маржинальностью размещайте в начале категорий - гости чаще выбирают первые позиции",
      icon: "💎"
    },
    {
      title: "🏷️ Психология названий",
      text: "Описательные названия (например, 'Сочный стейк рибай с трюфельным маслом') увеличивают продажи на 27%",
      icon: "🧠"
    },
    {
      title: "🌱 Сезонность ингредиентов",
      text: "Учитывайте сезонность - летом акцент на свежие овощи, зимой на сытные горячие блюда",
      icon: "📅"
    },
    {
      title: "👨‍🍳 Навыки персонала",
      text: "Адаптируйте сложность блюд под команду - сложные техники только при высоком уровне поваров",
      icon: "⭐"
    },
    {
      title: "📦 Оптимизация закупок",
      text: "ИИ автоматически находит общие ингредиенты для экономии - одни продукты используются в разных блюдах",
      icon: "📋"
    },
    {
      title: "🎨 Визуальная подача",
      text: "Современные гости 'едят глазами' - яркие, контрастные блюда привлекают больше внимания",
      icon: "🌈"
    },
    {
      title: "⏱️ Время приготовления",
      text: "Учитывайте пиковые часы - в меню должно быть 70% быстрых блюд (до 20 минут) для быстрой подачи",
      icon: "⚡"
    },
    {
      title: "🔄 A/B тестирование",
      text: "Создавайте несколько вариантов меню и тестируйте - разные названия и описания влияют на выбор гостей",
      icon: "🧪"
    },
    {
      title: "🌍 Региональные предпочтения",
      text: "Учитывайте местные вкусы - в Москве популярны авторские блюда, в регионах - традиционные",
      icon: "🗺️"
    },
    {
      title: "💡 Уникальные фишки",
      text: "Добавьте 1-2 signature блюда заведения - это создает запоминающийся образ и повышает лояльность",
      icon: "⭐"
    },
    {
      title: "📊 Анализ конкурентов",
      text: "Изучайте меню успешных заведений вашего сегмента - адаптируйте лучшие идеи под свою концепцию",
      icon: "🔍"
    },
    {
      title: "🍷 Сочетания с напитками",
      text: "Продумывайте wine pairing - правильные сочетания увеличивают средний чек на 15-20%",
      icon: "🍾"
    },
    {
      title: "📱 Социальные сети",
      text: "Создавайте 'инстаграмные' блюда - красивая подача привлекает молодую аудиторию и создает buzz",
      icon: "📸"
    }
  ];

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
      menu: [
        "🎯 Анализирую ваши пожелания и профиль заведения...",
        "🧠 Изучаю целевую аудиторию и предпочтения...",
        "🌍 Исследую тренды современной гастрономии...",
        "⚖️ Балансирую вкусы и ценовые категории...",
        "🔥 Подбираю оптимальные техники приготовления...",
        "📊 Рассчитываю маржинальность блюд...",
        "🎨 Создаю гармоничную структуру меню...",
        "💡 Оптимизирую закупки и ингредиенты...",
        "🏆 Добавляю signature блюда заведения...",
        "✨ Финальные штрихи - меню почти готово!"
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
  
  // Loading message states
  const [currentLoadingMessage, setCurrentLoadingMessage] = useState('');

  // Laboratory loading messages
  const getLaboratoryLoadingMessage = () => {
    const messages = [
      "🧪 Разогреваем молекулярный реактор...",
      "⚗️ Смешиваем невозможное с вкусным...", 
      "🔬 Анализируем вкусовые профили...",
      "🧬 Создаем кулинарную мутацию...",
      "⚡ Запускаем цепную реакцию вкуса...",
      "🌡️ Контролируем температуру эксперимента...",
      "🎭 Готовим сюрприз для ваших рецепторов...",
      "🚀 Отправляем блюдо в параллельную вселенную...",
      "🎪 Цирковые трюки с едой в процессе...",
      "🎨 Рисуем съедобные шедевры...",
      "💫 Призываем кулинарную магию...",
      "🎯 Целимся в центр вкуса...",
      "🌪️ Создаем вкусовой торнадо...",
      "🎵 Сочиняем симфонию ароматов...",
      "🎲 Бросаем кости судьбы и специй..."
    ];
    return messages[Math.floor(Math.random() * messages.length)];
  };

  // Improve dish loading messages  
  const getImproveDishLoadingMessage = () => {
    const messages = [
      "⚡ Прокачиваем ваше блюдо до версии 2.0...",
      "🔧 Апгрейд вкуса в процессе...",
      "💎 Полируем каждый ингредиент...",
      "🎯 Настраиваем идеальный баланс...",
      "🚀 Выводим блюдо на новый уровень...",
      "⭐ Добавляем звездочки Мишлен...",
      "🎨 Превращаем блюдо в искусство...",
      "🔥 Зажигаем кулинарный движок...",
      "💫 Применяем секретные техники...",
      "🎪 Показываем фокусы с едой...",
      "⚗️ Варим зелье вкуса...",
      "🎵 Дирижируем оркестром ароматов...",
      "🏆 Готовим блюдо-чемпион...",
      "✨ Добавляем щепотку волшебства...",
      "🎭 Режиссируем вкусовую драму..."
    ];
    return messages[Math.floor(Math.random() * messages.length)];
  };

  // Finances loading messages
  const getFinancesLoadingMessage = () => {
    const messages = [
      "💰 Подсчитываем каждую копейку...",
      "📊 Анализируем рыночные цены...",
      "🔍 Ищем скрытые возможности экономии...",
      "📈 Прогнозируем прибыльность...",
      "💡 Генерируем стратегии роста...",
      "🎯 Вычисляем точку безубыточности...",
      "📋 Составляем финансовую карту...",
      "💎 Оцениваем потенциал блюда...",
      "⚖️ Взвешиваем все за и против...",
      "🎰 Просчитываем шансы на успех...",
      "🔮 Предсказываем финансовое будущее...",
      "📝 Пишем бизнес-план...",
      "🏦 Консультируемся с экспертами...",
      "💼 Составляем отчет для инвесторов...",
      "🎪 Жонглируем цифрами..."
    ];
    return messages[Math.floor(Math.random() * messages.length)];
  };

  // Update loading message and progress
  React.useEffect(() => {
    let messageInterval, progressInterval;
    
    if (isAnalyzingFinances || isExperimenting || isImprovingDish) {
      // Determine loading time
      const loadingTime = isAnalyzingFinances ? 10000 : isExperimenting ? 8000 : 6000; // ms
      const progressStep = 100 / (loadingTime / 100); // Progress per 100ms
      
      let currentProgress = 0;
      setLoadingProgress(0);
      
      // Update progress every 100ms
      progressInterval = setInterval(() => {
        currentProgress += progressStep;
        if (currentProgress >= 100) {
          currentProgress = 100;
          clearInterval(progressInterval);
        }
        setLoadingProgress(Math.round(currentProgress));
      }, 100);
      
      // Update message every 2 seconds
      const updateMessage = () => {
        if (isAnalyzingFinances) {
          setCurrentLoadingMessage(getFinancesLoadingMessage());
        } else if (isExperimenting) {
          setCurrentLoadingMessage(getLaboratoryLoadingMessage());
        } else if (isImprovingDish) {
          setCurrentLoadingMessage(getImproveDishLoadingMessage());
        }
      };
      
      updateMessage(); // Set initial message
      messageInterval = setInterval(updateMessage, 2000);
    } else {
      // Reset when not loading
      setLoadingProgress(0);
      setCurrentLoadingMessage('');
    }
    
    return () => {
      if (messageInterval) clearInterval(messageInterval);
      if (progressInterval) clearInterval(progressInterval);
    };
  }, [isAnalyzingFinances, isExperimenting, isImprovingDish]);

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
    const tips = extractSection(/\*\*Особенности и советы от шефа:\*\*\s*(.*?)(?=\n\n|\*\*|$)/s) || 
                 extractSection(/\*\*СОВЕТЫ ОТ ШЕФА\*\*\s*(.*?)(?=\n\n|\*\*|$)/s) ||
                 extractSection(/\*\*Советы от шефа:\*\*\s*(.*?)(?=\n\n|\*\*|$)/s);
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
            <div className="space-y-3">
              {storage.split('\n').filter(line => line.trim()).map((line, index) => {
                const trimmedLine = line.trim();
                if (trimmedLine.startsWith('- ')) {
                  return (
                    <div key={index} className="flex items-start space-x-2">
                      <span className="text-purple-400 mt-1">•</span>
                      <EditableText 
                        field={`storage_item_${index}`} 
                        value={trimmedLine.substring(2)} 
                        className="text-gray-300 leading-relaxed flex-1" 
                      />
                    </div>
                  );
                } else {
                  return (
                    <div key={index}>
                      <EditableText 
                        field={`storage_line_${index}`} 
                        value={trimmedLine} 
                        className="text-gray-300 leading-relaxed block" 
                      />
                    </div>
                  );
                }
              })}
            </div>
          </div>
        )}

        {/* СОВЕТЫ ОТ ШЕФА */}
        {tips && (
          <div className="bg-gradient-to-r from-orange-900/20 to-red-900/20 rounded-lg p-4">
            <h3 className="text-xl font-bold text-orange-300 mb-4">СОВЕТЫ ОТ ШЕФА</h3>
            <div className="space-y-3">
              {tips.split('\n').filter(line => line.trim()).map((line, index) => {
                const trimmedLine = line.trim();
                if (trimmedLine.startsWith('- ')) {
                  return (
                    <div key={index} className="flex items-start space-x-2">
                      <span className="text-orange-400 mt-1">💡</span>
                      <EditableText 
                        field={`tips_item_${index}`} 
                        value={trimmedLine.substring(2)} 
                        className="text-gray-300 leading-relaxed flex-1" 
                      />
                    </div>
                  );
                } else if (trimmedLine.startsWith('*') && trimmedLine.endsWith('*')) {
                  return (
                    <div key={index} className="bg-orange-900/30 rounded-lg p-3 border-l-4 border-orange-400">
                      <EditableText 
                        field={`tips_highlight_${index}`} 
                        value={trimmedLine.slice(1, -1)} 
                        className="text-orange-200 font-semibold leading-relaxed" 
                      />
                    </div>
                  );
                } else {
                  return (
                    <div key={index}>
                      <EditableText 
                        field={`tips_line_${index}`} 
                        value={trimmedLine} 
                        className="text-gray-300 leading-relaxed block" 
                      />
                    </div>
                  );
                }
              })}
            </div>
          </div>
        )}

        {/* РЕКОМЕНДАЦИЯ ПОДАЧИ */}
        {serving && (
          <div className="bg-pink-900/20 rounded-lg p-4">
            <h3 className="text-xl font-bold text-pink-300 mb-2 flex items-center gap-2">
              {getServingIcon(venueProfile.venue_type)}
              ПОДАЧА
            </h3>
            <div className="text-gray-300 leading-relaxed">
              <EditableText field="serving" value={serving} className="text-gray-300 leading-relaxed" multiline={true} />
            </div>
            {venueProfile.venue_type && (
              <div className="mt-3 text-xs text-pink-200 bg-pink-900/30 rounded px-3 py-1">
                Адаптировано для: {venueTypes[venueProfile.venue_type]?.name}
              </div>
            )}
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
      // Fallback cities if API fails
      const fallbackCities = [
        { code: 'moskva', name: 'Москва' },
        { code: 'spb', name: 'Санкт-Петербург' },
        { code: 'novosibirsk', name: 'Новосибирск' },
        { code: 'yekaterinburg', name: 'Екатеринбург' },
        { code: 'kazan', name: 'Казань' },
        { code: 'nizhniy-novgorod', name: 'Нижний Новгород' }
      ];
      setCities(fallbackCities);
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

  // Venue Profile API functions
  const fetchVenueTypes = async () => {
    // Immediate fallback to prevent loading issues
    const fallbackVenueTypes = {
      "fine_dining": {
        "name": "Fine Dining Ресторан",
        "description": "Высококлассный ресторан с изысканной кухней",
        "complexity_level": "high",
        "price_multiplier": 2.5
      },
      "family_restaurant": {
        "name": "Семейный ресторан",
        "description": "Уютное заведение для всей семьи",
        "complexity_level": "medium",
        "price_multiplier": 1.5
      },
      "cafe": {
        "name": "Кафе",
        "description": "Непринужденная атмосфера, легкие блюда",
        "complexity_level": "low",
        "price_multiplier": 1.2
      },
      "bar_pub": {
        "name": "Бар/Паб",
        "description": "Барная еда и напитки",
        "complexity_level": "low", 
        "price_multiplier": 1.3
      },
      "fast_food": {
        "name": "Фаст-фуд",
        "description": "Быстрое питание",
        "complexity_level": "low",
        "price_multiplier": 1.0
      },
      "food_truck": {
        "name": "Фуд-трак",
        "description": "Мобильная точка питания",
        "complexity_level": "low",
        "price_multiplier": 1.1
      },
      "bakery_cafe": {
        "name": "Кафе-пекарня",
        "description": "Свежая выпечка и кофе",
        "complexity_level": "medium",
        "price_multiplier": 1.3
      },
      "buffet": {
        "name": "Буфет",
        "description": "Шведский стол",
        "complexity_level": "medium",
        "price_multiplier": 1.4
      }
    };

    // Set fallback immediately to prevent loading state
    setVenueTypes(fallbackVenueTypes);
    
    try {
      console.log('Fetching venue types from:', `${API}/venue-types`);
      
      // Try to get data from API with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
      
      const response = await axios.get(`${API}/venue-types`, {
        signal: controller.signal,
        timeout: 5000
      });
      
      clearTimeout(timeoutId);
      
      if (response.data && Object.keys(response.data).length > 0) {
        console.log('Venue types loaded from API:', response.data);
        setVenueTypes(response.data);
      } else {
        console.log('API returned empty data, using fallback');
      }
    } catch (error) {
      console.error('Error fetching venue types:', error);
      console.log('Using fallback venue types due to API error');
      // Fallback is already set above
    }
  };

  const getServingIcon = (venueType) => {
    const icons = {
      'fine_dining': '🍽️',
      'food_truck': '📦',
      'street_food': '🥡',
      'bar_pub': '🍺',
      'night_club': '🍸',
      'kids_cafe': '🧸',
      'coffee_shop': '☕',
      'canteen': '🍽️',
      'fast_food': '🍟',
      'bakery_cafe': '🥐',
      'buffet': '🍛',
      'cafe': '☕',
      'family_restaurant': '🍽️'
    };
    return icons[venueType] || '🍽️';
  };

  const fetchCuisineTypes = async () => {
    try {
      const response = await axios.get(`${API}/cuisine-types`);
      setCuisineTypes(response.data);
    } catch (error) {
      console.error('Error fetching cuisine types:', error);
    }
  };

  const fetchAverageCheckCategories = async () => {
    try {
      const response = await axios.get(`${API}/average-check-categories`);
      setAverageCheckCategories(response.data);
    } catch (error) {
      console.error('Error fetching average check categories:', error);
    }
  };

  const fetchVenueProfile = async () => {
    if (!currentUser?.id) return;
    try {
      const response = await axios.get(`${API}/venue-profile/${currentUser.id}`);
      setVenueProfile(response.data);
    } catch (error) {
      console.error('Error fetching venue profile:', error);
    }
  };

  const updateVenueProfile = async (profileData) => {
    if (!currentUser?.id) return;
    
    setIsUpdatingProfile(true);
    try {
      const response = await axios.post(`${API}/update-venue-profile/${currentUser.id}`, profileData);
      
      if (response.data.success) {
        setVenueProfile(prev => ({ ...prev, ...profileData }));
        alert('Профиль заведения обновлен успешно!');
        return true;
      }
    } catch (error) {
      console.error('Error updating venue profile:', error);
      alert('Ошибка при обновлении профиля: ' + (error.response?.data?.detail || error.message));
      return false;
    } finally {
      setIsUpdatingProfile(false);
    }
    return false;
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
    setLoadingType('finances');
    setLoadingMessage(getFinancesLoadingMessage());
    setLoadingProgress(0);
    
    const progressInterval = simulateProgress((progress, message) => {
      setLoadingProgress(progress);
      if (progress % 15 === 0) { // Меняем сообщение каждые 15%
        setLoadingMessage(getFinancesLoadingMessage());
      }
    }, 10000); // 10 секунд для детального анализа
    
    try {
      const response = await axios.post(`${API}/analyze-finances`, {
        user_id: currentUser.id,
        tech_card: techCard
      });
      
      setFinancesResult(response.data.analysis);
      
      // Завершаем анимацию
      clearInterval(progressInterval);
      setLoadingProgress(100);
      setLoadingMessage('💼 Финансовый анализ готов!');
      
      setTimeout(() => {
        setIsAnalyzingFinances(false);
        setLoadingProgress(0);
        setLoadingMessage('');
        setLoadingType('');
        setShowFinancesModal(true);
      }, 2000);
      
    } catch (error) {
      console.error('Error analyzing finances:', error);
      clearInterval(progressInterval);
      setIsAnalyzingFinances(false);
      setLoadingProgress(0);
      setLoadingMessage('');
      setLoadingType('');
      alert('Ошибка при анализе финансов: ' + (error.response?.data?.detail || error.message));
    }
  };

  const improveDish = async () => {
    if (!techCard || !currentUser?.id) return;
    
    setIsImprovingDish(true);
    setLoadingType('improve');
    setLoadingMessage(getImproveDishLoadingMessage());
    setLoadingProgress(0);
    
    const progressInterval = simulateProgress('improve', 6000); // 6 секунд загрузки
    
    try {
      const response = await axios.post(`${API}/improve-dish`, {
        user_id: currentUser.id,
        tech_card: techCard
      });
      
      setImproveDishResult(response.data.improved_dish);
      
      // Завершаем анимацию
      clearInterval(progressInterval);
      setLoadingProgress(100);
      setLoadingMessage('✨ Улучшение блюда готово!');
      
      setTimeout(() => {
        setIsImprovingDish(false);
        setLoadingProgress(0);
        setLoadingMessage('');
        setLoadingType('');
        setShowImproveDishModal(true);
      }, 2000);
      
    } catch (error) {
      console.error('Error improving dish:', error);
      clearInterval(progressInterval);
      setIsImprovingDish(false);
      setLoadingProgress(0);
      setLoadingMessage('');
      setLoadingType('');
      alert('Ошибка при улучшении блюда: ' + (error.response?.data?.detail || error.message));
    }
  };

  const conductExperiment = async () => {
    if (!currentUser?.id) return;

    setIsExperimenting(true);
    setLoadingType('laboratory');
    setLoadingMessage(getLaboratoryLoadingMessage());
    setLoadingProgress(0);
    
    const progressInterval = simulateProgress('laboratory', 8000);
    
    // Извлекаем название блюда из текущей техкарты (если есть)
    let baseDish = '';
    if (techCard) {
      const titleMatch = techCard.match(/\*\*Название:\*\*\s*(.*?)(?=\n|$)/);
      if (titleMatch) {
        baseDish = titleMatch[1].trim();
      }
    }
    
    try {
      const response = await axios.post(`${API}/laboratory-experiment`, {
        user_id: currentUser.id,
        experiment_type: experimentType,
        base_dish: baseDish
      });
      
      setLaboratoryResult(response.data);
      
      // Завершаем анимацию
      clearInterval(progressInterval);
      setLoadingProgress(100);
      setLoadingMessage('🧪 Эксперимент завершен!');
      
      setTimeout(() => {
        setIsExperimenting(false);
        setLoadingProgress(0);
        setLoadingMessage('');
        setLoadingType('');
        setShowLaboratoryModal(true);
      }, 2000);
      
    } catch (error) {
      console.error('Error conducting experiment:', error);
      clearInterval(progressInterval);
      setIsExperimenting(false);
      setLoadingProgress(0);
      setLoadingMessage('');
      setLoadingType('');
      alert('Ошибка при проведении эксперимента: ' + (error.response?.data?.detail || error.message));
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

      // Add enhanced context if available (from menu dishes)
      if (dishContext) {
        requestData.dish_description = dishContext.description;
        requestData.main_ingredients = dishContext.main_ingredients;
        requestData.category = dishContext.category;
        requestData.estimated_cost = dishContext.estimated_cost;
        requestData.estimated_price = dishContext.estimated_price;
        requestData.difficulty = dishContext.difficulty;
        requestData.cook_time = dishContext.cook_time;
        
        // Clear context after use
        setDishContext(null);
      }
      
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
      
      // Update dashboard stats
      const historyData = response.data.history || [];
      const totalTechCards = historyData.length;
      const totalMenus = historyData.filter(item => item.is_menu).length;
      const thisMonth = new Date();
      const thisMonthCards = historyData.filter(item => {
        const itemDate = new Date(item.created_at);
        return itemDate.getMonth() === thisMonth.getMonth() && 
               itemDate.getFullYear() === thisMonth.getFullYear();
      }).length;
      
      setDashboardStats({
        totalTechCards,
        totalMenus,
        tokensUsed: currentUser.monthly_tech_cards_used || 0,
        thisMonthCards
      });
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
        // Улучшенная логика для удаления цен с учетом различных форматов (граммы, штуки и т.д.)
        let cleanIngredient = cleanLine.replace('- ', '')
          .replace(/\s*—\s*~\d+(?:\.\d+)?\s*₽\s*$/g, '') // ~цена₽ в конце
          .replace(/\s*—\s*\d+(?:\.\d+)?\s*₽\s*$/g, '') // цена₽ в конце
          .replace(/\s*\(\d+(?:\.\d+)?\s*₽[^)]*\)/g, '') // (цена₽) в скобках
          .replace(/\s*\d+(?:\.\d+)?\s*₽(?:\s*за\s*[^,\n]*)?/g, '') // цена₽ за единицу
          .replace(/\s*\d+(?:\.\d+)?\s*руб\.?(?:\s*за\s*[^,\n]*)?/g, '') // цена руб за единицу
          .trim();
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

  const generateMenu = async () => {
    try {
      setIsGenerating(true);
      setShowMenuGenerationModal(true);
      setCurrentMenuTipIndex(0);
      setMenuGenerationProgress(0);
      
      // Start progress simulation and tips cycling
      const progressInterval = setInterval(() => {
        setMenuGenerationProgress(prev => Math.min(prev + Math.random() * 15, 90));
      }, 2000);
      
      const tipInterval = setInterval(() => {
        setCurrentMenuTipIndex(prev => (prev + 1) % menuGenerationTips.length);
      }, 4000); // Change tip every 4 seconds
      
      const menuRequest = {
        user_id: currentUser.id,
        menu_profile: menuProfile,
        venue_profile: venueProfile
      };

      console.log('Generating menu with profile:', menuRequest);
      
      const response = await axios.post(`${API}/generate-menu`, menuRequest);
      
      // Clear intervals
      clearInterval(progressInterval);
      clearInterval(tipInterval);
      
      if (response.data.success) {
        setMenuGenerationProgress(100);
        setTimeout(() => {
          setGeneratedMenu({...response.data.menu, menu_id: response.data.menu_id});
          setShowMenuWizard(false);
          setShowMenuGenerationModal(false);
          alert('Меню успешно создано!');
        }, 1000);
      } else {
        setShowMenuGenerationModal(false);
        throw new Error(response.data.error || 'Failed to generate menu');
      }
    } catch (error) {
      console.error('Error generating menu:', error);
      setShowMenuGenerationModal(false);
      alert('Ошибка при создании меню. Попробуйте еще раз.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Mass Tech Card Generation function
  const generateMassTechCards = async () => {
    if (!generatedMenu?.menu_id) {
      alert('Сначала создайте меню!');
      console.error('generatedMenu:', generatedMenu);
      return;
    }

    const totalDishes = (generatedMenu.categories || []).reduce((total, cat) => total + (cat.dishes?.length || 0), 0);
    
    if (totalDishes === 0) {
      alert('Нет блюд для генерации техкарт!');
      return;
    }

    if (!window.confirm(`Создать техкарты для всех ${totalDishes} блюд из меню? Это может занять несколько минут.`)) {
      return;
    }

    let tipInterval = null; // Declare outside try block

    try {
      setIsGeneratingMassCards(true);
      setShowMassGenerationModal(true);
      setCurrentTipIndex(0);
      
      // Initialize progress with tips cycling
      setMassGenerationProgress({
        total: totalDishes,
        completed: 0,
        current: 'Подготовка к генерации...',
        results: []
      });

      // Start tips cycling
      tipInterval = setInterval(() => {
        setCurrentTipIndex(prev => (prev + 1) % receptionTips.length);
      }, 4000); // Change tip every 4 seconds

      const massRequest = {
        user_id: currentUser.id,
        menu_id: generatedMenu.menu_id
      };

      console.log('Starting mass tech card generation:', massRequest);
      console.log('Current user:', currentUser);
      console.log('Generated menu:', generatedMenu);
      
      const response = await axios.post(`${API}/generate-mass-tech-cards`, massRequest, {
        timeout: 300000 // 5 minutes timeout for mass generation
      });
      
      // Clear tips interval
      if (tipInterval) clearInterval(tipInterval);
      
      if (response.data.success) {
        setMassGenerationProgress({
          total: totalDishes,
          completed: response.data.generated_count,
          current: 'Генерация завершена!',
          results: response.data.tech_cards
        });

        // Update user history to refresh counts
        await fetchUserHistory();
        
        setTimeout(() => {
          setShowMassGenerationModal(false);
          alert(`Массовая генерация завершена! Создано ${response.data.generated_count} из ${totalDishes} техкарт.`);
          
          if (response.data.failed_count > 0) {
            console.log('Failed generations:', response.data.failed_generations);
          }
        }, 2000);
      } else {
        if (tipInterval) clearInterval(tipInterval);
        throw new Error(response.data.error || 'Failed to generate mass tech cards');
      }
    } catch (error) {
      console.error('Error generating mass tech cards:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      
      // Clear tips interval
      if (tipInterval) clearInterval(tipInterval);
      setShowMassGenerationModal(false);
      
      // More detailed error message with timeout handling
      let errorMessage = 'Ошибка при массовой генерации техкарт';
      
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        errorMessage = 'Превышено время ожидания. Массовая генерация техкарт занимает много времени (до 5 минут). Попробуйте еще раз или обратитесь в поддержку.';
      } else if (error.response?.status === 403) {
        errorMessage = 'Массовая генерация техкарт доступна только для PRO пользователей. Обновите подписку.';
      } else if (error.response?.status === 404) {
        errorMessage = 'Меню не найдено. Попробуйте создать новое меню.';
      } else if (error.response?.data?.detail) {
        errorMessage += ': ' + error.response.data.detail;
      } else if (error.message) {
        errorMessage += ': ' + error.message;
      }
      
      alert(errorMessage);
    } finally {
      setIsGeneratingMassCards(false);
    }
  };

  const startVoiceRecognition = () => {
    if (recognition) {
      recognition.start();
    } else {
      console.log('Speech recognition not initialized');
    }
  };

  const stopVoiceRecognition = () => {
    if (recognition && isListening) {
      recognition.stop();
      setIsListening(false);
      setVoiceStatus('Запись остановлена');
      setTimeout(() => {
        setShowVoiceModal(false);
      }, 1000);
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
    // Load venue profile data
    fetchVenueTypes();
    fetchCuisineTypes();
    fetchAverageCheckCategories();
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
      // TEMPORARILY DISABLE TO UNBLOCK UI
      // fetchVenueProfile();
    }
  }, [currentUser?.id]);

  useEffect(() => {
    if (currentUser && currentView === 'dashboard') {
      fetchUserHistory();
    }
    // TEMPORARILY DISABLE PROJECT AND PROFILE LOADING TO UNBLOCK UI
    // if (currentUser && menuProjects.length === 0) {
    //   fetchMenuProjects();
    // }
  }, [currentView, currentUser]);

  // Generate simple menu function - MOVED UP for better React binding
  const generateSimpleMenu = async () => {
    if (!currentUser?.id) {
      alert('Пользователь не найден!');
      return;
    }

    if (!simpleMenuData.menuType || !simpleMenuData.expectations.trim()) {
      alert('Пожалуйста, выберите тип меню и опишите ваши ожидания!');
      return;
    }

    // 🚀 КРАСИВЫЙ ЗАГРУЗОЧНЫЙ ЭКРАН С ЛАЙФХАКАМИ
    setIsGeneratingSimpleMenu(true);
    setLoadingType('menu');
    setLoadingProgress(0);
    setLoadingMessage('🎯 Анализируем ваши пожелания...');
    
    // Запускаем анимацию прогресса и смену лайфхаков
    const progressInterval = simulateProgress('menu', 25000); // 25 секунд анимации
    
    // Use venue profile default dish count if not specified
    const dishCount = simpleMenuData.dishCount || venueProfile.default_dish_count || 12;
    
    try {
      const requestData = {
        user_id: currentUser.id,
        // Convert simple menu data to complex menu format for existing endpoint
        menu_profile: {
          menuType: "restaurant",
          dishCount: dishCount,
          averageCheck: "medium",
          cuisineStyle: venueProfile.cuisine_style || "classic",
          menuStyle: simpleMenuData.menuType,
          specialRequirements: [],
          menuDescription: simpleMenuData.expectations,
          expectations: simpleMenuData.expectations,
          additional_notes: `Generated via simple menu creation. Type: ${simpleMenuData.menuType}, Project: ${simpleMenuData.projectId || 'none'}`
        },
        venue_profile: {
          venue_name: venueProfile.venue_name || "Test Restaurant",
          venue_type: venueProfile.venue_type || "family_restaurant", 
          cuisine_type: (venueProfile.cuisine_focus && venueProfile.cuisine_focus[0]) || "russian",
          average_check: venueProfile.average_check || 800
        }
      };

      const response = await axios.post(`${API}/generate-menu`, requestData);
      console.log('SUCCESS - API Response received:', response.status, response.data);
      
      if (response.data.success) {
        // Parse menu data from actual API response structure
        const menuData = response.data.menu;
        const categories = menuData.categories || [];
        
        // Extract all dishes from categories
        let allDishes = [];
        categories.forEach(category => {
          const categoryDishes = (category.dishes || []).map(dish => ({
            ...dish,
            category: category.name || category.category || 'Без категории'
          }));
          allDishes = allDishes.concat(categoryDishes);
        });
        
        setGeneratedMenu({
          menu_id: response.data.menu_id,
          menu_concept: menuData.menu_name || menuData.description || 'Generated via simple menu creation',
          dishes: allDishes,
          dish_count: allDishes.length,
          generation_method: 'simple_adapted',
          categories: categories
        });

        // КРАСИВОЕ ЗАВЕРШЕНИЕ АНИМАЦИИ
        clearInterval(progressInterval);
        setLoadingProgress(100);
        setLoadingMessage('✨ Меню готово! Переносим в интерфейс...');
        
        // Небольшая задержка для показа завершения
        setTimeout(() => {
          setIsGeneratingSimpleMenu(false);
          setLoadingProgress(0);
          setLoadingMessage('');
          setLoadingType('');
          
          // CRITICAL FIX: Set currentView to menu-generator to show the generated menu
          setCurrentView('menu-generator');

          // Close modal and show success
          setShowSimpleMenuModal(false);
          setSimpleMenuData({
            menuType: '',
            expectations: '',
            dishCount: 0,
            customCategories: null,
            projectId: null
          });

          alert(`✅ Меню успешно создано!\n\n🍽️ Создано ${allDishes.length} блюд\n💡 Концепция: ${menuData.menu_name || 'Новое меню'}`);
        }, 2000);

        // Update user history
        await fetchUserHistory();
      } else {
        throw new Error(response.data.error || 'Failed to generate simple menu');
      }
    } catch (error) {
      console.error('Error generating simple menu:', error);
      let errorMessage = 'Ошибка при создании меню';
      
      // Останавливаем анимацию при ошибке
      clearInterval(progressInterval);
      
      if (error.response?.status === 403) {
        errorMessage = 'Создание меню доступно только для PRO пользователей!';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      alert(errorMessage);
    } finally {
      setIsGeneratingSimpleMenu(false);
      setLoadingProgress(0);
      setLoadingMessage('');
      setLoadingType('');
    }
  };

  // Fetch menu tech cards function
  const fetchMenuTechCards = async (menuId) => {
    if (!menuId) {
      alert('ID меню не найден!');
      return;
    }

    setIsLoadingMenuTechCards(true);
    try {
      const response = await axios.get(`${API}/menu/${menuId}/tech-cards`);
      
      if (response.data.success) {
        setMenuTechCards(response.data);
        setShowMenuTechCards(true);
        console.log('Menu tech cards loaded:', response.data);
      } else {
        throw new Error('Failed to fetch menu tech cards');
      }
    } catch (error) {
      console.error('Error fetching menu tech cards:', error);
      alert('Ошибка при загрузке техкарт меню: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsLoadingMenuTechCards(false);
    }
  };

  // Replace dish function
  const replaceDish = async () => {
    if (!replacingDishData || !currentUser?.id) {
      alert('Недостаточно данных для замены блюда');
      return;
    }

    setIsReplacingDish(true);
    try {
      const response = await axios.post(`${API}/replace-dish`, {
        user_id: currentUser.id,
        menu_id: replacingDishData.menu_id,
        dish_name: replacingDishData.dish_name,
        category: replacingDishData.category,
        replacement_prompt: replacementPrompt
      });

      if (response.data.success) {
        alert(response.data.message);
        
        // КРИТИЧЕСКИ ВАЖНО: Обновляем generatedMenu state с новым блюдом
        if (generatedMenu && response.data.new_dish) {
          const updatedMenu = { ...generatedMenu };
          
          // Находим и заменяем блюдо в соответствующей категории
          updatedMenu.categories = updatedMenu.categories.map(category => {
            if (category.category_name === replacingDishData.category) {
              return {
                ...category,
                dishes: category.dishes.map(dish => 
                  dish.name === replacingDishData.dish_name 
                    ? response.data.new_dish 
                    : dish
                )
              };
            }
            return category;
          });
          
          setGeneratedMenu(updatedMenu);
          console.log('✅ Меню обновлено с новым блюдом:', response.data.new_dish.name);
        }
        
        // Refresh menu tech cards if they are currently displayed
        if (showMenuTechCards && menuTechCards) {
          await fetchMenuTechCards(replacingDishData.menu_id);
        }
        
        // Close modal
        setShowReplaceDishModal(false);
        setReplacingDishData(null);
        setReplacementPrompt('');
        
        // Update user history
        await fetchUserHistory();
      } else {
        throw new Error(response.data.error || 'Failed to replace dish');
      }
    } catch (error) {
      console.error('Error replacing dish:', error);
      alert('Ошибка при замене блюда: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsReplacingDish(false);
    }
  };

  // Open replace dish modal
  const openReplaceDishModal = (dishName, category, menuId) => {
    setReplacingDishData({
      dish_name: dishName,
      category: category,
      menu_id: menuId
    });
    setReplacementPrompt(''); // Reset prompt
    setShowReplaceDishModal(true);
  };

  // Menu Projects functions
  const fetchMenuProjects = async () => {
    if (!currentUser?.id) return;
    
    setIsLoadingProjects(true);
    try {
      const response = await axios.get(`${API}/menu-projects/${currentUser.id}`);
      
      if (response.data.success) {
        setMenuProjects(response.data.projects);
      } else {
        throw new Error('Failed to fetch menu projects');
      }
    } catch (error) {
      console.error('Error fetching menu projects:', error);
      alert('Ошибка при загрузке проектов');
    } finally {
      setIsLoadingProjects(false);
    }
  };

  const createMenuProject = async () => {
    if (!currentUser?.id) {
      alert('Пользователь не найден!');
      return;
    }

    if (!newProjectData.projectName.trim() || !newProjectData.projectType) {
      alert('Пожалуйста, заполните название и тип проекта!');
      return;
    }

    setIsCreatingProject(true);
    try {
      const response = await axios.post(`${API}/create-menu-project`, {
        user_id: currentUser.id,
        project_name: newProjectData.projectName,
        description: newProjectData.description,
        project_type: newProjectData.projectType,
        venue_type: newProjectData.venueType
      });

      if (response.data.success) {
        alert(response.data.message);
        
        // Reset form and close modal
        setNewProjectData({
          projectName: '',
          description: '',
          projectType: '',
          venueType: null
        });
        setShowCreateProjectModal(false);
        
        // Refresh projects list
        await fetchMenuProjects();
      } else {
        throw new Error(response.data.error || 'Failed to create project');
      }
    } catch (error) {
      console.error('Error creating menu project:', error);
      alert('Ошибка при создании проекта: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsCreatingProject(false);
    }
  };

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
              className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-colors mb-4"
            >
              НАЧАТЬ ТЕСТИРОВАНИЕ
            </button>
            
            {/* BYPASS BUTTON FOR TESTING */}
            <button
              onClick={() => {
                // Создаем тестового пользователя без выбора города
                const testUser = {
                  id: 'test_user_' + Date.now(),
                  name: 'Тест Предприниматель',
                  email: 'entrepreneur@test.com',
                  city: 'moskva',
                  subscription_plan: 'pro',
                  monthly_tech_cards_used: 0,
                  created_at: new Date().toISOString()
                };
                setCurrentUser(testUser);
                localStorage.setItem('receptor_user', JSON.stringify(testUser));
              }}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition-colors text-sm"
            >
              🚀 БЫСТРЫЙ ТЕСТ (обход регистрации)
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
              
              <div className="flex items-center space-x-3 sm:space-x-6">
                <button
                  onClick={() => setCurrentView('dashboard')}
                  className={`font-semibold text-sm sm:text-base transition-colors ${
                    currentView === 'dashboard' 
                      ? 'text-purple-200 border-b border-purple-300' 
                      : 'text-purple-300 hover:text-purple-200'
                  }`}
                  title="📊 Главная панель управления"
                >
                  ГЛАВНАЯ
                </button>
                <button
                  onClick={() => setCurrentView('create')}
                  className={`font-semibold text-sm sm:text-base transition-colors ${
                    currentView === 'create' 
                      ? 'text-purple-200 border-b border-purple-300' 
                      : 'text-purple-300 hover:text-purple-200'
                  }`}
                  title="🍽️ Создать техкарту"
                >
                  ТЕХКАРТЫ
                </button>
                <button
                  onClick={() => setCurrentView('menu-generator')}
                  className={`font-semibold text-sm sm:text-base transition-colors ${
                    currentView === 'menu-generator' 
                      ? 'text-purple-200 border-b border-purple-300' 
                      : 'text-purple-300 hover:text-purple-200'
                  }`}
                  title="🎯 Генератор готовых меню"
                >
                  МЕНЮ
                </button>
                <button
                  onClick={() => setShowProjectsModal(true)}
                  className="text-purple-300 hover:text-purple-200 font-semibold text-sm sm:text-base transition-colors"
                  title="📁 Управление проектами меню"
                >
                  ПРОЕКТЫ {menuProjects.length > 0 && `(${menuProjects.length})`}
                </button>
                <button
                  onClick={() => {
                    setShowHistory(!showHistory);
                    if (!showHistory) {
                      fetchUserHistory();
                    }
                  }}
                  className="text-purple-300 hover:text-purple-200 font-semibold text-sm sm:text-base"
                  title="📋 Просмотреть все созданные техкарты и сохраненные эксперименты"
                >
                  ИСТОРИЯ
                </button>
                <span className="text-purple-300 font-bold text-sm sm:text-base">{currentUser.name}</span>
                <button
                  onClick={handleLogout}
                  className="text-purple-300 hover:text-purple-200 font-semibold text-sm sm:text-base"
                  title="🚪 Выйти из аккаунта и очистить данные сессии"
                >
                  ВЫЙТИ
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:py-12">
        {/* Dashboard View */}
        {currentView === 'dashboard' && (
          <div className="space-y-8">
            {/* Welcome Section */}
            <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 border border-purple-400/30 rounded-xl p-6 sm:p-8">
              <h2 className="text-2xl sm:text-3xl font-bold text-purple-300 mb-4">
                Добро пожаловать, {currentUser.name}! 👋
              </h2>
              <p className="text-gray-300 text-base sm:text-lg mb-6">
                {venueProfile.venue_name ? 
                  `Управляйте ${venueProfile.venue_name} с помощью AI` : 
                  'Создавайте профессиональные техкарты и меню за минуты'
                }
              </p>
              
              {/* Quick Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-purple-800/30 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-purple-300">{dashboardStats.totalTechCards}</div>
                  <div className="text-sm text-gray-400">Техкарт создано</div>
                </div>
                <div className="bg-blue-800/30 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-blue-300">{dashboardStats.totalMenus}</div>
                  <div className="text-sm text-gray-400">Готовых меню</div>
                </div>
                <div className="bg-green-800/30 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-green-300">{dashboardStats.thisMonthCards}</div>
                  <div className="text-sm text-gray-400">За этот месяц</div>
                </div>
                <div className="bg-yellow-800/30 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-yellow-300">
                    {currentUser.subscription_plan?.toUpperCase() || 'FREE'}
                  </div>
                  <div className="text-sm text-gray-400">Ваш план</div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              <div 
                className="bg-gradient-to-br from-purple-600/20 to-pink-600/20 border border-purple-400/30 rounded-xl p-6 cursor-pointer hover:scale-105 transition-transform"
                onClick={() => setCurrentView('create')}
              >
                <div className="text-4xl mb-4">🍽️</div>
                <h3 className="text-xl font-bold text-purple-300 mb-2">Создать техкарту</h3>
                <p className="text-gray-400 text-sm">Сгенерируйте детальную техкарту для любого блюда</p>
              </div>

              <div 
                className="bg-gradient-to-br from-cyan-600/20 to-blue-600/20 border border-cyan-400/30 rounded-xl p-6 cursor-pointer hover:scale-105 transition-transform"
                onClick={() => setCurrentView('menu-generator')}
              >
                <div className="text-4xl mb-4">🎯</div>
                <h3 className="text-xl font-bold text-cyan-300 mb-2">Генератор меню</h3>
                <p className="text-gray-400 text-sm">Создайте полное меню за 15 минут</p>
              </div>

              <div 
                className="bg-gradient-to-br from-orange-600/20 to-red-600/20 border border-orange-400/30 rounded-xl p-6 cursor-pointer hover:scale-105 transition-transform"
                onClick={() => setShowVenueProfileModal(true)}
              >
                <div className="text-4xl mb-4">🏢</div>
                <h3 className="text-xl font-bold text-orange-300 mb-2">Мое заведение</h3>
                <p className="text-gray-400 text-sm">Настройте профиль для персонализации</p>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
              <h3 className="text-xl font-bold text-purple-300 mb-4">Последняя активность</h3>
              {userHistory.length > 0 ? (
                <div className="space-y-3">
                  {userHistory.slice(0, 5).map((item, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="text-2xl">
                          {item.is_laboratory ? '🧪' : '🍽️'}
                        </div>
                        <div>
                          <div className="font-semibold text-gray-200">{item.dish_name}</div>
                          <div className="text-xs text-gray-400">
                            {new Date(item.created_at).toLocaleDateString('ru-RU')}
                          </div>
                        </div>
                      </div>
                      <button 
                        onClick={() => {
                          setTechCard(item.content);
                          setCurrentView('create');
                        }}
                        className="text-purple-400 hover:text-purple-300 text-sm"
                      >
                        Открыть
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-center py-8">
                  Пока нет созданных техкарт. Начните с создания первой!
                </p>
              )}
            </div>
          </div>
        )}

        {/* Generated Menu View */}
        {currentView === 'menu-generator' && generatedMenu && !showMenuWizard && (
          <div className="max-w-6xl mx-auto">
            {/* Menu Header */}  
            <div className="bg-gradient-to-r from-amber-600/20 to-orange-600/20 border border-amber-400/30 rounded-xl p-6 mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-4xl">🍽️</span>
                    <h2 className="text-2xl sm:text-3xl font-bold text-amber-300">
                      {generatedMenu.menu_name || 'Сгенерированное меню'}
                    </h2>
                  </div>
                  <p className="text-gray-300 text-lg">
                    {generatedMenu.description || 'Меню создано с учетом всех ваших требований'}
                  </p>
                  <div className="flex gap-4 mt-3 text-sm text-gray-400">
                    <span>📊 Всего блюд: {(generatedMenu.categories || []).reduce((total, cat) => total + (cat.dishes?.length || 0), 0)}</span>
                    <span>🏷️ Категорий: {(generatedMenu.categories || []).length}</span>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setGeneratedMenu(null);
                    setShowMenuWizard(false);
                  }}
                  className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors"
                  title="🆕 Создать новое меню"
                >
                  🆕 Новое меню
                </button>
              </div>
            </div>

            {/* Menu Preview Toggle */}
            <div className="flex justify-center mb-8">
              <div className="bg-gray-800/50 rounded-lg p-2 flex gap-2">
                <button 
                  onClick={() => setMenuViewMode('customer')}
                  className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                    menuViewMode === 'customer' 
                      ? 'bg-amber-600 text-white' 
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  🍽️ Меню для гостей
                </button>
                <button 
                  onClick={() => setMenuViewMode('business')}
                  className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                    menuViewMode === 'business' 
                      ? 'bg-purple-600 text-white' 
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  📊 Бизнес-анализ
                </button>
              </div>
            </div>

            {/* Customer Menu View */}
            {menuViewMode === 'customer' && (
              <div className="space-y-8">
                {(generatedMenu.categories || []).map((category, categoryIndex) => (
                  <div key={categoryIndex} className="bg-white/5 backdrop-blur-lg rounded-xl p-8 border border-amber-400/20">
                    <h3 className="text-2xl font-bold text-amber-300 mb-6 text-center border-b border-amber-400/30 pb-3">
                      {category.category_name}
                    </h3>
                    
                    <div className="space-y-4">
                      {(category.dishes || []).map((dish, dishIndex) => (
                        <div key={dishIndex} className="border-b border-gray-600/30 pb-4 last:border-b-0">
                          <div className="flex justify-between items-start mb-2">
                            <div className="flex-1">
                              <h4 className="text-xl font-bold text-white mb-2">{dish.name}</h4>
                              <p className="text-gray-300 leading-relaxed">{dish.description}</p>
                              {dish.portion_size && (
                                <p className="text-gray-400 text-sm mt-1">Выход: {dish.portion_size}</p>
                              )}
                            </div>
                            <div className="text-right ml-6">
                              <div className="text-2xl font-bold text-amber-300">
                                {dish.estimated_price}₽
                              </div>
                              <div className="flex gap-2 mt-2">
                                <button
                                  onClick={() => openReplaceDishModal(dish.name, category.category_name, generatedMenu.menu_id)}
                                  className="bg-yellow-600/20 hover:bg-yellow-600/40 text-yellow-300 px-3 py-1 rounded-lg text-sm border border-yellow-600/30 transition-all"
                                  title="🔄 Заменить блюдо"
                                >
                                  🔄 Заменить
                                </button>
                                <button
                                  onClick={() => {
                                    const fullDishContext = {
                                      name: dish.name,
                                      description: dish.description,
                                      main_ingredients: dish.main_ingredients || [],
                                      category: category.category_name,
                                      estimated_cost: dish.estimated_cost,
                                      estimated_price: dish.estimated_price,
                                      difficulty: dish.difficulty,
                                      cook_time: dish.cook_time
                                    };
                                    
                                    setDishContext(fullDishContext);
                                    setDishName(`${dish.name} (из меню "${generatedMenu.menu_name || 'Сгенерированное меню'}")
                                    
Категория: ${category.category_name}
Описание: ${dish.description}
Основные ингредиенты: ${(dish.main_ingredients || []).join(', ')}
Ориентировочная себестоимость: ${dish.estimated_cost}₽
Время готовки: ${dish.cook_time} мин
Сложность: ${dish.difficulty}`);
                                    setCurrentView('create');
                                  }}
                                  className="bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 px-3 py-1 rounded-lg text-sm border border-emerald-600/30 transition-all"
                                  title="📋 Создать техкарту"
                                >
                                  📋 Техкарта
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Business Analysis View */}
            {menuViewMode === 'business' && (
              <div className="space-y-6">
                {/* Ingredient Optimization Info */}
                {generatedMenu.ingredient_optimization && (
                  <div className="bg-green-900/20 border border-green-400/30 rounded-xl p-6">
                    <h3 className="text-xl font-bold text-green-300 mb-4">💡 Оптимизация ингредиентов</h3>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-semibold text-green-200 mb-2">Общие ингредиенты:</h4>
                        <div className="flex flex-wrap gap-2">
                          {(generatedMenu.ingredient_optimization.shared_ingredients || []).map((ingredient, index) => (
                            <span key={index} className="px-3 py-1 bg-green-600/20 text-green-300 rounded-full text-sm">
                              {ingredient}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h4 className="font-semibold text-green-200 mb-2">Экономия на закупках:</h4>
                        <div className="text-2xl font-bold text-green-300">
                          {generatedMenu.ingredient_optimization.cost_savings || '15-20%'}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Business Menu Categories */}
                {(generatedMenu.categories || []).map((category, categoryIndex) => (
                  <div key={categoryIndex} className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
                    <h3 className="text-xl font-bold text-cyan-300 mb-4">
                      {category.category_name}
                      <span className="text-sm text-gray-400 ml-2">({category.dishes?.length || 0} блюд)</span>
                    </h3>
                    
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {(category.dishes || []).map((dish, dishIndex) => (
                        <div key={dishIndex} className="bg-gray-700/50 rounded-lg p-4 hover:bg-gray-700/70 transition-colors">
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-bold text-white">{dish.name}</h4>
                            <div className="flex gap-2">
                              <button
                                onClick={() => openReplaceDishModal(dish.name, category.category_name, generatedMenu.menu_id)}
                                className="text-yellow-400 hover:text-yellow-300 text-sm"
                                title="🔄 Заменить блюдо"
                              >
                                🔄
                              </button>
                              <button
                                onClick={() => {
                                  const fullDishContext = {
                                    name: dish.name,
                                    description: dish.description,
                                    main_ingredients: dish.main_ingredients || [],
                                    category: category.category_name,
                                    estimated_cost: dish.estimated_cost,
                                    estimated_price: dish.estimated_price,
                                    difficulty: dish.difficulty,
                                    cook_time: dish.cook_time
                                  };
                                  
                                  setDishContext(fullDishContext);
                                  setDishName(`${dish.name} (из меню "${generatedMenu.menu_name || 'Сгенерированное меню'}")
                                  
Категория: ${category.category_name}
Описание: ${dish.description}
Основные ингредиенты: ${(dish.main_ingredients || []).join(', ')}
Ориентировочная себестоимость: ${dish.estimated_cost}₽
Время готовки: ${dish.cook_time} мин
Сложность: ${dish.difficulty}`);
                                  setCurrentView('create');
                                }}
                                className="text-cyan-400 hover:text-cyan-300 text-sm"
                                title="📋 Создать техкарту"
                              >
                                📋
                              </button>
                            </div>
                          </div>
                          
                          <p className="text-gray-300 text-sm mb-3">{dish.description}</p>
                          
                          <div className="grid grid-cols-2 gap-4 text-xs">
                            <div>
                              <span className="text-gray-400">Себестоимость:</span>
                              <span className="text-green-300 font-semibold ml-1">{dish.estimated_cost}₽</span>
                            </div>
                            <div>
                              <span className="text-gray-400">Цена:</span>
                              <span className="text-yellow-300 font-semibold ml-1">{dish.estimated_price}₽</span>
                            </div>
                            <div>
                              <span className="text-gray-400">Сложность:</span>
                              <span className="text-blue-300 font-semibold ml-1">{dish.difficulty}</span>
                            </div>
                            <div>
                              <span className="text-gray-400">Время:</span>
                              <span className="text-purple-300 font-semibold ml-1">{dish.cook_time} мин</span>
                            </div>
                          </div>
                          
                          {dish.main_ingredients && (
                            <div className="mt-3">
                              <span className="text-gray-400 text-xs">Ингредиенты:</span>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {dish.main_ingredients.slice(0, 3).map((ingredient, idx) => (
                                  <span key={idx} className="px-2 py-1 bg-gray-600/50 text-gray-300 rounded text-xs">
                                    {ingredient}
                                  </span>
                                ))}
                                {dish.main_ingredients.length > 3 && (
                                  <span className="px-2 py-1 text-gray-400 text-xs">
                                    +{dish.main_ingredients.length - 3}
                                  </span>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Action Buttons */}
            <div className="mt-8 flex flex-col sm:flex-row gap-4">
              <button
                onClick={generateMassTechCards}
                disabled={isGeneratingMassCards}
                className={`flex-1 ${isGeneratingMassCards 
                  ? 'bg-gray-600 cursor-not-allowed' 
                  : 'bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600'
                } text-white font-bold py-3 px-6 rounded-lg transition-all`}
                title="⚡ Создать техкарты для всего меню"
              >
                {isGeneratingMassCards ? (
                  <>
                    <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Генерирую техкарты...
                  </>
                ) : (
                  `⚡ СОЗДАТЬ ВСЕ ТЕХКАРТЫ (${(generatedMenu.categories || []).reduce((total, cat) => total + (cat.dishes?.length || 0), 0)} блюд)`
                )}
              </button>
              
              <button
                onClick={() => fetchMenuTechCards(generatedMenu.menu_id)}
                disabled={isLoadingMenuTechCards}
                className="bg-green-600 hover:bg-green-700 disabled:bg-green-800 disabled:opacity-50 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                title="📋 Посмотреть созданные техкарты из этого меню"
              >
                {isLoadingMenuTechCards ? '⏳ Загрузка...' : '📋 МОЕ МЕНЮ'}
              </button>
              
              <button
                onClick={() => {
                  // Export menu to PDF
                  alert('Экспорт меню в PDF скоро будет доступен!');
                }}
                className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                title="📄 Экспортировать меню в PDF"
              >
                📄 Экспорт PDF
              </button>
            </div>
          </div>
        )}

        {/* Menu Generator View */}
        {currentView === 'menu-generator' && (
          <div className="max-w-6xl mx-auto">
            {!showMenuWizard ? (
              // Menu Generator Landing
              <div className="text-center space-y-8">
                {/* Hero Section */}
                <div className="bg-gradient-to-r from-cyan-600/20 to-blue-600/20 border border-cyan-400/30 rounded-2xl p-8 sm:p-12">
                  <div className="text-6xl sm:text-8xl mb-6">🎯</div>
                  <h2 className="text-3xl sm:text-5xl font-bold text-cyan-300 mb-6">
                    ГЕНЕРАТОР МЕНЮ
                  </h2>
                  <p className="text-xl sm:text-2xl text-gray-300 mb-8 max-w-4xl mx-auto">
                    Создайте <span className="text-cyan-400 font-bold">сбалансированное меню</span> за 15 минут вместо месяца работы!
                  </p>
                  
                  {/* Key Benefits */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
                    <div className="bg-cyan-900/30 rounded-xl p-4">
                      <div className="text-3xl mb-2">⚡</div>
                      <div className="font-bold text-cyan-300">15 минут</div>
                      <div className="text-sm text-gray-400">вместо месяца</div>
                    </div>
                    <div className="bg-blue-900/30 rounded-xl p-4">
                      <div className="text-3xl mb-2">🧠</div>
                      <div className="font-bold text-blue-300">AI оптимизация</div>
                      <div className="text-sm text-gray-400">умные ингредиенты</div>
                    </div>
                    <div className="bg-purple-900/30 rounded-xl p-4">
                      <div className="text-3xl mb-2">💰</div>
                      <div className="font-bold text-purple-300">Экономия</div>
                      <div className="text-sm text-gray-400">до 100.000₽</div>
                    </div>
                  </div>
                  
                  <button
                    onClick={() => {
                      // Ensure we're in the menu-generator view
                      setCurrentView('menu-generator');
                      
                      // Initialize simple menu data with venue profile defaults
                      setSimpleMenuData({
                        menuType: '',
                        expectations: '',
                        dishCount: venueProfile.default_dish_count || 12,
                        customCategories: null,
                        projectId: null
                      });
                      setShowSimpleMenuModal(true);
                    }}
                    className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white font-bold py-4 px-8 rounded-xl text-xl transform hover:scale-105 transition-all shadow-lg"
                    title="🎯 Простое создание меню"
                  >
                    🚀 СОЗДАТЬ МЕНЮ ЗА 4 КЛИКА
                  </button>
                </div>

                {/* Profile Setup Section */}
                <div className="bg-purple-900/20 border border-purple-400/30 rounded-xl p-6">
                  <div className="text-4xl mb-4">⚙️</div>
                  <h3 className="text-xl font-bold text-purple-300 mb-4">Настройте профиль заведения для лучших результатов</h3>
                  <p className="text-gray-400 mb-6">
                    Укажите подробности о вашем заведении один раз, чтобы ИИ создавал идеальные меню автоматически.
                  </p>
                  <button
                    onClick={() => setShowVenueProfileModal(true)}
                    className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-colors mr-4"
                  >
                    ⚙️ НАСТРОИТЬ ПРОФИЛЬ
                  </button>
                  <button
                    onClick={() => {
                      // Auto-fill from venue profile
                      if (venueProfile.cuisine_type && !menuProfile.cuisineStyle) {
                        setMenuProfile(prev => ({
                          ...prev,
                          cuisineStyle: venueProfile.cuisine_type,
                          region: currentUser.city || 'moskva'
                        }));
                      }
                      setShowMenuWizard(true);
                    }}
                    className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                  >
                    🧙‍♂️ РАСШИРЕННЫЙ МАСТЕР
                  </button>
                </div>
              </div>
            ) : (
              // 5-Step Menu Creation Wizard with Enhanced UI/UX
              <div className="wizard-container max-w-4xl mx-auto">
                {/* Enhanced Header */}
                <div className="flex items-center justify-between mb-8">
                  <div className="flex items-center space-x-4">
                    <button
                      onClick={() => setShowMenuWizard(false)}
                      className="text-gray-400 hover:text-white text-2xl transition-all duration-300 hover:scale-110"
                      title="← Назад к выбору типа меню"
                    >
                      ←
                    </button>
                    <div>
                      <h2 className="text-2xl sm:text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-purple-300">
                        🧙‍♂️ МАСТЕР СОЗДАНИЯ МЕНЮ
                      </h2>
                      <p className="text-sm text-gray-400 mt-1">Создаем идеальное меню за 5 простых шагов</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-400">
                      Шаг {menuWizardStep} из 5
                    </div>
                    <div className="text-xs text-purple-400 mt-1">
                      {['Основы', 'Кухня', 'Цели', 'Техника', 'Финиш'][menuWizardStep - 1]}
                    </div>
                  </div>
                </div>

                {/* Enhanced Progress Bar with Step Indicators */}
                <div className="mb-12">
                  <div className="relative">
                    {/* Progress Track */}
                    <div className="bg-gray-700/50 rounded-full h-3 relative overflow-hidden">
                      <div 
                        className="wizard-progress-bar h-full transition-all duration-700 ease-out"
                        style={{ width: `${(menuWizardStep / 5) * 100}%` }}
                      ></div>
                    </div>
                    
                    {/* Step Indicators */}
                    <div className="flex justify-between absolute -top-2 left-0 right-0">
                      {[1, 2, 3, 4, 5].map((step) => (
                        <div
                          key={step}
                          className={`wizard-step-indicator w-7 h-7 rounded-full border-2 flex items-center justify-center text-xs font-bold transition-all duration-300 ${
                            step < menuWizardStep 
                              ? 'completed bg-green-500 border-green-400 text-white' 
                              : step === menuWizardStep
                                ? 'active bg-purple-500 border-purple-400 text-white'
                                : 'bg-gray-600 border-gray-500 text-gray-300'
                          }`}
                        >
                          {step < menuWizardStep ? '✓' : step}
                        </div>
                      ))}
                    </div>
                    
                    {/* Step Labels */}
                    <div className="flex justify-between mt-8 text-xs text-gray-400">
                      {['🏢 Основы', '🍳 Кухня', '🎯 Цели', '⚙️ Техника', '🚀 Финиш'].map((label, index) => (
                        <div key={index} className="text-center">
                          <div className={`transition-colors ${index + 1 <= menuWizardStep ? 'text-purple-300' : 'text-gray-500'}`}>
                            {label}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Step 1: Basic Menu Parameters */}
                {menuWizardStep === 1 && (
                  <div className="wizard-step-content bg-gray-800/50 backdrop-blur-lg rounded-2xl p-8 border border-gray-700/50">
                    <div className="space-y-8">
                      <div className="text-center mb-6">
                        <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-purple-300 mb-2">
                          🏢 Основные параметры меню
                        </h3>
                        <p className="text-sm text-gray-400">Определяем базовые характеристики будущего меню</p>
                      </div>
                      
                      {/* Venue Profile Integration */}
                      {venueProfile.venue_name ? (
                        <div className="bg-gradient-to-r from-purple-900/30 to-purple-800/20 border border-purple-400/30 rounded-xl p-6 mb-6 hover:border-purple-400/50 transition-all duration-300">
                          <div className="flex items-center justify-between">
                            <div>
                              <h4 className="font-bold text-purple-300 text-lg">{venueProfile.venue_name}</h4>
                              <p className="text-sm text-gray-400 mt-1">
                                {venueProfile.venue_type} • {venueProfile.cuisine_type} • {venueProfile.average_check}
                              </p>
                            </div>
                            <button
                              onClick={() => setShowVenueProfileModal(true)}
                              className="text-purple-400 hover:text-purple-300 text-sm bg-purple-800/30 px-3 py-1 rounded-lg transition-all duration-300 hover:bg-purple-700/40"
                            >
                              ⚙️ Изменить
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="bg-gradient-to-r from-yellow-900/30 to-orange-900/20 border border-yellow-400/30 rounded-xl p-6 mb-6 hover:border-yellow-400/50 transition-all duration-300">
                          <div className="flex items-center justify-between">
                            <div>
                              <h4 className="font-bold text-yellow-300 text-lg">Профиль заведения не настроен</h4>
                              <p className="text-sm text-gray-400 mt-1">Настройте профиль для более точной генерации меню</p>
                            </div>
                            <button
                              onClick={() => setShowVenueProfileModal(true)}
                              className="bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700 text-white px-4 py-2 rounded-lg text-sm transition-all duration-300 font-semibold"
                            >
                              🏢 Настроить
                            </button>
                          </div>
                        </div>
                      )}

                      {/* Menu Type Selection with Enhanced Cards */}
                      <div>
                        <label className="block text-lg font-bold text-gray-300 mb-4">
                          <span className="text-cyan-400">🎯</span> Тип меню для генерации:
                        </label>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                          {[
                            { value: 'full_menu', label: '🍽️ Полное меню', desc: 'Все категории блюд', popular: true },
                            { value: 'seasonal', label: '🍂 Сезонное меню', desc: 'С учетом сезона' },
                            { value: 'business_lunch', label: '💼 Бизнес-ланч', desc: 'Комплексные обеды' },
                            { value: 'evening_menu', label: '🌙 Вечернее меню', desc: 'Ужины и алкоголь' },
                            { value: 'breakfast', label: '☀️ Завтраки', desc: 'Утреннее меню' },
                            { value: 'bar_menu', label: '🍷 Барная карта', desc: 'Напитки + закуски' },
                            { value: 'dessert_menu', label: '🍰 Десертная карта', desc: 'Сладости и десерты' },
                            { value: 'banquet', label: '🎉 Банкетное меню', desc: 'Для мероприятий' },
                            { value: 'street_food', label: '🚚 Стрит-фуд', desc: 'Быстрое питание' }
                          ].map((type) => (
                            <button
                              key={type.value}
                              onClick={() => setMenuProfile(prev => ({ ...prev, menuType: type.value }))}
                              className={`wizard-option-card relative p-5 rounded-xl border text-left ${
                                menuProfile.menuType === type.value
                                  ? 'selected'
                                  : 'border-gray-600 bg-gray-700/50 text-gray-300 hover:border-purple-600'
                              }`}
                            >
                              {type.popular && (
                                <div className="absolute -top-2 -right-2 bg-gradient-to-r from-orange-500 to-pink-500 text-white text-xs px-2 py-1 rounded-full font-bold">
                                  ★ Популярно
                                </div>
                              )}
                              <div className="font-semibold text-base mb-1">{type.label}</div>
                              <div className="text-xs text-gray-400">{type.desc}</div>
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Enhanced Menu Constructor */}
                      <div className="bg-gray-700/30 rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                          <label className="text-lg font-bold text-gray-300">
                            <span className="text-purple-400">📊</span> Структура меню
                          </label>
                          <button
                            onClick={() => setMenuProfile(prev => ({ ...prev, useConstructor: !prev.useConstructor }))}
                            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                              menuProfile.useConstructor
                                ? 'bg-purple-600 text-white'
                                : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                            }`}
                          >
                            {menuProfile.useConstructor ? '📋 Конструктор' : '📊 Общее количество'}
                          </button>
                        </div>

                        {!menuProfile.useConstructor ? (
                          // Simple mode: total dish count
                          <>
                            <div className="text-center mb-4">
                              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-400 text-3xl font-bold">
                                {menuProfile.dishCount}
                              </span>
                              <span className="text-gray-400 ml-2">блюд всего</span>
                            </div>
                            <div className="px-2">
                              <input
                                type="range"
                                min="5"
                                max="50"
                                value={menuProfile.dishCount}
                                onChange={(e) => setMenuProfile(prev => ({ ...prev, dishCount: parseInt(e.target.value) }))}
                                className="wizard-slider w-full h-3 rounded-lg appearance-none cursor-pointer"
                              />
                              <div className="flex justify-between text-sm text-gray-400 mt-3">
                                <span className="flex flex-col items-center">
                                  <span className="text-xs">🥗</span>
                                  <span>5 блюд</span>
                                </span>
                                <span className="flex flex-col items-center">
                                  <span className="text-xs">🍽️</span>
                                  <span>25 блюд</span>
                                </span>
                                <span className="flex flex-col items-center">
                                  <span className="text-xs">🏪</span>
                                  <span>50 блюд</span>
                                </span>
                              </div>
                            </div>
                          </>
                        ) : (
                          // Constructor mode: categories
                          <div className="space-y-4">
                            <div className="text-center mb-4">
                              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-400 text-2xl font-bold">
                                {Object.values(menuProfile.categories).reduce((a, b) => a + b, 0)}
                              </span>
                              <span className="text-gray-400 ml-2">блюд всего</span>
                            </div>
                            
                            {[
                              { key: 'appetizers', label: '🥗 Закуски/Салаты', icon: '🥗', max: 10 },
                              { key: 'soups', label: '🍲 Супы', icon: '🍲', max: 6 },
                              { key: 'main_dishes', label: '🍖 Горячие блюда', icon: '🍖', max: 15 },
                              { key: 'desserts', label: '🍰 Десерты', icon: '🍰', max: 8 },
                              { key: 'beverages', label: '🥤 Напитки', icon: '🥤', max: 5 },
                              { key: 'snacks', label: '🍿 Закуски к напиткам', icon: '🍿', max: 5 }
                            ].map((category, index) => (
                              <div key={category.key} className="bg-gray-600/30 rounded-lg p-4">
                                <div className="flex items-center justify-between mb-2">
                                  <label className="text-sm font-semibold text-gray-300">
                                    {category.label}
                                  </label>
                                  <span className="text-cyan-400 font-bold text-lg">
                                    {menuProfile.categories[category.key] || 0}
                                  </span>
                                </div>
                                <input
                                  type="range"
                                  min="0"
                                  max={category.max}
                                  value={menuProfile.categories[category.key] || 0}
                                  onChange={(e) => setMenuProfile(prev => ({
                                    ...prev,
                                    categories: {
                                      ...prev.categories,
                                      [category.key]: parseInt(e.target.value)
                                    }
                                  }))}
                                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                                  style={{
                                    background: `linear-gradient(to right, #8b5cf6 0%, #8b5cf6 ${((menuProfile.categories[category.key] || 0) / category.max) * 100}%, #374151 ${((menuProfile.categories[category.key] || 0) / category.max) * 100}%, #374151 100%)`
                                  }}
                                />
                              </div>
                            ))}
                            
                            <div className="bg-purple-900/20 border border-purple-400/30 rounded-lg p-3 text-center">
                              <p className="text-sm text-purple-300">
                                💡 <strong>Конструктор меню</strong> дает точный контроль над структурой. 
                                ИИ создаст именно указанное количество блюд в каждой категории.
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 2: Cuisine Style & Menu Character */}
                {menuWizardStep === 2 && (
                  <div className="space-y-6">
                    <h3 className="text-xl font-bold text-cyan-300 mb-6">🌍 Стиль кухни и характер меню</h3>
                    
                    {/* Primary Cuisine Style */}
                    <div>
                      <label className="block text-sm font-bold text-gray-300 mb-3">Основной стиль кухни:</label>
                      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                        {[
                          { value: 'european', label: '🇪🇺 Европейская', desc: 'Классические рецепты', flag: '🇪🇺' },
                          { value: 'italian', label: '🇮🇹 Итальянская', desc: 'Паста, пицца, ризотто', flag: '🇮🇹' },
                          { value: 'french', label: '🇫🇷 Французская', desc: 'Высокая кухня, соусы', flag: '🇫🇷' },
                          { value: 'asian', label: '🥢 Азиатская', desc: 'Вок, димсамы, суши', flag: '🥢' },
                          { value: 'japanese', label: '🇯🇵 Японская', desc: 'Суши, роллы, супы', flag: '🇯🇵' },
                          { value: 'chinese', label: '🇨🇳 Китайская', desc: 'Вок, димсамы, утка', flag: '🇨🇳' },
                          { value: 'american', label: '🇺🇸 Американская', desc: 'Бургеры, стейки, BBQ', flag: '🇺🇸' },
                          { value: 'mexican', label: '🇲🇽 Мексиканская', desc: 'Тако, буррито, гуакамоле', flag: '🇲🇽' },
                          { value: 'russian', label: '🇷🇺 Русская', desc: 'Борщ, блины, котлеты', flag: '🇷🇺' },
                          { value: 'georgian', label: '🇬🇪 Грузинская', desc: 'Хачапури, хинкали, шашлык', flag: '🇬🇪' },
                          { value: 'uzbek', label: '🇺🇿 Узбекская', desc: 'Плов, манты, лагман', flag: '🇺🇿' },
                          { value: 'fusion', label: '🎭 Фьюжн', desc: 'Микс различных кухонь', flag: '🎭' }
                        ].map((cuisine) => (
                          <button
                            key={cuisine.value}
                            onClick={() => setMenuProfile(prev => ({ ...prev, cuisineStyle: cuisine.value }))}
                            className={`p-4 rounded-lg border text-left transition-all hover:scale-105 ${
                              menuProfile.cuisineStyle === cuisine.value
                                ? 'border-cyan-400 bg-cyan-600/20 text-cyan-300 scale-105'
                                : 'border-gray-600 bg-gray-700/50 text-gray-300 hover:border-cyan-600'
                            }`}
                          >
                            <div className="flex items-center gap-2 font-semibold">{cuisine.flag} <span>{cuisine.label.replace(cuisine.flag, '').trim()}</span></div>
                            <div className="text-xs text-gray-400 mt-1">{cuisine.desc}</div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Cuisine Influences (Multi-select) */}
                    <div>
                      <label className="block text-sm font-bold text-gray-300 mb-3">
                        Дополнительные влияния кухонь (можно выбрать несколько):
                      </label>
                      <div className="grid grid-cols-3 lg:grid-cols-6 gap-2">
                        {[
                          { value: 'mediterranean', label: '🌊 Средиземноморская' },
                          { value: 'indian', label: '🇮🇳 Индийская' },
                          { value: 'thai', label: '🇹🇭 Тайская' },
                          { value: 'korean', label: '🇰🇷 Корейская' },
                          { value: 'turkish', label: '🇹🇷 Турецкая' },
                          { value: 'scandinavian', label: '❄️ Скандинавская' },
                          { value: 'middle_eastern', label: '🕌 Ближневосточная' },
                          { value: 'brazilian', label: '🇧🇷 Бразильская' },
                          { value: 'peruvian', label: '🇵🇪 Перуанская' },
                          { value: 'african', label: '🌍 Африканская' }
                        ].map((influence) => (
                          <button
                            key={influence.value}
                            onClick={() => {
                              const current = menuProfile.cuisineInfluences || [];
                              const updated = current.includes(influence.value)
                                ? current.filter(c => c !== influence.value)
                                : [...current, influence.value];
                              setMenuProfile(prev => ({ ...prev, cuisineInfluences: updated }));
                            }}
                            className={`p-2 rounded-lg border text-center transition-all text-xs ${
                              (menuProfile.cuisineInfluences || []).includes(influence.value)
                                ? 'border-purple-400 bg-purple-600/20 text-purple-300'
                                : 'border-gray-600 bg-gray-700/50 text-gray-300 hover:border-purple-600'
                            }`}
                          >
                            {influence.label}
                          </button>
                        ))}
                      </div>
                      <div className="text-xs text-gray-400 text-center mt-2">
                        💡 Выбрано: {(menuProfile.cuisineInfluences || []).length} влияний
                      </div>
                    </div>

                    {/* Menu Style */}
                    <div>
                      <label className="block text-sm font-bold text-gray-300 mb-3">Стиль подачи и презентации:</label>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        {[
                          { value: 'classic', label: '👨‍🍳 Классический', desc: 'Традиционная подача' },
                          { value: 'modern', label: '✨ Современный', desc: 'Молекулярная гастрономия' },
                          { value: 'rustic', label: '🏠 Деревенский', desc: 'Домашний стиль' },
                          { value: 'street', label: '🚚 Стрит-фуд', desc: 'Уличная еда' },
                          { value: 'fine_dining', label: '🌟 Высокая кухня', desc: 'Изысканная подача' },
                          { value: 'comfort', label: '🤗 Комфорт-фуд', desc: 'Сытно и уютно' },
                          { value: 'health', label: '💪 Здоровое питание', desc: 'ПП и фитнес' },
                          { value: 'innovative', label: '🔬 Инновационный', desc: 'Авторские техники' }
                        ].map((style) => (
                          <button
                            key={style.value}
                            onClick={() => setMenuProfile(prev => ({ ...prev, menuStyle: style.value }))}
                            className={`p-4 rounded-lg border text-left transition-all hover:scale-105 ${
                              menuProfile.menuStyle === style.value
                                ? 'border-cyan-400 bg-cyan-600/20 text-cyan-300 scale-105'
                                : 'border-gray-600 bg-gray-700/50 text-gray-300 hover:border-cyan-600'
                            }`}
                          >
                            <div className="font-semibold text-sm">{style.label}</div>
                            <div className="text-xs text-gray-400 mt-1">{style.desc}</div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 3: Enhanced Business Goals & Target Audience */}
                {menuWizardStep === 3 && (
                  <div className="wizard-step-content bg-gray-800/50 backdrop-blur-lg rounded-2xl p-8 border border-gray-700/50 space-y-8">
                    <div className="text-center mb-6">
                      <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-purple-300 mb-2">
                        🎯 Целевая аудитория и регион
                      </h3>
                      <p className="text-sm text-gray-400">Определяем кто и где будет посещать заведение</p>
                    </div>
                    
                    {/* Enhanced Age Distribution */}
                    <div className="bg-gray-700/30 rounded-xl p-6">
                      <label className="block text-lg font-bold text-gray-300 mb-4">
                        <span className="text-purple-400">👥</span> Возрастное распределение посетителей
                      </label>
                      <div className="space-y-4">
                        {[
                          { key: '18-25', label: '👶 18-25 лет', desc: 'Студенты, молодежь', color: 'from-green-500 to-emerald-500' },
                          { key: '26-35', label: '💼 26-35 лет', desc: 'Молодые профессионалы', color: 'from-blue-500 to-cyan-500' },
                          { key: '36-50', label: '👨‍💼 36-50 лет', desc: 'Зрелые специалисты', color: 'from-purple-500 to-pink-500' },
                          { key: '50+', label: '👴 50+ лет', desc: 'Старшее поколение', color: 'from-orange-500 to-red-500' }
                        ].map((age) => (
                          <div key={age.key} className="bg-gray-600/30 rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                              <label className="text-sm font-semibold text-gray-300">
                                {age.label} - <span className="text-gray-400">{age.desc}</span>
                              </label>
                              <span className="text-cyan-400 font-bold text-lg">
                                {menuProfile.audienceAges[age.key]}%
                              </span>
                            </div>
                            <input
                              type="range"
                              min="0"
                              max="100"
                              value={menuProfile.audienceAges[age.key]}
                              onChange={(e) => setMenuProfile(prev => ({
                                ...prev,
                                audienceAges: {
                                  ...prev.audienceAges,
                                  [age.key]: parseInt(e.target.value)
                                }
                              }))}
                              className="w-full h-3 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                              style={{
                                background: `linear-gradient(to right, var(--tw-gradient-from) 0%, var(--tw-gradient-to) ${menuProfile.audienceAges[age.key]}%, #374151 ${menuProfile.audienceAges[age.key]}%, #374151 100%)`
                              }}
                            />
                          </div>
                        ))}
                        <div className="bg-purple-900/20 border border-purple-400/30 rounded-lg p-3">
                          <p className="text-sm text-purple-300 text-center">
                            💡 Общий процент: {Object.values(menuProfile.audienceAges).reduce((a, b) => a + b, 0)}% 
                            (не обязательно должно быть 100%)
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Enhanced Occupations */}
                    <div>
                      <label className="block text-lg font-bold text-gray-300 mb-4">
                        <span className="text-green-400">💼</span> Род занятий посетителей (множественный выбор)
                      </label>
                      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                        {[
                          { value: 'students', label: '🎓 Студенты', desc: 'Доступные цены, быстро' },
                          { value: 'office_workers', label: '💻 Офисные сотрудники', desc: 'Деловые обеды' },
                          { value: 'entrepreneurs', label: '🚀 Предприниматели', desc: 'Качество и статус' },
                          { value: 'creatives', label: '🎨 Творческие профессии', desc: 'Атмосфера и уникальность' },
                          { value: 'medical_workers', label: '⚕️ Медработники', desc: 'Здоровое питание' },
                          { value: 'teachers', label: '👩‍🏫 Педагоги', desc: 'Семейные ценности' },
                          { value: 'retirees', label: '🏠 Пенсионеры', desc: 'Традиционная кухня' },
                          { value: 'tourists', label: '📸 Туристы', desc: 'Локальные блюда' },
                          { value: 'families', label: '👨‍👩‍👧‍👦 Семьи с детьми', desc: 'Детское меню' }
                        ].map((occupation) => (
                          <button
                            key={occupation.value}
                            onClick={() => {
                              const current = menuProfile.audienceOccupations || [];
                              const updated = current.includes(occupation.value)
                                ? current.filter(o => o !== occupation.value)
                                : [...current, occupation.value];
                              setMenuProfile(prev => ({ ...prev, audienceOccupations: updated }));
                            }}
                            className={`wizard-option-card p-4 rounded-lg border text-left transition-all ${
                              (menuProfile.audienceOccupations || []).includes(occupation.value)
                                ? 'selected border-green-400 bg-green-600/20'
                                : 'border-gray-600 bg-gray-700/50 text-gray-300 hover:border-green-600'
                            }`}
                          >
                            <div className="font-semibold text-sm">{occupation.label}</div>
                            <div className="text-xs text-gray-400 mt-1">{occupation.desc}</div>
                          </button>
                        ))}
                      </div>
                      <div className="text-sm text-gray-400 text-center mt-3">
                        ✅ Выбрано: {(menuProfile.audienceOccupations || []).length} категорий
                      </div>
                    </div>

                    {/* Enhanced Regional Details */}
                    <div className="bg-gray-700/30 rounded-xl p-6">
                      <label className="block text-lg font-bold text-gray-300 mb-4">
                        <span className="text-yellow-400">🗺️</span> Региональные особенности
                      </label>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {/* City Type */}
                        <div>
                          <label className="block text-sm font-semibold text-gray-300 mb-2">Тип города:</label>
                          <div className="space-y-2">
                            {[
                              { value: 'capital', label: '🏛️ Столица', desc: 'Москва, СПб' },
                              { value: 'major_city', label: '🏢 Крупный город', desc: 'Миллионник' },
                              { value: 'province', label: '🏘️ Провинция', desc: 'Малый город' }
                            ].map((type) => (
                              <button
                                key={type.value}
                                onClick={() => setMenuProfile(prev => ({
                                  ...prev,
                                  regionDetails: {
                                    ...prev.regionDetails,
                                    type: type.value
                                  }
                                }))}
                                className={`w-full p-3 rounded-lg border text-left transition-all ${
                                  menuProfile.regionDetails.type === type.value
                                    ? 'border-yellow-400 bg-yellow-600/20'
                                    : 'border-gray-600 bg-gray-700/30 hover:border-yellow-600'
                                }`}
                              >
                                <div className="text-sm font-semibold">{type.label}</div>
                                <div className="text-xs text-gray-400">{type.desc}</div>
                              </button>
                            ))}
                          </div>
                        </div>

                        {/* Geography */}
                        <div>
                          <label className="block text-sm font-semibold text-gray-300 mb-2">География:</label>
                          <div className="space-y-2">
                            {[
                              { value: 'sea', label: '🌊 Приморский', desc: 'Морепродукты' },
                              { value: 'mountains', label: '⛰️ Горный', desc: 'Мясо, дичь' },
                              { value: 'plains', label: '🌾 Равнинный', desc: 'Овощи, злаки' }
                            ].map((geo) => (
                              <button
                                key={geo.value}
                                onClick={() => setMenuProfile(prev => ({
                                  ...prev,
                                  regionDetails: {
                                    ...prev.regionDetails,
                                    geography: geo.value
                                  }
                                }))}
                                className={`w-full p-3 rounded-lg border text-left transition-all ${
                                  menuProfile.regionDetails.geography === geo.value
                                    ? 'border-blue-400 bg-blue-600/20'
                                    : 'border-gray-600 bg-gray-700/30 hover:border-blue-600'
                                }`}
                              >
                                <div className="text-sm font-semibold">{geo.label}</div>
                                <div className="text-xs text-gray-400">{geo.desc}</div>
                              </button>
                            ))}
                          </div>
                        </div>

                        {/* Climate */}
                        <div>
                          <label className="block text-sm font-semibold text-gray-300 mb-2">Климат:</label>
                          <div className="space-y-2">
                            {[
                              { value: 'cold', label: '❄️ Холодный', desc: 'Сытная еда' },
                              { value: 'temperate', label: '🌤️ Умеренный', desc: 'Универсально' },
                              { value: 'warm', label: '☀️ Теплый', desc: 'Легкие блюда' }
                            ].map((climate) => (
                              <button
                                key={climate.value}
                                onClick={() => setMenuProfile(prev => ({
                                  ...prev,
                                  regionDetails: {
                                    ...prev.regionDetails,
                                    climate: climate.value
                                  }
                                }))}
                                className={`w-full p-3 rounded-lg border text-left transition-all ${
                                  menuProfile.regionDetails.climate === climate.value
                                    ? 'border-orange-400 bg-orange-600/20'
                                    : 'border-gray-600 bg-gray-700/30 hover:border-orange-600'
                                }`}
                              >
                                <div className="text-sm font-semibold">{climate.label}</div>
                                <div className="text-xs text-gray-400">{climate.desc}</div>
                              </button>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Menu Goals (Multi-select) */}
                    <div>
                      <label className="block text-sm font-bold text-gray-300 mb-3">
                        Цели меню (можно выбрать несколько):
                      </label>
                      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                        {[
                          { value: 'increase_check', label: '💰 Увеличить средний чек', desc: 'Дорогие позиции' },
                          { value: 'reduce_costs', label: '📉 Снизить себестоимость', desc: 'Оптимизация закупок' },
                          { value: 'speed_service', label: '⚡ Ускорить обслуживание', desc: 'Быстрые блюда' },
                          { value: 'expand_audience', label: '🎯 Расширить аудиторию', desc: 'Разнообразие блюд' },
                          { value: 'seasonal_update', label: '🍂 Сезонное обновление', desc: 'Актуальные продукты' },
                          { value: 'brand_positioning', label: '🏆 Позиционирование бренда', desc: 'Уникальность' },
                          { value: 'reduce_waste', label: '♻️ Сократить отходы', desc: 'Эко-подход' },
                          { value: 'staff_training', label: '👨‍🍳 Обучение персонала', desc: 'Простые рецепты' },
                          { value: 'instagram_friendly', label: '📱 Instagram-френдли', desc: 'Красивая подача' }
                        ].map((goal) => (
                          <button
                            key={goal.value}
                            onClick={() => {
                              const current = menuProfile.menuGoals || [];
                              const updated = current.includes(goal.value)
                                ? current.filter(g => g !== goal.value)
                                : [...current, goal.value];
                              setMenuProfile(prev => ({ ...prev, menuGoals: updated }));
                            }}
                            className={`p-3 rounded-lg border text-left transition-all ${
                              (menuProfile.menuGoals || []).includes(goal.value)
                                ? 'border-green-400 bg-green-600/20 text-green-300'
                                : 'border-gray-600 bg-gray-700/50 text-gray-300 hover:border-green-600'
                            }`}
                          >
                            <div className="font-semibold text-sm">{goal.label}</div>
                            <div className="text-xs text-gray-400 mt-1">{goal.desc}</div>
                          </button>
                        ))}
                      </div>
                      <div className="text-xs text-gray-400 text-center mt-2">
                        💡 Выбрано целей: {(menuProfile.menuGoals || []).length}
                      </div>
                    </div>

                    {/* Dietary Options */}
                    <div>
                      <label className="block text-sm font-bold text-gray-300 mb-3">
                        Диетические опции (отметьте нужные):
                      </label>
                      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                        {[
                          { value: 'vegetarian', label: '🌱 Вегетарианские', desc: 'Без мяса' },
                          { value: 'vegan', label: '🥬 Веганские', desc: 'Только растительное' },
                          { value: 'gluten_free', label: '🌾 Без глютена', desc: 'Для целиакии' },
                          { value: 'keto', label: '🥩 Кето-диета', desc: 'Низкоуглеводные' },
                          { value: 'paleo', label: '🦴 Палео-диета', desc: 'Древний рацион' },
                          { value: 'halal', label: '☪️ Халяль', desc: 'Исламские требования' },
                          { value: 'kosher', label: '✡️ Кошерные', desc: 'Иудейские требования' },
                          { value: 'diabetic', label: '🩺 Диабетические', desc: 'Для диабетиков' },
                          { value: 'low_calorie', label: '📏 Низкокалорийные', desc: 'Для похудения' },
                          { value: 'raw_food', label: '🥗 Сыроедение', desc: 'Без термообработки' }
                        ].map((diet) => (
                          <button
                            key={diet.value}
                            onClick={() => {
                              const current = menuProfile.dietaryOptions || [];
                              const updated = current.includes(diet.value)
                                ? current.filter(d => d !== diet.value)
                                : [...current, diet.value];
                              setMenuProfile(prev => ({ ...prev, dietaryOptions: updated }));
                            }}
                            className={`p-3 rounded-lg border text-left transition-all ${
                              (menuProfile.dietaryOptions || []).includes(diet.value)
                                ? 'border-purple-400 bg-purple-600/20 text-purple-300'
                                : 'border-gray-600 bg-gray-700/50 text-gray-300 hover:border-purple-600'
                            }`}
                          >
                            <div className="font-semibold text-xs">{diet.label}</div>
                            <div className="text-xs text-gray-400 mt-1">{diet.desc}</div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
                {/* Step 4: Kitchen Capabilities & Technical Details */}
                {menuWizardStep === 4 && (
                  <div className="space-y-6">
                    <h3 className="text-xl font-bold text-cyan-300 mb-6">🔧 Возможности кухни и технические детали</h3>
                    
                    {/* Kitchen Equipment Integration */}
                    {venueProfile.kitchen_equipment && venueProfile.kitchen_equipment.length > 0 ? (
                      <div className="bg-green-900/20 border border-green-400/30 rounded-xl p-4 mb-6">
                        <h4 className="font-bold text-green-300 mb-2">✅ Оборудование из профиля заведения:</h4>
                        <div className="flex flex-wrap gap-2">
                          {venueProfile.kitchen_equipment.map((equipment, index) => (
                            <span key={index} className="px-3 py-1 bg-green-600/20 text-green-300 rounded-full text-sm">
                              {equipment}
                            </span>
                          ))}
                        </div>
                        <button
                          onClick={() => setShowVenueProfileModal(true)}
                          className="text-green-400 hover:text-green-300 text-sm mt-2"
                        >
                          ⚙️ Изменить оборудование
                        </button>
                      </div>
                    ) : (
                      <div className="bg-yellow-900/20 border border-yellow-400/30 rounded-xl p-4 mb-6">
                        <h4 className="font-bold text-yellow-300">⚠️ Оборудование не указано в профиле</h4>
                        <p className="text-sm text-gray-400 mb-2">Укажите доступное оборудование для более точной генерации меню</p>
                        <button
                          onClick={() => setShowVenueProfileModal(true)}
                          className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-lg text-sm"
                        >
                          🔧 Настроить оборудование
                        </button>
                      </div>
                    )}

                    {/* Staff Skill Level */}
                    <div>
                      <label className="block text-sm font-bold text-gray-300 mb-3">
                        Уровень навыков персонала: <span className="text-cyan-400">{
                          menuProfile.staffSkillLevel === 'beginner' ? 'Начинающий' :
                          menuProfile.staffSkillLevel === 'medium' ? 'Средний' : 
                          menuProfile.staffSkillLevel === 'advanced' ? 'Продвинутый' : 'Профессиональный'
                        }</span>
                      </label>
                      <div className="px-4">
                        <input
                          type="range"
                          min="1"
                          max="4"
                          value={
                            menuProfile.staffSkillLevel === 'beginner' ? 1 :
                            menuProfile.staffSkillLevel === 'medium' ? 2 :
                            menuProfile.staffSkillLevel === 'advanced' ? 3 : 4
                          }
                          onChange={(e) => {
                            const levels = ['beginner', 'medium', 'advanced', 'professional'];
                            setMenuProfile(prev => ({ ...prev, staffSkillLevel: levels[parseInt(e.target.value) - 1] }));
                          }}
                          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                          style={{
                            background: `linear-gradient(to right, #ef4444 0%, #f97316 25%, #eab308 50%, #22c55e 75%, #22c55e 100%)`
                          }}
                        />
                        <div className="flex justify-between text-xs text-gray-400 mt-1">
                          <span>🔰 Начинающий</span>
                          <span>⭐ Средний</span>
                          <span>🎯 Продвинутый</span>
                          <span>👨‍🍳 Профи</span>
                        </div>
                      </div>
                    </div>

                    {/* Preparation Time Constraints */}
                    <div>
                      <label className="block text-sm font-bold text-gray-300 mb-3">
                        Ограничения по времени приготовления: <span className="text-cyan-400">{
                          menuProfile.preparationTime === 'fast' ? 'Быстро (до 15 мин)' :
                          menuProfile.preparationTime === 'medium' ? 'Средне (15-45 мин)' : 'Медленно (45+ мин)'
                        }</span>
                      </label>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        {[
                          { value: 'fast', label: '⚡ Быстро', desc: 'До 15 минут', time: '⏱️ <15 мин' },
                          { value: 'medium', label: '⏳ Средне', desc: '15-45 минут', time: '⏱️ 15-45 мин' },
                          { value: 'slow', label: '🐌 Медленно', desc: 'Более 45 минут', time: '⏱️ 45+ мин' }
                        ].map((time) => (
                          <button
                            key={time.value}
                            onClick={() => setMenuProfile(prev => ({ ...prev, preparationTime: time.value }))}
                            className={`p-4 rounded-lg border text-center transition-all ${
                              menuProfile.preparationTime === time.value
                                ? 'border-cyan-400 bg-cyan-600/20 text-cyan-300'
                                : 'border-gray-600 bg-gray-700/50 text-gray-300 hover:border-cyan-600'
                            }`}
                          >
                            <div className="font-bold">{time.label}</div>
                            <div className="text-xs text-gray-400 mt-1">{time.desc}</div>
                            <div className="text-xs text-cyan-400 mt-1">{time.time}</div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Ingredient Budget Level */}
                    <div>
                      <label className="block text-sm font-bold text-gray-300 mb-3">
                        Бюджет на ингредиенты: <span className="text-cyan-400">{
                          menuProfile.ingredientBudget === 'low' ? 'Ограниченный' :
                          menuProfile.ingredientBudget === 'medium' ? 'Средний' : 'Высокий'
                        }</span>
                      </label>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        {[
                          { value: 'low', label: '💰 Ограниченный', desc: 'Доступные продукты', range: 'до 30% от выручки' },
                          { value: 'medium', label: '💰💰 Средний', desc: 'Качественные продукты', range: '30-40% от выручки' },
                          { value: 'high', label: '💰💰💰 Высокий', desc: 'Премиум ингредиенты', range: '40%+ от выручки' }
                        ].map((budget) => (
                          <button
                            key={budget.value}
                            onClick={() => setMenuProfile(prev => ({ ...prev, ingredientBudget: budget.value }))}
                            className={`p-4 rounded-lg border text-center transition-all ${
                              menuProfile.ingredientBudget === budget.value
                                ? 'border-cyan-400 bg-cyan-600/20 text-cyan-300'
                                : 'border-gray-600 bg-gray-700/50 text-gray-300 hover:border-cyan-600'
                            }`}
                          >
                            <div className="font-bold">{budget.label}</div>
                            <div className="text-xs text-gray-400 mt-1">{budget.desc}</div>
                            <div className="text-xs text-yellow-400 mt-1">{budget.range}</div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Additional Kitchen Capabilities */}
                    <div>
                      <label className="block text-sm font-bold text-gray-300 mb-3">
                        Дополнительные возможности (отметьте доступные):
                      </label>
                      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                        {[
                          { value: 'delivery', label: '🚚 Доставка', desc: 'Упаковка, сохранность' },
                          { value: 'takeaway', label: '🥡 Навынос', desc: 'Быстрое приготовление' },
                          { value: 'catering', label: '🎪 Кейтеринг', desc: 'Массовое производство' },
                          { value: 'prep_kitchen', label: '🏭 Заготовочная', desc: 'Заготовки заранее' },
                          { value: 'pastry_section', label: '🧁 Кондитерский цех', desc: 'Выпечка, десерты' },
                          { value: 'wine_program', label: '🍷 Винная программа', desc: 'Сочетание с винами' },
                          { value: 'breakfast_service', label: '🌅 Завтраки', desc: 'Утреннее меню' },
                          { value: 'late_night', label: '🌙 Ночное меню', desc: 'Поздние часы' },
                          { value: 'banquet_hall', label: '🎉 Банкетный зал', desc: 'Мероприятия' }
                        ].map((capability) => (
                          <button
                            key={capability.value}
                            onClick={() => {
                              const current = menuProfile.kitchenCapabilities || [];
                              const updated = current.includes(capability.value)
                                ? current.filter(c => c !== capability.value)
                                : [...current, capability.value];
                              setMenuProfile(prev => ({ ...prev, kitchenCapabilities: updated }));
                            }}
                            className={`p-3 rounded-lg border text-left transition-all ${
                              (menuProfile.kitchenCapabilities || []).includes(capability.value)
                                ? 'border-blue-400 bg-blue-600/20 text-blue-300'
                                : 'border-gray-600 bg-gray-700/50 text-gray-300 hover:border-blue-600'
                            }`}
                          >
                            <div className="font-semibold text-xs">{capability.label}</div>
                            <div className="text-xs text-gray-400 mt-1">{capability.desc}</div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 5: Free Form Description & Expectations */}
                {menuWizardStep === 5 && (
                  <div className="space-y-6">
                    <h3 className="text-xl font-bold text-cyan-300 mb-6">✍️ Опишите ваши ожидания от меню</h3>
                    
                    {/* Menu Description */}
                    <div>
                      <label className="block text-sm font-bold text-gray-300 mb-3">
                        Краткое описание заведения и его концепции:
                      </label>
                      <textarea
                        value={menuProfile.menuDescription}
                        onChange={(e) => setMenuProfile(prev => ({ ...prev, menuDescription: e.target.value }))}
                        placeholder="Расскажите о своем заведении: какая атмосфера, кто ваши клиенты, какие особенности интерьера, расположения... Например: 'Уютная семейная пиццерия в центре города с открытой кухней и игровой зоной для детей. Ориентируемся на семьи с детьми и студентов.'"
                        className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:border-cyan-400 focus:outline-none resize-none"
                        rows="4"
                      />
                      <div className="text-xs text-gray-400 mt-1">
                        {menuProfile.menuDescription.length}/500 символов
                      </div>
                    </div>

                    {/* Expectations */}
                    <div>
                      <label className="block text-sm font-bold text-gray-300 mb-3">
                        Что вы ожидаете от нового меню?
                      </label>
                      <textarea
                        value={menuProfile.expectations}
                        onChange={(e) => setMenuProfile(prev => ({ ...prev, expectations: e.target.value }))}
                        placeholder="Опишите свои ожидания подробно: какие блюда хотели бы видеть, какой стиль подачи, особые требования к ингредиентам, проблемы которые хотите решить... Например: 'Хочу добавить больше вегетарианских блюд, уменьшить время приготовления, использовать сезонные продукты, сделать меню более Instagram-френдли для привлечения молодежи.'"
                        className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:border-cyan-400 focus:outline-none resize-none"
                        rows="5"
                      />
                      <div className="text-xs text-gray-400 mt-1">
                        {menuProfile.expectations.length}/1000 символов
                      </div>
                    </div>

                    {/* Additional Notes */}
                    <div>
                      <label className="block text-sm font-bold text-gray-300 mb-3">
                        Дополнительные пожелания и особенности:
                      </label>
                      <textarea
                        value={menuProfile.additionalNotes}
                        onChange={(e) => setMenuProfile(prev => ({ ...prev, additionalNotes: e.target.value }))}
                        placeholder="Любые дополнительные детали: сезонные ограничения, предпочтения поставщиков, аллергии которые нужно учесть, планируемые акции, особенности подачи... Например: 'У нас нет фритюрницы, работаем только с локальными поставщиками, планируем запустить доставку, нужны блюда которые не теряют вид при транспортировке.'"
                        className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:border-cyan-400 focus:outline-none resize-none"
                        rows="4"
                      />
                      <div className="text-xs text-gray-400 mt-1">
                        {menuProfile.additionalNotes.length}/500 символов
                      </div>
                    </div>

                    {/* Summary Preview */}
                    <div className="bg-gradient-to-r from-cyan-600/20 to-blue-600/20 border border-cyan-400/30 rounded-xl p-6">
                      <h4 className="text-xl font-bold text-cyan-300 mb-4">📋 Итоговый профиль меню</h4>
                      
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 text-sm">
                        <div className="space-y-3">
                          <div>
                            <span className="text-gray-400">Тип меню:</span>
                            <span className="text-cyan-300 font-semibold ml-2">
                              {menuProfile.menuType === 'full_menu' && '🍽️ Полное меню'}
                              {menuProfile.menuType === 'seasonal' && '🍂 Сезонное меню'}
                              {menuProfile.menuType === 'business_lunch' && '💼 Бизнес-ланч'}
                              {menuProfile.menuType === 'evening_menu' && '🌙 Вечернее меню'}
                              {menuProfile.menuType === 'breakfast' && '☀️ Завтраки'}
                              {menuProfile.menuType === 'bar_menu' && '🍷 Барная карта'}
                              {menuProfile.menuType === 'dessert_menu' && '🍰 Десертная карта'}
                              {menuProfile.menuType === 'banquet' && '🎉 Банкетное меню'}
                              {menuProfile.menuType === 'street_food' && '🚚 Стрит-фуд'}
                            </span>
                          </div>
                          
                          <div>
                            <span className="text-gray-400">Количество блюд:</span>
                            <span className="text-cyan-300 font-semibold ml-2">{menuProfile.dishCount}</span>
                          </div>
                          
                          <div>
                            <span className="text-gray-400">Средний чек:</span>
                            <span className="text-cyan-300 font-semibold ml-2">
                              {menuProfile.averageCheckMin}₽ - {menuProfile.averageCheckMax}₽
                            </span>
                          </div>
                          
                          <div>
                            <span className="text-gray-400">Кухня:</span>
                            <span className="text-cyan-300 font-semibold ml-2">
                              {menuProfile.cuisineStyle === 'european' && '🇪🇺 Европейская'}
                              {menuProfile.cuisineStyle === 'italian' && '🇮🇹 Итальянская'}
                              {menuProfile.cuisineStyle === 'french' && '🇫🇷 Французская'}
                              {menuProfile.cuisineStyle === 'asian' && '🥢 Азиатская'}
                              {menuProfile.cuisineStyle === 'japanese' && '🇯🇵 Японская'}
                              {menuProfile.cuisineStyle === 'chinese' && '🇨🇳 Китайская'}
                              {menuProfile.cuisineStyle === 'american' && '🇺🇸 Американская'}
                              {menuProfile.cuisineStyle === 'mexican' && '🇲🇽 Мексиканская'}
                              {menuProfile.cuisineStyle === 'russian' && '🇷🇺 Русская'}
                              {menuProfile.cuisineStyle === 'georgian' && '🇬🇪 Грузинская'}
                              {menuProfile.cuisineStyle === 'uzbek' && '🇺🇿 Узбекская'}
                              {menuProfile.cuisineStyle === 'fusion' && '🎭 Фьюжн'}
                            </span>
                          </div>
                          
                          <div>
                            <span className="text-gray-400">Целевая аудитория:</span>
                            <span className="text-cyan-300 font-semibold ml-2">
                              {menuProfile.targetAudience === 'families' && '👨‍👩‍👧‍👦 Семьи с детьми'}
                              {menuProfile.targetAudience === 'business' && '💼 Бизнес-аудитория'}
                              {menuProfile.targetAudience === 'students' && '🎓 Студенты'}
                              {menuProfile.targetAudience === 'young_professionals' && '💻 Молодые специалисты'}
                              {menuProfile.targetAudience === 'seniors' && '👴👵 Пожилые люди'}
                              {menuProfile.targetAudience === 'tourists' && '📸 Туристы'}
                              {menuProfile.targetAudience === 'hipsters' && '🎨 Творческая молодежь'}
                              {menuProfile.targetAudience === 'athletes' && '💪 Спортсмены'}
                              {menuProfile.targetAudience === 'gourmets' && '🍷 Гурманы'}
                            </span>
                          </div>
                        </div>
                        
                        <div className="space-y-3">
                          <div>
                            <span className="text-gray-400">Регион:</span>
                            <span className="text-cyan-300 font-semibold ml-2">
                              {menuProfile.region === 'moskva' && '🏛️ Москва'}
                              {menuProfile.region === 'spb' && '🏰 СПб'}
                              {menuProfile.region === 'kazan' && '🕌 Казань'}
                              {menuProfile.region === 'ekaterinburg' && '🏔️ Екатеринбург'}
                              {menuProfile.region === 'novosibirsk' && '❄️ Новосибирск'}
                              {menuProfile.region === 'krasnodar' && '🌻 Краснодар'}
                              {menuProfile.region === 'rostov' && '🌾 Ростов-на-Дону'}
                              {menuProfile.region === 'volgograd' && '🏞️ Волгоград'}
                              {menuProfile.region === 'other' && '🌍 Другой регион'}
                            </span>
                          </div>
                          
                          {(menuProfile.cuisineInfluences || []).length > 0 && (
                            <div>
                              <span className="text-gray-400">Влияния кухонь:</span>
                              <div className="mt-1">
                                {(menuProfile.cuisineInfluences || []).map(influence => (
                                  <span key={influence} className="inline-block px-2 py-1 bg-purple-600/20 text-purple-300 rounded text-xs mr-1 mb-1">
                                    {influence}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {(menuProfile.menuGoals || []).length > 0 && (
                            <div>
                              <span className="text-gray-400">Цели меню:</span>
                              <div className="mt-1">
                                {(menuProfile.menuGoals || []).slice(0, 3).map(goal => (
                                  <span key={goal} className="inline-block px-2 py-1 bg-green-600/20 text-green-300 rounded text-xs mr-1 mb-1">
                                    {goal}
                                  </span>
                                ))}
                                {(menuProfile.menuGoals || []).length > 3 && (
                                  <span className="text-gray-400 text-xs">+{(menuProfile.menuGoals || []).length - 3} еще</span>
                                )}
                              </div>
                            </div>
                          )}
                          
                          <div>
                            <span className="text-gray-400">Уровень персонала:</span>
                            <span className="text-cyan-300 font-semibold ml-2">
                              {menuProfile.staffSkillLevel === 'beginner' && '🔰 Начинающий'}
                              {menuProfile.staffSkillLevel === 'medium' && '⭐ Средний'}
                              {menuProfile.staffSkillLevel === 'advanced' && '🎯 Продвинутый'}
                              {menuProfile.staffSkillLevel === 'professional' && '👨‍🍳 Профессиональный'}
                            </span>
                          </div>
                          
                          <div>
                            <span className="text-gray-400">Время приготовления:</span>
                            <span className="text-cyan-300 font-semibold ml-2">
                              {menuProfile.preparationTime === 'fast' && '⚡ Быстро'}
                              {menuProfile.preparationTime === 'medium' && '⏳ Средне'}
                              {menuProfile.preparationTime === 'slow' && '🐌 Медленно'}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      {(menuProfile.menuDescription || menuProfile.expectations) && (
                        <div className="mt-4 pt-4 border-t border-cyan-400/30">
                          {menuProfile.menuDescription && (
                            <div className="mb-3">
                              <span className="text-gray-400 font-semibold">Описание заведения:</span>
                              <p className="text-cyan-300 text-sm mt-1 italic">"{menuProfile.menuDescription}"</p>
                            </div>
                          )}
                          {menuProfile.expectations && (
                            <div>
                              <span className="text-gray-400 font-semibold">Ожидания от меню:</span>
                              <p className="text-cyan-300 text-sm mt-1 italic">"{menuProfile.expectations}"</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
                {menuWizardStep === 4 && (
                  <div className="space-y-6">
                    <h3 className="text-xl font-bold text-cyan-300 mb-6">🎯 Финальная проверка</h3>
                    
                    <div className="bg-gray-700/50 rounded-xl p-6 space-y-4">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <div className="text-sm text-gray-400">Тип заведения:</div>
                          <div className="font-semibold text-cyan-300">
                            {menuProfile.menuType === 'restaurant' && '🍽️ Ресторан'}
                            {menuProfile.menuType === 'cafe' && '☕ Кофейня'}
                            {menuProfile.menuType === 'fastfood' && '🍔 Фаст-фуд'}
                            {menuProfile.menuType === 'bar' && '🍷 Бар'}
                            {menuProfile.menuType === 'bistro' && '🥘 Бистро'}
                            {menuProfile.menuType === 'pizzeria' && '🍕 Пиццерия'}
                            {menuProfile.menuType === 'sushi' && '🍣 Суши-бар'}
                            {menuProfile.menuType === 'bakery' && '🥐 Пекарня'}
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-400">Количество блюд:</div>
                          <div className="font-semibold text-cyan-300">{menuProfile.dishCount} блюд</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-400">Средний чек:</div>
                          <div className="font-semibold text-cyan-300">
                            {menuProfile.averageCheck === 'budget' && '💰 До 500₽'}
                            {menuProfile.averageCheck === 'medium' && '💰💰 500-1500₽'}
                            {menuProfile.averageCheck === 'premium' && '💰💰💰 1500-3000₽'}
                            {menuProfile.averageCheck === 'luxury' && '💰💰💰💰 3000₽+'}
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-400">Стиль кухни:</div>
                          <div className="font-semibold text-cyan-300">
                            {menuProfile.cuisineStyle === 'european' && '🇪🇺 Европейская'}
                            {menuProfile.cuisineStyle === 'italian' && '🇮🇹 Итальянская'}
                            {menuProfile.cuisineStyle === 'asian' && '🥢 Азиатская'}
                            {menuProfile.cuisineStyle === 'american' && '🇺🇸 Американская'}
                            {menuProfile.cuisineStyle === 'fusion' && '🎭 Фьюжн'}
                            {menuProfile.cuisineStyle === 'russian' && '🇷🇺 Русская'}
                            {menuProfile.cuisineStyle === 'georgian' && '🇬🇪 Грузинская'}
                            {menuProfile.cuisineStyle === 'mexican' && '🇲🇽 Мексиканская'}
                            {menuProfile.cuisineStyle === 'indian' && '🇮🇳 Индийская'}
                          </div>
                        </div>
                      </div>
                      
                      {menuProfile.specialRequirements && menuProfile.specialRequirements.length > 0 && (
                        <div>
                          <div className="text-sm text-gray-400 mb-2">Особые требования:</div>
                          <div className="flex flex-wrap gap-2">
                            {menuProfile.specialRequirements.map(req => (
                              <span key={req} className="px-3 py-1 bg-cyan-600/20 text-cyan-300 rounded-full text-sm">
                                {req === 'vegetarian' && '🌱 Вегетарианское'}
                                {req === 'vegan' && '🥬 Веганское'}  
                                {req === 'halal' && '☪️ Халяль'}
                                {req === 'glutenfree' && '🌾 Без глютена'}
                                {req === 'local' && '🏞️ Локальные продукты'}
                                {req === 'seasonal' && '🍂 Сезонное'}
                                {req === 'healthy' && '💪 ПП'}
                                {req === 'premium' && '💎 Премиум'}
                                {req === 'budget' && '💰 Бюджетное'}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <div className="bg-gradient-to-r from-cyan-600/20 to-blue-600/20 border border-cyan-400/30 rounded-xl p-6 text-center">
                      <div className="text-4xl mb-4">🚀</div>
                      <h4 className="text-xl font-bold text-cyan-300 mb-2">Готово к генерации!</h4>
                      <p className="text-gray-300">
                        ИИ создаст {menuProfile.dishCount} блюд с умной оптимизацией ингредиентов для максимальной экономии закупок
                      </p>
                    </div>
                  </div>
                )}

                {/* Enhanced Navigation Buttons */}
                <div className="flex justify-between mt-12 pt-8 border-t border-gray-600/50">
                  <button
                    onClick={() => setMenuWizardStep(Math.max(1, menuWizardStep - 1))}
                    disabled={menuWizardStep === 1}
                    className="group flex items-center px-6 py-3 rounded-xl bg-gray-600/80 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed text-white font-semibold transition-all duration-300 hover:scale-105 hover:shadow-lg"
                  >
                    <span className="mr-2 group-hover:-translate-x-1 transition-transform duration-300">←</span>
                    Назад
                  </button>
                  
                  <button
                    onClick={() => {
                      if (menuWizardStep < 5) {
                        setMenuWizardStep(menuWizardStep + 1);
                      } else {
                        // Generate menu
                        generateMenu();
                      }
                    }}
                    disabled={
                      (menuWizardStep === 1 && (!menuProfile.menuType)) ||
                      (menuWizardStep === 2 && !menuProfile.cuisineStyle) ||
                      (menuWizardStep === 3 && (!menuProfile.audienceOccupations || menuProfile.audienceOccupations.length === 0)) ||
                      isGenerating
                    }
                    className="wizard-next-button group flex items-center px-8 py-3 rounded-xl text-white font-bold transition-all duration-300 hover:scale-105 disabled:opacity-30 disabled:cursor-not-allowed disabled:transform-none relative overflow-hidden"
                  >
                    {isGenerating ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 818-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014  12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Создаю меню...
                      </>
                    ) : menuWizardStep === 5 ? (
                      <>
                        <span className="mr-2">🚀</span>
                        Создать меню
                        <span className="ml-2 group-hover:translate-x-1 transition-transform duration-300">✨</span>
                      </>
                    ) : (
                      <>
                        Далее
                        <span className="ml-2 group-hover:translate-x-1 transition-transform duration-300">→</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Create Tech Card View (existing content) */}
        {currentView === 'create' && (
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
                          <h4 className="text-purple-300 font-bold mb-3 text-sm sm:text-base">📝 СОЗДАНИЕ ТЕХКАРТЫ</h4>
                          <div className="space-y-2 text-xs sm:text-sm text-gray-300">
                            <p>• <strong>Пишите максимально подробно</strong> - чем точнее опишете, тем лучше результат</p>
                            <p>• <strong>Укажите количество порций</strong> - например "на 4 порции"</p>
                            <p>• <strong>Добавьте особенности</strong> - "средней прожарки", "с хрустящей корочкой"</p>
                            <p>• <strong>Голосовой ввод 🎤</strong> - нажмите кнопку микрофона для диктовки блюда</p>
                            <p className="text-purple-200">💡 <em>Пример: "Стейк из говядины на 4 порции, средней прожарки, общий выход 800г"</em></p>
                          </div>
                        </div>
                        
                        <div>
                          <h4 className="text-purple-300 font-bold mb-3 text-sm sm:text-base">✏️ РЕДАКТИРОВАНИЕ</h4>
                          <div className="space-y-2 text-xs sm:text-sm text-gray-300">
                            <p>• <strong>Редактируйте ингредиенты</strong> - можно менять количество и цены интерактивно</p>
                            <p>• <strong>AI редактирование</strong> - опишите что изменить, ИИ переделает техкарту</p>
                            <p>• <strong>Ручная правка</strong> - кликайте на любой текст для быстрого редактирования</p>
                            <p>• <strong>Сохранение в PDF</strong> - техкарта без цен для печати в кухню</p>
                          </div>
                        </div>

                        <div>
                          <h4 className="text-yellow-300 font-bold mb-3 text-sm sm:text-base">⭐ PRO ФУНКЦИИ</h4>
                          <div className="space-y-2 text-xs sm:text-sm text-gray-300">
                            <p>• <strong>🏢 ПРОФИЛЬ ЗАВЕДЕНИЯ</strong> - настройка типа заведения, кухни, среднего чека</p>
                            <p>• <strong>🌟 ВДОХНОВЕНИЕ</strong> - креативные твисты на блюда из других кухонь</p>
                            <p>• <strong>🧪 ЛАБОРАТОРИЯ</strong> - экспериментальные блюда с изображениями от ИИ</p>
                            <p>• <strong>⚡ ПРОКАЧАТЬ БЛЮДО</strong> - улучшение рецептов до профессионального уровня</p>
                            <p>• <strong>💼 ФИНАНСОВЫЙ АНАЛИЗ</strong> - детальный анализ рентабельности с советами</p>
                            <p>• <strong>💬 СКРИПТ ПРОДАЖ</strong> - тексты для официантов и продвижения блюд</p>
                            <p>• <strong>🍷 ФУДПЕЙРИНГ</strong> - рекомендации напитков и гарниров к блюду</p>
                            <p>• <strong>📸 СОВЕТЫ ПО ФОТО</strong> - профессиональные советы по фотосъемке блюд</p>
                          </div>
                        </div>

                        <div>
                          <h4 className="text-cyan-300 font-bold mb-3 text-sm sm:text-base">🔧 ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ</h4>
                          <div className="space-y-2 text-xs sm:text-sm text-gray-300">
                            <p>• <strong>📋 ИСТОРИЯ</strong> - все созданные техкарты сохраняются автоматически</p>
                            <p>• <strong>🔄 ПЕРСОНАЛИЗАЦИЯ</strong> - PRO функции адаптируются под ваш профиль заведения</p>
                            <p>• <strong>💾 СОХРАНЕНИЕ ЭКСПЕРИМЕНТОВ</strong> - результаты лаборатории можно сохранить</p>
                            <p>• <strong>🎯 УМНЫЕ РЕКОМЕНДАЦИИ</strong> - все функции учитывают тип вашего заведения</p>
                          </div>
                        </div>
                      </div>
                      
                      <div className="mt-4 sm:mt-6 pt-3 sm:pt-4 border-t border-purple-400/30">
                        <h4 className="text-yellow-300 font-bold mb-2 text-sm sm:text-base">💰 О СЕБЕСТОИМОСТИ</h4>
                        <p className="text-xs sm:text-sm text-gray-300">
                          Себестоимость рассчитывается по среднерыночным ценам 2025 года с учетом вашего региона и инфляции. 
                          Нейросеть может ошибаться - всегда проверяйте расчеты! 
                          <strong className="text-purple-300"> Детальный калькулятор на основе прайсов ваших поставщиков в разработке.</strong>
                        </p>
                      </div>

                      <div className="mt-4 sm:mt-6 pt-3 sm:pt-4 border-t border-purple-400/30">
                        <h4 className="text-green-300 font-bold mb-2 text-sm sm:text-base">🚀 СОВЕТЫ ДЛЯ МАКСИМАЛЬНОЙ ЭФФЕКТИВНОСТИ</h4>
                        <div className="space-y-1 text-xs sm:text-sm text-gray-300">
                          <p>• <strong>Настройте профиль заведения</strong> - все функции станут более точными</p>
                          <p>• <strong>Используйте функции последовательно</strong> - сначала создайте техкарту, затем PRO функции</p>
                          <p>• <strong>Экспериментируйте в Лаборатории</strong> - создавайте уникальные блюда для меню</p>
                          <p>• <strong>Анализируйте финансы</strong> - оптимизируйте затраты и увеличивайте прибыль</p>
                        </div>
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
                        onClick={isListening ? stopVoiceRecognition : startVoiceRecognition}
                        disabled={false}
                        className={`absolute right-2 bottom-2 p-2 rounded-lg transition-all duration-300 ${
                          isListening 
                            ? 'bg-red-600 hover:bg-red-700 animate-pulse shadow-lg shadow-red-500/50' 
                            : 'bg-purple-600 hover:bg-purple-700'
                        } text-white w-10 h-10 sm:w-12 sm:h-12 flex items-center justify-center`}
                        title={isListening ? "Остановить запись" : "Голосовой ввод"}
                      >
                        {isListening ? (
                          // Stop icon when recording
                          <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
                          </svg>
                        ) : (
                          // Microphone icon when not recording
                          <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                          </svg>
                        )}
                      </button>
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={!dishName.trim() || isGenerating}
                    className={`w-full ${isGenerating ? 'bg-gray-600 cursor-not-allowed' : 'btn-primary'} text-white font-bold py-3 sm:py-4 px-6 rounded-lg transition-colors flex items-center justify-center text-sm sm:text-base min-h-[48px] sm:min-h-[56px]`}
                    title="Создать техкарту с расчетом себестоимости и рецептом"
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
                    
                    {/* Venue Profile Button */}
                    <button
                      onClick={() => setShowVenueProfileModal(true)}
                      className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold py-3 sm:py-4 px-4 sm:px-6 rounded-lg transition-all transform hover:scale-105 mb-3 sm:mb-4 text-sm sm:text-base min-h-[48px] shadow-lg"
                      title="🏢 Настройте тип заведения, кухню и средний чек для персонализации всех функций"
                    >
                      🏢 ПРОФИЛЬ ЗАВЕДЕНИЯ
                    </button>
                    {venueProfile.venue_type && (
                      <div className="text-xs sm:text-sm text-purple-300 text-center mb-3 sm:mb-4 p-2 bg-purple-900/20 rounded">
                        {venueTypes[venueProfile.venue_type]?.name} • {venueProfile.cuisine_focus?.map(c => cuisineTypes[c]?.name).join(', ')} • {venueProfile.average_check}₽
                      </div>
                    )}
                    {userEquipment.length > 0 && (
                      <div className="text-xs sm:text-sm text-purple-400 text-center mb-3 sm:mb-4">
                        Выбрано {userEquipment.length} единиц оборудования
                      </div>
                    )}
                    
                    {/* Price Management Button */}
                    <button
                      onClick={() => setShowPriceModal(true)}
                      className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 sm:py-4 px-4 sm:px-6 rounded-lg transition-colors mb-3 sm:mb-4 text-sm sm:text-base min-h-[48px]"
                      title="📊 Загрузите Excel/CSV файлы с ценами поставщиков для точного расчета себестоимости"
                    >
                      УПРАВЛЕНИЕ ПРАЙСАМИ
                    </button>
                    {userPrices.length > 0 && (
                      <div className="text-xs sm:text-sm text-green-400 text-center mb-3 sm:mb-4">
                        Загружено {userPrices.length} позиций
                      </div>
                    )}
                    <div className="text-xs sm:text-sm text-green-400 text-center mb-3 sm:mb-4 p-2 bg-green-900/20 rounded">
                      ✅ Загрузка Excel/CSV прайс-листов полностью готова!
                    </div>
                    
                    {/* ПРО AI функции */}
                    <div className="border-t border-purple-400/20 pt-3 sm:pt-4">
                      <h4 className="text-sm sm:text-base font-bold text-purple-200 mb-3">AI ДОПОЛНЕНИЯ</h4>
                      
                      <div className="grid grid-cols-1 gap-2 sm:gap-3">
                        <button
                          onClick={() => generateSalesScript()}
                          disabled={isGenerating}
                          className={`w-full ${isGenerating ? 'bg-gray-600 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px]`}
                          title="💬 СКРИПТ ПРОДАЖ: Генерирует профессиональные тексты для официантов с аргументами и техниками продаж"
                        >
                          СКРИПТ ПРОДАЖ
                        </button>
                        
                        <button
                          onClick={generateFoodPairing}
                          disabled={isGenerating}
                          className={`w-full ${isGenerating ? 'bg-gray-600 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px]`}
                          title="🍷 ФУДПЕЙРИНГ: Подбирает идеальные напитки, гарниры и закуски к вашему блюду с объяснением сочетаний"
                        >
                          ФУДПЕЙРИНГ
                        </button>
                        
                        <button
                          onClick={generateInspiration}
                          disabled={isGenerating}
                          className={`w-full ${isGenerating ? 'bg-gray-600 cursor-not-allowed' : 'btn-inspiration'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px]`}
                          title="🌟 ВДОХНОВЕНИЕ: Создает креативный твист на ваше блюдо, используя техники и ингредиенты кухонь других стран"
                        >
                          🌟 ВДОХНОВЕНИЕ
                        </button>
                        
                        <button
                          onClick={conductExperiment}
                          disabled={isExperimenting}
                          className={`w-full ${isExperimenting ? 'bg-gray-600 cursor-not-allowed' : 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px] laboratory-button`}
                          title="🧪 ЛАБОРАТОРИЯ: Создает экспериментальные блюда с неожиданными сочетаниями ингредиентов и генерирует изображение результата"
                        >
                          {isExperimenting ? 'ЭКСПЕРИМЕНТИРУЮ...' : '🧪 ЛАБОРАТОРИЯ'}
                        </button>
                        
                        <button
                          onClick={generatePhotoTips}
                          disabled={isGenerating}
                          className={`w-full ${isGenerating ? 'bg-gray-600 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px]`}
                          title="📸 СОВЕТЫ ПО ФОТО: Профессиональные рекомендации по фотографии блюд для социальных сетей и меню"
                        >
                          СОВЕТЫ ПО ФОТО
                        </button>
                        
                        <button
                          onClick={improveDish}
                          disabled={isImprovingDish || !techCard}
                          className={`w-full ${isImprovingDish || !techCard ? 'bg-gray-600 cursor-not-allowed' : 'bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px]`}
                          title="⚡ ПРОКАЧАТЬ БЛЮДО: Улучшает ваш рецепт профессиональными техниками и секретами шеф-поваров до версии 2.0"
                        >
                          {isImprovingDish ? 'УЛУЧШАЮ...' : '⚡ ПРОКАЧАТЬ БЛЮДО'}
                        </button>
                        
                        <button
                          onClick={analyzeFinances}
                          disabled={isAnalyzingFinances || !techCard}
                          className={`w-full ${isAnalyzingFinances || !techCard ? 'bg-gray-600 cursor-not-allowed' : 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px]`}
                          title="💼 ФИНАНСОВЫЙ АНАЛИЗ: Анализирует рентабельность блюда и дает конкретные советы по оптимизации затрат и увеличению прибыли"
                        >
                          {isAnalyzingFinances ? 'АНАЛИЗИРУЮ...' : '💼 ФИНАНСЫ'}
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
                      title="🤖 Изменить техкарту с помощью ИИ на основе ваших инструкций"
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
                    title="✏️ Открыть режим ручного редактирования техкарты в текстовом поле"
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
                      title="📋 Скопировать техкарту в буфер обмена для вставки в другие приложения"
                    >
                      КОПИРОВАТЬ
                    </button>
                    <button 
                      onClick={handlePrintTechCard}
                      className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-bold transition-colors text-sm sm:text-base min-h-[44px] sm:min-h-[48px]"
                      title="📄 Экспортировать техкарту в PDF без цен для печати на кухне"
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
                        title="➕ Добавить новый ингредиент в список для редактирования"
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
                        title="💾 Сохранить изменения ингредиентов в техкарте с пересчетом стоимости"
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
                              title="🗑️ Удалить ингредиент из списка"
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
                              
                              // Если не найден, считаем по ингредиентам с учетом единиц измерения
                              const totalWeight = currentIngredients.reduce((total, ing) => {
                                const quantity = parseFloat(ing.quantity) || 0;
                                const unit = (ing.unit || 'г').toLowerCase();
                                
                                // Конвертируем в граммы с учетом единиц измерения
                                if (unit.includes('кг')) {
                                  return total + (quantity * 1000); // кг в граммы
                                } else if (unit.includes('л')) {
                                  return total + (quantity * 1000); // литры принимаем как граммы (плотность ~1)
                                } else if (unit.includes('мл')) {
                                  return total + quantity; // мл = граммы (плотность ~1)
                                } else if (unit.includes('шт') || unit.includes('штук')) {
                                  // Для штучных товаров используем примерные веса
                                  const name = (ing.name || '').toLowerCase();
                                  if (name.includes('булочка') || name.includes('булка')) {
                                    return total + (quantity * 80); // булочка ~80г
                                  } else if (name.includes('яйц')) {
                                    return total + (quantity * 50); // яйцо ~50г
                                  } else if (name.includes('картофел')) {
                                    return total + (quantity * 150); // средняя картофелина ~150г
                                  } else if (name.includes('лук')) {
                                    return total + (quantity * 100); // средняя луковица ~100г
                                  } else if (name.includes('помидор') || name.includes('томат')) {
                                    return total + (quantity * 120); // средний помидор ~120г
                                  } else {
                                    return total + (quantity * 50); // средний вес штучного продукта
                                  }
                                } else {
                                  return total + quantity; // по умолчанию считаем граммы
                                }
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
        )}
      </main>

      {/* Voice Recognition Modal */}
      {showVoiceModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 text-center border border-purple-500/30 max-w-md w-full mx-4">
            <div className="mb-6">
              {isListening ? (
                <div className="w-20 h-20 mx-auto bg-red-500 rounded-full flex items-center justify-center animate-pulse shadow-lg shadow-red-500/50">
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
            <p className="text-gray-300 mb-6">
              {voiceStatus}
            </p>
            
            {/* Action buttons */}
            <div className="flex gap-4 justify-center">
              {isListening ? (
                <button
                  onClick={stopVoiceRecognition}
                  className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
                  </svg>
                  ОСТАНОВИТЬ
                </button>
              ) : (
                <button
                  onClick={() => setShowVoiceModal(false)}
                  className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
                >
                  ЗАКРЫТЬ
                </button>
              )}
            </div>
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
                title="➕ Добавить новую строку ингредиента в редактор"
              >
                ДОБАВИТЬ
              </button>
              <button
                onClick={saveIngredientsChanges}
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg"
                title="💾 Применить изменения ингредиентов к техкарте"
              >
                СОХРАНИТЬ
              </button>
              <button
                onClick={() => setIsEditingIngredients(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
                title="❌ Закрыть редактор без сохранения изменений"
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
                title="❌ Закрыть окно управления прайсами"
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
                title="🗑️ Удалить все загруженные прайс-листы из памяти"
              >
                ОЧИСТИТЬ ВСЕ
              </button>
              <button
                onClick={() => setShowPriceModal(false)}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
                title="✅ Закрыть окно управления прайсами"
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
      {(isGenerating || isGeneratingSimpleMenu) && (
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
                  {loadingType === 'menu' && 'Создаю идеальное меню...'}
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
              
              {/* Tips and Lifehacks for Menu Generation */}
              {loadingType === 'menu' && (
                <div className="mt-8 p-4 bg-gradient-to-br from-purple-900/20 to-blue-900/20 rounded-xl border border-purple-400/30">
                  <div className="flex items-start space-x-3">
                    <div className="text-3xl flex-shrink-0 animate-bounce">
                      {menuGenerationTips[currentMenuTipIndex]?.icon}
                    </div>
                    <div className="text-left">
                      <h4 className="text-purple-300 font-bold text-sm mb-2">
                        {menuGenerationTips[currentMenuTipIndex]?.title}
                      </h4>
                      <p className="text-gray-300 text-xs leading-relaxed">
                        {menuGenerationTips[currentMenuTipIndex]?.text}
                      </p>
                    </div>
                  </div>
                  <div className="mt-3 flex justify-center space-x-1">
                    {menuGenerationTips.slice(0, 5).map((_, index) => (
                      <div
                        key={index}
                        className={`w-1.5 h-1.5 rounded-full transition-all ${
                          index === (currentMenuTipIndex % 5) ? 'bg-purple-400' : 'bg-gray-600'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              )}
              
              {/* Tips for Other Types */}
              {loadingType === 'techcard' && (
                <div className="mt-8 p-4 bg-gradient-to-br from-purple-900/20 to-blue-900/20 rounded-xl border border-purple-400/30">
                  <div className="flex items-start space-x-3">
                    <div className="text-3xl flex-shrink-0 animate-bounce">
                      {receptionTips[currentTipIndex]?.icon}
                    </div>
                    <div className="text-left">
                      <h4 className="text-purple-300 font-bold text-sm mb-2">
                        {receptionTips[currentTipIndex]?.title}
                      </h4>
                      <p className="text-gray-300 text-xs leading-relaxed">
                        {receptionTips[currentTipIndex]?.text}
                      </p>
                    </div>
                  </div>
                  <div className="mt-3 flex justify-center space-x-1">
                    {receptionTips.slice(0, 5).map((_, index) => (
                      <div
                        key={index}
                        className={`w-1.5 h-1.5 rounded-full transition-all ${
                          index === (currentTipIndex % 5) ? 'bg-purple-400' : 'bg-gray-600'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              )}
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

      {/* Finances Modal - Simplified Version */}
      {showFinancesModal && financesResult && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-6 w-full max-w-5xl max-h-[90vh] overflow-y-auto border border-green-500/30">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-3xl font-bold text-green-300">💼 ФИНАНСОВЫЙ АНАЛИЗ: {financesResult.dish_name}</h2>
              <button
                onClick={() => setShowFinancesModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            {/* Информация об анализе с проверкой расчетов */}
            <div className="mb-6">
              <div className="text-center mb-4">
                <p className="text-gray-400 text-sm">
                  📅 {financesResult.analysis_date} • 📍 {financesResult.region} • 🔄 Актуальные цены из интернета
                </p>
              </div>
              
              {/* Проверка расчетов */}
              {financesResult.cost_verification && (
                <div className={`p-4 rounded-lg border ${financesResult.cost_verification.calculation_correct ? 'bg-green-900/20 border-green-500/30' : 'bg-red-900/20 border-red-500/30'}`}>
                  <div className="flex items-center justify-center space-x-4">
                    <span className={`text-sm font-bold ${financesResult.cost_verification.calculation_correct ? 'text-green-300' : 'text-red-300'}`}>
                      {financesResult.cost_verification.calculation_correct ? '✅ Расчеты проверены' : '❌ Ошибка в расчетах'}
                    </span>
                    <span className="text-gray-400 text-xs">
                      Сумма ингредиентов: {financesResult.cost_verification.ingredients_sum}₽ 
                      | Общая стоимость: {financesResult.cost_verification.total_cost_check}₽
                    </span>
                  </div>
                </div>
              )}
            </div>
            
            {/* Краткая сводка */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
              <div className="bg-gradient-to-r from-green-600/20 to-emerald-600/20 rounded-xl p-6 text-center border border-green-500/30 shadow-lg">
                <div className="text-green-300 text-sm font-bold uppercase tracking-wider">Себестоимость</div>
                <div className="text-3xl font-bold text-white mt-2">{financesResult.total_cost}₽</div>
                <div className="text-green-400 text-xs mt-1">на 1 порцию</div>
              </div>
              <div className="bg-gradient-to-r from-blue-600/20 to-cyan-600/20 rounded-xl p-6 text-center border border-blue-500/30 shadow-lg">
                <div className="text-blue-300 text-sm font-bold uppercase tracking-wider">Рекомендуемая цена</div>
                <div className="text-3xl font-bold text-white mt-2">{financesResult.recommended_price}₽</div>
                <div className="text-blue-400 text-xs mt-1">× {((financesResult.recommended_price / financesResult.total_cost) || 3).toFixed(1)} коэффициент</div>
              </div>
              <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 rounded-xl p-6 text-center border border-purple-500/30 shadow-lg">
                <div className="text-purple-300 text-sm font-bold uppercase tracking-wider">Маржа</div>
                <div className="text-3xl font-bold text-white mt-2">{financesResult.margin_percent}%</div>
                <div className="text-purple-400 text-xs mt-1">прибыль {((financesResult.recommended_price - financesResult.total_cost) || 0).toFixed(0)}₽</div>
              </div>
              <div className="bg-gradient-to-r from-yellow-600/20 to-orange-600/20 rounded-xl p-6 text-center border border-yellow-500/30 shadow-lg">
                <div className="text-yellow-300 text-sm font-bold uppercase tracking-wider">Рентабельность</div>
                <div className="text-3xl font-bold text-white mt-2">
                  {'★'.repeat(financesResult.profitability_rating)}{'☆'.repeat(5 - financesResult.profitability_rating)}
                </div>
                <div className="text-yellow-400 text-xs mt-1">{financesResult.profitability_rating}/5 баллов</div>
              </div>
            </div>
            
            {/* Разбор ингредиентов с актуальными ценами */}
            {financesResult.ingredient_costs && (
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-green-300 mb-6 flex items-center">
                  🛒 АКТУАЛЬНЫЕ ЦЕНЫ ИНГРЕДИЕНТОВ
                  <span className="ml-3 text-sm text-gray-400 font-normal">на основе поиска в интернете</span>
                </h3>
                <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl p-6 border border-gray-600/30">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-600">
                          <th className="text-left py-3 px-4 text-green-300 font-bold">ИНГРЕДИЕНТ</th>
                          <th className="text-center py-3 px-4 text-blue-300 font-bold">КОЛИЧЕСТВО</th>
                          <th className="text-center py-3 px-4 text-purple-300 font-bold">ТЕКУЩАЯ ЦЕНА</th>
                          <th className="text-center py-3 px-4 text-orange-300 font-bold">РЫНОЧНАЯ ЦЕНА</th>
                          <th className="text-center py-3 px-4 text-green-300 font-bold">ЭКОНОМИЯ</th>
                        </tr>
                      </thead>
                      <tbody>
                        {financesResult.ingredient_costs.map((item, index) => (
                          <tr key={index} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                            <td className="py-3 px-4 text-white font-medium">{item.ingredient}</td>
                            <td className="py-3 px-4 text-center text-blue-200">{item.quantity}</td>
                            <td className="py-3 px-4 text-center text-purple-200">{item.current_price}₽</td>
                            <td className="py-3 px-4 text-center text-orange-200">{item.market_price}₽</td>
                            <td className="py-3 px-4 text-center">
                              <span className={`px-2 py-1 rounded text-xs font-bold ${
                                parseFloat(item.savings_potential) > 0 ? 'bg-green-600/20 text-green-300' : 'bg-red-600/20 text-red-300'
                              }`}>
                                {item.savings_potential}₽
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
            
            {/* Анализ конкурентов */}
            {financesResult.competitor_analysis && (
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-green-300 mb-6 flex items-center">
                  🏆 АНАЛИЗ КОНКУРЕНТОВ
                  <span className="ml-3 text-sm text-gray-400 font-normal">цены в вашем городе</span>
                </h3>
                <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl p-6 border border-gray-600/30">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                    <div className="text-center">
                      <div className="text-gray-400 text-sm">Средняя цена</div>
                      <div className="text-3xl font-bold text-white">{financesResult.competitor_analysis.average_price}₽</div>
                    </div>
                    <div className="text-center">
                      <div className="text-gray-400 text-sm">Диапазон цен</div>
                      <div className="text-3xl font-bold text-white">{financesResult.competitor_analysis.price_range}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-gray-400 text-sm">Ваша позиция</div>
                      <div className="text-xl font-bold text-yellow-400">{financesResult.competitor_analysis.market_position}</div>
                    </div>
                  </div>
                  
                  {financesResult.competitor_analysis.competitors && (
                    <div className="space-y-3">
                      <h4 className="text-lg font-bold text-blue-300">Конкуренты:</h4>
                      {financesResult.competitor_analysis.competitors.map((comp, index) => (
                        <div key={index} className="flex justify-between items-center bg-gray-700/50 rounded-lg p-3">
                          <span className="text-white font-medium">{comp.name}</span>
                          <div className="text-right">
                            <div className="text-green-400 font-bold">{comp.price}₽</div>
                            <div className="text-gray-400 text-xs">{comp.source}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* Практические рекомендации */}
            {financesResult.practical_recommendations && (
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-green-300 mb-6 flex items-center">
                  💡 ПРАКТИЧЕСКИЕ РЕКОМЕНДАЦИИ
                  <span className="ml-3 text-sm text-gray-400 font-normal">конкретные действия</span>
                </h3>
                <div className="space-y-4">
                  {financesResult.practical_recommendations.map((rec, index) => (
                    <div key={index} className="bg-gradient-to-r from-yellow-900/20 to-orange-900/20 rounded-xl p-6 border border-yellow-500/30 shadow-lg">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <h4 className="text-lg font-bold text-yellow-300 mb-2">
                            {rec.urgency === 'высокая' ? '🔥' : rec.urgency === 'средняя' ? '⚡' : '📅'} 
                            ДЕЙСТВИЕ #{index + 1}
                          </h4>
                          <p className="text-gray-300 leading-relaxed">{rec.action}</p>
                        </div>
                        <div className="ml-6 text-right">
                          <div className="text-2xl font-bold text-green-400">{rec.savings}₽</div>
                          <div className="text-sm text-gray-400">экономия</div>
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-blue-900/20 rounded-lg p-3 border border-blue-500/30">
                          <div className="text-blue-300 text-sm font-bold">Влияние на качество</div>
                          <div className="text-white">{rec.impact}</div>
                        </div>
                        <div className="bg-purple-900/20 rounded-lg p-3 border border-purple-500/30">
                          <div className="text-purple-300 text-sm font-bold">Срочность</div>
                          <div className="text-white">{rec.urgency}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Финансовая сводка */}
            {financesResult.financial_summary && (
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-green-300 mb-6 flex items-center">
                  📊 ФИНАНСОВАЯ СВОДКА
                  <span className="ml-3 text-sm text-gray-400 font-normal">ключевые показатели</span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl p-6 border border-gray-600/30">
                    <div className="text-gray-400 text-sm uppercase tracking-wider">Точка безубыточности</div>
                    <div className="text-3xl font-bold text-blue-400 mt-2">{financesResult.financial_summary.break_even_portions}</div>
                    <div className="text-blue-300 text-xs mt-1">порций</div>
                  </div>
                  <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl p-6 border border-gray-600/30">
                    <div className="text-gray-400 text-sm uppercase tracking-wider">Цель в день</div>
                    <div className="text-3xl font-bold text-purple-400 mt-2">{financesResult.financial_summary.daily_target}</div>
                    <div className="text-purple-300 text-xs mt-1">порций для прибыли</div>
                  </div>
                  <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl p-6 border border-gray-600/30">
                    <div className="text-gray-400 text-sm uppercase tracking-wider">Месячный потенциал</div>
                    <div className="text-3xl font-bold text-yellow-400 mt-2">{financesResult.financial_summary.monthly_potential}</div>
                    <div className="text-yellow-300 text-xs mt-1">рублей</div>
                  </div>
                  <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl p-6 border border-gray-600/30">
                    <div className="text-gray-400 text-sm uppercase tracking-wider">ROI</div>
                    <div className="text-3xl font-bold text-orange-400 mt-2">{financesResult.financial_summary.roi_percent}%</div>
                    <div className="text-orange-300 text-xs mt-1">возврат инвестиций</div>
                  </div>
                  <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl p-6 border border-gray-600/30">
                    <div className="text-gray-400 text-sm uppercase tracking-wider">Рекомендация по цене</div>
                    <div className="text-lg font-bold text-green-400 mt-2">{financesResult.financial_summary.price_elasticity || 'N/A'}</div>
                    <div className="text-green-300 text-xs mt-1">стратегия</div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Рыночная аналитика */}
            {financesResult.market_insights && (
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-green-300 mb-6 flex items-center">
                  🔮 РЫНОЧНАЯ АНАЛИТИКА
                  <span className="ml-3 text-sm text-gray-400 font-normal">тренды и прогнозы</span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl p-6 border border-gray-600/30">
                    <h4 className="text-lg font-bold text-blue-300 mb-3">📈 Тренды цен</h4>
                    <p className="text-gray-300">{financesResult.market_insights.price_trends}</p>
                  </div>
                  <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl p-6 border border-gray-600/30">
                    <h4 className="text-lg font-bold text-purple-300 mb-3">🌟 Конкурентное преимущество</h4>
                    <p className="text-gray-300">{financesResult.market_insights.competitive_advantage}</p>
                  </div>
                  <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl p-6 border border-gray-600/30">
                    <h4 className="text-lg font-bold text-yellow-300 mb-3">🍂 Сезонное влияние</h4>
                    <p className="text-gray-300">{financesResult.market_insights.seasonal_impact}</p>
                  </div>
                  <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl p-6 border border-gray-600/30">
                    <h4 className="text-lg font-bold text-red-300 mb-3">⚠️ Основные риски</h4>
                    <div className="space-y-2">
                      {financesResult.market_insights.risk_factors?.map((risk, index) => (
                        <div key={index} className="text-gray-300 text-sm">• {risk}</div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Кнопка закрытия */}
            <div className="flex justify-center mt-8">
              <button
                onClick={() => setShowFinancesModal(false)}
                className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white px-12 py-4 rounded-xl font-bold text-lg transition-all duration-300 transform hover:scale-105 shadow-lg"
              >
                💼 ЗАКРЫТЬ АНАЛИЗ
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Improve Dish Modal */}
      {showImproveDishModal && improveDishResult && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto border border-orange-500/30">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-orange-300">⚡ БЛЮДО ПРОКАЧАНО!</h2>
              <button
                onClick={() => setShowImproveDishModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-6">
              <div className="bg-gradient-to-r from-orange-900/30 to-red-900/30 rounded-xl p-6 border border-orange-500/30">
                <h3 className="text-lg font-bold text-orange-300 mb-3">
                  🔥 ПРОФЕССИОНАЛЬНАЯ ВЕРСИЯ ВАШЕГО БЛЮДА
                </h3>
                <p className="text-gray-300 text-sm">
                  Мишленовский шеф-повар улучшил ваш рецепт с помощью профессиональных техник и секретов.
                  Суть блюда сохранена, но качество выведено на ресторанный уровень!
                </p>
              </div>
              
              <div className="bg-gray-800/50 rounded-xl p-6">
                <div className="prose prose-invert max-w-none">
                  <div 
                    className="text-gray-300 leading-relaxed"
                    dangerouslySetInnerHTML={{ 
                      __html: formatProAIContent(improveDishResult)
                    }}
                  />
                </div>
              </div>
            </div>
            
            <div className="flex justify-between space-x-4 mt-8">
              <button
                onClick={async () => {
                  // Заменяем текущую техкарту на улучшенную
                  try {
                    // Сохраняем улучшенную техкарту в базу
                    const response = await axios.post(`${API}/save-tech-card`, {
                      user_id: currentUser.id,
                      content: improveDishResult,
                      dish_name: improveDishResult.split('\n')[0]?.replace(/\*\*/g, '').replace('Название:', '').trim() || 'Улучшенное блюдо',
                      city: currentUser.city,
                      is_improved: true
                    });
                    
                    // Устанавливаем новую техкарту
                    setTechCard(improveDishResult);
                    setCurrentIngredients(parseIngredientsFromTechCard(improveDishResult));
                    setCurrentTechCardId(response.data.id);
                    setShowImproveDishModal(false);
                    
                    alert('Улучшенная техкарта сохранена и установлена как активная!');
                  } catch (error) {
                    console.error('Error saving improved dish:', error);
                    alert('Ошибка при сохранении улучшенной техкарты');
                  }
                }}
                className="flex-1 bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 text-white px-6 py-3 rounded-lg font-bold transition-colors"
              >
                💾 ИСПОЛЬЗОВАТЬ УЛУЧШЕННУЮ ВЕРСИЮ
              </button>
              
              <button
                onClick={() => setShowImproveDishModal(false)}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-bold transition-colors"
              >
                ЗАКРЫТЬ
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Laboratory Modal */}
      {showLaboratoryModal && laboratoryResult && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-6 w-full max-w-5xl max-h-[90vh] overflow-y-auto border border-cyan-500/30 laboratory-modal">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-cyan-300">🧪 ЛАБОРАТОРИЯ: ЭКСПЕРИМЕНТ ЗАВЕРШЕН!</h2>
              <button
                onClick={() => setShowLaboratoryModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            {/* Тип эксперимента */}
            <div className="mb-6">
              <div className="bg-gradient-to-r from-cyan-900/30 to-blue-900/30 rounded-xl p-4 border border-cyan-500/30">
                <h3 className="text-lg font-bold text-cyan-300 mb-2">
                  ⚗️ ТИП ЭКСПЕРИМЕНТА: {laboratoryResult.experiment_type?.toUpperCase()}
                </h3>
                <p className="text-gray-300 text-sm">
                  {laboratoryResult.experiment_type === 'random' && '🎲 Случайное сочетание домашних ингредиентов'}
                  {laboratoryResult.experiment_type === 'snack' && '🍿 Полноценное блюдо из снеков и сладостей'}
                  {laboratoryResult.experiment_type === 'fusion' && '🌍 Фьюжн кухонь с домашними продуктами'}
                  {laboratoryResult.experiment_type === 'molecular' && '🧪 Домашняя молекулярная гастрономия'}
                  {laboratoryResult.experiment_type === 'extreme' && '🔥 Экстремальные домашние эксперименты'}
                </p>
              </div>
            </div>
            
            {/* Сгенерированное изображение */}
            {laboratoryResult.image_url && (
              <div className="mb-6">
                <h3 className="text-xl font-bold text-cyan-300 mb-4">📸 ВИЗУАЛИЗАЦИЯ ЭКСПЕРИМЕНТА</h3>
                <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl p-4 border border-cyan-500/30">
                  <img 
                    src={laboratoryResult.image_url} 
                    alt="Экспериментальное блюдо" 
                    className="w-full max-w-md mx-auto rounded-lg shadow-lg"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.parentElement.innerHTML = '<p class="text-gray-400 text-center">Изображение недоступно</p>';
                    }}
                  />
                  <div className="mt-4 flex justify-center space-x-4">
                    <button
                      onClick={() => window.open(laboratoryResult.image_url, '_blank')}
                      className="bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded-lg text-sm"
                    >
                      📱 ОТКРЫТЬ В ПОЛНОМ РАЗМЕРЕ
                    </button>
                    <button
                      onClick={() => {
                        const link = document.createElement('a');
                        link.href = laboratoryResult.image_url;
                        link.download = 'receptor-experiment.jpg';
                        link.click();
                      }}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"
                    >
                      💾 СКАЧАТЬ ИЗОБРАЖЕНИЕ
                    </button>
                  </div>
                </div>
              </div>
            )}
            
            {/* Результат эксперимента */}
            <div className="mb-6">
              <h3 className="text-xl font-bold text-cyan-300 mb-4">🔬 РЕЗУЛЬТАТ ЭКСПЕРИМЕНТА</h3>
              <div className="bg-gray-800/50 rounded-xl p-6 border border-cyan-500/30">
                <div className="prose prose-invert max-w-none">
                  <div 
                    className="text-gray-300 leading-relaxed"
                    dangerouslySetInnerHTML={{ 
                      __html: formatProAIContent(laboratoryResult.experiment)
                    }}
                  />
                </div>
              </div>
            </div>
            
            {/* Выбор типа эксперимента для следующего раза */}
            <div className="mb-6">
              <h3 className="text-lg font-bold text-cyan-300 mb-4">🎯 ПРОВЕСТИ ДРУГОЙ ЭКСПЕРИМЕНТ</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <button
                  onClick={() => {
                    setExperimentType('random');
                    setShowLaboratoryModal(false);
                    setTimeout(() => conductExperiment(), 500);
                  }}
                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white py-3 px-4 rounded-lg text-sm font-bold transition-colors"
                >
                  🎲 СЛУЧАЙНЫЙ
                </button>
                <button
                  onClick={() => {
                    setExperimentType('snack');
                    setShowLaboratoryModal(false);
                    setTimeout(() => conductExperiment(), 500);
                  }}
                  className="bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700 text-white py-3 px-4 rounded-lg text-sm font-bold transition-colors"
                >
                  🍿 СНЕКОВЫЙ
                </button>
                <button
                  onClick={() => {
                    setExperimentType('fusion');
                    setShowLaboratoryModal(false);
                    setTimeout(() => conductExperiment(), 500);
                  }}
                  className="bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 text-white py-3 px-4 rounded-lg text-sm font-bold transition-colors"
                >
                  🌍 ФЬЮЖН
                </button>
                <button
                  onClick={() => {
                    setExperimentType('molecular');
                    setShowLaboratoryModal(false);
                    setTimeout(() => conductExperiment(), 500);
                  }}
                  className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white py-3 px-4 rounded-lg text-sm font-bold transition-colors"
                >
                  🧪 ДОМАШНЯЯ МОЛЕКУЛЯРКА
                </button>
              </div>
            </div>
            
            {/* Действия */}
            <div className="flex justify-between space-x-4 mt-8">
              <button
                onClick={async () => {
                  // Сохраняем экспериментальное блюдо как новую техкарту
                  try {
                    const response = await axios.post(`${API}/save-laboratory-experiment`, {
                      user_id: currentUser.id,
                      experiment: laboratoryResult.experiment,
                      experiment_type: laboratoryResult.experiment_type,
                      image_url: laboratoryResult.image_url
                    });
                    
                    // Устанавливаем новую техкарту
                    setTechCard(laboratoryResult.experiment);
                    setCurrentIngredients(parseIngredientsFromTechCard(laboratoryResult.experiment));
                    setCurrentTechCardId(response.data.id);
                    setShowLaboratoryModal(false);
                    
                    alert('Экспериментальное блюдо сохранено в истории техкарт!');
                  } catch (error) {
                    console.error('Error saving experiment:', error);
                    alert('Ошибка при сохранении эксперимента');
                  }
                }}
                className="flex-1 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white px-6 py-3 rounded-lg font-bold transition-colors"
                title="💾 Сохранить экспериментальное блюдо как полноценную техкарту в историю"
              >
                💾 СОХРАНИТЬ В ИСТОРИЮ
              </button>
              
              <button
                onClick={() => {
                  // Поделиться в соцсетях
                  const shareText = `🧪 Провел кулинарный эксперимент в RECEPTOR PRO! Смотрите что получилось 😱\n\n#экспериментальнаякулинария #receptorpro #кулинарныйэксперимент`;
                  
                  if (navigator.share) {
                    navigator.share({
                      title: 'Кулинарный эксперимент',
                      text: shareText,
                      url: window.location.href
                    });
                  } else {
                    navigator.clipboard.writeText(shareText + '\n\n' + window.location.href);
                    alert('Текст скопирован в буфер обмена!');
                  }
                }}
                className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-6 py-3 rounded-lg font-bold transition-colors"
                title="📱 Поделиться результатом эксперимента в социальных сетях"
              >
                📱 ПОДЕЛИТЬСЯ
              </button>
              
              <button
                onClick={() => setShowLaboratoryModal(false)}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-bold transition-colors"
                title="❌ Закрыть окно лаборатории без сохранения"
              >
                ЗАКРЫТЬ
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Venue Profile Modal */}
      {showVenueProfileModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 rounded-xl p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto border border-purple-400/30">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-purple-300 flex items-center gap-3">
                🏢 ПРОФИЛЬ ЗАВЕДЕНИЯ
                {profileStep > 1 && (
                  <span className="text-sm bg-purple-600 text-white px-3 py-1 rounded-full">
                    Шаг {profileStep}/4
                  </span>
                )}
              </h2>
              <button
                onClick={() => {
                  setShowVenueProfileModal(false);
                  setProfileStep(1);
                }}
                className="text-gray-400 hover:text-white transition-colors text-2xl"
              >
                ✕
              </button>
            </div>

            {/* Wizard Step 1: Venue Type */}
            {profileStep === 1 && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <h3 className="text-xl font-bold text-purple-200 mb-2">Выберите тип заведения</h3>
                  <p className="text-gray-300">Это влияет на сложность рецептов и стиль подачи</p>
                  {Object.keys(venueTypes).length === 0 && (
                    <p className="text-yellow-400 text-sm mt-2">⚠️ Загрузка типов заведений...</p>
                  )}
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.keys(venueTypes).length === 0 ? (
                    <div className="col-span-full text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400 mx-auto mb-4"></div>
                      <p className="text-gray-400">Загружаем типы заведений...</p>
                    </div>
                  ) : (
                    Object.entries(venueTypes).map(([key, venue]) => (
                      <div
                        key={key}
                        className={`cursor-pointer p-4 rounded-lg border-2 transition-all hover:scale-105 ${
                          venueProfile.venue_type === key
                            ? 'border-purple-400 bg-purple-900/50'
                            : 'border-gray-600 hover:border-purple-500'
                        }`}
                        onClick={() => {
                          console.log('Venue type selected:', key);
                          setVenueProfile(prev => ({ ...prev, venue_type: key }));
                        }}
                      >
                        <h4 className="text-lg font-bold text-purple-200 mb-2">{venue.name}</h4>
                        <p className="text-sm text-gray-300 mb-3">{venue.description}</p>
                        <div className="text-xs text-gray-400">
                          <div>Сложность: {venue.complexity_level === 'high' ? '🔴 Высокая' : venue.complexity_level === 'medium' ? '🟡 Средняя' : '🟢 Низкая'}</div>
                          <div>Ценовой коэффициент: {venue.price_multiplier}x</div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
                
                <div className="flex justify-end">
                  <button
                    onClick={() => {
                      console.log('Next button clicked, venue_type:', venueProfile.venue_type);
                      if (venueProfile.venue_type) {
                        setProfileStep(2);
                      }
                    }}
                    disabled={!venueProfile.venue_type}
                    className={`px-6 py-3 rounded-lg font-bold transition-colors ${
                      venueProfile.venue_type
                        ? 'bg-purple-600 hover:bg-purple-700 text-white'
                        : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    ДАЛЕЕ →
                  </button>
                </div>
                
                {/* Debug info */}
                {process.env.NODE_ENV === 'development' && (
                  <div className="text-xs text-gray-500 mt-4 p-2 bg-gray-800 rounded">
                    Debug: venueTypes count: {Object.keys(venueTypes).length}, 
                    selected: {venueProfile.venue_type || 'none'}
                  </div>
                )}
              </div>
            )}

            {/* Wizard Step 2: Cuisine Focus */}
            {profileStep === 2 && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <h3 className="text-xl font-bold text-purple-200 mb-2">Выберите направления кухни</h3>
                  <p className="text-gray-300">Можно выбрать несколько направлений</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(cuisineTypes).map(([key, cuisine]) => (
                    <div
                      key={key}
                      className={`cursor-pointer p-4 rounded-lg border-2 transition-all hover:scale-105 ${
                        venueProfile.cuisine_focus?.includes(key)
                          ? 'border-purple-400 bg-purple-900/50'
                          : 'border-gray-600 hover:border-purple-500'
                      }`}
                      onClick={() => setVenueProfile(prev => ({
                        ...prev,
                        cuisine_focus: prev.cuisine_focus?.includes(key)
                          ? prev.cuisine_focus.filter(c => c !== key)
                          : [...(prev.cuisine_focus || []), key]
                      }))}
                    >
                      <h4 className="text-lg font-bold text-purple-200 mb-2">{cuisine.name}</h4>
                      <div className="text-xs text-gray-300 mb-2">
                        <div><strong>Ключевые ингредиенты:</strong> {cuisine.key_ingredients?.slice(0, 3).join(', ')}</div>
                        <div><strong>Методы:</strong> {cuisine.cooking_methods?.slice(0, 2).join(', ')}</div>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="flex justify-between">
                  <button
                    onClick={() => setProfileStep(1)}
                    className="px-6 py-3 rounded-lg font-bold bg-gray-600 hover:bg-gray-700 text-white transition-colors"
                  >
                    ← НАЗАД
                  </button>
                  <button
                    onClick={() => setProfileStep(3)}
                    className="px-6 py-3 rounded-lg font-bold bg-purple-600 hover:bg-purple-700 text-white transition-colors"
                  >
                    ДАЛЕЕ →
                  </button>
                </div>
              </div>
            )}

            {/* Wizard Step 3: Average Check & Details */}
            {profileStep === 3 && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <h3 className="text-xl font-bold text-purple-200 mb-2">Детали заведения</h3>
                  <p className="text-gray-300">Расскажите подробнее о вашем заведении</p>
                </div>
                
                {/* Average Check */}
                <div>
                  <label className="block text-purple-200 font-bold mb-3">Средний чек (₽)</label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                    {Object.entries(averageCheckCategories).map(([key, category]) => (
                      <div
                        key={key}
                        className={`cursor-pointer p-3 rounded-lg border-2 text-center transition-all hover:scale-105 ${
                          venueProfile.average_check >= category.range[0] && venueProfile.average_check <= category.range[1]
                            ? 'border-purple-400 bg-purple-900/50'
                            : 'border-gray-600 hover:border-purple-500'
                        }`}
                        onClick={() => setVenueProfile(prev => ({ ...prev, average_check: category.range[1] }))}
                      >
                        <div className="text-sm font-bold text-purple-200">{category.name}</div>
                        <div className="text-xs text-gray-400">{category.range[0]}-{category.range[1]}₽</div>
                      </div>
                    ))}
                  </div>
                  <input
                    type="number"
                    value={venueProfile.average_check || ''}
                    onChange={(e) => setVenueProfile(prev => ({ ...prev, average_check: parseInt(e.target.value) || 0 }))}
                    placeholder="Введите точную сумму"
                    className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white"
                  />
                </div>

                {/* Venue Name */}
                <div>
                  <label className="block text-purple-200 font-bold mb-2">Название заведения</label>
                  <input
                    type="text"
                    value={venueProfile.venue_name || ''}
                    onChange={(e) => setVenueProfile(prev => ({ ...prev, venue_name: e.target.value }))}
                    placeholder="Например: Ресторан 'Уют'"
                    className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white"
                  />
                </div>

                {/* Venue Concept */}
                <div>
                  <label className="block text-purple-200 font-bold mb-2">Концепция заведения</label>
                  <textarea
                    value={venueProfile.venue_concept || ''}
                    onChange={(e) => setVenueProfile(prev => ({ ...prev, venue_concept: e.target.value }))}
                    placeholder="Опишите концепцию вашего заведения..."
                    rows={3}
                    className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white resize-none"
                  />
                </div>

                {/* Target Audience */}
                <div>
                  <label className="block text-purple-200 font-bold mb-2">Целевая аудитория</label>
                  <input
                    type="text"
                    value={venueProfile.target_audience || ''}
                    onChange={(e) => setVenueProfile(prev => ({ ...prev, target_audience: e.target.value }))}
                    placeholder="Например: молодые семьи, бизнес-клиенты"
                    className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white"
                  />
                </div>
                
                <div className="flex justify-between">
                  <button
                    onClick={() => setProfileStep(2)}
                    className="px-6 py-3 rounded-lg font-bold bg-gray-600 hover:bg-gray-700 text-white transition-colors"
                  >
                    ← НАЗАД
                  </button>
                  <button
                    onClick={() => setProfileStep(4)}
                    className="px-6 py-3 rounded-lg font-bold bg-purple-600 hover:bg-purple-700 text-white transition-colors"
                  >
                    ДАЛЕЕ →
                  </button>
                </div>
              </div>
            )}

            {/* Wizard Step 4: Kitchen Equipment & Save */}
            {profileStep === 4 && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <h3 className="text-xl font-bold text-purple-200 mb-2">Кухонное оборудование</h3>
                  <p className="text-gray-300">Выберите доступное оборудование</p>
                </div>
                
                {/* Kitchen Equipment */}
                {Object.entries(kitchenEquipment).map(([category, items]) => (
                  <div key={category} className="space-y-3">
                    <h4 className="text-lg font-bold text-purple-200 capitalize">
                      {category === 'cooking_methods' ? 'Методы готовки' : 
                       category === 'prep_equipment' ? 'Подготовка' : 'Хранение'}
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                      {items.map((equipment) => (
                        <label key={equipment.id} className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={venueProfile.kitchen_equipment?.includes(equipment.id) || false}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setVenueProfile(prev => ({
                                  ...prev,
                                  kitchen_equipment: [...(prev.kitchen_equipment || []), equipment.id]
                                }));
                              } else {
                                setVenueProfile(prev => ({
                                  ...prev,
                                  kitchen_equipment: (prev.kitchen_equipment || []).filter(id => id !== equipment.id)
                                }));
                              }
                            }}
                            className="text-purple-600"
                          />
                          <span className="text-gray-300 text-sm">{equipment.name}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
                
                <div className="flex justify-between pt-6 border-t border-purple-400/30">
                  <button
                    onClick={() => setProfileStep(3)}
                    className="px-6 py-3 rounded-lg font-bold bg-gray-600 hover:bg-gray-700 text-white transition-colors"
                    title="← Вернуться к предыдущему шагу настройки профиля"
                  >
                    ← НАЗАД
                  </button>
                  <button
                    onClick={async () => {
                      const success = await updateVenueProfile(venueProfile);
                      if (success) {
                        setShowVenueProfileModal(false);
                        setProfileStep(1);
                      }
                    }}
                    disabled={isUpdatingProfile}
                    className={`px-6 py-3 rounded-lg font-bold transition-colors ${
                      isUpdatingProfile
                        ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                        : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white'
                    }`}
                    title="💾 Сохранить профиль заведения для персонализации всех функций"
                  >
                    {isUpdatingProfile ? 'СОХРАНЕНИЕ...' : '💾 СОХРАНИТЬ ПРОФИЛЬ'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Loading Modal */}
      {(isAnalyzingFinances || isExperimenting || isImprovingDish) && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 rounded-xl p-8 w-full max-w-md border border-purple-400/30">
            <div className="text-center">
              {/* Icon based on loading type */}
              <div className="text-6xl mb-4">
                {isAnalyzingFinances && '💰'}
                {isExperimenting && '🧪'}
                {isImprovingDish && '⚡'}
              </div>
              
              {/* Loading message */}
              <h3 className="text-xl font-bold text-purple-300 mb-4 min-h-[3rem] flex items-center justify-center">
                {currentLoadingMessage}
              </h3>
              
              {/* Progress bar */}
              <div className="w-full bg-gray-700 rounded-full h-3 mb-4">
                <div 
                  className="bg-gradient-to-r from-purple-600 to-pink-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${loadingProgress}%` }}
                ></div>
              </div>
              
              {/* Progress percentage */}
              <div className="text-purple-200 text-sm mb-4 font-bold">
                {loadingProgress}%
              </div>
              
              {/* Animated dots */}
              <div className="flex justify-center space-x-2">
                <div className="w-3 h-3 bg-purple-500 rounded-full animate-bounce"></div>
                <div className="w-3 h-3 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-3 h-3 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
              
              {/* Processing text */}
              <p className="text-gray-300 text-sm mt-4">
                {isAnalyzingFinances && 'Анализируем рентабельность и составляем рекомендации...'}
                {isExperimenting && 'Создаем кулинарный шедевр и генерируем изображение...'}
                {isImprovingDish && 'Применяем секретные техники шеф-поваров...'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Finances Analysis Modal */}
      {showFinancesModal && financesResult && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gradient-to-br from-gray-900 via-green-900 to-gray-900 rounded-xl p-6 w-full max-w-6xl max-h-[90vh] overflow-y-auto border border-green-400/30">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-green-300 flex items-center gap-3">
                💼 ФИНАНСОВЫЙ АНАЛИЗ ЗАВЕРШЕН
              </h2>
              <button
                onClick={() => setShowFinancesModal(false)}
                className="text-gray-400 hover:text-white transition-colors text-2xl"
              >
                ✕
              </button>
            </div>

            {/* Financial Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <div className="bg-gradient-to-r from-green-900/50 to-emerald-900/50 rounded-xl p-4 border border-green-500/30">
                <div className="text-green-400 text-sm font-bold mb-1">СЕБЕСТОИМОСТЬ</div>
                <div className="text-2xl font-bold text-white">{financesResult.total_cost || 'N/A'}₽</div>
              </div>
              <div className="bg-gradient-to-r from-blue-900/50 to-cyan-900/50 rounded-xl p-4 border border-blue-500/30">
                <div className="text-blue-400 text-sm font-bold mb-1">РЕК. ЦЕНА</div>
                <div className="text-2xl font-bold text-white">{financesResult.recommended_price || 'N/A'}₽</div>
              </div>
              <div className="bg-gradient-to-r from-purple-900/50 to-pink-900/50 rounded-xl p-4 border border-purple-500/30">
                <div className="text-purple-400 text-sm font-bold mb-1">МАРЖА</div>
                <div className="text-2xl font-bold text-white">{financesResult.margin_percent || 'N/A'}%</div>
              </div>
              <div className="bg-gradient-to-r from-orange-900/50 to-red-900/50 rounded-xl p-4 border border-orange-500/30">
                <div className="text-orange-400 text-sm font-bold mb-1">РЕНТАБЕЛЬНОСТЬ</div>
                <div className="text-2xl font-bold text-white">{financesResult.profitability_rating || 'N/A'}/5 ⭐</div>
              </div>
            </div>

            {/* Smart Cost Cuts */}
            {financesResult.smart_cost_cuts && financesResult.smart_cost_cuts.length > 0 && (
              <div className="mb-8">
                <h3 className="text-xl font-bold text-green-300 mb-4 flex items-center gap-2">
                  💡 УМНАЯ ОПТИМИЗАЦИЯ ЗАТРАТ
                </h3>
                <div className="bg-gradient-to-r from-green-900/20 to-emerald-900/20 rounded-xl p-6 border border-green-500/30">
                  <div className="space-y-4">
                    {financesResult.smart_cost_cuts.map((cut, index) => (
                      <div key={index} className="flex items-start space-x-4 p-4 bg-gray-800/50 rounded-lg">
                        <div className="bg-green-600 rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0">
                          <span className="text-white font-bold">{index + 1}</span>
                        </div>
                        <div className="flex-1">
                          <div className="text-green-200 font-bold text-lg mb-2">{cut.change}</div>
                          <div className="flex justify-between items-center text-sm">
                            <span className="text-gray-300">Было: {cut.current_cost}</span>
                            <span className="text-gray-300">Станет: {cut.new_cost}</span>
                            <span className="bg-green-600 text-white px-3 py-1 rounded-full font-bold">
                              Экономия: {cut.savings}
                            </span>
                          </div>
                          <div className="text-xs text-gray-400 mt-2">
                            Влияние на качество: {cut.quality_impact}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Revenue Hacks */}
            {financesResult.revenue_hacks && financesResult.revenue_hacks.length > 0 && (
              <div className="mb-8">
                <h3 className="text-xl font-bold text-blue-300 mb-4 flex items-center gap-2">
                  🚀 СТРАТЕГИИ РОСТА ВЫРУЧКИ
                </h3>
                <div className="bg-gradient-to-r from-blue-900/20 to-cyan-900/20 rounded-xl p-6 border border-blue-500/30">
                  <div className="space-y-4">
                    {financesResult.revenue_hacks.map((hack, index) => (
                      <div key={index} className="p-4 bg-gray-800/50 rounded-lg">
                        <div className="text-blue-200 font-bold text-lg mb-2">{hack.strategy}</div>
                        <div className="text-gray-300 mb-3">{hack.implementation}</div>
                        <div className="text-blue-400 font-bold">Потенциальная прибыль: {hack.potential_gain}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Action Plan */}
            {financesResult.action_plan && financesResult.action_plan.length > 0 && (
              <div className="mb-8">
                <h3 className="text-xl font-bold text-purple-300 mb-4 flex items-center gap-2">
                  📋 ПЛАН ДЕЙСТВИЙ
                </h3>
                <div className="bg-gradient-to-r from-purple-900/20 to-pink-900/20 rounded-xl p-6 border border-purple-500/30">
                  <div className="space-y-4">
                    {financesResult.action_plan.map((action, index) => (
                      <div key={index} className="flex items-start space-x-4 p-4 bg-gray-800/50 rounded-lg">
                        <div className={`rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0 ${
                          action.priority === 'высокий' ? 'bg-red-600' :
                          action.priority === 'средний' ? 'bg-yellow-600' : 'bg-green-600'
                        }`}>
                          <span className="text-white font-bold text-xs">
                            {action.priority === 'высокий' ? '🔥' :
                             action.priority === 'средний' ? '⚡' : '💡'}
                          </span>
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`px-2 py-1 rounded text-xs font-bold ${
                              action.priority === 'высокий' ? 'bg-red-600 text-white' :
                              action.priority === 'средний' ? 'bg-yellow-600 text-white' : 'bg-green-600 text-white'
                            }`}>
                              {action.priority.toUpperCase()}
                            </span>
                          </div>
                          <div className="text-purple-200 font-bold mb-2">{action.action}</div>
                          <div className="text-gray-300 text-sm">{action.expected_result}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Financial Forecast */}
            {financesResult.financial_forecast && (
              <div className="mb-8">
                <h3 className="text-xl font-bold text-orange-300 mb-4 flex items-center gap-2">
                  📈 ФИНАНСОВЫЙ ПРОГНОЗ
                </h3>
                <div className="bg-gradient-to-r from-orange-900/20 to-red-900/20 rounded-xl p-6 border border-orange-500/30">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <div>
                        <div className="text-orange-200 font-bold">Точка безубыточности</div>
                        <div className="text-2xl font-bold text-white">{financesResult.financial_forecast.daily_breakeven} порций/день</div>
                      </div>
                      <div>
                        <div className="text-orange-200 font-bold">Целевые продажи</div>
                        <div className="text-2xl font-bold text-white">{financesResult.financial_forecast.target_daily} порций/день</div>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div>
                        <div className="text-orange-200 font-bold">Месячный потенциал</div>
                        <div className="text-2xl font-bold text-white">{financesResult.financial_forecast.monthly_revenue_potential}</div>
                      </div>
                      <div>
                        <div className="text-orange-200 font-bold">Прибыль с порции</div>
                        <div className="text-2xl font-bold text-white">{financesResult.financial_forecast.profit_margin_realistic}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Red Flags & Golden Opportunities */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              {/* Red Flags */}
              {financesResult.red_flags && financesResult.red_flags.length > 0 && (
                <div>
                  <h3 className="text-xl font-bold text-red-300 mb-4 flex items-center gap-2">
                    ⚠️ КРИТИЧЕСКИЕ ТОЧКИ
                  </h3>
                  <div className="bg-gradient-to-r from-red-900/20 to-pink-900/20 rounded-xl p-4 border border-red-500/30">
                    <div className="space-y-3">
                      {financesResult.red_flags.map((flag, index) => (
                        <div key={index} className="flex items-start space-x-3">
                          <div className="text-red-400 mt-1">🚨</div>
                          <div className="text-red-200">{flag}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Golden Opportunities */}
              {financesResult.golden_opportunities && financesResult.golden_opportunities.length > 0 && (
                <div>
                  <h3 className="text-xl font-bold text-yellow-300 mb-4 flex items-center gap-2">
                    💎 ЗОЛОТЫЕ ВОЗМОЖНОСТИ
                  </h3>
                  <div className="bg-gradient-to-r from-yellow-900/20 to-orange-900/20 rounded-xl p-4 border border-yellow-500/30">
                    <div className="space-y-3">
                      {financesResult.golden_opportunities.map((opportunity, index) => (
                        <div key={index} className="flex items-start space-x-3">
                          <div className="text-yellow-400 mt-1">💎</div>
                          <div className="text-yellow-200">{opportunity}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex justify-between space-x-4 pt-6 border-t border-green-400/30">
              <button
                onClick={() => {
                  const analysisText = `ФИНАНСОВЫЙ АНАЛИЗ БЛЮДА\n\nСебестоимость: ${financesResult.total_cost}₽\nРекомендуемая цена: ${financesResult.recommended_price}₽\nМаржа: ${financesResult.margin_percent}%\n\n📊 Анализ создан в RECEPTOR PRO`;
                  navigator.clipboard.writeText(analysisText);
                  alert('Анализ скопирован в буфер обмена!');
                }}
                className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white px-6 py-3 rounded-lg font-bold transition-colors"
              >
                📋 КОПИРОВАТЬ АНАЛИЗ
              </button>
              
              <button
                onClick={() => setShowFinancesModal(false)}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-bold transition-colors"
              >
                ЗАКРЫТЬ АНАЛИЗ
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Enhanced Mass Tech Card Generation Progress Modal */}
      {showMassGenerationModal && (
        <div className="mass-generation-modal fixed inset-0 flex items-center justify-center z-50 p-4">
          <div className="mass-progress-container w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="text-center">
              {/* Enhanced Header */}
              <div className="mb-8">
                <div className="text-6xl mb-4 animate-pulse">⚡</div>
                <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-purple-300 mb-2">
                  МАССОВАЯ ГЕНЕРАЦИЯ ТЕХКАРТ
                </h2>
                <p className="text-gray-400">Создаем техкарты для всех блюд из меню</p>
              </div>
              
              {/* Enhanced Progress Bar */}
              <div className="mb-8">
                <div className="relative mb-4">
                  <div className="bg-gray-700/50 rounded-2xl h-6 overflow-hidden">
                    <div 
                      className="mass-progress-bar h-full transition-all duration-1000 ease-out"
                      style={{ width: `${massGenerationProgress.total > 0 ? (massGenerationProgress.completed / massGenerationProgress.total) * 100 : 0}%` }}
                    ></div>
                  </div>
                  
                  {/* Progress Statistics */}
                  <div className="flex justify-between items-center mt-4">
                    <div className="text-left">
                      <div className="text-2xl font-bold text-cyan-300">
                        {massGenerationProgress.completed}
                      </div>
                      <div className="text-xs text-gray-400">Готово</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg text-purple-300 font-semibold">
                        {massGenerationProgress.total > 0 ? Math.round((massGenerationProgress.completed / massGenerationProgress.total) * 100) : 0}%
                      </div>
                      <div className="text-xs text-gray-400">Прогресс</div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-purple-300">
                        {massGenerationProgress.total}
                      </div>
                      <div className="text-xs text-gray-400">Всего</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Enhanced Current Status with Tips */}
              <div className="mb-8 space-y-6">
                {/* Progress Status */}
                <div className="p-6 bg-gradient-to-r from-gray-700/30 to-gray-800/30 rounded-2xl border border-cyan-400/20">
                  <div className="flex items-center justify-center mb-2">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400 mr-3"></div>
                    <p className="text-cyan-300 font-bold text-lg">
                      {massGenerationProgress.current}
                    </p>
                  </div>
                  <p className="text-gray-400 text-sm">
                    Каждая техкарта создается с учетом всех параметров меню
                  </p>
                </div>

                {/* Tips and Lifehacks while waiting */}
                {massGenerationProgress.completed < massGenerationProgress.total && (
                  <div className="p-6 bg-gradient-to-br from-purple-900/20 to-blue-900/20 rounded-2xl border border-purple-400/30">
                    <div className="flex items-start space-x-4">
                      <div className="text-4xl flex-shrink-0 animate-bounce">
                        {receptionTips[currentTipIndex]?.icon}
                      </div>
                      <div className="text-left">
                        <h4 className="text-purple-300 font-bold text-lg mb-2">
                          {receptionTips[currentTipIndex]?.title}
                        </h4>
                        <p className="text-gray-300 text-sm leading-relaxed">
                          {receptionTips[currentTipIndex]?.text}
                        </p>
                      </div>
                    </div>
                    <div className="mt-4 flex justify-center space-x-2">
                      {receptionTips.map((_, index) => (
                        <div
                          key={index}
                          className={`w-2 h-2 rounded-full transition-all ${
                            index === currentTipIndex ? 'bg-purple-400' : 'bg-gray-600'
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Enhanced Results List */}
              {massGenerationProgress.results.length > 0 && (
                <div className="mb-8">
                  <h3 className="text-xl font-bold text-green-300 mb-4 flex items-center justify-center">
                    <span className="mr-2">✅</span>
                    Созданные техкарты
                    <span className="ml-2 bg-green-500/20 text-green-300 px-2 py-1 rounded-full text-sm">
                      {massGenerationProgress.results.length}
                    </span>
                  </h3>
                  <div className="max-h-60 overflow-y-auto space-y-2 bg-gray-800/30 rounded-xl p-4">
                    {massGenerationProgress.results.map((result, index) => (
                      <div key={index} className="tech-card-item">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white font-bold text-sm mr-3">
                              {index + 1}
                            </div>
                            <span className="text-gray-200 font-semibold">{result.dish_name}</span>
                          </div>
                          <div className="text-right">
                            <div className="text-sm text-purple-300 font-medium">{result.category}</div>
                            <div className="text-xs text-gray-400">Техкарта готова</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Enhanced Action Buttons */}
              <div className="flex gap-6">
                {massGenerationProgress.completed === massGenerationProgress.total && massGenerationProgress.total > 0 ? (
                  <>
                    <button
                      onClick={() => {
                        setShowMassGenerationModal(false);
                        setCurrentView('history');
                      }}
                      className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-bold py-4 px-8 rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-lg group"
                    >
                      <span className="flex items-center justify-center">
                        <span className="mr-2 group-hover:scale-110 transition-transform">📋</span>
                        ПРОСМОТРЕТЬ ТЕХКАРТЫ
                        <span className="ml-2 group-hover:translate-x-1 transition-transform">→</span>
                      </span>
                    </button>
                    <button
                      onClick={() => setShowMassGenerationModal(false)}
                      className="flex-1 bg-gray-600/80 hover:bg-gray-700 text-white font-bold py-4 px-8 rounded-xl transition-all duration-300 hover:scale-105"
                    >
                      ЗАКРЫТЬ
                    </button>
                  </>
                ) : (
                  <button
                    disabled
                    className="w-full bg-gradient-to-r from-purple-600/50 to-cyan-600/50 cursor-not-allowed text-white font-bold py-4 px-8 rounded-xl relative overflow-hidden"
                  >
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                      <span className="text-lg">ГЕНЕРАЦИЯ В ПРОЦЕССЕ</span>
                      <div className="ml-3">
                        <div className="flex space-x-1">
                          <div className="w-1 h-1 bg-white rounded-full animate-ping"></div>
                          <div className="w-1 h-1 bg-white rounded-full animate-ping" style={{animationDelay: '0.1s'}}></div>
                          <div className="w-1 h-1 bg-white rounded-full animate-ping" style={{animationDelay: '0.2s'}}></div>
                        </div>
                      </div>
                    </div>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Menu Generation Progress Modal (NEW!) */}
      {showMenuGenerationModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl p-8 w-full max-w-3xl border border-purple-400/30">
            <div className="text-center">
              {/* Header */}
              <div className="mb-8">
                <div className="text-6xl mb-4 animate-bounce">🧙‍♂️</div>
                <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-purple-300 mb-2">
                  СОЗДАЕМ ВАШЕ МЕНЮ
                </h2>
                <p className="text-gray-400">Анализируем требования и создаем идеальное меню</p>
              </div>
              
              {/* Progress Bar */}
              <div className="mb-8">
                <div className="bg-gray-700/50 rounded-2xl h-6 overflow-hidden mb-4">
                  <div 
                    className="bg-gradient-to-r from-purple-500 to-cyan-500 h-full transition-all duration-1000 ease-out"
                    style={{ width: `${menuGenerationProgress}%` }}
                  ></div>
                </div>
                <p className="text-purple-300 font-semibold text-lg">
                  {menuGenerationProgress < 30 ? 'Анализируем ваши требования...' :
                   menuGenerationProgress < 60 ? 'Создаем структуру меню...' :
                   menuGenerationProgress < 90 ? 'Генерируем названия блюд...' :
                   menuGenerationProgress < 100 ? 'Финальная проверка...' : 'Готово!'}
                </p>
              </div>

              {/* Lifehacks while waiting */}
              <div className="p-6 bg-gradient-to-br from-purple-900/20 to-blue-900/20 rounded-2xl border border-purple-400/30">
                <div className="flex items-start space-x-4">
                  <div className="text-4xl flex-shrink-0 animate-pulse">
                    {menuGenerationTips[currentMenuTipIndex]?.icon}
                  </div>
                  <div className="text-left">
                    <h4 className="text-purple-300 font-bold text-lg mb-2">
                      {menuGenerationTips[currentMenuTipIndex]?.title}
                    </h4>
                    <p className="text-gray-300 text-sm leading-relaxed">
                      {menuGenerationTips[currentMenuTipIndex]?.text}
                    </p>
                  </div>
                </div>
                <div className="mt-6 flex justify-center space-x-2">
                  {menuGenerationTips.map((_, index) => (
                    <div
                      key={index}
                      className={`w-2 h-2 rounded-full transition-all ${
                        index === currentMenuTipIndex ? 'bg-purple-400' : 'bg-gray-600'
                      }`}
                    />
                  ))}
                </div>
              </div>
              
              {/* Stats */}
              <div className="mt-8 grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-cyan-300">
                    {menuProfile.useConstructor ? 
                      Object.values(menuProfile.categories).reduce((a, b) => a + b, 0) : 
                      menuProfile.dishCount}
                  </div>
                  <div className="text-xs text-gray-400">Блюд</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-purple-300">{menuProfile.cuisineStyle || 'Не указано'}</div>
                  <div className="text-xs text-gray-400">Кухня</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-300">{venueProfile.venue_name || 'Заведение'}</div>
                  <div className="text-xs text-gray-400">Для</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Menu Tech Cards Modal */}
      {showMenuTechCards && menuTechCards && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800/95 backdrop-blur-lg rounded-2xl w-full max-w-6xl max-h-[90vh] overflow-y-auto border border-purple-400/20">
            {/* Header */}
            <div className="sticky top-0 bg-gray-800/95 backdrop-blur-lg border-b border-purple-400/20 p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-3xl font-bold text-purple-300 mb-2">📋 ТЕХКАРТЫ МЕНЮ</h2>
                  <p className="text-gray-400">Всего создано техкарт: {menuTechCards.total_cards}</p>
                </div>
                <button
                  onClick={() => {
                    setShowMenuTechCards(false);
                    setMenuTechCards(null);
                  }}
                  className="text-gray-400 hover:text-white text-3xl font-bold transition-colors"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              {menuTechCards.total_cards === 0 ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📋</div>
                  <h3 className="text-xl font-bold text-gray-300 mb-2">Техкарты ещё не созданы</h3>
                  <p className="text-gray-400 mb-6">Используйте кнопку "СОЗДАТЬ ВСЕ ТЕХКАРТЫ" для генерации</p>
                  <button
                    onClick={() => {
                      setShowMenuTechCards(false);
                      generateMassTechCards();
                    }}
                    className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                  >
                    🚀 СОЗДАТЬ ВСЕ ТЕХКАРТЫ
                  </button>
                </div>
              ) : (
                <div className="space-y-8">
                  {Object.entries(menuTechCards.tech_cards_by_category).map(([category, cards]) => (
                    <div key={category} className="bg-gray-700/30 rounded-lg p-6">
                      <h3 className="text-2xl font-bold text-purple-300 mb-4 capitalize">
                        {category} ({cards.length} блюд)
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {cards.map((card, index) => (
                          <div key={card.id} className="bg-gray-800/50 rounded-lg p-4 border border-gray-600/50">
                            <h4 className="font-bold text-white mb-2 line-clamp-2">{card.dish_name}</h4>
                            <p className="text-gray-300 text-sm mb-3 line-clamp-3">{card.content_preview}</p>
                            <div className="text-xs text-gray-400 mb-3">
                              Создано: {new Date(card.created_at).toLocaleDateString('ru-RU')}
                            </div>
                            <div className="flex gap-2">
                              <button
                                onClick={() => {
                                  // View full tech card
                                  setTechCard(card.content);
                                  setShowMenuTechCards(false);
                                  setCurrentTechCardId(card.id);
                                }}
                                className="flex-1 bg-green-600 hover:bg-green-700 text-white text-xs py-2 px-3 rounded transition-colors"
                              >
                                👁️ Смотреть
                              </button>
                              <button
                                onClick={() => openReplaceDishModal(card.dish_name, category, menuTechCards.menu_id)}
                                className="flex-1 bg-orange-600 hover:bg-orange-700 text-white text-xs py-2 px-3 rounded transition-colors"
                                title="Заменить это блюдо на другое"
                              >
                                🔄 Заменить
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            {menuTechCards.total_cards > 0 && (
              <div className="sticky bottom-0 bg-gray-800/95 backdrop-blur-lg border-t border-purple-400/20 p-6">
                <div className="flex justify-center gap-4">
                  <button
                    onClick={() => {
                      setShowMenuTechCards(false);
                      // Export all tech cards to PDF
                      alert('Экспорт всех техкарт в PDF скоро будет доступен!');
                    }}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                  >
                    📄 Экспорт всех в PDF
                  </button>
                  <button
                    onClick={() => {
                      setShowMenuTechCards(false);
                      generateMassTechCards();
                    }}
                    className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                  >
                    ➕ Добавить техкарты
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Menu Projects Modal - NEW! */}
      {showProjectsModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800/95 backdrop-blur-lg rounded-2xl w-full max-w-5xl max-h-[90vh] overflow-y-auto border border-purple-400/20">
            {/* Header */}
            <div className="sticky top-0 bg-gray-800/95 backdrop-blur-lg border-b border-purple-400/20 p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-3xl font-bold text-purple-300 mb-2">📁 ПРОЕКТЫ МЕНЮ</h2>
                  <p className="text-gray-400">Организуйте ваши меню и техкарты по проектам</p>
                </div>
                <button
                  onClick={() => setShowProjectsModal(false)}
                  className="text-gray-400 hover:text-white text-3xl font-bold transition-colors"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              {isLoadingProjects ? (
                <div className="text-center py-12">
                  <div className="text-4xl mb-4">⏳</div>
                  <p className="text-gray-400">Загружаем проекты...</p>
                </div>
              ) : menuProjects.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📁</div>
                  <h3 className="text-xl font-bold text-gray-300 mb-4">Пока нет проектов</h3>
                  <p className="text-gray-400 mb-6">
                    Создайте первый проект для организации ваших меню
                  </p>
                  <button
                    onClick={() => setShowCreateProjectModal(true)}
                    className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                  >
                    ➕ СОЗДАТЬ ПЕРВЫЙ ПРОЕКТ
                  </button>
                </div>
              ) : (
                <div>
                  {/* Create Project Button */}
                  <div className="mb-6">
                    <button
                      onClick={() => setShowCreateProjectModal(true)}
                      className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                    >
                      ➕ НОВЫЙ ПРОЕКТ
                    </button>
                  </div>

                  {/* Projects Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {menuProjects.map(project => (
                      <div key={project.id} className="bg-gray-700/50 rounded-lg p-6 border border-gray-600/50">
                        <div className="flex justify-between items-start mb-4">
                          <h3 className="font-bold text-white text-lg line-clamp-2">{project.project_name}</h3>
                          <div className="flex space-x-2">
                            <button
                              onClick={() => {
                                // TODO: View project details
                                alert('Просмотр проекта скоро будет доступен!');
                              }}
                              className="text-gray-400 hover:text-purple-300 transition-colors"
                              title="Просмотреть проект"
                            >
                              👁️
                            </button>
                            <button
                              onClick={() => {
                                // TODO: Edit project
                                alert('Редактирование проекта скоро будет доступен!');
                              }}
                              className="text-gray-400 hover:text-cyan-300 transition-colors"
                              title="Редактировать проект"
                            >
                              ✏️
                            </button>
                          </div>
                        </div>
                        
                        <p className="text-gray-300 text-sm mb-4 line-clamp-3">
                          {project.description || 'Описание отсутствует'}
                        </p>
                        
                        <div className="bg-gray-800/50 rounded-lg p-3 mb-4">
                          <div className="text-xs text-gray-400 mb-2">Статистика:</div>
                          <div className="flex justify-between text-sm">
                            <span className="text-cyan-300">📋 Меню: {project.menus_count}</span>
                            <span className="text-green-300">🍽️ Техкарты: {project.tech_cards_count}</span>
                          </div>
                        </div>
                        
                        <div className="text-xs text-gray-400 mb-4">
                          <div>Тип: <span className="text-purple-300 capitalize">{project.project_type}</span></div>
                          <div>Создан: {new Date(project.created_at).toLocaleDateString('ru-RU')}</div>
                        </div>
                        
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              setSimpleMenuData(prev => ({ ...prev, projectId: project.id }));
                              setShowProjectsModal(false);
                              setShowSimpleMenuModal(true);
                            }}
                            className="flex-1 bg-purple-600 hover:bg-purple-700 text-white text-xs py-2 px-3 rounded transition-colors"
                          >
                            ➕ Добавить меню
                          </button>
                          <button
                            onClick={() => {
                              // TODO: View project content
                              alert('Просмотр содержимого проекта скоро будет доступен!');
                            }}
                            className="flex-1 bg-gray-600 hover:bg-gray-700 text-white text-xs py-2 px-3 rounded transition-colors"
                          >
                            📂 Открыть
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Create Project Modal - NEW! */}
      {showCreateProjectModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800/95 backdrop-blur-lg rounded-2xl w-full max-w-2xl border border-purple-400/20">
            {/* Header */}
            <div className="border-b border-purple-400/20 p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold text-purple-300 mb-2">➕ СОЗДАТЬ ПРОЕКТ</h2>
                  <p className="text-gray-400">Новый проект для организации меню</p>
                </div>
                <button
                  onClick={() => {
                    setShowCreateProjectModal(false);
                    setNewProjectData({
                      projectName: '',
                      description: '',
                      projectType: '',
                      venueType: null
                    });
                  }}
                  className="text-gray-400 hover:text-white text-3xl font-bold transition-colors"
                  disabled={isCreatingProject}
                >
                  ×
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Project Name */}
              <div>
                <label className="block text-white font-bold mb-2">
                  📝 Название проекта *
                </label>
                <input
                  type="text"
                  value={newProjectData.projectName}
                  onChange={(e) => setNewProjectData(prev => ({ ...prev, projectName: e.target.value }))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:border-purple-400 focus:outline-none"
                  placeholder="Например: Летнее меню 2025, Банкетное меню, Детская кухня..."
                  maxLength={100}
                />
              </div>

              {/* Project Type */}
              <div>
                <label className="block text-white font-bold mb-2">
                  🎯 Тип проекта *
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { value: 'restaurant_launch', label: '🚀 Запуск ресторана', desc: 'Новое заведение' },
                    { value: 'seasonal_update', label: '🍂 Сезонное обновление', desc: 'Сезонные изменения' },
                    { value: 'special_event', label: '🎉 Специальное событие', desc: 'Банкеты, праздники' },
                    { value: 'menu_refresh', label: '🔄 Обновление меню', desc: 'Освежить текущее' }
                  ].map(type => (
                    <button
                      key={type.value}
                      onClick={() => setNewProjectData(prev => ({ ...prev, projectType: type.value }))}
                      className={`p-4 rounded-lg border text-left transition-all ${
                        newProjectData.projectType === type.value
                          ? 'bg-purple-600/20 border-purple-400 text-purple-200'
                          : 'bg-gray-700/50 border-gray-600 text-gray-300 hover:border-purple-500'
                      }`}
                    >
                      <div className="font-bold text-sm">{type.label}</div>
                      <div className="text-xs text-gray-400 mt-1">{type.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-white font-bold mb-2">
                  💭 Описание (необязательно)
                </label>
                <textarea
                  value={newProjectData.description}
                  onChange={(e) => setNewProjectData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:border-purple-400 focus:outline-none resize-none"
                  rows={3}
                  placeholder="Краткое описание проекта, целей, особенностей..."
                  maxLength={500}
                />
              </div>
            </div>

            {/* Footer */}
            <div className="border-t border-purple-400/20 p-6">
              <div className="flex gap-4">
                <button
                  onClick={() => {
                    setShowCreateProjectModal(false);
                    setNewProjectData({
                      projectName: '',
                      description: '',
                      projectType: '',
                      venueType: null
                    });
                  }}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                  disabled={isCreatingProject}
                >
                  ❌ Отменить
                </button>
                <button
                  onClick={createMenuProject}
                  disabled={isCreatingProject || !newProjectData.projectName.trim() || !newProjectData.projectType}
                  className="flex-2 bg-gradient-to-r from-purple-600 to-green-600 hover:from-purple-700 hover:to-green-700 disabled:from-gray-600 disabled:to-gray-700 disabled:opacity-50 text-white font-bold py-3 px-8 rounded-lg transition-all"
                >
                  {isCreatingProject ? (
                    <>⏳ Создаём проект...</>
                  ) : (
                    <>➕ СОЗДАТЬ ПРОЕКТ</>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Simple Menu Creation Modal - NEW! */}
      {showSimpleMenuModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800/95 backdrop-blur-lg rounded-2xl w-full max-w-3xl border border-purple-400/20">
            {/* Header */}
            <div className="border-b border-purple-400/20 p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-3xl font-bold text-purple-300 mb-2">🚀 СОЗДАТЬ МЕНЮ ЗА 4 КЛИКА</h2>
                  <p className="text-gray-400">Простое создание меню на основе профиля заведения</p>
                </div>
                <button
                  onClick={() => setShowSimpleMenuModal(false)}
                  className="text-gray-400 hover:text-white text-3xl font-bold transition-colors"
                  disabled={isGeneratingSimpleMenu}
                >
                  ×
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Step 1: Menu Type */}
              <div>
                <label className="block text-white font-bold mb-3">
                  🎯 1. Выберите тип меню:
                </label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { value: 'full', label: '🍽️ Полное меню', desc: 'Все категории блюд' },
                    { value: 'seasonal', label: '🍂 Сезонное', desc: 'Сезонные ингредиенты' },
                    { value: 'business_lunch', label: '⏰ Бизнес-ланч', desc: 'Быстрые блюда' },
                    { value: 'event', label: '🎉 Событийное', desc: 'Специальное меню' }
                  ].map(type => (
                    <button
                      key={type.value}
                      onClick={() => setSimpleMenuData(prev => ({ ...prev, menuType: type.value }))}
                      className={`p-4 rounded-lg border text-left transition-all ${
                        simpleMenuData.menuType === type.value
                          ? 'bg-purple-600/20 border-purple-400 text-purple-200'
                          : 'bg-gray-700/50 border-gray-600 text-gray-300 hover:border-purple-500'
                      }`}
                    >
                      <div className="font-bold text-sm">{type.label}</div>
                      <div className="text-xs text-gray-400 mt-1">{type.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Step 2: Expectations */}
              <div>
                <label className="block text-white font-bold mb-3">
                  💭 2. Опишите ваши ожидания от меню:
                </label>
                <textarea
                  value={simpleMenuData.expectations}
                  onChange={(e) => setSimpleMenuData(prev => ({ ...prev, expectations: e.target.value }))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:border-purple-400 focus:outline-none resize-none"
                  rows={4}
                  placeholder="Например: 'Хочу современное меню с акцентом на здоровую еду. Много овощей, рыба, минимум жирного. Подходящее для офисных сотрудников на обед. Цены средние, порции сытные.'"
                />
                <div className="text-xs text-gray-400 mt-2">
                  💡 Чем подробнее опишите, тем лучше результат
                </div>
              </div>

              {/* Step 3: Dish Count (Optional) */}
              <div>
                <label className="block text-white font-bold mb-3">
                  📊 3. Количество блюд (необязательно):
                </label>
                <div className="flex items-center space-x-4">
                  <input
                    type="number"
                    min="6"
                    max="50"
                    value={simpleMenuData.dishCount || venueProfile.default_dish_count || 12}
                    onChange={(e) => setSimpleMenuData(prev => ({ 
                      ...prev, 
                      dishCount: parseInt(e.target.value) || 12 
                    }))}
                    className="bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white w-20 focus:border-purple-400 focus:outline-none"
                  />
                  <span className="text-gray-400">блюд</span>
                  <div className="text-xs text-gray-400">
                    (По умолчанию: {venueProfile.default_dish_count || 12} из профиля заведения)
                  </div>
                </div>
              </div>

              {/* Step 4: Project Selection - RE-ENABLED! */}
              <div>
                <label className="block text-white font-bold mb-3">
                  📁 4. Добавить в проект (необязательно):
                </label>
                <div className="flex gap-3">
                  <select
                    value={simpleMenuData.projectId || ''}
                    onChange={(e) => setSimpleMenuData(prev => ({ 
                      ...prev, 
                      projectId: e.target.value || null 
                    }))}
                    className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:border-purple-400 focus:outline-none"
                  >
                    <option value="">Без проекта</option>
                    {menuProjects.map(project => (
                      <option key={project.id} value={project.id}>
                        {project.project_name} ({project.menus_count + project.tech_cards_count} элементов)
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={() => setShowCreateProjectModal(true)}
                    className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition-colors text-sm"
                  >
                    ➕ Новый
                  </button>
                </div>
                <div className="text-xs text-gray-400 mt-2">
                  💡 Проекты помогают организовать меню по темам: "Летнее меню", "Банкет", "Детское меню"
                </div>
              </div>

              {/* Profile Warning */}
              {(!venueProfile.venue_type || !venueProfile.cuisine_focus?.length) && (
                <div className="bg-yellow-900/20 border border-yellow-400/30 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <span className="text-yellow-400 text-xl">⚠️</span>
                    <div>
                      <p className="text-yellow-200 font-semibold mb-1">Профиль заведения не настроен</p>
                      <p className="text-yellow-100 text-sm mb-3">
                        Для лучших результатов рекомендуем настроить профиль заведения перед созданием меню.
                      </p>
                      <button
                        onClick={() => {
                          setShowSimpleMenuModal(false);
                          setShowVenueProfileModal(true);
                        }}
                        className="bg-yellow-600 hover:bg-yellow-700 text-white text-sm font-bold py-2 px-4 rounded transition-colors mr-2"
                      >
                        ⚙️ НАСТРОИТЬ ПРОФИЛЬ
                      </button>
                      <button
                        onClick={async () => {
                          // Quick setup with defaults based on menu type
                          const quickProfile = {
                            venue_type: simpleMenuData.menuType === 'business_lunch' ? 'office_cafe' : 'family_restaurant',
                            cuisine_focus: ['russian'],
                            average_check: 800,
                            region: currentUser?.city || 'moskva'
                          };
                          
                          try {
                            await axios.post(`${API}/update-venue-profile/${currentUser.id}`, quickProfile);
                            // Update local venue profile
                            setVenueProfile(prev => ({ ...prev, ...quickProfile }));
                            alert('✅ Быстрая настройка профиля завершена!');
                          } catch (error) {
                            console.error('Error quick setup profile:', error);
                            alert('Ошибка быстрой настройки. Используйте полную настройку.');
                          }
                        }}
                        className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold py-2 px-3 rounded transition-colors"
                      >
                        ⚡ Быстро
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Quick Profile Setup - NEW! */}
              {(venueProfile.venue_type || venueProfile.cuisine_focus?.length) && (
                <div className="bg-green-900/20 border border-green-400/30 rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div className="flex items-start gap-3">
                      <span className="text-green-400 text-xl">✅</span>
                      <div>
                        <p className="text-green-200 font-semibold mb-1">Профиль настроен</p>
                        <p className="text-green-100 text-sm">
                          Тип: {venueProfile.venue_type || 'не указан'}, 
                          Кухня: {venueProfile.cuisine_focus?.join(', ') || 'не указана'}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        setShowSimpleMenuModal(false);
                        setShowVenueProfileModal(true);
                      }}
                      className="bg-green-600 hover:bg-green-700 text-white text-xs font-bold py-1 px-3 rounded transition-colors"
                    >
                      ⚙️ Изменить
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="border-t border-purple-400/20 p-6">
              <div className="flex gap-4">
                <button
                  onClick={() => setShowSimpleMenuModal(false)}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                  disabled={isGeneratingSimpleMenu}
                >
                  ❌ Отменить
                </button>
                <button
                  onClick={generateSimpleMenu}
                  disabled={isGeneratingSimpleMenu || !simpleMenuData.menuType || !simpleMenuData.expectations.trim()}
                  className="flex-2 bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-700 hover:to-cyan-700 disabled:from-gray-600 disabled:to-gray-700 disabled:opacity-50 text-white font-bold py-3 px-8 rounded-lg transition-all z-[9999] relative pointer-events-auto"
                >
                  {isGeneratingSimpleMenu ? (
                    <>⏳ Создаём меню...</>
                  ) : (
                    <>🚀 СОЗДАТЬ МЕНЮ</>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Replace Dish Modal */}
      {showReplaceDishModal && replacingDishData && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800/95 backdrop-blur-lg rounded-2xl w-full max-w-2xl border border-purple-400/20">
            {/* Header */}
            <div className="border-b border-purple-400/20 p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold text-purple-300 mb-2">🔄 ЗАМЕНИТЬ БЛЮДО</h2>
                  <p className="text-gray-400">
                    Заменяем: <span className="text-white font-semibold">"{replacingDishData.dish_name}"</span>
                  </p>
                  <p className="text-gray-400">
                    Категория: <span className="text-purple-300">{replacingDishData.category}</span>
                  </p>
                </div>
                <button
                  onClick={() => {
                    setShowReplaceDishModal(false);
                    setReplacingDishData(null);
                    setReplacementPrompt('');
                  }}
                  className="text-gray-400 hover:text-white text-3xl font-bold transition-colors"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              <div className="mb-6">
                <label className="block text-white font-bold mb-2">
                  💭 Опишите пожелания для замены (необязательно):
                </label>
                <textarea
                  value={replacementPrompt}
                  onChange={(e) => setReplacementPrompt(e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:border-purple-400 focus:outline-none resize-none"
                  rows={4}
                  placeholder="Например: 'Хочу более острое блюдо', 'Сделай вегетарианскую версию', 'Используй морепродукты вместо мяса', 'Адаптируй под азиатскую кухню'..."
                />
                <div className="text-xs text-gray-400 mt-2">
                  💡 Подсказка: Чем конкретнее описание, тем лучше результат замены
                </div>
              </div>

              <div className="bg-yellow-900/20 border border-yellow-400/30 rounded-lg p-4 mb-6">
                <div className="flex items-start gap-3">
                  <span className="text-yellow-400 text-xl">⚠️</span>
                  <div>
                    <p className="text-yellow-200 font-semibold mb-1">Что произойдет:</p>
                    <ul className="text-yellow-100 text-sm space-y-1">
                      <li>• ИИ создаст новое блюдо в том же стиле</li>
                      <li>• Техкарта будет сохранена в истории</li>
                      <li>• Старое блюдо останется в архиве</li>
                      <li>• Потратится 1 техкарта из лимита</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4">
                <button
                  onClick={() => {
                    setShowReplaceDishModal(false);
                    setReplacingDishData(null);
                    setReplacementPrompt('');
                  }}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                  disabled={isReplacingDish}
                >
                  ❌ Отменить
                </button>
                <button
                  onClick={replaceDish}
                  disabled={isReplacingDish}
                  className="flex-1 bg-orange-600 hover:bg-orange-700 disabled:bg-orange-800 disabled:opacity-50 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                >
                  {isReplacingDish ? '⏳ Заменяем...' : '🔄 ЗАМЕНИТЬ БЛЮДО'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;