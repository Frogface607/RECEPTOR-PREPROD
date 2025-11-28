import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './App.css';
import OnboardingTour from './OnboardingTour';
import TourSystem from './components/TourSystem';
import tourConfigs from './tours/tourConfigs';
import ModernAuthModal from './components/ModernAuthModal';
import PricingPage from './components/PricingPage';
import CulinaryAssistant from './components/CulinaryAssistant';
import TechCardConstructor from './components/techcard-constructor';
import { FEATURE_HACCP, FORCE_TECHCARD_V2 } from './config/featureFlags';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8002';
const API = `${BACKEND_URL}/api`;  // Backend routes already include /api prefix

// Note: formatProAIContent function is already defined below and handles markdown formatting

function App() {
  // Check if debug mode is enabled (?debug=1 in URL)
  const isDebugMode = new URLSearchParams(window.location.search).get('debug') === '1';
  
  const [currentUser, setCurrentUser] = useState(null);
  const [showRegistration, setShowRegistration] = useState(false);
  
  // 🎯 Onboarding state
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [activeTour, setActiveTour] = useState(null); // 'welcome', 'createTechcard', 'aiKitchen', 'iiko', 'finance'
  
  // 🚀 Modern Auth state
  const [showModernAuth, setShowModernAuth] = useState(false);
  
  // Check if user is new (first time) - show onboarding
  useEffect(() => {
    const hasSeenOnboarding = localStorage.getItem('hasSeenOnboarding');
    const hasGeneratedTechcards = localStorage.getItem('userHistory');
    
    // Show onboarding if:
    // 1. Never seen before
    // 2. OR never generated any techcards
    if (!hasSeenOnboarding && !hasGeneratedTechcards) {
      // Delay to let UI load first
      const timer = setTimeout(() => {
        setActiveTour('welcome');
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, []);
  
  const handleOnboardingComplete = () => {
    localStorage.setItem('hasSeenOnboarding', 'true');
    setShowOnboarding(false);
    setActiveTour(null);
  };

  const handleOnboardingSkip = () => {
    localStorage.setItem('hasSeenOnboarding', 'skipped');
    setShowOnboarding(false);
    setActiveTour(null);
  };
  
  // УПРОЩЕНИЕ: Убрали выбор города - он не влияет на функционал
  // const [cities, setCities] = useState([]);
  // const [selectedCity, setSelectedCity] = useState('');
  
  // Moved to later section with other generation states
  
  // Ingredient mapping states
  const [mappingModalOpen, setMappingModalOpen] = useState(false);
  const [mappingIngredientIndex, setMappingIngredientIndex] = useState(null);
  const [catalogSearchQuery, setCatalogSearchQuery] = useState('');
  const [catalogSearchResults, setCatalogSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isRecalculating, setIsRecalculating] = useState(false);
  const [mappingActiveTab, setMappingActiveTab] = useState('iiko'); // P0: Default source is iiko
  const [personalCabinetTab, setPersonalCabinetTab] = useState('profile'); // Personal cabinet tab: 'profile', 'subscription', 'venue', 'integrations', 'settings'
  const [usdaSearchQuery, setUsdaSearchQuery] = useState('');
  const [usdaSearchResults, setUsdaSearchResults] = useState([]);
  const [isSearchingUsda, setIsSearchingUsda] = useState(false);
  const [priceSearchQuery, setPriceSearchQuery] = useState('');
  const [priceSearchResults, setPriceSearchResults] = useState([]);
  const [isSearchingPrice, setIsSearchingPrice] = useState(false);
  const [iikoSearchQuery, setIikoSearchQuery] = useState('');
  const [iikoSearchResults, setIikoSearchResults] = useState([]);
  const [iikoSearchBadge, setIikoSearchBadge] = useState({
    count: 0,
    last_sync: null,
    connection_status: 'not_connected'
  });
  const [isSearchingIiko, setIsSearchingIiko] = useState(false);
  
  // Auto-mapping states (IK-02B-FE/02)
  const [showAutoMappingModal, setShowAutoMappingModal] = useState(false);
  const [autoMappingResults, setAutoMappingResults] = useState([]);
  const [autoMappingFilter, setAutoMappingFilter] = useState('all'); // 'all', 'no_product_code', 'low_confidence'
  const [autoMappingSearch, setAutoMappingSearch] = useState('');
  const [isAutoMapping, setIsAutoMapping] = useState(false);
  const [autoMappingMessage, setAutoMappingMessage] = useState({ type: '', text: '' });
  const [preserveExistingProductCode, setPreserveExistingProductCode] = useState(true);
  const [tcV2Backup, setTcV2Backup] = useState(null); // For undo functionality
  const [tcV2Ready, setTcV2Ready] = useState(false); // Track when tcV2 is fully loaded
  
  // Export wizard states (CREATE EXPORT WIZARD UI)
  const [showExportWizard, setShowExportWizard] = useState(false);
  const [showAdvancedActions, setShowAdvancedActions] = useState(false); // P1: Advanced actions dropdown
  const [exportWizardStep, setExportWizardStep] = useState(1); // 1-4
  const [exportWizardData, setExportWizardData] = useState({
    preCheckResults: null,
    autoMappingResults: null,
    coverageBefore: null,
    coverageAfter: null,
    exportUrl: null,
    stepTimings: {}
  });
  const [isExportProcessing, setIsExportProcessing] = useState(false);
  const [exportMessage, setExportMessage] = useState({ type: '', text: '' });

  // NEW: Unified Export Wizard states
  const [showUnifiedExportWizard, setShowUnifiedExportWizard] = useState(false);
  const [selectedExportType, setSelectedExportType] = useState(null); // 'xlsx', 'zip', 'pdf', 'full_package'
  const [exportProgress, setExportProgress] = useState(0);
  const [exportStatus, setExportStatus] = useState('idle'); // 'idle', 'processing', 'success', 'error'
  const [currentExportStep, setCurrentExportStep] = useState('');
  const [exportResults, setExportResults] = useState([]);
  
  // Phase 3: FE-04-min Export to iiko (2 steps) states
  const [showPhase3ExportModal, setShowPhase3ExportModal] = useState(false);
  const [phase3ExportState, setPhase3ExportState] = useState('idle'); // 'idle', 'running_preflight', 'ready_zip', 'error'
  const [preflightResult, setPreflightResult] = useState(null);
  const [phase3ExportMessage, setPhase3ExportMessage] = useState({ type: '', text: '' });
  const [zipDownloadUrl, setZipDownloadUrl] = useState(null);
  const [phase3ErrorDetails, setPhase3ErrorDetails] = useState(null);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingType, setLoadingType] = useState(''); // 'techcard', 'sales', 'pairing', 'photo'
  const [techCard, setTechCard] = useState(null);
  const [tcV2, setTcV2] = useState(null); // TechCardV2 data object
  const [userTechCards, setUserTechCards] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editInstruction, setEditInstruction] = useState('');
  const [isEditingAI, setIsEditingAI] = useState(false);
  const [currentTechCardId, setCurrentTechCardId] = useState(null);
  const [ingredients, setIngredients] = useState([]);

  // ===== AI-KITCHEN STATE =====
  const [aiKitchenDishName, setAiKitchenDishName] = useState('');
  const [aiKitchenRecipe, setAiKitchenRecipe] = useState(null);

  // ===== WIZARD STATE MANAGEMENT =====
  const [wizardStep, setWizardStep] = useState(1);
  const [wizardData, setWizardData] = useState({
    // Step 1: Базовая информация
    dishName: '',
    cuisine: '',
    restaurantType: 'casual',
    
    // Step 2: Настройки
    budget: 500,
    equipment: [],
    dietary: [],
    portions: 1,
    
    // Step 3: AI результат (будет заполнено после генерации)
    generatedCard: null
  });

  // Wizard navigation functions
  const nextWizardStep = () => {
    if (wizardStep < 4) {
      setWizardStep(wizardStep + 1);
    }
  };
  
  const prevWizardStep = () => {
    if (wizardStep > 1) {
      setWizardStep(wizardStep - 1);
    }
  };
  
  const updateWizardData = (step, data) => {
    setWizardData(prev => ({
      ...prev,
      ...data
    }));
  };

  // ===== WIZARD COMPONENTS =====
  
  // Progress Bar Component
  const WizardProgressBar = () => {
    const steps = [
      { number: 1, title: "Основное", icon: "📝" },
      { number: 2, title: "Настройки", icon: "⚙️" },
      { number: 3, title: "Генерация", icon: "🤖" },
      { number: 4, title: "Результат", icon: "✨" }
    ];

    return (
      <div className="mb-8">
        <div className="flex items-center justify-between relative">
          {/* Progress line background */}
          <div className="absolute top-6 left-0 right-0 h-1 bg-gray-700 rounded-full" />
          
          {/* Active progress line */}
          <div 
            className="absolute top-6 left-0 h-1 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-500 ease-in-out"
            style={{ width: `${((wizardStep - 1) / (steps.length - 1)) * 100}%` }}
          />
          
          {steps.map((step, index) => {
            const isActive = wizardStep === step.number;
            const isCompleted = wizardStep > step.number;
            const isAccessible = wizardStep >= step.number;
            
            return (
              <div key={step.number} className="relative z-10">
                <button
                  onClick={() => {
                    // Можно вернуться к предыдущим шагам
                    if (step.number < wizardStep) {
                      setWizardStep(step.number);
                    }
                  }}
                  disabled={!isAccessible && step.number > wizardStep}
                  className={`
                    w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold transition-all duration-300 border-2
                    ${isActive 
                      ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white border-transparent shadow-lg shadow-purple-500/30 scale-110' 
                      : isCompleted 
                        ? 'bg-green-500 text-white border-green-400 hover:scale-105' 
                        : 'bg-gray-700 text-gray-400 border-gray-600'
                    }
                    ${isAccessible && step.number < wizardStep ? 'cursor-pointer hover:scale-105' : 'cursor-default'}
                  `}
                  title={`${step.title} ${isCompleted ? '(завершено)' : isActive ? '(текущий)' : ''}`}
                >
                  {isCompleted ? '✓' : step.icon}
                </button>
                
                <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2">
                  <div className={`text-xs font-medium whitespace-nowrap ${
                    isActive ? 'text-purple-300' : isCompleted ? 'text-green-300' : 'text-gray-500'
                  }`}>
                    {step.title}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };
  
  // Step 1: Базовая информация
  const WizardStep1 = () => {
    const cuisines = [
      'русская', 'итальянская', 'французская', 'японская', 'китайская', 
      'мексиканская', 'индийская', 'средиземноморская', 'американская', 'грузинская'
    ];
    
    const restaurantTypes = [
      { value: 'fine-dining', label: 'Fine Dining', desc: 'Высокая кухня' },
      { value: 'casual', label: 'Casual Dining', desc: 'Повседневное' },
      { value: 'fast-casual', label: 'Fast Casual', desc: 'Быстрое питание' },
      { value: 'cafe', label: 'Кафе/Бистро', desc: 'Легкие блюда' }
    ];

    return (
      <div className="space-y-6">
        <div className="text-center mb-6">
          <h3 className="text-2xl font-bold text-purple-300 mb-2">Расскажите о блюде</h3>
          <p className="text-gray-400">Базовая информация для создания техкарты</p>
        </div>
        
        {/* Название блюда */}
        <div>
          <label className="block text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
            📝 Название и описание блюда
          </label>
          <div className="relative">
            <textarea
              value={wizardData.dishName}
              onChange={(e) => updateWizardData(1, { dishName: e.target.value })}
              placeholder="Опишите блюдо подробно. Например: Стейк из говядины с картофельным пюре и грибным соусом"
              className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none min-h-[120px] resize-none"
              rows={5}
              required
            />
            <div className="absolute bottom-3 right-3 text-xs text-gray-500">
              {wizardData.dishName.length}/500
            </div>
          </div>
        </div>

        {/* Тип кухни */}
        <div>
          <label className="block text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
            🍽️ Тип кухни
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {cuisines.map(cuisine => (
              <button
                key={cuisine}
                type="button"
                onClick={() => updateWizardData(1, { cuisine })}
                className={`px-3 py-2 rounded-lg border transition-colors capitalize ${
                  wizardData.cuisine === cuisine
                    ? 'bg-purple-600 border-purple-500 text-white'
                    : 'bg-gray-700 border-gray-600 text-gray-300 hover:border-purple-500'
                }`}
              >
                {cuisine}
              </button>
            ))}
          </div>
        </div>

        {/* Тип заведения */}
        <div>
          <label className="block text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
            🏪 Тип заведения
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {restaurantTypes.map(type => (
              <button
                key={type.value}
                type="button"
                onClick={() => updateWizardData(1, { restaurantType: type.value })}
                className={`p-4 rounded-lg border text-left transition-colors ${
                  wizardData.restaurantType === type.value
                    ? 'bg-purple-600/20 border-purple-500 text-white'
                    : 'bg-gray-700 border-gray-600 text-gray-300 hover:border-purple-500'
                }`}
              >
                <div className="font-medium">{type.label}</div>
                <div className="text-sm opacity-70">{type.desc}</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // Step 2: Настройки
  const WizardStep2 = () => {
    const equipmentOptions = [
      { id: 'плита', label: '🔥 Плита', category: 'basic' },
      { id: 'духовка', label: '🔥 Духовка', category: 'basic' },
      { id: 'гриль', label: '🥩 Гриль', category: 'cooking' },
      { id: 'фритюр', label: '🍟 Фритюр', category: 'cooking' },
      { id: 'пароварка', label: '💨 Пароварка', category: 'cooking' },
      { id: 'блендер', label: '🌪️ Блендер', category: 'prep' },
      { id: 'миксер', label: '🥄 Миксер', category: 'prep' },
      { id: 'мясорубка', label: '🥩 Мясорубка', category: 'prep' }
    ];

    const dietaryOptions = [
      { id: 'vegetarian', label: '🌱 Вегетарианское', color: 'green' },
      { id: 'vegan', label: '🌿 Веганское', color: 'green' },
      { id: 'gluten-free', label: '🌾 Без глютена', color: 'blue' },
      { id: 'lactose-free', label: '🥛 Без лактозы', color: 'blue' },
      { id: 'keto', label: '🥑 Кето', color: 'purple' },
      { id: 'low-carb', label: '🥬 Низкоуглеводное', color: 'purple' }
    ];

    const toggleEquipment = (equipmentId) => {
      const newEquipment = wizardData.equipment.includes(equipmentId)
        ? wizardData.equipment.filter(id => id !== equipmentId)
        : [...wizardData.equipment, equipmentId];
      updateWizardData(2, { equipment: newEquipment });
    };

    const toggleDietary = (dietaryId) => {
      const newDietary = wizardData.dietary.includes(dietaryId)
        ? wizardData.dietary.filter(id => id !== dietaryId)
        : [...wizardData.dietary, dietaryId];
      updateWizardData(2, { dietary: newDietary });
    };

    return (
      <div className="space-y-6">
        <div className="text-center mb-6">
          <h3 className="text-2xl font-bold text-purple-300 mb-2">Настройки техкарты</h3>
          <p className="text-gray-400">Бюджет, оборудование и особенности блюда</p>
        </div>

        {/* Бюджет */}
        <div>
          <label className="block text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
            💰 Бюджет на порцию
          </label>
          <div className="space-y-3">
            <input
              type="range"
              min="100"
              max="2000"
              step="50"
              value={wizardData.budget}
              onChange={(e) => updateWizardData(2, { budget: parseInt(e.target.value) })}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
            />
            <div className="flex justify-between text-sm text-gray-400">
              <span>100₽</span>
              <span className="text-white font-bold">{wizardData.budget}₽</span>
              <span>2000₽</span>
            </div>
            <div className="text-center">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                wizardData.budget <= 300 ? 'bg-green-600/20 text-green-300' :
                wizardData.budget <= 700 ? 'bg-yellow-600/20 text-yellow-300' :
                'bg-red-600/20 text-red-300'
              }`}>
                {wizardData.budget <= 300 ? '💚 Эконом' :
                 wizardData.budget <= 700 ? '💛 Стандарт' : '💎 Премиум'}
              </span>
            </div>
          </div>
        </div>

        {/* Количество порций */}
        <div>
          <label className="block text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
            🍽️ Количество порций
          </label>
          <div className="flex items-center space-x-4">
            <button
              type="button"
              onClick={() => updateWizardData(2, { portions: Math.max(1, wizardData.portions - 1) })}
              className="w-10 h-10 bg-gray-700 hover:bg-gray-600 text-white rounded-lg flex items-center justify-center font-bold"
            >
              -
            </button>
            <span className="text-2xl font-bold text-white min-w-[60px] text-center">
              {wizardData.portions}
            </span>
            <button
              type="button"
              onClick={() => updateWizardData(2, { portions: Math.min(20, wizardData.portions + 1) })}
              className="w-10 h-10 bg-gray-700 hover:bg-gray-600 text-white rounded-lg flex items-center justify-center font-bold"
            >
              +
            </button>
          </div>
        </div>

        {/* Оборудование */}
        <div>
          <label className="block text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
            🔧 Доступное оборудование
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {equipmentOptions.map(equipment => (
              <button
                key={equipment.id}
                type="button"
                onClick={() => toggleEquipment(equipment.id)}
                className={`p-3 rounded-lg border text-left transition-colors ${
                  wizardData.equipment.includes(equipment.id)
                    ? 'bg-purple-600/20 border-purple-500 text-white'
                    : 'bg-gray-700 border-gray-600 text-gray-300 hover:border-purple-500'
                }`}
              >
                <div className="text-sm font-medium">{equipment.label}</div>
              </button>
            ))}
          </div>
          {wizardData.equipment.length === 0 && (
            <p className="text-orange-400 text-sm mt-2">⚠️ Выберите хотя бы одну единицу оборудования</p>
          )}
        </div>

        {/* Диетические ограничения */}
        <div>
          <label className="block text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
            🥗 Диетические особенности (опционально)
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {dietaryOptions.map(dietary => (
              <button
                key={dietary.id}
                type="button"
                onClick={() => toggleDietary(dietary.id)}
                className={`p-3 rounded-lg border text-left transition-colors ${
                  wizardData.dietary.includes(dietary.id)
                    ? `bg-${dietary.color}-600/20 border-${dietary.color}-500 text-white`
                    : 'bg-gray-700 border-gray-600 text-gray-300 hover:border-gray-500'
                }`}
              >
                <div className="text-sm font-medium">{dietary.label}</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // Step 3: AI Генерация 
  const WizardStep3 = () => {
    const handleGenerateCard = async () => {
      // Use global isGenerating state
      setIsGenerating(true);
      setGenerationStatus(null);
      setGenerationError(null);
      setGenerationIssues([]);
      
      // Using wizard data directly
      
      try {
        if (isDebugMode) {
          console.log('🚀 Generating tech card with wizard data:', wizardData);
        }
        
        const response = await axios.post(`${API}/v1/techcards.v2/generate`, {
          name: wizardData.dishName,
          cuisine: wizardData.cuisine,
          equipment: wizardData.equipment,
          budget: wizardData.budget,
          dietary: wizardData.dietary,
          portions: wizardData.portions,
          restaurant_type: wizardData.restaurantType,
          user_id: currentUser?.id || 'demo_user'
        });

        console.log('✅ Tech card generation response:', response.data);
        
        if (response.data.status === 'READY' || response.data.status === 'DRAFT') {
          // Store the generated card in global state
          setTcV2(response.data.card);
          setTechCard(null); // Clear V1 card
          setCurrentTechCardId(response.data.card?.meta?.id || null);
          
          // Update wizard data
          updateWizardData(3, { generatedCard: response.data.card });
          
          // Set generation status
          setGenerationStatus(response.data.status.toLowerCase());
          setGenerationIssues(response.data.issues || []);
          
          // Auto-advance to next step
          setTimeout(() => nextWizardStep(), 1000);
        } else {
          throw new Error(response.data.message || 'Generation failed');
        }
      } catch (error) {
        console.error('❌ Generation error:', error);
        setGenerationError('Ошибка генерации техкарты: ' + (error.response?.data?.detail || error.message));
        setGenerationStatus('error');
        alert('Ошибка генерации техкарты. Попробуйте еще раз.');
      } finally {
        setIsGenerating(false);
      }
    };

    return (
      <div className="space-y-6">
        <div className="text-center mb-8">
          <h3 className="text-2xl font-bold text-purple-300 mb-2">Создание техкарты</h3>
          <p className="text-gray-400">AI создаст техкарту на основе ваших данных</p>
        </div>

        {/* Summary */}
        <div className="bg-gray-700/50 rounded-lg p-6 space-y-4">
          <h4 className="text-lg font-semibold text-white mb-4">📋 Краткое содержание:</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Блюдо:</span>
              <span className="text-white ml-2 font-medium">{wizardData.dishName.slice(0, 50)}...</span>
            </div>
            
            <div>
              <span className="text-gray-400">Кухня:</span>
              <span className="text-white ml-2 capitalize">{wizardData.cuisine}</span>
            </div>
            
            <div>
              <span className="text-gray-400">Бюджет:</span>
              <span className="text-white ml-2">{wizardData.budget}₽ на порцию</span>
            </div>
            
            <div>
              <span className="text-gray-400">Порций:</span>
              <span className="text-white ml-2">{wizardData.portions}</span>
            </div>
            
            <div className="col-span-1 md:col-span-2">
              <span className="text-gray-400">Оборудование:</span>
              <span className="text-white ml-2">{wizardData.equipment.join(', ')}</span>
            </div>
            
            {wizardData.dietary.length > 0 && (
              <div className="col-span-1 md:col-span-2">
                <span className="text-gray-400">Особенности:</span>
                <span className="text-white ml-2">{wizardData.dietary.join(', ')}</span>
              </div>
            )}
          </div>
        </div>

        {/* Generation Button or Progress */}
        {!wizardData.generatedCard ? (
          <div className="text-center">
            {isGenerating ? (
              <div className="space-y-4">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
                <p className="text-purple-300 font-medium">🤖 Создаю техкарту...</p>
                <div className="animate-pulse text-gray-400 text-sm">
                  Анализирую ингредиенты • Рассчитываю пропорции • Создаю рецепт...
                </div>
              </div>
            ) : (
              <button
                onClick={handleGenerateCard}
                className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold py-4 px-8 rounded-lg text-lg transition-all duration-300 transform hover:scale-105 shadow-lg shadow-purple-500/25"
              >
                🚀 Создать техкарту
              </button>
            )}
            
            {/* Error display */}
            {generationError && (
              <div className="mt-4 bg-red-900/30 border border-red-400/50 rounded-lg p-4">
                <div className="text-red-300 font-medium">❌ Ошибка генерации</div>
                <div className="text-red-400 text-sm mt-1">{generationError}</div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center space-y-4">
            <div className="text-6xl">✅</div>
            <h4 className="text-xl font-bold text-green-400">Техкарта создана успешно!</h4>
            <p className="text-gray-400">Переходим к финальному просмотру...</p>
            
            {/* Show generation issues if any */}
            {generationIssues && generationIssues.length > 0 && (
              <div className="bg-yellow-900/30 border border-yellow-400/50 rounded-lg p-4 max-w-md mx-auto">
                <div className="text-yellow-300 font-medium mb-2">⚠️ Замечания</div>
                <div className="text-yellow-400 text-sm space-y-1">
                  {generationIssues.slice(0, 3).map((issue, idx) => (
                    <div key={idx}>• {typeof issue === 'string' ? issue : issue.message || issue.type}</div>
                  ))}
                  {generationIssues.length > 3 && (
                    <div className="text-yellow-500">...и еще {generationIssues.length - 3}</div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  // Step 4: Финальный просмотр
  const WizardStep4 = () => {
    const handleFinishWizard = () => {
      // Tech card is already set in global state from Step 3
      // Just reset wizard to create a new card
      setWizardStep(1);
      setWizardData({
        dishName: '',
        cuisine: '',
        restaurantType: 'casual',
        budget: 500,
        equipment: [],
        dietary: [],
        portions: 1,
        generatedCard: null
      });
    };

    const handleExportToIIKO = () => {
      // This will trigger the existing IIKO export workflow
      handleFinishWizard();
      // Open export modal or navigate to export section
      setTimeout(() => {
        setShowPhase3ExportModal(true);
      }, 500);
    };

    return (
      <div className="space-y-6">
        <div className="text-center mb-8">
          <h3 className="text-2xl font-bold text-green-400 mb-2">🎉 Техкарта готова!</h3>
          <p className="text-gray-400">Просмотрите результат и выберите дальнейшие действия</p>
        </div>

        {/* Tech Card Preview */}
        {wizardData.generatedCard && (
          <div className="bg-gray-700/50 rounded-lg p-6 space-y-6">
            <h4 className="text-xl font-semibold text-white">
              📋 {wizardData.generatedCard.meta?.title || wizardData.dishName}
            </h4>
            
            {/* Basic Info */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="bg-purple-600/20 rounded-lg p-4">
                <div className="text-purple-300 font-medium">Кухня</div>
                <div className="text-white capitalize">{wizardData.cuisine}</div>
              </div>
              
              <div className="bg-blue-600/20 rounded-lg p-4">
                <div className="text-blue-300 font-medium">Порций</div>
                <div className="text-white">{wizardData.portions}</div>
              </div>
              
              <div className="bg-green-600/20 rounded-lg p-4">
                <div className="text-green-300 font-medium">Бюджет</div>
                <div className="text-white">{wizardData.budget}₽</div>
              </div>
            </div>

            {/* Ingredients Preview */}
            {wizardData.generatedCard.ingredients && (
              <div>
                <h5 className="text-lg font-semibold text-white mb-3">🥘 Ингредиенты:</h5>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {wizardData.generatedCard.ingredients.slice(0, 6).map((ingredient, index) => (
                    <div key={index} className="bg-gray-600/50 rounded px-3 py-2 text-sm">
                      <span className="text-white">{ingredient.name}</span>
                      <span className="text-gray-400 ml-2">
                        {ingredient.brutto_g || ingredient.netto_g}г
                      </span>
                    </div>
                  ))}
                  {wizardData.generatedCard.ingredients.length > 6 && (
                    <div className="text-gray-400 text-sm">
                      и еще {wizardData.generatedCard.ingredients.length - 6} ингредиентов...
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={handleFinishWizard}
            className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white font-bold py-4 px-6 rounded-lg transition-colors flex items-center justify-center"
          >
            ✏️ Редактировать техкарту
          </button>
          
          <button
            onClick={handleExportToIIKO}
            className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-4 px-6 rounded-lg transition-colors flex items-center justify-center"
          >
            Экспортировать в IIKO
          </button>
        </div>

        {/* Additional Actions */}
        <div className="text-center space-y-3">
          <button
            onClick={() => {
              setWizardStep(1);
              setWizardData({
                dishName: '',
                cuisine: '',
                restaurantType: 'casual',
                budget: 500,
                equipment: [],
                dietary: [],
                portions: 1,
                generatedCard: null
              });
            }}
            className="text-gray-400 hover:text-white transition-colors"
          >
            🔄 Создать новую техкарту
          </button>
        </div>
      </div>
    );
  };

  const canProceedToNextStep = () => {
    switch(wizardStep) {
      case 1:
        return wizardData.dishName.trim().length > 5 && wizardData.cuisine && wizardData.restaurantType;
      case 2: 
        return wizardData.budget > 0 && wizardData.equipment.length > 0;
      case 3:
        return wizardData.generatedCard !== null;
      default:
        return false;
    }
  };

  const handleGenerateTechCard = async (e) => {
    e.preventDefault();
    console.log('Generate button clicked');
    console.log('Dish name:', wizardData.dishName);
    console.log('Current user:', currentUser);
    
    // Clear previous status
    setGenerationStatus(null);
    setGenerationError(null);
    setGenerationIssues([]);
    
    if (!wizardData.dishName.trim()) {
      setGenerationError('Пожалуйста, введите название блюда');
      setGenerationStatus('error');
      return;
    }
    
    // Demo mode allows immediate access
    if (!currentUserOrDemo?.id) {
      setGenerationError('Ошибка инициализации пользователя');
      setGenerationStatus('error');
      return;
    }
    
    // Запускаем анимированную загрузку
    setIsGenerating(true);
    setLoadingType('techcard');
    const progressInterval = simulateProgress('techcard', 15000);
    
    const requestStartTime = Date.now();
    
    // Create AbortController for timeout handling
    const abortController = new AbortController();
    const timeoutId = setTimeout(() => {
      abortController.abort();
    }, 300000); // 5 minute timeout for V2 techcards
    
    try {
      const endpoint = `${API}/v1/techcards.v2/generate`;
      
      if (isDebugMode) {
        console.log('[DEBUG] Starting request to:', endpoint);
        console.log('[DEBUG] FORCE_TECHCARD_V2:', FORCE_TECHCARD_V2);
      }
      
      const requestData = {
        name: wizardData.dishName.trim(),
        cuisine: venueProfile?.cuisine || "европейская", 
        equipment: userEquipment.length > 0 ? userEquipment : ["плита", "кастрюля"],
        budget: venueProfile?.averageCheck ? parseFloat(venueProfile.averageCheck) : 300.0,
        dietary: [],
        user_id: currentUserOrDemo?.id || 'demo_user'
      };

      // Add enhanced context if available (from menu dishes)
      if (dishContext) {
        requestData.description = dishContext.description;
        // Clear context after use
        setDishContext(null);
      }
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
        signal: abortController.signal // Add abort signal
      });
      
      // Clear timeout on successful response
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('[V2] HTTP Error:', response.status, errorText);
        throw new Error(`Ошибка сервера (${response.status}): ${errorText}`);
      }
      
      const responseData = await response.json();
      
      if (isDebugMode) {
        console.log('[DEBUG] Response received:', responseData);
      }
      
      const requestDuration = Date.now() - requestStartTime;
      if (isDebugMode) {
        console.log(`[V2] API request completed in ${requestDuration}ms`);
      }
      
      // Complete the animation quickly
      clearInterval(progressInterval);
      setLoadingProgress(100);
      
      // ТС-001: Normalize response structure (handle both formats)
      const normalizedData = {
        status: responseData.status || (responseData.card ? 'success' : 'error'),
        card: responseData.card || responseData.techcard || responseData,
        issues: responseData.issues || responseData.validation_issues || []
      };
      
      if (isDebugMode) {
        console.log('[V2] Normalized data structure:', {
          status: normalizedData.status,
          hasCard: !!normalizedData.card,
          issuesCount: normalizedData.issues?.length || 0
        });
      }
      
      if (normalizedData.status === 'success' && normalizedData.card) {
        const techCardV2 = normalizedData.card;
        setTcV2(techCardV2);
        
        // Set the current tech card ID from the generated tech card
        if (techCardV2.meta && techCardV2.meta.id) {
          setCurrentTechCardId(techCardV2.meta.id);
          if (isDebugMode) {
            console.log('[V2] Set currentTechCardId to:', techCardV2.meta.id);
          }
        }
        
        setGenerationStatus('success');
        setGenerationIssues(normalizedData.issues || []);
        
        // Log success for debugging
        if (isDebugMode) {
          console.log('[V2] Generated TechCard V2 successfully');
          console.log('[V2] tcV2.version:', techCardV2.meta?.version);
          console.log('[V2] tcV2.status:', normalizedData.status);
          console.log('[V2] API endpoint used:', endpoint);
        }
        
        // Clear any previous V1 tech card state to avoid conflicts
        setTechCard(null);
        
        // Parse ingredients from V2 format
        const parsedIngredients = techCardV2.ingredients?.map((ing, index) => ({
          id: index + 1,
          name: ing.name,
          quantity: ing.netto_g.toString(),
          unit: ing.unit,
          unitPrice: '0', // Will be calculated from cost data
          totalPrice: '0',
          originalQuantity: ing.netto_g.toString(),
          originalPrice: '0'
        })) || [];
        
        setCurrentIngredients(parsedIngredients);
        
        setLoadingMessage('✨ Техкарта готова!');
        
      } else if (normalizedData.status === 'draft' && normalizedData.card) {
        const techCardV2 = normalizedData.card;
        setTcV2(techCardV2);
        
        // Set the current tech card ID from the generated tech card
        if (techCardV2.meta && techCardV2.meta.id) {
          setCurrentTechCardId(techCardV2.meta.id);
          if (isDebugMode) {
            console.log('[V2] Set currentTechCardId to:', techCardV2.meta.id);
          }
        }
        
        setGenerationStatus('draft');
        setGenerationIssues(normalizedData.issues || []);
        
        if (isDebugMode) {
          console.log('[V2] Generated draft tcV2 - validation issues found');
          console.log('[V2] Issues:', normalizedData.issues);
        }
        
        // Clear any previous V1 tech card state to avoid conflicts
        setTechCard(null);
        
        // Parse ingredients for draft version too
        const parsedIngredients = techCardV2.ingredients?.map((ing, index) => ({
          id: index + 1,
          name: ing.name,
          quantity: ing.netto_g.toString(),
          unit: ing.unit,
          unitPrice: '0',
          totalPrice: '0',
          originalQuantity: ing.netto_g.toString(),
          originalPrice: '0'
        })) || [];
        
        setCurrentIngredients(parsedIngredients);
        
        setLoadingMessage('⚠️ Техкарта создана (черновик)');
        
      } else if (normalizedData.status === 'READY' && normalizedData.card) {
        // TC-001: Handle READY status as success  
        const techCardV2 = normalizedData.card;
        setTcV2(techCardV2);
        
        if (techCardV2.meta && techCardV2.meta.id) {
          setCurrentTechCardId(techCardV2.meta.id);
          console.log('[V2] Set currentTechCardId to:', techCardV2.meta.id);
        }
        
        setGenerationStatus('success'); // Treat READY as success
        setGenerationIssues(normalizedData.issues || []);
        
        console.log('[V2] Generated TechCard V2 with READY status');
        
        // Clear any previous V1 tech card state to avoid conflicts
        setTechCard(null);
        
        const parsedIngredients = techCardV2.ingredients?.map((ing, index) => ({
          id: index + 1,
          name: ing.name,
          quantity: ing.netto_g.toString(),
          unit: ing.unit,
          unitPrice: '0',
          totalPrice: '0',
          originalQuantity: ing.netto_g.toString(),
          originalPrice: '0'
        })) || [];
        
        setCurrentIngredients(parsedIngredients);
        
        setLoadingMessage('✨ Техкарта готова!');
        
      } else {
        // Handle error cases
        const errorMsg = normalizedData.message || 'Неизвестная ошибка генерации';
        throw new Error(errorMsg);
      }
      
    } catch (error) {
      console.error('[V2] Generation error:', error);
      
      // Clear timeout if still active
      clearTimeout(timeoutId);
      
      // Always complete progress
      clearInterval(progressInterval);
      setLoadingProgress(100);
      
      // Handle different error types
      let errorMessage = 'Неизвестная ошибка при генерации техкарты';
      
      if (error.name === 'AbortError') {
        errorMessage = 'Превышено время ожидания ответа сервера (30 сек). Попробуйте позже.';
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      // Set error state
      setGenerationStatus('error');
      setGenerationError(errorMessage);
      setLoadingMessage('❌ Ошибка генерации');
      
      if (isDebugMode) {
        console.log('[DEBUG] Exception occurred:', error);
        console.log('[DEBUG] Error type:', error.name);
      }
    } finally {
      // Always clean up
      clearTimeout(timeoutId);
      clearInterval(progressInterval);
      
      // Always clean up UI state after a delay
      setTimeout(() => {
        setIsGenerating(false);
        setLoadingProgress(0);
        setLoadingMessage('');
        setLoadingType('');
      }, 2000);
    }
  };

  // Subscription states
  const [subscriptionPlans, setSubscriptionPlans] = useState({});
  const [userSubscription, setUserSubscription] = useState(null);
  const [kitchenEquipment, setKitchenEquipment] = useState({});
  const [userEquipment, setUserEquipment] = useState([]);
  const [showPricingModal, setShowPricingModal] = useState(false);
  const [showEquipmentModal, setShowEquipmentModal] = useState(false);
  const [isUpgrading, setIsUpgrading] = useState(false);
  // Upload states for Task 1.2
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showDataModal, setShowDataModal] = useState(false);
  const [uploadType, setUploadType] = useState('prices'); // 'prices' | 'nutrition'
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadPreview, setUploadPreview] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState(null);
  
  // iiko RMS integration states (IK-02B-FE/01)
  const [showIikoRmsModal, setShowIikoRmsModal] = useState(false);
  const [iikoRmsConnection, setIikoRmsConnection] = useState({
    status: 'not_connected', // 'not_connected', 'connected', 'needs_reconnection', 'error'
    host: '',
    login: '',
    organization_name: '',
    last_connection: null,
    sync_status: 'never_synced', // 'never_synced', 'syncing', 'completed', 'failed'
    products_count: 0,
    last_sync: null,
    error_message: ''
  });
  const [iikoRmsCredentials, setIikoRmsCredentials] = useState({
    host: '',  // Пользователь вводит свои данные
    login: '',
    password: ''
  });
  const [isConnectingIikoRms, setIsConnectingIikoRms] = useState(false);
  const [isSyncingIikoRms, setIsSyncingIikoRms] = useState(false);
  const [iikoRmsMessage, setIikoRmsMessage] = useState({ type: '', text: '' });
  
  // Inline editing states for Task 0.1
  const [editingIngredientIndex, setEditingIngredientIndex] = useState(null);
  const [editingData, setEditingData] = useState({});
  const [editingErrors, setEditingErrors] = useState({});
  const [showSubRecipeModal, setShowSubRecipeModal] = useState(false);
  const [availableSubRecipes, setAvailableSubRecipes] = useState([]);
  const [recalcError, setRecalcError] = useState(null);
  

  const [userHistory, setUserHistory] = useState([]);
  const [showPriceModal, setShowPriceModal] = useState(false);
  const [userPrices, setUserPrices] = useState([]);
  const [uploadingPrices, setUploadingPrices] = useState(false);
  
  // УПРОЩЕНИЕ: Убрали неиспользуемые состояния редактора ингредиентов
  // const [editableIngredients, setEditableIngredients] = useState([]);
  // const [isEditingIngredients, setIsEditingIngredients] = useState(false);
  // const [editableSteps, setEditableSteps] = useState([]);
  // const [isEditingSteps, setIsEditingSteps] = useState(false);

  // Instructions state
  const [showInstructions, setShowInstructions] = useState(false);

  // Interactive ingredients state (оставили для совместимости)
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
  
  // User Profile Edit states
  const [showProfileEditModal, setShowProfileEditModal] = useState(false);
  const [editProfileData, setEditProfileData] = useState({
    name: '',
    email: '',
    city: ''
  });
  const [isUpdatingUserProfile, setIsUpdatingUserProfile] = useState(false);
  
  // Set Password states (for users without password)
  const [showSetPasswordModal, setShowSetPasswordModal] = useState(false);
  const [setPasswordData, setSetPasswordData] = useState({
    password: '',
    confirmPassword: ''
  });
  const [isSettingPassword, setIsSettingPassword] = useState(false);
  
  // Pricing Page state
  const [showPricingPage, setShowPricingPage] = useState(false);
  const [venueTypes, setVenueTypes] = useState({});
  const [cuisineTypes, setCuisineTypes] = useState({});
  const [averageCheckCategories, setAverageCheckCategories] = useState({});
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);
  const [profileStep, setProfileStep] = useState(0); // 0 = IIKO, 1-4 = Profile wizard, 5 = Deep Research
  const [isResearching, setIsResearching] = useState(false);
  const [researchProgress, setResearchProgress] = useState(0);
  const [currentResearchMessage, setCurrentResearchMessage] = useState('');
  const [deepResearchData, setDeepResearchData] = useState(null);

  // Dashboard states
  const [currentView, setCurrentView] = useState('dashboard'); // 'dashboard', 'create', 'menu-generator', 'my-venue'
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

  // NEW: Enhanced Project Analytics states
  const [showProjectContentModal, setShowProjectContentModal] = useState(false);
  const [projectContent, setProjectContent] = useState(null);
  const [projectAnalytics, setProjectAnalytics] = useState(null);
  const [isLoadingProjectContent, setIsLoadingProjectContent] = useState(false);
  const [isLoadingProjectAnalytics, setIsLoadingProjectAnalytics] = useState(false);
  const [isExportingProject, setIsExportingProject] = useState(false);

  // Analytics & OLAP Reports states - NEW!
  const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);
  const [selectedAnalyticsType, setSelectedAnalyticsType] = useState('overview'); // 'overview', 'olap', 'projects'
  const [olapReportData, setOlapReportData] = useState(null);

  // Enhanced tech card context for menu dishes
  const [dishContext, setDishContext] = useState(null);

  // IIKo Integration states - NEW!
  const [showIikoModal, setShowIikoModal] = useState(false);
  const [iikoOrganizations, setIikoOrganizations] = useState([]);
  const [selectedOrganization, setSelectedOrganization] = useState(null);
  const [iikoMenu, setIikoMenu] = useState(null);
  const [isLoadingIiko, setIsLoadingIiko] = useState(false);
  const [iikoHealthStatus, setIikoHealthStatus] = useState(null);
  const [showUploadTechCardModal, setShowUploadTechCardModal] = useState(false);
  const [techCardToUpload, setTechCardToUpload] = useState(null);
  const [isUploadingTechCard, setIsUploadingTechCard] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [showSyncMenuModal, setShowSyncMenuModal] = useState(false);
  const [syncSettings, setSyncSettings] = useState({
    syncPrices: true,
    syncCategories: true
  });
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncProgress, setSyncProgress] = useState(null);
  // NEW - Category viewer states
  const [showCategoryViewer, setShowCategoryViewer] = useState(false);
  const [categoryData, setCategoryData] = useState(null);
  const [isLoadingCategory, setIsLoadingCategory] = useState(false);
  // NEW - Category management states
  const [iikoCategories, setIikoCategories] = useState([]);
  const [isLoadingCategories, setIsLoadingCategories] = useState(false);
  const [isCreatingCategory, setIsCreatingCategory] = useState(false);
  const [categoryCreationResult, setCategoryCreationResult] = useState(null);
  const [showAllCategoriesModal, setShowAllCategoriesModal] = useState(false);

  // NEW - Assembly Charts (Tech Cards) Management states
  const [showAssemblyChartsModal, setShowAssemblyChartsModal] = useState(false);
  const [assemblyCharts, setAssemblyCharts] = useState([]);
  const [isLoadingAssemblyCharts, setIsLoadingAssemblyCharts] = useState(false);
  const [showCreateAssemblyChartModal, setShowCreateAssemblyChartModal] = useState(false);
  const [isCreatingAssemblyChart, setIsCreatingAssemblyChart] = useState(false);
  const [assemblyChartData, setAssemblyChartData] = useState({
    name: '',
    description: '',
    ingredients: [],
    preparation_steps: []
  });
  const [syncStatus, setSyncStatus] = useState(null);
  const [showSyncStatusModal, setShowSyncStatusModal] = useState(false);

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

  // IK-04/02: XLSX Import states
  const [showXlsxImportModal, setShowXlsxImportModal] = useState(false);
  const [xlsxFile, setXlsxFile] = useState(null);
  const [xlsxPreview, setXlsxPreview] = useState(null);
  const [xlsxImportProgress, setXlsxImportProgress] = useState(false);
  const [xlsxImportResults, setXlsxImportResults] = useState(null);
  const [xlsxAutoMapping, setXlsxAutoMapping] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  // GX-02: Quality Validation states
  const [qualityScore, setQualityScore] = useState(null);
  const [qualityBanners, setQualityBanners] = useState([]);
  const [isValidatingQuality, setIsValidatingQuality] = useState(false);
  const [autoNormalize, setAutoNormalize] = useState(true); // Auto-normalize ranges

  // UX-Polish: Enhanced XLSX Import states
  const [xlsxImportStage, setXlsxImportStage] = useState('idle'); // idle, parsing, validation, conversions, extraction, done
  const [xlsxImportErrors, setXlsxImportErrors] = useState([]);
  const [xlsxImportWarnings, setXlsxImportWarnings] = useState([]);
  
  // UX-Polish: Auto-mapping enhancement states  
  const [mappingActionLog, setMappingActionLog] = useState([]);
  const [lastMappingAction, setLastMappingAction] = useState(null);

  // HACCP Pro states
  const [haccpProEnabled, setHaccpProEnabled] = useState(false);
  const [currentTechCardHaccp, setCurrentTechCardHaccp] = useState(null);
  const [showHaccpAuditModal, setShowHaccpAuditModal] = useState(false);
  const [haccpAuditResult, setHaccpAuditResult] = useState(null);
  const [isHaccpAuditing, setIsHaccpAuditing] = useState(false);
  const [isAutoGeneratingHaccp, setIsAutoGeneratingHaccp] = useState(false);

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
      title: "🏪 Мое заведение",
      text: "Настройте информацию о заведении для более точных техкарт - тип кухни, средний чек, целевая аудитория",
      icon: "⚙️"
    },
    {
      title: "📋 Экспорт в PDF",
      text: "Все техкарты можно экспортировать в PDF без цен - идеально для передачи персоналу",
      icon: "📄"
    },
    {
      title: "🔍 Поиск по истории",
      text: "Используйте раздел 'ТЕХКАРТЫ' чтобы быстро найти нужные техкарты",
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
      title: "🚀 PRO-функции Receptor",
      text: "Используйте 'Финансы' для анализа себестоимости, 'Скрипт продаж' для обучения официантов",
      icon: "💼"
    },
    {
      title: "🔄 Замена блюд",
      text: "Кнопка 'Заменить блюдо' в меню создает альтернативный вариант - тестируйте разные концепции!",
      icon: "🔀"
    },
    {
      title: "📤 IIKo интеграция",
      text: "Загружайте готовые техкарты прямо в POS-систему одним кликом через кнопку 'IIKo'",
      icon: "🏢"
    },
    {
      title: "🧪 Лаборатория блюд",
      text: "Функция 'Лаборатория' создает экспериментальные сочетания + визуализацию блюда с помощью ИИ",
      icon: "⚗️"
    },
    {
      title: "📸 Фото-маркетинг",
      text: "Используйте 'Советы по фото' для создания инстаграм-контента - правильные фото увеличивают заказы",
      icon: "📷"
    },
    {
      title: "🌟 Вдохновение шефов",
      text: "Функция 'Вдохновение' адаптирует рецепты мировых шеф-поваров под ваш стиль и бюджет",
      icon: "✨"
    },
    {
      title: "💬 Продажи через персонал",
      text: "Генерируйте скрипты продаж для каждого блюда - обученные официанты продают на 40% больше",
      icon: "🎤"
    },
    {
      title: "📊 Аналитика затрат",
      text: "Каждая техкарта содержит точный расчет себестоимости по регионам - отслеживайте прибыльность",
      icon: "📈"
    },
    {
      title: "🏗️ Проекты меню",
      text: "Создавайте отдельные проекты для разных концепций - летнее меню, банкеты, детское питание",
      icon: "📁"
    },
    {
      title: "⚡ Быстрые техкарты",
      text: "Для отдельных блюд используйте главную страницу - одна техкарта создается за 30 секунд",
      icon: "🏃‍♂️"
    },
    {
      title: "🎭 Персонализация под заведение",
      text: "Заполните профиль заведения один раз - все рецепты будут адаптированы под ваш формат и аудиторию",
      icon: "🏪"
    },
    {
      title: "💾 История и экспорт",
      text: "Все созданные меню и техкарты сохраняются в истории - экспортируйте в PDF или Excel",
      icon: "💿"
    }
  ];

  // Tips for V1 to V2 conversion
  const [currentConversionTipIndex, setCurrentConversionTipIndex] = useState(0);
  const conversionTips = [
    {
      title: "🎯 Магия автомаппинга",
      text: "При конвертации V1→V2 система автоматически подберет артикулы из вашего IIKO каталога - экономия часов работы!",
      icon: "🔗"
    },
    {
      title: "💰 Точная себестоимость",
      text: "V2 техкарта содержит реальные цены ингредиентов из прайс-листов - видите прибыльность каждого блюда",
      icon: "💎"
    },
    {
      title: "📊 Готово к IIKO",
      text: "После конвертации техкарту можно загрузить в IIKO одной кнопкой - никакого ручного ввода!",
      icon: "🚀"
    },
    {
      title: "🔄 Всегда можно вернуться",
      text: "V1 рецепты сохраняются в истории - экспериментируйте с разными вариантами и выбирайте лучший",
      icon: "💾"
    },
    {
      title: "⚡ Прокачка рецептов",
      text: "Используйте AI-функции для V1 рецепта ПЕРЕД конвертацией: улучшите блюдо, добавьте твист, подберите напитки",
      icon: "✨"
    },
    {
      title: "🎨 Креатив → Структура",
      text: "V1 - для творчества и экспериментов, V2 - для точных расчетов и работы. Лучшее из двух миров!",
      icon: "🌟"
    },
    {
      title: "📝 Сохраняйте результаты AI",
      text: "Результаты AI-функций (Вдохновение, Прокачка) можно сохранить как новые V1 рецепты и тоже конвертировать",
      icon: "💡"
    },
    {
      title: "🏢 Профиль заведения",
      text: "Заполните профиль один раз - все V2 техкарты будут адаптированы под ваш тип заведения и регион",
      icon: "🏪"
    }
  ];


  // Additional tips array
  const additionalTips = [
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

  // Simple tech card generation states
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStatus, setGenerationStatus] = useState(null);
  const [generationError, setGenerationError] = useState(null);
  const [generationIssues, setGenerationIssues] = useState([]);

  // Login states
  const [showLogin, setShowLogin] = useState(false);
  const [loginEmail, setLoginEmail] = useState('');

  // Registration form state
  const [registrationData, setRegistrationData] = useState({
    email: '',
    name: '',
    city: '',
    password: ''
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

  // Load venue profile for smart tech card generation
  const loadVenueProfile = async () => {
    try {
      const userId = currentUser?.id || 'demo_user';
      const response = await axios.get(`${API}/venue-profile/${userId}`);
      if (response.data) {
        setVenueProfile(response.data);
        console.log('📍 Venue profile loaded:', response.data);
      }
    } catch (error) {
      console.log('ℹ️ No venue profile found, using defaults');
      // Set empty profile - form will work without it
      setVenueProfile({});
    }
  };

  // Load iiko RMS status on component mount (IK-02B-FE/01)
  useEffect(() => {
    checkIikoRmsStatus();
  }, []);
  
  // 🚀 CRITICAL FIX: Load venue profile when currentUser is available
  useEffect(() => {
    if (currentUser?.id) {
      loadVenueProfile();
    }
  }, [currentUser?.id]);
  
  // 🚀 CRITICAL FIX: Auto-restore IIKO connection after currentUser is loaded
  useEffect(() => {
    if (!currentUser || !currentUser.id) {
      console.log('⏳ Waiting for currentUser to load before auto-restore...');
      return;
    }
    
    const tryAutoConnect = async () => {
      try {
        console.log('🔄 Проверяем сохраненные учетные данные на бэкенде для пользователя:', currentUser.id);
        
        // CRITICAL FIX: Use actual currentUser.id, not demo_user
        const response = await axios.post(`${API}/v1/iiko/rms/restore-connection`, null, {
          params: { user_id: currentUser.id }
        });
        
        if (response.data.status === 'connected' || response.data.status === 'restored') {
          console.log('✅ Автоматическое подключение к iiko успешно через бэкенд');
          
          // CRITICAL FIX: Update full connection state
          setIikoRmsConnection({
            status: 'connected',
            host: response.data.host || '',
            login: response.data.login || '',
            organization_id: response.data.organization_id || 'default',
            organization_name: response.data.organization_name || '',
            last_connection: response.data.last_connection || new Date().toISOString(),
            sync_status: response.data.sync_status || 'never_synced',
            products_count: response.data.products_count || 0,
            last_sync: response.data.last_sync || null,
            error_message: ''
          });
          
          // Update credentials for UI
          setIikoRmsCredentials({
            host: response.data.host || '',
            login: response.data.login || '',
            password: '' // Don't store password in UI
          });
          
          // Обновляем статус подключения и синхронизации
          await checkIikoRmsStatus();
          
          console.log('✅ IIKO RMS автоматически восстановлено. Синхронизировано товаров:', response.data.products_count || 0);
        } else if (response.data.status === 'no_stored_credentials') {
          console.log('ℹ️ Нет сохраненных учетных данных на бэкенде');
        } else if (response.data.status === 'manually_disconnected') {
          console.log('ℹ️ Подключение было отключено вручную');
        } else {
          console.log('⚠️ Не удалось восстановить подключение:', response.data.status);
        }
      } catch (error) {
        console.error('❌ Ошибка автоподключения через бэкенд:', error);
      }
    };
    
    tryAutoConnect();
  }, [currentUser]); // CRITICAL FIX: Run when currentUser loads

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
        "🧠 Изучаю целевую аудиторию и региональные предпочтения...",
        "🌍 Исследую актуальные тренды мировой гастрономии...",
        "💰 Анализирую бюджет и ценовую стратегию...",
        "⚖️ Балансирую вкусы и категории блюд...",
        "🔥 Подбираю оптимальные техники приготовления...",
        "👨‍🍳 Адаптирую рецепты под навыки команды...",
        "📊 Рассчитываю маржинальность каждого блюда...",
        "🎨 Создаю гармоничную структуру меню...",
        "💡 Оптимизирую закупки и общие ингредиенты...",
        "🏷️ Придумываю продающие названия и описания...",
        "⏱️ Настраиваю время приготовления под пики нагрузки...",
        "🌱 Добавляю сезонные и локальные ингредиенты...",
        "🏆 Создаю signature блюда для узнаваемости заведения...",
        "📸 Продумываю визуальную подачу для соцсетей...",
        "💎 Полирую финальные детали меню...",
        "🎉 Упаковываю готовое меню с любовью...",
        "✨ Меню готово к покорению сердец гостей!"
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
      ],
      conversion: [
        "🔄 Анализирую структуру рецепта V1...",
        "📊 Извлекаю ингредиенты и пропорции...",
        "🔗 Подбираю артикулы из IIKO каталога...",
        "💰 Рассчитываю точную себестоимость...",
        "📝 Форматирую в профессиональную техкарту...",
        "✅ Проверяю соответствие стандартам V2...",
        "🎯 Оптимизирую для загрузки в IIKO...",
        "✨ Техкарта V2 готова!"
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

  // Convert TechCardV2 JSON to display text format
  const convertV2ToDisplayText = (tcV2) => {
    if (!tcV2) return '';
    
    const meta = tcV2.meta || {};
    const title = meta.title || 'Техкарта';
    const yield_data = tcV2.yield || tcV2.yield_ || {}; // Fix: Support both yield and yield_ formats
    const ingredients = tcV2.ingredients || [];
    const process = tcV2.process || [];
    const storage = tcV2.storage || {};
    const nutrition = tcV2.nutrition || {};
    const cost = tcV2.cost || {};
    
    let text = `**Название:** ${title}\n\n`;
    
    // Basic info
    text += `**Выход:** ${yield_data.perBatch_g || 0}г (${tcV2.portions || 1} порций по ${yield_data.perPortion_g || 0}г)\n\n`;
    
    // Ingredients table
    if (ingredients.length > 0) {
      text += `**Ингредиенты:**\n\n`;
      ingredients.forEach(ing => {
        text += `- ${ing.name} — ${ing.netto_g}${ing.unit} (брутто: ${ing.brutto_g}${ing.unit}, потери: ${ing.loss_pct}%)\n`;
      });
      text += '\n';
    }
    
    // Process steps
    if (process.length > 0) {
      text += `**Пошаговый рецепт:**\n\n`;
      process.forEach((step, index) => {
        text += `${step.n || index + 1}. ${step.action}`;
        if (step.time_min) text += ` (${step.time_min} мин)`;
        if (step.temp_c) text += ` при ${step.temp_c}°C`;
        text += '\n';
      });
      text += '\n';
    }
    
    // Storage
    if (storage.conditions) {
      text += `**Заготовки и хранение:** ${storage.conditions}\n`;
      if (storage.shelfLife_hours) text += `Срок хранения: ${storage.shelfLife_hours} часов\n`;
      if (storage.servingTemp_c) text += `Температура подачи: ${storage.servingTemp_c}°C\n`;
      text += '\n';
    }
    
    // Nutrition
    if (nutrition.per100g) {
      const per100g = nutrition.per100g;
      text += `**КБЖУ на 100 г:** ${per100g.kcal || 0} ккал, Б: ${per100g.proteins_g || 0}г, Ж: ${per100g.fats_g || 0}г, У: ${per100g.carbs_g || 0}г\n`;
    }
    if (nutrition.perPortion) {
      const perPortion = nutrition.perPortion;
      text += `**КБЖУ на 1 порцию:** ${perPortion.kcal || 0} ккал, Б: ${perPortion.proteins_g || 0}г, Ж: ${perPortion.fats_g || 0}г, У: ${perPortion.carbs_g || 0}г\n`;
    }
    text += '\n';
    
    // Cost
    if (cost.rawCost) {
      text += `**💸 Себестоимость:** ${cost.rawCost}₽ (на порцию: ${cost.costPerPortion}₽)\n`;
      if (cost.markup_pct) text += `Наценка: ${cost.markup_pct}% \n`;
      text += '\n';
    }
    
    return text;
  };

  // Render TechCardV2 directly from JSON data
  const renderTechCardV2 = (tcV2) => {
    // DEBUG: Only log in debug mode
    if (isDebugMode) {
      console.log('renderTechCardV2 called with:', tcV2 ? 'tcV2 data present' : 'tcV2 is null/undefined');
    }
    if (!tcV2) return null;

    // Специальная обработка для конвертированных V1→V2 техкарт
    if (tcV2.converted_from_v1 && tcV2.content) {
      return (
        <div className="space-y-6">
          {/* Заголовок с метками */}
          <div className="text-center mb-6">
            <h1 className="text-3xl font-semibold text-gray-200 mb-3">
              {tcV2.meta?.title || 'Техкарта'}
            </h1>
            <div className="flex justify-center gap-2 mb-4">
              <span className="bg-purple-600 text-white px-3 py-1 rounded-full text-sm">V2 Техкарта</span>
              <span className="bg-gray-600 text-white px-3 py-1 rounded-full text-sm">Из рецепта</span>
              <span className="bg-purple-500 text-white px-3 py-1 rounded-full text-sm">ГОТОВО</span>
            </div>
          </div>

          {/* Контент */}
          <div className="bg-gray-800/50 border border-gray-600/30 rounded-xl p-6">
            <div className="whitespace-pre-wrap text-gray-200 leading-relaxed">
              {tcV2.content}
            </div>
          </div>
        </div>
      );
    }

    const meta = tcV2.meta || {};
    const yield_data = tcV2.yield || tcV2.yield_ || {}; // Fix: Support both yield and yield_ formats
    const ingredients = tcV2.ingredients || {};
    const process = tcV2.process || [];
    const storage = tcV2.storage || {};
    const nutrition = tcV2.nutrition || {};
    const nutritionMeta = tcV2.nutritionMeta || {};
    const cost = tcV2.cost || {};
    const costMeta = tcV2.costMeta || {};
    const issues = tcV2.issues || [];

    return (
      <div className="space-y-6">
        {/* НАЗВАНИЕ И СТАТУС */}
        <div className="text-center">
          <div className="flex items-center justify-center gap-4 mb-4">
            <h1 className="text-3xl font-semibold text-gray-200">
              {meta.title || 'Техкарта'}
            </h1>
            <div className="flex gap-2">
              <span className="bg-purple-600 text-white px-3 py-1 rounded-full text-sm font-semibold">
                TechCard v2
              </span>
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${(tcV2.status === 'success' || tcV2.status === 'READY') ? 'bg-purple-500 text-white' : 'bg-gray-600 text-white'}`}>
                {tcV2.status === 'READY' ? 'ГОТОВО' : (tcV2.status || 'draft')}
              </span>
            </div>
          </div>
          {meta.cuisine && (
            <p className="text-gray-400 text-lg">{meta.cuisine}</p>
          )}
        </div>

        {/* GX-01: LLM Unavailable Banner */}
        {issues.some(issue => issue?.type === 'llmUnavailable' || issue?.includes?.('llmUnavailable') || (typeof issue === 'string' && issue.includes('llmUnavailable'))) && (
          <div className="bg-gray-800/50 border border-gray-600/50 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-3">
              <div>
                <div className="font-semibold text-gray-300">Генерация недоступна</div>
                <div className="text-gray-400 text-sm mt-1">
                  Вы можете: (а) маппить артикулы из iiko, (б) отредактировать ингредиенты вручную, (в) экспортировать ТТК
                </div>
              </div>
            </div>
          </div>
        )}

        {/* GX-02: Quality Validation Banners */}
        {qualityBanners && qualityBanners.length > 0 && (
          <div className="space-y-3 mb-6">
            {qualityBanners.map((banner, index) => (
              <div key={index} className="bg-gray-800/50 border border-gray-600/50 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <div className="flex-1">
                    <div className="font-semibold mb-2 text-gray-200">
                      {banner.title}
                    </div>
                    
                    {banner.messages && banner.messages.length > 0 && (
                      <div className="space-y-1 mb-3">
                        {banner.messages.map((message, msgIndex) => (
                          <div key={msgIndex} className="text-sm text-gray-400">
                            {message}
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {banner.action && (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            if (banner.type === 'error') {
                              validateTechCardQuality();
                            } else {
                              normalizeTechCardRanges();
                            }
                          }}
                          disabled={isValidatingQuality}
                          className={`px-3 py-1 rounded text-xs font-semibold transition-colors ${
                            'bg-purple-600 hover:bg-purple-700 text-white'
                          } ${isValidatingQuality ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                          {isValidatingQuality ? 'Обработка...' : banner.action}
                        </button>
                        
                        {/* Quality Score Display */}
                        {qualityScore && (
                          <div className="ml-auto">
                            <div className={`text-xs px-2 py-1 rounded-full font-semibold ${
                              qualityScore.level === 'excellent' 
                                ? 'bg-purple-600 text-white'
                                : qualityScore.level === 'good'
                                ? 'bg-purple-500 text-white'
                                : qualityScore.level === 'needs_improvement'
                                ? 'bg-gray-600 text-white'
                                : 'bg-gray-700 text-white'
                            }`}>
                              Качество: {qualityScore.score}%
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ВЫХОД И ПОРЦИИ */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-800/30 rounded-lg p-4 text-center border border-gray-700">
            <h4 className="text-gray-300 font-semibold mb-2">ПОРЦИЙ</h4>
            <p className="text-gray-200 text-xl">{tcV2.portions || 1}</p>
          </div>
          <div className="bg-gray-800/30 rounded-lg p-4 text-center border border-gray-700">
            <h4 className="text-gray-300 font-semibold mb-2">НА ПОРЦИЮ</h4>
            <p className="text-gray-200 text-xl">{yield_data.perPortion_g || 0}г</p>
          </div>
          <div className="bg-gray-800/30 rounded-lg p-4 text-center border border-gray-700">
            <h4 className="text-gray-300 font-semibold mb-2">ОБЩИЙ ВЫХОД</h4>
            <p className="text-gray-200 text-xl">{yield_data.perBatch_g || 0}г</p>
          </div>
        </div>

        {/* Coverage indicators */}
        <div className="flex flex-wrap gap-2 mb-4">
          {/* Price coverage chip - only show if costMeta exists and has coverage data */}
          {costMeta && typeof costMeta.coveragePct === 'number' && (
            <div 
              className={`px-3 py-1 rounded-full text-sm font-semibold cursor-help ${
                (costMeta.coveragePct >= 90) ? 'bg-purple-600 text-white' :
                (costMeta.coveragePct >= 70) ? 'bg-purple-500 text-white' :
                'bg-gray-600 text-white'
              }`}
              title={
                costMeta.source === 'mixed' 
                  ? `Источники: смешанные (цены из разных каталогов). Обновлено: ${costMeta.asOf || 'не указано'}`
                  : `Источник: ${costMeta.source === 'user' ? 'Загруженные пользователем' : 
                                costMeta.source === 'catalog' ? 'Каталог разработчика' : 
                                costMeta.source === 'bootstrap' ? 'Демо каталог' : 
                                costMeta.source}. Обновлено: ${costMeta.asOf || 'не указано'}`
              }
            >
              Цены {costMeta.coveragePct}% • {
                costMeta.source === 'user' ? 'User' :
                costMeta.source === 'catalog' ? 'Catalog' :
                costMeta.source === 'bootstrap' ? 'Bootstrap' :
                costMeta.source === 'mixed' ? 'Mixed' :
                costMeta.source || 'Unknown'
              }
            </div>
          )}
          
          {/* Nutrition coverage chip - only show if nutritionMeta exists and has coverage data */}
          {nutritionMeta && typeof nutritionMeta.coveragePct === 'number' && (
            <div 
              className={`px-3 py-1 rounded-full text-sm font-semibold cursor-help ${
                (nutritionMeta.coveragePct >= 90) ? 'bg-purple-600 text-white' :
                (nutritionMeta.coveragePct >= 70) ? 'bg-purple-500 text-white' :
                'bg-gray-600 text-white'
              }`}
              title={
                nutritionMeta.source === 'Mixed' 
                  ? `Источники: ${nutritionMeta.breakdown || 'USDA + каталоги'}. Обновлено: ${nutritionMeta.asOf || 'не указано'}`
                  : `Источник: ${nutritionMeta.source === 'usda' ? 'USDA FoodData Central' : 
                                nutritionMeta.source === 'catalog' ? 'Каталог разработчика' : 
                                nutritionMeta.source === 'bootstrap' ? 'Демо каталог' : 
                                nutritionMeta.source}. Обновлено: ${nutritionMeta.asOf || 'не указано'}`
              }
            >
              БЖУ {nutritionMeta.coveragePct}% • {
                nutritionMeta.source === 'usda' ? 'USDA' :
                nutritionMeta.source === 'catalog' ? 'CAT' :
                nutritionMeta.source === 'bootstrap' ? 'BOOT' :
                nutritionMeta.source === 'Mixed' ? 'Mixed' :
                nutritionMeta.source || 'Unknown'
              }
            </div>
          )}
          {isRecalculating && (
            <div className="px-3 py-1 bg-purple-600 text-white rounded-full text-sm font-semibold animate-pulse">
              Пересчет...
            </div>
          )}
        </div>

        {/* Stale price warning banner */}
        {tcV2 && tcV2.issues && tcV2.issues.some(issue => issue.type === 'stalePrice') && (
          <div className="bg-gray-800/50 border border-gray-600/50 rounded-lg p-3 mb-4">
            <div className="text-gray-300 text-sm font-semibold mb-1">Предупреждение о ценах:</div>
            <div className="text-gray-400 text-sm">
              Часть прайс-листа устарела (данные старше 30 дней). Рекомендуется обновить цены.
              {tcV2.costMeta && tcV2.costMeta.asOf && (
                <span className="ml-1">Последнее обновление: {tcV2.costMeta.asOf}</span>
              )}
            </div>
          </div>
        )}

        {/* Recalc error banner */}
        {recalcError && (
          <div className="bg-gray-800/50 border border-gray-600/50 rounded-lg p-3 mb-4">
            <div className="text-gray-300 text-sm">
              {recalcError}
            </div>
          </div>
        )}

        {/* Anchor validity issues banner */}
        {issues && issues.length > 0 && (
          <div className="mb-4">
            {issues.some(issue => typeof issue === 'string' && (issue.includes('Отсутствуют обязательные') || issue.includes('Обнаружены запрещённые'))) && (
              <div className="bg-gray-800/50 border border-gray-600/50 rounded-lg p-3 mb-2">
                <div className="text-gray-300 text-sm font-semibold mb-1">Нарушения анкерной валидности:</div>
                {issues.filter(issue => typeof issue === 'string' && (issue.includes('Отсутствуют обязательные') || issue.includes('Обнаружены запрещённые'))).map((issue, idx) => (
                  <div key={idx} className="text-gray-400 text-sm">• {issue}</div>
                ))}
              </div>
            )}
            {issues.some(issue => typeof issue === 'string' && issue.includes('Несоответствие белка')) && (
              <div className="bg-gray-800/50 border border-gray-600/50 rounded-lg p-3 mb-2">
                <div className="text-gray-300 text-sm font-semibold mb-1">Предупреждения:</div>
                {issues.filter(issue => typeof issue === 'string' && issue.includes('Несоответствие белка')).map((issue, idx) => (
                  <div key={idx} className="text-gray-400 text-sm">• {issue}</div>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* ИНГРЕДИЕНТЫ ТАБЛИЦА */}
        {ingredients.length > 0 && (
          <div className="bg-gray-800/30 rounded-lg p-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-200 uppercase tracking-wide">ИНГРЕДИЕНТЫ</h3>
              {editingIngredientIndex !== null ? (
                <div className="flex gap-2">
                  <button
                    onClick={saveIngredientEdit}
                    className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-sm transition-colors"
                    disabled={Object.keys(editingErrors).length > 0}
                  >
                    Сохранить изменения
                  </button>
                  <button
                    onClick={cancelIngredientEdit}
                    className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm transition-colors"
                  >
                    Отмена
                  </button>
                </div>
              ) : (
                <button
                  onClick={saveTechCardToHistory}
                  disabled={isRecalculating}
                  className={`px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-colors ${isRecalculating ? 'opacity-50 cursor-not-allowed' : ''}`}
                  title="Пересчитать и сохранить техкарту в базу данных"
                >
                  {isRecalculating ? 'Сохранение...' : 'СОХРАНИТЬ ТЕХКАРТУ'}
                </button>
              )}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-2 text-gray-300 font-semibold">Ингредиент</th>
                    <th className="text-center py-2 text-gray-300 font-semibold">Брутто</th>
                    <th className="text-center py-2 text-gray-300 font-semibold">Потери %</th>
                    <th className="text-center py-2 text-gray-300 font-semibold">Нетто</th>
                    <th className="text-center py-2 text-gray-300 font-semibold">Ед.изм</th>
                    <th className="text-center py-2 text-gray-300 font-semibold">Артикул (iiko)</th>
                    <th className="text-center py-2 text-gray-300 font-semibold">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {ingredients.map((ing, index) => {
                    const isEditing = editingIngredientIndex === index;
                    const hasSubRecipeIssue = generationIssues.some(issue => 
                      issue.type === 'subRecipeNotReady' && issue.name === ing.name
                    );
                    
                    return (
                      <tr key={index} className={`border-b border-gray-800 ${isEditing ? 'bg-purple-900/20' : ''}`}>
                        <td className="py-2 text-gray-300">
                          <div className="flex items-center gap-2">
                            <div>
                              <div className="flex items-center gap-1">
                                {isEditing ? (
                                  <input
                                    type="text"
                                    value={editingData.name || ''}
                                    onChange={(e) => handleEditingChange('name', e.target.value)}
                                    onKeyDown={handleEditKeyDown}
                                    className="w-48 px-2 py-1 bg-gray-700 text-white rounded text-sm border-gray-600"
                                    placeholder="Название ингредиента"
                                  />
                                ) : (
                                  <span 
                                    className="cursor-pointer hover:bg-gray-700 px-2 py-1 rounded"
                                    onClick={() => startIngredientEdit(index)}
                                  >
                                    {ing.name}
                                  </span>
                                )}
                                {/* Source badges для ингредиентов */}
                                <div className="flex items-center gap-1 flex-wrap">
                                  {/* Nutrition source badges */}
                                  {ing.canonical_id && (
                                    <>
                                      {/* USDA badge - показываем если источник общий USDA или mixed */}
                                      {(nutritionMeta.source === 'usda' || nutritionMeta.source === 'Mixed') && (
                                        <span className="text-xs bg-purple-600/20 text-purple-300 px-1 py-0.5 rounded border border-purple-500/30" title="БЖУ: USDA FoodData Central">USDA</span>
                                      )}
                                      {/* CAT badge - показываем если источник каталог или mixed */}
                                      {(nutritionMeta.source === 'catalog' || (nutritionMeta.source === 'Mixed' && !nutritionMeta.source.includes('usda'))) && (
                                        <span className="text-xs bg-purple-600/20 text-purple-300 px-1 py-0.5 rounded border border-purple-500/30" title="БЖУ: Каталог разработчика">CAT</span>
                                      )}
                                      {/* BOOT badge - показываем если источник bootstrap */}
                                      {nutritionMeta.source === 'bootstrap' && (
                                        <span className="text-xs bg-gray-600/20 text-gray-300 px-1 py-0.5 rounded border border-gray-500/30" title="БЖУ: Демо каталог">BOOT</span>
                                      )}
                                    </>
                                  )}
                                  
                                  {/* Price source badges */}
                                  {ing.skuId && (
                                    <>
                                      {costMeta.source === 'user' && (
                                        <span className="text-xs bg-purple-600/20 text-purple-300 px-1 py-0.5 rounded border border-purple-500/30" title="Цена: Загруженные пользователем">USER</span>
                                      )}
                                      {costMeta.source === 'catalog' && (
                                        <span className="text-xs bg-purple-600/20 text-purple-300 px-1 py-0.5 rounded border border-purple-500/30" title="Цена: Каталог разработчика">CAT</span>
                                      )}
                                      {costMeta.source === 'bootstrap' && (
                                        <span className="text-xs bg-gray-600/20 text-gray-300 px-1 py-0.5 rounded border border-gray-500/30" title="Цена: Демо каталог">BOOT</span>
                                      )}
                                      {costMeta.source === 'mixed' && (
                                        <span className="text-xs bg-gray-600/20 text-gray-300 px-1 py-0.5 rounded border border-gray-500/30" title="Цена: Смешанные источники">Mixed</span>
                                      )}
                                    </>
                                  )}
                                  
                                  {/* CLEANUP TECH CARD DATA & UI: Убираем все warning'и из интерфейса */}
                                </div>
                              </div>
                              {ing.subRecipe && (
                                <div className="text-xs text-gray-400 mt-1">
                                  см. ТК "{ing.subRecipe.title}"
                                  <button
                                    onClick={() => window.open(`${API}/v1/techcards.v2/print?id=${ing.subRecipe.id}`, '_blank')}
                                    className="ml-2 text-purple-400 hover:text-purple-300 underline"
                                  >
                                    Открыть ГОСТ-печать
                                  </button>
                                </div>
                              )}
                              {hasSubRecipeIssue && (
                                <div className="bg-gray-800/30 border-l-2 border-gray-600 px-2 py-1 mt-1 text-xs text-gray-400">
                                  Подрецепт не готов (нет cost/БЖУ)
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                        
                        {/* Brutto column */}
                        <td className="text-center py-2">
                          {isEditing ? (
                            <div>
                              <input
                                type="number"
                                step="0.1"
                                value={editingData.brutto_g || ''}
                                onChange={(e) => handleEditingChange('brutto_g', e.target.value)}
                                onKeyDown={handleEditKeyDown}
                                className={`w-16 px-1 py-1 bg-gray-700 text-white rounded text-center text-sm ${
                                  editingErrors.brutto_g ? 'border-red-500' : 'border-gray-600'
                                }`}
                                autoFocus
                              />
                              {/* CLEANUP TECH CARD DATA & UI: Убираем validation errors */}
                            </div>
                          ) : (
                            <span 
                              className="text-gray-300 cursor-pointer hover:bg-gray-700 px-2 py-1 rounded"
                              onClick={() => startIngredientEdit(index)}
                            >
                              {ing.brutto_g}
                            </span>
                          )}
                        </td>
                        
                        {/* Loss % column */}
                        <td className="text-center py-2">
                          {isEditing ? (
                            <div>
                              <input
                                type="number"
                                step="0.1"
                                value={editingData.loss_pct || ''}
                                onChange={(e) => handleEditingChange('loss_pct', e.target.value)}
                                onKeyDown={handleEditKeyDown}
                                className={`w-16 px-1 py-1 bg-gray-700 text-white rounded text-center text-sm ${
                                  editingErrors.loss_pct ? 'border-red-500' : 'border-gray-600'
                                }`}
                              />
                              {/* CLEANUP TECH CARD DATA & UI: Убираем validation errors */}
                            </div>
                          ) : (
                            <span 
                              className="text-gray-300 cursor-pointer hover:bg-gray-700 px-2 py-1 rounded"
                              onClick={() => startIngredientEdit(index)}
                            >
                              {ing.loss_pct}
                            </span>
                          )}
                        </td>
                        
                        {/* Netto column */}
                        <td className="text-center py-2">
                          {isEditing ? (
                            <div>
                              <input
                                type="number"
                                step="0.1"
                                value={editingData.netto_g || ''}
                                onChange={(e) => handleEditingChange('netto_g', e.target.value)}
                                onKeyDown={handleEditKeyDown}
                                className={`w-16 px-1 py-1 bg-gray-700 text-white rounded text-center text-sm font-bold ${
                                  editingErrors.netto_g ? 'border-red-500' : 'border-gray-600'
                                }`}
                              />
                              {/* CLEANUP TECH CARD DATA & UI: Убираем validation errors */}
                            </div>
                          ) : (
                            <span 
                              className="text-gray-300 font-bold cursor-pointer hover:bg-gray-700 px-2 py-1 rounded"
                              onClick={() => startIngredientEdit(index)}
                            >
                              {ing.netto_g}
                            </span>
                          )}
                        </td>
                        
                        {/* Unit column */}
                        <td className="text-center py-2">
                          {isEditing ? (
                            <select
                              value={editingData.unit || 'g'}
                              onChange={(e) => handleEditingChange('unit', e.target.value)}
                              onKeyDown={handleEditKeyDown}
                              className="w-16 px-1 py-1 bg-gray-700 text-white rounded text-center text-sm border-gray-600"
                            >
                              <option value="g">г</option>
                              <option value="ml">мл</option>
                              <option value="pcs">шт</option>
                            </select>
                          ) : (
                            <span 
                              className="text-gray-400 cursor-pointer hover:bg-gray-700 px-2 py-1 rounded"
                              onClick={() => startIngredientEdit(index)}
                            >
                              {ing.unit}
                            </span>
                          )}
                        </td>
                        
                        <td className="text-center py-2 text-gray-400 text-xs">
                          {/* B. Terminology & UI: показываем Артикул (iiko) вместо GUID */}
                          {ing.product_code ? (
                            <span className="bg-purple-600/20 text-purple-300 px-2 py-1 rounded text-xs font-mono border border-purple-500/30">
                              Артикул: {ing.product_code}
                            </span>
                          ) : ing.skuId ? (
                            <span className="bg-gray-600/20 text-gray-400 px-2 py-1 rounded text-xs border border-gray-500/30" title={`GUID: ${ing.skuId}`}>
                              GUID
                            </span>
                          ) : '-'}
                        </td>
                        <td className="text-center py-2">
                          <div className="flex justify-center gap-2">
                            {/* Улучшенная кнопка сопоставления с IIKO */}
                            <button
                              className="bg-purple-600/20 border border-purple-500/50 text-purple-300 hover:bg-purple-600 hover:text-white px-3 py-1 rounded-lg text-sm font-medium transition-colors flex items-center gap-1"
                              onClick={() => handleOpenIngredientMapping(index)}
                              title="Связать с товаром из IIKO системы"
                            >
                              IIKO
                            </button>
                            {/* Кнопка "Добавить подрецепт" временно скрыта */}
                            {false && (
                              <button
                                className="text-gray-400 hover:text-blue-300 transition-colors p-1"
                                onClick={() => openSubRecipeModal(index)}
                                title="Назначить подрецепт"
                              >
                                ➕
                              </button>
                            )}
                            {ing.subRecipe && (
                              <button
                                className="text-gray-400 hover:text-gray-300 hover:bg-gray-700/50 transition-colors p-1 rounded"
                                onClick={() => removeSubRecipe(index)}
                                title="Убрать подрецепт"
                              >
                                ×
                              </button>
                            )}
                            {/* Кнопка удаления ингредиента */}
                            <button
                              className="text-gray-400 hover:text-gray-300 hover:bg-gray-700/50 transition-colors p-1 rounded"
                              onClick={() => removeV2Ingredient(index)}
                              title="Удалить ингредиент"
                            >
                              ×
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            
            {/* Кнопка добавления ингредиента */}
            <div className="mt-4 flex justify-center">
              <button
                onClick={addV2Ingredient}
                className="bg-purple-600/20 border border-purple-500/50 text-purple-300 hover:bg-purple-600 hover:text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                Добавить ингредиент
              </button>
            </div>
          </div>
        )}

        {/* ТЕХНОЛОГИЧЕСКИЙ ПРОЦЕСС */}
        {process.length > 0 && (
          <div className="bg-gray-800/30 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-200 mb-4 uppercase tracking-wide">ТЕХНОЛОГИЧЕСКИЙ ПРОЦЕСС</h3>
            <div className="space-y-3">
              {process.map((step, index) => (
                <div key={index} className="bg-gray-700/20 rounded-lg p-3 border-l-4 border-purple-500">
                  <div className="flex items-start gap-3">
                    <span className="bg-purple-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold flex-shrink-0">
                      {step.n || index + 1}
                    </span>
                    <div className="flex-1">
                      <p className="text-gray-300 mb-2">{step.action}</p>
                      <div className="flex flex-wrap gap-4 text-sm">
                        {step.time_min && (
                          <span className="text-gray-400">{step.time_min} мин</span>
                        )}
                        {step.temp_c && (
                          <span className="text-gray-400">{step.temp_c}°C</span>
                        )}
                        {step.equipment && step.equipment.length > 0 && (
                          <span className="text-gray-400">{step.equipment.join(', ')}</span>
                        )}
                        {/* CLEANUP TECH CARD DATA & UI: Убираем CCP warning'и */}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ХРАНЕНИЕ */}
        {storage.conditions && (
          <div className="bg-gray-800/30 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-200 mb-3 uppercase tracking-wide">ХРАНЕНИЕ И ПОДАЧА</h3>
            <div className="text-gray-300 space-y-2">
              <p><strong>Условия хранения:</strong> {storage.conditions}</p>
              {storage.shelfLife_hours && (
                <p><strong>Срок хранения:</strong> {storage.shelfLife_hours} часов</p>
              )}
              {storage.servingTemp_c && (
                <p><strong>Температура подачи:</strong> {storage.servingTemp_c}°C</p>
              )}
            </div>
          </div>
        )}

        {/* ПИЩЕВАЯ ЦЕННОСТЬ */}
        {nutritionMeta.coveragePct > 0 && (nutrition.per100g || nutrition.perPortion) ? (
          <div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {nutrition.per100g && (
                <div className="bg-gray-800/30 rounded-lg p-4 border border-gray-700">
                  <h4 className="text-gray-300 font-semibold mb-3 text-center">КБЖУ на 100г</h4>
                  <div className="grid grid-cols-4 gap-2 text-center text-sm">
                    <div>
                      <div className="text-gray-200 font-semibold">
                        {Math.round(nutrition.per100g.kcal || 0)}
                      </div>
                      <div className="text-gray-400">ккал</div>
                    </div>
                    <div>
                      <div className="text-gray-200 font-semibold">
                        {(nutrition.per100g.proteins_g || 0).toFixed(1)}
                      </div>
                      <div className="text-gray-400">белки</div>
                    </div>
                    <div>
                      <div className="text-gray-200 font-semibold">
                        {(nutrition.per100g.fats_g || 0).toFixed(1)}
                      </div>
                      <div className="text-gray-400">жиры</div>
                    </div>
                    <div>
                      <div className="text-gray-200 font-semibold">
                        {(nutrition.per100g.carbs_g || 0).toFixed(1)}
                      </div>
                      <div className="text-gray-400">углеводы</div>
                    </div>
                  </div>
                </div>
              )}
              {nutrition.perPortion && (
                <div className="bg-gray-800/30 rounded-lg p-4 border border-gray-700">
                  <h4 className="text-gray-300 font-semibold mb-3 text-center">КБЖУ на порцию</h4>
                  <div className="grid grid-cols-4 gap-2 text-center text-sm">
                    <div>
                      <div className="text-gray-200 font-semibold">
                        {Math.round(nutrition.perPortion.kcal || 0)}
                      </div>
                      <div className="text-gray-400">ккал</div>
                    </div>
                    <div>
                      <div className="text-gray-200 font-semibold">
                        {(nutrition.perPortion.proteins_g || 0).toFixed(1)}
                      </div>
                      <div className="text-gray-400">белки</div>
                    </div>
                    <div>
                      <div className="text-gray-200 font-semibold">
                        {(nutrition.perPortion.fats_g || 0).toFixed(1)}
                      </div>
                      <div className="text-gray-400">жиры</div>
                    </div>
                    <div>
                      <div className="text-gray-200 font-semibold">
                        {(nutrition.perPortion.carbs_g || 0).toFixed(1)}
                      </div>
                      <div className="text-gray-400">углеводы</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
            {/* МЕТАДАННЫЕ ПИТАНИЯ */}
            {/* CLEANUP TECH CARD DATA & UI: Убираем предупреждения о покрытии */}
            {nutritionMeta.coveragePct === 100 && (
              <div className="mt-3 text-sm text-gray-400 text-center">
                Полные данные по всем ингредиентам
                {nutritionMeta.source && (
                  <span className="ml-2">• Источник: {nutritionMeta.source}</span>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="bg-gray-800/30 rounded-lg p-6 text-center border border-gray-700">
            <h3 className="text-lg font-semibold text-gray-300 mb-2">ПИЩЕВАЯ ЦЕННОСТЬ</h3>
            <div className="text-gray-400">
              <p>Данные не заполнены</p>
              <p className="text-sm mt-1">
                {nutritionMeta.coveragePct === 0 ? 
                  'Отсутствуют данные по ингредиентам в базе' : 
                  'Расчет не выполнен'
                }
              </p>
            </div>
          </div>
        )}

        {/* СТОИМОСТЬ И МЕТАДАННЫЕ */}
        {tcV2 && (
          <div className="bg-gray-800/30 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-200 uppercase tracking-wide">
                ФИНАНСОВЫЙ АНАЛИЗ
              </h3>
              <button
                onClick={() => {
                  // Пересчёт финансов через backend API
                  if (confirm('Пересчитать финансы техкарты с актуальными ценами?')) {
                    // TODO: Implement financial recalculation
                    alert('Функция пересчёта финансов будет добавлена в следующей версии!');
                  }
                }}
                className="bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 px-3 py-1 rounded-lg text-sm transition-colors border border-purple-500/30"
                title="Пересчитать финансы с актуальными ценами"
              >
                Пересчитать
              </button>
            </div>
            
            {cost.rawCost ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {/* Себестоимость 100г */}
                <div className="text-center bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                  <div className="text-3xl font-semibold text-gray-200 mb-2">
                    {tcV2.yield?.perPortion_g ? Math.round((parseFloat(cost.costPerPortion) * 100) / tcV2.yield.perPortion_g * 10) / 10 : Math.round((parseFloat(cost.costPerPortion) * 100) / 200 * 10) / 10}₽
                  </div>
                  <div className="text-gray-300 font-medium text-sm mb-1">Себестоимость 100г</div>
                  <div className="text-xs text-gray-400">базовый расчет для сравнения</div>
                </div>
                
                {/* Себестоимость порции */}
                <div className="text-center bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                  <div className="text-4xl font-semibold text-gray-200 mb-2">{cost.costPerPortion}₽</div>
                  <div className="text-gray-300 font-medium text-sm mb-1">Себестоимость порции</div>
                  <div className="text-xs text-gray-400">~{Math.round((tcV2.yield?.perPortion_g || 200))}г готового блюда</div>
                </div>
                
                {/* Рекомендуемая цена в меню */}
                <div className="text-center bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                  <div className="text-4xl font-semibold text-gray-200 mb-2">
                    {Math.round(parseFloat(cost.costPerPortion) * 3.5)}₽
                  </div>
                  <div className="text-gray-300 font-medium text-sm mb-1">Рекомендуемая цена</div>
                  <div className="text-xs text-gray-400">наценка 250% • маржа {Math.round((1 - 1/3.5) * 100)}%</div>
                </div>
                
              </div>
            ) : (
              <div className="text-center py-8">
                <h4 className="text-xl font-semibold text-gray-300 mb-3">Себестоимость не рассчитана</h4>
                <p className="text-gray-400 text-sm mb-4">
                  {costMeta.coveragePct === 0 ? 
                    'Цены ингредиентов не найдены в IIKO каталоге. Подключите IIKO или используйте функцию "ФИНАНСЫ" для оценки стоимости.' :
                    'Недостаточно данных для расчета стоимости'
                  }
                </p>
                <div className="flex justify-center gap-3">
                  <button
                    onClick={analyzeFinances}
                    disabled={isAnalyzingFinances}
                    className={`${isAnalyzingFinances ? 'bg-gray-600 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'} text-white font-semibold py-2 px-6 rounded-lg transition-colors text-sm`}
                  >
                    {isAnalyzingFinances ? 'АНАЛИЗИРУЮ...' : 'ОЦЕНИТЬ ФИНАНСЫ'}
                  </button>
                </div>
              </div>
            )}
            
            {/* Дополнительная информация */}
            <div className="mt-4 pt-4 border-t border-gray-700">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                
                {/* Покрытие цен */}
                {costMeta.coveragePct && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Покрытие цен:</span>
                    <span className={`font-semibold ${costMeta.coveragePct >= 80 ? 'text-gray-300' : 'text-gray-400'}`}>
                      {costMeta.coveragePct}%
                    </span>
                  </div>
                )}
                
                {/* Источник данных */}
                {costMeta.source && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Источник:</span>
                    <span className="text-gray-300">{costMeta.source}</span>
                  </div>
                )}
                
                {/* Маржинальность */}
                <div className="flex justify-between">
                  <span className="text-gray-400">Маржа при рек. цене:</span>
                  <span className="text-gray-300 font-semibold">~71%</span>
                </div>
                
                {/* Дата обновления */}
                {costMeta.asOf && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Обновлено:</span>
                    <span className="text-gray-300">{costMeta.asOf}</span>
                  </div>
                )}
                
              </div>
            </div>
            
            <div className="mt-3 text-center">
              <div className="text-xs text-gray-500">
                Рекомендуемая цена рассчитана с учетом стандартной ресторанной наценки
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Ingredient mapping functions
  const handleOpenIngredientMapping = (ingredientIndex) => {
    setMappingIngredientIndex(ingredientIndex);
    setMappingModalOpen(true);
    setMappingActiveTab('iiko'); // P0: Default to iiko source
    setCatalogSearchQuery('');
    setCatalogSearchResults([]);
    setUsdaSearchQuery('');
    setUsdaSearchResults([]);
    setPriceSearchQuery('');
    setPriceSearchResults([]);
    setIikoSearchQuery('');
    setIikoSearchResults([]);
    
    // Auto-fill search with ingredient name
    if (tcV2 && tcV2.ingredients && tcV2.ingredients[ingredientIndex]) {
      const ingredientName = tcV2.ingredients[ingredientIndex].name;
      setCatalogSearchQuery(ingredientName);
      setUsdaSearchQuery(ingredientName);
      setPriceSearchQuery(ingredientName);
      performCatalogSearch(ingredientName);
      debouncedUsdaSearch(ingredientName);
      debouncedPriceSearch(ingredientName);
      debouncedIikoSearch(ingredientName);
    }
  };

  const performCatalogSearch = async (query) => {
    if (!query.trim()) {
      setCatalogSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch(`${API}/v1/techcards.v2/catalog-search?q=${encodeURIComponent(query)}&limit=10`);
      const data = await response.json();
      
      if (data.status === 'success') {
        setCatalogSearchResults(data.items || []);
      } else {
        setCatalogSearchResults([]);
      }
    } catch (error) {
      console.error('Catalog search error:', error);
      setCatalogSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const performUsdaSearch = async (query) => {
    if (!query.trim()) {
      setUsdaSearchResults([]);
      return;
    }

    setIsSearchingUsda(true);
    try {
      const response = await fetch(`${API}/v1/techcards.v2/catalog-search?source=usda&q=${encodeURIComponent(query)}&limit=20`);
      const data = await response.json();
      
      if (data.status === 'success') {
        setUsdaSearchResults(data.items || []);
      } else {
        setUsdaSearchResults([]);
      }
    } catch (error) {
      console.error('USDA search error:', error);
      setUsdaSearchResults([]);
    } finally {
      setIsSearchingUsda(false);
    }
  };

  // Debounced USDA search
  const [usdaSearchTimeout, setUsdaSearchTimeout] = useState(null);
  const debouncedUsdaSearch = (query) => {
    if (usdaSearchTimeout) {
      clearTimeout(usdaSearchTimeout);
    }
    const timeout = setTimeout(() => {
      performUsdaSearch(query);
    }, 250);
    setUsdaSearchTimeout(timeout);
  };

  const performPriceSearch = async (query) => {
    if (!query.trim()) {
      setPriceSearchResults([]);
      return;
    }

    setIsSearchingPrice(true);
    try {
      const response = await fetch(`${API}/v1/techcards.v2/catalog-search?source=price&q=${encodeURIComponent(query)}&limit=20`);
      const data = await response.json();
      
      if (data.status === 'success') {
        setPriceSearchResults(data.items || []);
      } else {
        setPriceSearchResults([]);
      }
    } catch (error) {
      console.error('Price search error:', error);
      setPriceSearchResults([]);
    } finally {
      setIsSearchingPrice(false);
    }
  };

  // Debounced Price search
  const [priceSearchTimeout, setPriceSearchTimeout] = useState(null);
  const [iikoSearchTimeout, setIikoSearchTimeout] = useState(null);
  const debouncedPriceSearch = (query) => {
    if (priceSearchTimeout) {
      clearTimeout(priceSearchTimeout);
    }
    const timeout = setTimeout(() => {
      performPriceSearch(query);
    }, 250);
    setPriceSearchTimeout(timeout);
  };

  const debouncedIikoSearch = (query) => {
    if (iikoSearchTimeout) {
      clearTimeout(iikoSearchTimeout);
    }
    const timeout = setTimeout(() => {
      performIikoSearch(query);
    }, 250);
    setIikoSearchTimeout(timeout);
  };

  const handleAssignIngredientMapping = async (catalogItem) => {
    if (!tcV2 || mappingIngredientIndex === null) return;

    // MAP-01: Enhanced product_code extraction with proper article priority
    let productCode = null;
    const skuId = catalogItem.sku_id || catalogItem.skuId;
    
    // Priority 1: Use article (nomenclature.num) - the correct field for iiko
    if (catalogItem.source === 'iiko' && catalogItem.article) {
      // Format article as five-digit with leading zeros
      productCode = String(catalogItem.article).padStart(5, '0');
      console.log(`MAP-01: Using article ${productCode} from catalogItem.article`);
    } 
    // Priority 2: Use product_code if already formatted correctly
    else if (catalogItem.product_code) {
      productCode = catalogItem.product_code;
      console.log(`MAP-01: Using product_code ${productCode} from catalogItem.product_code`);
    } 
    // Priority 3: Use code only if it's not a GUID (avoid hyphens)
    else if (catalogItem.code && !catalogItem.code.includes('-')) {
      productCode = catalogItem.code;
      console.log(`MAP-01: Using code ${productCode} from catalogItem.code (not GUID)`);
    }
    // Priority 4: If article missing but we have skuId, make additional request
    else if (skuId && catalogItem.source === 'iiko') {
      try {
        console.log(`MAP-01: Article missing, looking up by skuId: ${skuId}`);
        const response = await fetch(`${API}/v1/techcards.v2/catalog-search?q=${encodeURIComponent(skuId)}&search_by=id&source=iiko&limit=1`);
        const data = await response.json();
        
        if (data.status === 'success' && data.items.length > 0 && data.items[0].article) {
          productCode = String(data.items[0].article).padStart(5, '0');
          console.log(`MAP-01: Found article ${productCode} via additional lookup for skuId ${skuId}`);
        } else {
          console.warn(`MAP-01: Could not find article for skuId ${skuId}, will use skuId as fallback`);
        }
      } catch (error) {
        console.warn('MAP-01: Error in additional article lookup:', error);
      }
    }

    // Update tcV2 with mapping
    const updatedTcV2 = {
      ...tcV2,
      ingredients: tcV2.ingredients.map((ing, index) => {
        if (index === mappingIngredientIndex) {
          return {
            ...ing,
            canonical_id: catalogItem.canonical_id || ing.canonical_id || null,
            skuId: skuId || ing.skuId || null,
            product_code: productCode || ing.product_code || null, // MAP-01: Save article when available
            source: catalogItem.source || ing.source || null
          };
        }
        return ing;
      })
    };

    console.log(`MAP-01: Assigned ingredient mapping - productCode: ${productCode}, skuId: ${skuId}, source: ${catalogItem.source}`);

    setTcV2(updatedTcV2);
    setMappingModalOpen(false);
    
    // CRITICAL FIX: Persist mapping to MongoDB
    try {
      if (updatedTcV2.meta && updatedTcV2.meta.id) {
        console.log(`🔥 PERSIST: Saving manual SKU mapping to MongoDB for tech card ${updatedTcV2.meta.id}`);
        await axios.put(`${API}/v1/techcards.v2/${updatedTcV2.meta.id}`, updatedTcV2);
        console.log('✅ PERSIST: Manual mapping saved successfully');
      }
    } catch (error) {
      console.error('❌ PERSIST: Failed to save manual mapping:', error);
    }
    
    // Clear search states
    setUsdaSearchQuery('');
    setUsdaSearchResults([]);
    setPriceSearchQuery('');
    setPriceSearchResults([]);
    setIikoSearchQuery('');
    setIikoSearchResults([]);

    // Perform recalculation
    await performRecalculation(updatedTcV2);
  };

  const performRecalculation = async (updatedCard) => {
    setIsRecalculating(true);
    setRecalcError(null);
    try {
      const response = await fetch(`${API}/v1/techcards.v2/recalc`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatedCard)
      });

      const data = await response.json();
      
      if (data.status === 'success' && data.card) {
        setTcV2(data.card);
        console.log('✅ Recalculation successful');
      } else {
        console.error('Recalculation failed:', data.message);
        setRecalcError(`Ошибка пересчета: ${data.message}`);
      }
    } catch (error) {
      console.error('Recalculation error:', error);
      setRecalcError('Ошибка при пересчете техкарты');
    } finally {
      setIsRecalculating(false);
    }
  };

  const saveTechCardToHistory = async () => {
    if (!tcV2) {
      console.error('❌ No tcV2 to save');
      return;
    }
    
    setIsRecalculating(true);
    setRecalcError(null);
    
    try {
      console.log('🔄 Starting save process...');
      console.log('📦 Current tcV2:', tcV2);
      
      // Сначала пересчитываем
      const recalcResponse = await fetch(`${API}/v1/techcards.v2/recalc`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tcV2)
      });
      
      const recalcData = await recalcResponse.json();
      console.log('✅ Recalculation response:', recalcData);
      
      if (recalcData.status !== 'success' || !recalcData.card) {
        throw new Error(recalcData.message || 'Ошибка пересчёта');
      }
      
      setTcV2(recalcData.card);
      
      // Затем сохраняем в историю
      const techcardId = recalcData.card.meta?.id || recalcData.card._id || recalcData.card.id;
      console.log('🔍 Searching for techcard_id...');
      console.log('   meta.id:', recalcData.card.meta?.id);
      console.log('   _id:', recalcData.card._id);
      console.log('   id:', recalcData.card.id);
      console.log('📌 Selected techcard_id:', techcardId);
      
      if (!techcardId) {
        throw new Error('Не удалось найти ID техкарты для сохранения');
      }
      
      console.log('💾 Sending save request...');
      const saveResponse = await fetch(`${API}/v1/techcards.v2/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          techcard_id: techcardId, 
          techcard: recalcData.card 
        })
      });
      
      const saveData = await saveResponse.json();
      console.log('📥 Save response:', saveData);
      
      if (saveData.status === 'success') {
        console.log('✅ Techcard saved to history successfully');
        alert('✅ Техкарта успешно сохранена!');
        // Обновляем историю
        loadUserTechCards();
      } else {
        throw new Error(saveData.message || 'Ошибка сохранения');
      }
    } catch (error) {
      console.error('❌ Error saving techcard:', error);
      setRecalcError(`Ошибка сохранения: ${error.message}`);
      alert(`❌ Ошибка сохранения техкарты: ${error.message}`);
    } finally {
      setIsRecalculating(false);
    }
  };

  const formatTechCard = (content) => {
    // V1 Recipes and V1 Tech Cards support - always show them
    // FORCE_TECHCARD_V2 only affects tech card GENERATION, not display
    if (!content) {
      return (
        <div className="text-center py-8 text-gray-400">
          <p className="text-lg">🍳 Контент не найден</p>
        </div>
      );
    }

    // Проверяем, это V1 рецепт (с эмодзи) или V2 техкарта
    const isV1Recipe = content.includes('🎯') || content.includes('⏱️') || content.includes('👥');
    
    if (isV1Recipe) {
      // Для V1 рецептов просто отображаем как есть с базовым форматированием
      return (
        <div className="whitespace-pre-wrap text-gray-200 leading-relaxed">
          {content}
        </div>
      );
    }

    // Для V2 техкарт используем старую логику парсинга
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

        {/* HACCP - ПОЛНОСТЬЮ ОТКЛЮЧЕН */}
        {false && (
          <div className="bg-gradient-to-r from-orange-900/20 to-yellow-900/20 rounded-lg p-4 border border-orange-500/30">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-orange-300 flex items-center space-x-2">
                <span>🛡️ HACCP</span>
                <span className="text-xs bg-purple-600 px-2 py-1 rounded">PRO</span>
                {currentTechCardHaccp?.hazards?.length > 0 ? (
                  <span className="bg-green-600 px-2 py-1 rounded text-xs">OK</span>
                ) : (
                  <span className="bg-orange-600 px-2 py-1 rounded text-xs">Требуется проверка</span>
                )}
                {isAutoGeneratingHaccp && (
                  <span className="text-xs text-orange-400">Обновляется...</span>
                )}
              </h3>
              <button
                onClick={auditHaccp}
                disabled={isHaccpAuditing}
                className="bg-orange-600 hover:bg-orange-700 disabled:bg-gray-600 px-4 py-2 rounded text-sm font-medium transition-colors"
              >
                {isHaccpAuditing ? 'Проверяем...' : 'HACCP АУДИТ'}
              </button>
            </div>
            
            <div className="space-y-3">
              {/* HACCP Pro status info */}
              <div className="bg-orange-800/30 p-3 rounded-lg text-xs">
                <div className="text-orange-300 font-medium">HACCP Pro модуль (Debug)</div>
                <div className="text-gray-400">
                  Статус: {haccpProEnabled ? '✅ Включен' : '❌ Выключен'} | 
                  Подписка: {currentUser?.subscription_plan || 'N/A'} |
                  User: {currentUser?.email || currentUser?.name || 'N/A'}
                </div>
                {!haccpProEnabled && (
                  <div className="text-orange-400 mt-2">
                    💡 Включите HACCP Pro в настройках профиля заведения (шаг 4)
                  </div>
                )}
              </div>
              
              {/* Allergens chips */}
              {currentTechCardHaccp?.allergens && currentTechCardHaccp.allergens.length > 0 && (
                <div>
                  <h4 className="text-sm font-bold text-orange-400 mb-2">Аллергены:</h4>
                  <div className="flex flex-wrap gap-2">
                    {currentTechCardHaccp.allergens.map((allergen, idx) => (
                      <span key={idx} className="bg-red-600 px-2 py-1 rounded-full text-xs">
                        {allergen}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Critical Control Points */}
              {currentTechCardHaccp?.ccp && currentTechCardHaccp.ccp.length > 0 && (
                <div>
                  <h4 className="text-sm font-bold text-orange-400 mb-2">Критические контрольные точки:</h4>
                  <div className="space-y-2">
                    {currentTechCardHaccp.ccp.slice(0, 2).map((ccp, idx) => (
                      <div key={idx} className="bg-orange-800/30 p-2 rounded text-xs">
                        <div className="font-medium">{ccp.name}</div>
                        <div className="text-gray-400">Предел: {ccp.limit}</div>
                      </div>
                    ))}
                    {currentTechCardHaccp.ccp.length > 2 && (
                      <div className="text-xs text-gray-400">
                        +{currentTechCardHaccp.ccp.length - 2} больше точек
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              {/* Storage */}
              {currentTechCardHaccp?.storage && (
                <div>
                  <h4 className="text-sm font-bold text-orange-400 mb-2">Хранение:</h4>
                  <p className="text-xs text-gray-300">{currentTechCardHaccp.storage}</p>
                </div>
              )}
              
              {/* Hazards count */}
              {currentTechCardHaccp?.hazards && currentTechCardHaccp.hazards.length > 0 && (
                <div className="text-xs text-gray-400">
                  Выявлено рисков: {currentTechCardHaccp.hazards.length}
                </div>
              )}
            </div>
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

  // УПРОЩЕНИЕ: Убрали fetchCities - город больше не нужен
  // const fetchCities = async () => {
  //   try {
  //     const response = await axios.get(`${API}/cities`);
  //     setCities(response.data);
  //   } catch (error) {
  //     console.error('Error fetching cities:', error);
  //     // Fallback cities if API fails
  //     const fallbackCities = [
  //       { code: 'moskva', name: 'Москва' },
  //       { code: 'spb', name: 'Санкт-Петербург' },
  //       { code: 'novosibirsk', name: 'Новосибирск' },
  //       { code: 'yekaterinburg', name: 'Екатеринбург' },
  //       { code: 'kazan', name: 'Казань' },
  //       { code: 'nizhniy-novgorod', name: 'Нижний Новгород' }
  //     ];
  //     setCities(fallbackCities);
  //   }
  // };

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

  // HACCP Audit function - ОТКЛЮЧЕНО
  const auditHaccp = async () => {
    return; // ПОЛНОСТЬЮ ОТКЛЮЧЕНО
    if (!FEATURE_HACCP) return;
    if (!techCard || !currentUser?.id) return;
    
    setIsHaccpAuditing(true);
    
    try {
      // Parse tech card content to create a simple structure for the API
      const cardData = {
        meta: {
          name: techCard.match(/\*\*Название:\*\*\s*(.*?)(?=\n|$)/)?.[1]?.trim() || "Блюдо",
          category: techCard.match(/\*\*Категория:\*\*\s*(.*?)(?=\n|$)/)?.[1]?.trim() || "Основные блюда",
          cuisine: "международная"
        },
        ingredients: [], // Simplified for now
        process: [], // Simplified for now
        yield: {
          portions: 4,
          per_portion_g: 250,
          total_net_g: 1000
        },
        haccp: currentTechCardHaccp || {
          hazards: [],
          ccp: [],
          storage: null
        },
        allergens: []
      };

      const response = await fetch(`${API}/v1/haccp.v2/audit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(cardData),
      });

      if (response.ok) {
        const auditData = await response.json();
        setHaccpAuditResult(auditData);
        setShowHaccpAuditModal(true);
        console.log('HACCP audit completed:', auditData);
      } else {
        const errorText = await response.text();
        console.error('HACCP audit failed:', errorText);
        alert('Не удалось выполнить аудит. Попробуйте ещё раз');
      }
    } catch (error) {
      console.error('Error during HACCP audit:', error);
      alert('Не удалось выполнить аудит. Попробуйте ещё раз');
    } finally {
      setIsHaccpAuditing(false);
    }
  };

  // Apply HACCP patch function - ОТКЛЮЧЕНО
  const applyHaccpPatch = () => {
    return; // ПОЛНОСТЬЮ ОТКЛЮЧЕНО
    if (!FEATURE_HACCP) return;
    if (!haccpAuditResult?.patch) return;
    
    // For now, just update the HACCP data
    // In a real implementation, you'd update the entire tech card
    setCurrentTechCardHaccp(haccpAuditResult.patch.haccp);
    setShowHaccpAuditModal(false);
    
    // Show success message
    alert('Исправления применены');
  };

  // IIKo Integration API functions - NEW!
  const fetchIikoHealth = async () => {
    try {
      const response = await axios.get(`${API}/iiko/health`);
      setIikoHealthStatus(response.data);
      return response.data;
    } catch (error) {
      console.error('Error checking IIKo health:', error);
      setIikoHealthStatus({
        status: 'error',
        iiko_connection: 'failed',
        error: error.response?.data?.detail || error.message
      });
      return null;
    }
  };

  const fetchIikoOrganizations = async () => {
    setIsLoadingIiko(true);
    try {
      const response = await axios.get(`${API}/iiko/organizations`);
      
      if (response.data.success && response.data.organizations) {
        setIikoOrganizations(response.data.organizations);
      } else {
        setIikoOrganizations([]);
        console.warn('No organizations found in IIKo response');
      }
    } catch (error) {
      console.error('Error fetching IIKo organizations:', error);
      alert('Ошибка получения списка организаций IIKo: ' + (error.response?.data?.detail || error.message));
      setIikoOrganizations([]);
    } finally {
      setIsLoadingIiko(false);
    }
  };

  const fetchIikoMenu = async (organizationId) => {
    if (!organizationId) return;
    
    setIsLoadingIiko(true);
    try {
      const response = await axios.get(`${API}/iiko/menu/${organizationId}`);
      
      if (response.data.success && response.data.menu) {
        setIikoMenu(response.data.menu);
      } else {
        setIikoMenu(null);
        console.warn('No menu data found in IIKo response');
      }
    } catch (error) {
      console.error('Error fetching IIKo menu:', error);
      alert('Ошибка получения меню IIKo: ' + (error.response?.data?.detail || error.message));
      setIikoMenu(null);
    } finally {
      setIsLoadingIiko(false);
    }
  };

  const uploadTechCardToIiko = async (techCardData, organizationId) => {
    setIsUploadingTechCard(true);
    try {
      // Extract tech card details from content
      const lines = techCardData.content.split('\n');
      let dishName = '';
      let description = '';
      let ingredients = [];
      let steps = [];
      let price = null;
      
      // Parse tech card content
      lines.forEach(line => {
        if (line.includes('Название:')) {
          dishName = line.replace(/\*\*Название:\*\*/g, '').trim();
        }
        if (line.includes('Описание:')) {
          description = line.replace(/\*\*Описание:\*\*/g, '').trim();
        }
        if (line.includes('Рекомендуемая цена') && line.includes('₽')) {
          const priceMatch = line.match(/(\d+(?:\.\d+)?)\s*₽/);
          if (priceMatch) {
            price = parseFloat(priceMatch[1]);
          }
        }
        if (line.trim().startsWith('- ') && line.includes('—')) {
          const ingredient = line.replace(/^-\s*/, '').trim();
          const [name, ...rest] = ingredient.split('—');
          ingredients.push({
            name: name.trim(),
            quantity: rest.join('—').trim() || '1',
            unit: 'шт'
          });
        }
      });
      
      // Prepare upload data
      const uploadData = {
        name: dishName || techCardData.dish_name,
        description: description || 'Блюдо создано с помощью AI-Menu-Designer',
        ingredients: ingredients.length > 0 ? ingredients : [
          {name: 'Ингредиенты уточняются', quantity: '1', unit: 'шт'}
        ],
        preparation_steps: steps.length > 0 ? steps : ['Готовится по технологической карте'],
        organization_id: organizationId,
        price: price,
        weight: null
      };
      
      const response = await axios.post(`${API}/iiko/tech-cards/upload`, uploadData);
      
      setUploadResult({
        success: true,
        message: response.data.message || 'Техкарта успешно подготовлена для загрузки в IIKo',
        syncId: response.data.sync_id,
        data: response.data
      });
      
      return response.data;
    } catch (error) {
      console.error('Error uploading tech card to IIKo:', error);
      const errorMessage = error.response?.data?.detail || error.message;
      setUploadResult({
        success: false,
        message: `Ошибка загрузки техкарты в IIKo: ${errorMessage}`,
        error: errorMessage
      });
      throw error;
    } finally {
      setIsUploadingTechCard(false);
    }
  };

  const syncMenuWithIiko = async (organizationIds, syncSettings) => {
    setIsSyncing(true);
    setSyncProgress({
      status: 'starting',
      message: 'Запуск синхронизации...',
      organizations: organizationIds.length
    });
    
    try {
      const response = await axios.post(`${API}/iiko/sync-menu`, {
        organization_ids: organizationIds,
        sync_prices: syncSettings.syncPrices,
        sync_categories: syncSettings.syncCategories
      });
      
      setSyncProgress({
        status: 'in_progress',
        syncJobId: response.data.sync_job_id,
        message: response.data.message || 'Синхронизация запущена',
        organizations: response.data.organizations_count
      });
      
      // Poll for sync status
      if (response.data.sync_job_id) {
        pollSyncStatus(response.data.sync_job_id);
      }
      
      return response.data;
    } catch (error) {
      console.error('Error syncing menu with IIKo:', error);
      setSyncProgress({
        status: 'error',
        message: `Ошибка синхронизации: ${error.response?.data?.detail || error.message}`,
        error: error.response?.data?.detail || error.message
      });
      throw error;
    }
  };

  const pollSyncStatus = async (syncJobId) => {
    const maxPolls = 30; // 30 polls * 2 seconds = 1 minute max
    let pollCount = 0;
    
    const poll = async () => {
      try {
        const response = await axios.get(`${API}/iiko/sync/status/${syncJobId}`);
        const syncJob = response.data.sync_job;
        
        setSyncProgress({
          status: syncJob.status,
          syncJobId: syncJobId,
          message: syncJob.status === 'completed' 
            ? 'Синхронизация завершена успешно!' 
            : syncJob.status === 'failed'
            ? `Синхронизация завершилась с ошибкой: ${syncJob.error}`
            : 'Синхронизация в процессе...',
          results: syncJob.results || null,
          error: syncJob.error || null
        });
        
        if (syncJob.status === 'completed' || syncJob.status === 'failed') {
          setIsSyncing(false);
          return;
        }
        
        pollCount++;
        if (pollCount < maxPolls) {
          setTimeout(poll, 2000); // Poll every 2 seconds
        } else {
          setSyncProgress({
            status: 'timeout',
            message: 'Превышено время ожидания синхронизации',
            syncJobId: syncJobId
          });
          setIsSyncing(false);
        }
      } catch (error) {
        console.error('Error polling sync status:', error);
        setSyncProgress({
          status: 'error',
          message: 'Ошибка получения статуса синхронизации',
          error: error.message
        });
        setIsSyncing(false);
      }
    };
    
    setTimeout(poll, 2000); // Start polling after 2 seconds
  };

  const openIikoIntegration = async () => {
    setShowIikoModal(true);
    
    // Check IIKo health status
    await fetchIikoHealth();
    
    // Load organizations if health is OK
    if (iikoHealthStatus?.status !== 'error') {
      await fetchIikoOrganizations();
    }
  };

  // NEW - Function to fetch and display category items beautifully
  const viewIikoCategory = async (categoryName) => {
    if (!selectedOrganization?.id) {
      alert('Сначала выберите организацию');
      return;
    }

    setIsLoadingCategory(true);
    setShowCategoryViewer(true);
    setCategoryData(null);

    try {
      const response = await axios.get(`${API}/iiko/category/${selectedOrganization.id}/${categoryName}`);
      
      if (response.data.success) {
        setCategoryData({
          category: response.data.category,
          items: response.data.items,
          summary: response.data.summary,
          searchedFor: categoryName
        });
      } else {
        setCategoryData({
          success: false,
          error: `Категория "${categoryName}" не найдена`,
          similarCategories: response.data.similar_categories || [],
          allCategories: response.data.all_categories || [],
          searchedFor: categoryName
        });
      }
    } catch (error) {
      console.error('Error fetching category:', error);
      setCategoryData({
        success: false,
        error: `Ошибка загрузки категории: ${error.response?.data?.detail || error.message}`,
        searchedFor: categoryName
      });
    } finally {
      setIsLoadingCategory(false);
    }
  };

  // ============== INLINE EDITING FUNCTIONS (Task 0.1) ==============
  
  const startIngredientEdit = (ingredientIndex) => {
    if (!tcV2 || !tcV2.ingredients[ingredientIndex]) return;
    
    const ingredient = tcV2.ingredients[ingredientIndex];
    setEditingIngredientIndex(ingredientIndex);
    setEditingData({
      name: ingredient.name,
      brutto_g: ingredient.brutto_g,
      loss_pct: ingredient.loss_pct,
      netto_g: ingredient.netto_g,
      unit: ingredient.unit
    });
    setEditingErrors({});
    setRecalcError(null);
  };

  const cancelIngredientEdit = () => {
    setEditingIngredientIndex(null);
    setEditingData({});
    setEditingErrors({});
  };

  const validateEditingData = (data) => {
    const errors = {};
    
    if (data.brutto_g < 0) errors.brutto_g = "Брутто не может быть отрицательным";
    if (data.loss_pct < 0 || data.loss_pct > 60) errors.loss_pct = "Потери должны быть от 0 до 60%";
    if (data.netto_g < 0) errors.netto_g = "Нетто не может быть отрицательным";
    
    return errors;
  };

  const handleEditingChange = (field, value) => {
    // Для текстовых полей (name, unit) используем значение как есть
    const fieldValue = (field === 'name' || field === 'unit') ? value : (parseFloat(value) || 0);
    let newData = { ...editingData, [field]: fieldValue };
    
    // Auto-calculate related fields только для числовых полей
    if (field === 'brutto_g' || field === 'loss_pct') {
      newData.netto_g = newData.brutto_g * (1 - newData.loss_pct / 100);
    } else if (field === 'netto_g') {
      if (newData.loss_pct < 100) {
        newData.brutto_g = newData.netto_g / (1 - newData.loss_pct / 100);
      }
    }
    
    setEditingData(newData);
    setEditingErrors(validateEditingData(newData));
  };

  const saveIngredientEdit = async () => {
    if (editingIngredientIndex === null || !tcV2) return;
    
    const errors = validateEditingData(editingData);
    if (Object.keys(errors).length > 0) {
      setEditingErrors(errors);
      return;
    }

    // Update tcV2 with new ingredient data
    const updatedTcV2 = {
      ...tcV2,
      ingredients: tcV2.ingredients.map((ing, index) => {
        if (index === editingIngredientIndex) {
          return {
            ...ing,
            name: editingData.name,
            brutto_g: Math.round(editingData.brutto_g * 10) / 10,
            loss_pct: Math.round(editingData.loss_pct * 10) / 10,
            netto_g: Math.round(editingData.netto_g * 10) / 10,
            unit: editingData.unit
          };
        }
        return ing;
      })
    };

    setTcV2(updatedTcV2);
    setEditingIngredientIndex(null);
    setEditingData({});
    
    // Trigger recalculation
    await performRecalculation(updatedTcV2);
  };

  const handleEditKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      saveIngredientEdit();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      cancelIngredientEdit();
    }
  };

  // ============== ADD/REMOVE INGREDIENT FUNCTIONS ==============
  
  const addV2Ingredient = async () => {
    if (!tcV2) return;
    
    const newIngredient = {
      name: 'Новый ингредиент',
      brutto_g: 100,
      loss_pct: 0,
      netto_g: 100,
      unit: 'g',
      skuId: null,
      product_code: null,
      canonical_id: null,
      source: 'user'
    };
    
    const updatedTcV2 = {
      ...tcV2,
      ingredients: [...tcV2.ingredients, newIngredient]
    };
    
    setTcV2(updatedTcV2);
    
    // Trigger recalculation
    await performRecalculation(updatedTcV2);
  };
  
  const removeV2Ingredient = async (ingredientIndex) => {
    if (!tcV2 || !tcV2.ingredients[ingredientIndex]) return;
    
    // Подтверждение удаления
    const ingredientName = tcV2.ingredients[ingredientIndex].name;
    if (!window.confirm(`Удалить ингредиент "${ingredientName}"?`)) {
      return;
    }
    
    const updatedTcV2 = {
      ...tcV2,
      ingredients: tcV2.ingredients.filter((_, index) => index !== ingredientIndex)
    };
    
    setTcV2(updatedTcV2);
    
    // Trigger recalculation
    await performRecalculation(updatedTcV2);
  };

  const openSubRecipeModal = (ingredientIndex) => {
    setMappingIngredientIndex(ingredientIndex);
    setShowSubRecipeModal(true);
    fetchAvailableSubRecipes();
  };

  const fetchAvailableSubRecipes = async () => {
    try {
      // Fetch user's tech cards as potential sub-recipes
      const response = await axios.get(`${API}/user-history/${currentUser.id}`);
      if (response.data && response.data.length > 0) {
        const subRecipes = response.data
          .filter(item => item.id !== tcV2?.meta?.id) // Don't include current card
          .slice(0, 20) // Limit to 20
          .map(item => ({
            id: item.id,
            title: item.dish_name || item.title || 'Без названия',
            created_at: item.created_at
          }));
        setAvailableSubRecipes(subRecipes);
      }
    } catch (error) {
      console.error('Error fetching sub-recipes:', error);
      setAvailableSubRecipes([]);
    }
  };

  const assignSubRecipe = async (subRecipe) => {
    if (!tcV2 || mappingIngredientIndex === null) return;

    const updatedTcV2 = {
      ...tcV2,
      ingredients: tcV2.ingredients.map((ing, index) => {
        if (index === mappingIngredientIndex) {
          return {
            ...ing,
            subRecipe: {
              id: subRecipe.id,
              title: subRecipe.title
            },
            skuId: null // Clear SKU when assigning sub-recipe
          };
        }
        return ing;
      })
    };

    setTcV2(updatedTcV2);
    setShowSubRecipeModal(false);
    
    // Trigger recalculation
    await performRecalculation(updatedTcV2);
  };

  const removeSubRecipe = async (ingredientIndex) => {
    if (!tcV2) return;

    const updatedTcV2 = {
      ...tcV2,
      ingredients: tcV2.ingredients.map((ing, index) => {
        if (index === ingredientIndex) {
          const newIng = { ...ing };
          delete newIng.subRecipe;
          return newIng;
        }
        return ing;
      })
    };

    setTcV2(updatedTcV2);
    await performRecalculation(updatedTcV2);
  };

  // ============== UPLOAD FUNCTIONS (Task 1.2) ==============
  
  const openUploadModal = (type) => {
    setUploadType(type);
    setUploadFile(null);
    setUploadPreview(null);
    setUploadResults(null);
    setShowUploadModal(true);
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const validTypes = uploadType === 'prices' 
      ? ['.csv', '.xlsx', '.xls'] 
      : ['.json', '.csv'];
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    
    if (!validTypes.includes(fileExtension)) {
      alert(`Для ${uploadType === 'prices' ? 'прайсов' : 'БЖУ'} поддерживаются файлы: ${validTypes.join(', ')}`);
      return;
    }

    setUploadFile(file);
    
    // Generate preview for display
    if (uploadType === 'prices') {
      setUploadPreview({
        name: file.name,
        size: (file.size / 1024).toFixed(1) + ' KB',
        type: 'Прайс-лист',
        expectedColumns: 'Название продукта, Цена, Единица измерения, Категория'
      });
    } else {
      setUploadPreview({
        name: file.name,
        size: (file.size / 1024).toFixed(1) + ' KB', 
        type: 'Данные по питанию',
        expectedFormat: fileExtension === '.json' ? 'JSON с полями name, per100g' : 'CSV с колонками: название, ккал, белки, жиры, углеводы'
      });
    }
  };

  const handleUpload = async () => {
    if (!uploadFile || !currentUser) return;

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('user_id', currentUser.id);

      const endpoint = uploadType === 'prices' ? '/upload-prices' : '/upload-nutrition';
      const response = await axios.post(`${API}${endpoint}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data.success) {
        setUploadResults({
          success: true,
          count: response.data.count,
          message: response.data.message,
          preview: response.data[uploadType === 'prices' ? 'prices' : 'nutrition'] || []
        });
      } else {
        setUploadResults({
          success: false,
          error: response.data.error || 'Ошибка загрузки файла'
        });
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadResults({
        success: false,
        error: error.response?.data?.detail || error.message || 'Ошибка загрузки файла'
      });
    } finally {
      setIsUploading(false);
    }
  };

  const triggerRecalc = async () => {
    if (!currentUser || !tcV2) return;

    setIsRecalculating(true);
    try {
      const response = await axios.post(`${API}/v1/techcards.v2/recalc`, {
        card: tcV2,
        user_id: currentUser.id
      });

      if (response.data.success && response.data.card) {
        setTcV2(response.data.card);
        alert(`Пересчёт выполнен! Обновлены данные по стоимости и питанию.`);
        setShowUploadModal(false);
      } else {
        alert('Ошибка пересчёта: ' + (response.data.error || 'Неизвестная ошибка'));
      }
    } catch (error) {
      console.error('Recalc error:', error);
      alert('Ошибка пересчёта: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsRecalculating(false);
    }
  };

  // ============== IIKO RMS INTEGRATION FUNCTIONS (IK-02B-FE/01) ==============
  
  const connectToIikoRms = async () => {
    if (!iikoRmsCredentials.host || !iikoRmsCredentials.login || !iikoRmsCredentials.password) {
      setIikoRmsMessage({ type: 'error', text: 'Заполните все поля для подключения' });
      return;
    }

    setIsConnectingIikoRms(true);
    setIikoRmsMessage({ type: '', text: '' });
    
    try {
      const response = await axios.post(`${API}/v1/iiko/rms/connect`, {
        host: iikoRmsCredentials.host,
        login: iikoRmsCredentials.login,
        password: iikoRmsCredentials.password,
        user_id: currentUser?.id || 'anonymous'
      });

      if (response.data.status === 'connected') {
        const organizations = response.data.organizations || [];
        const orgName = organizations[0]?.name || 'Неизвестная организация';
        
        setIikoRmsConnection({
          status: 'connected',
          host: iikoRmsCredentials.host,
          login: iikoRmsCredentials.login,
          organization_name: orgName,
          last_connection: new Date().toISOString(),
          sync_status: 'never_synced',
          products_count: 0,
          last_sync: null,
          error_message: ''
        });
        
        // Save connection for sticky behavior
        localStorage.setItem('iikoRmsConnected', 'true');
        
        setIikoRmsMessage({ 
          type: 'success', 
          text: `✅ Подключение успешно! Организация: ${orgName}` 
        });
        
        // Сохранение учетных данных теперь происходит автоматически на бэкенде
        // при успешном подключении - больше не используем localStorage
        console.log('💾 Учетные данные iiko сохранены на бэкенде для автоматического входа');
        
        // Check connection status
        await checkIikoRmsStatus();
      } else {
        throw new Error(response.data.error || 'Неизвестная ошибка подключения');
      }
    } catch (error) {
      console.error('iiko RMS connect error:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Ошибка подключения к серверу iiko RMS';
      
      setIikoRmsConnection(prev => ({
        ...prev,
        status: 'error',
        error_message: errorMsg
      }));
      
      setIikoRmsMessage({ type: 'error', text: `❌ ${errorMsg}` });
    } finally {
      setIsConnectingIikoRms(false);
    }
  };

  const disconnectFromIikoRms = async () => {
    try {
      setIikoRmsMessage({ type: 'info', text: '🔄 Отключение от iiko RMS...' });
      
      // Отключение теперь происходит через бэкенд API
      const response = await axios.post(`${API}/v1/iiko/rms/disconnect`, null, {
        params: { user_id: currentUserOrDemo.id }
      });
      
      if (response.data.status === 'disconnected') {
        setIikoRmsConnection({
          status: 'not_connected',
          host: '',
          login: '',
          organization_name: '',
          last_connection: null,
          sync_status: 'never_synced',
          products_count: 0,
          last_sync: null,
          error_message: ''
        });
        
        setIikoRmsMessage({ 
          type: 'success', 
          text: '✅ Подключение разорвано. Данные авторизации удалены с бэкенда.' 
        });
      }
    } catch (error) {
      console.error('iiko RMS disconnect error:', error);
      setIikoRmsMessage({ 
        type: 'error', 
        text: `❌ Ошибка отключения: ${error.message}` 
      });
    }
  };

  const restoreIikoRmsConnection = async () => {
    try {
      setIikoRmsMessage({ type: 'info', text: '🔄 Восстановление подключения...' });
      
      const response = await axios.post(`${API}/v1/iiko/rms/restore-connection?user_id=${currentUser?.id || 'anonymous'}`);
      
      if (response.data.status === 'restored') {
        setIikoRmsConnection({
          status: 'connected',
          host: response.data.host,
          login: response.data.login,
          organization_name: response.data.organization_name,
          last_connection: new Date().toISOString(),
          sync_status: 'never_synced',
          products_count: 0,
          last_sync: null,
          error_message: ''
        });
        
        setIikoRmsMessage({ 
          type: 'success', 
          text: '✅ Подключение восстановлено!' 
        });
        
        return true;
      } else if (response.data.status === 'needs_reconnection') {
        setIikoRmsConnection(prev => ({
          ...prev,
          status: 'needs_reconnection',
          error_message: 'Требуется повторная авторизация'
        }));
        
        setIikoRmsMessage({ 
          type: 'warning', 
          text: '⚠️ Нужно переподключиться. Сессия истекла.' 
        });
        
        return false;
      } else if (response.data.status === 'manually_disconnected') {
        // Connection was manually disconnected, don't restore
        return false;
      } else {
        setIikoRmsMessage({ 
          type: 'error', 
          text: `❌ Не удалось восстановить подключение: ${response.data.error || 'Unknown error'}` 
        });
        return false;
      }
    } catch (error) {
      console.error('iiko RMS restore connection error:', error);
      setIikoRmsMessage({ 
        type: 'error', 
        text: `❌ Ошибка восстановления: ${error.message}` 
      });
      return false;
    }
  };

  const syncIikoRmsNomenclature = async () => {
    if (iikoRmsConnection.status !== 'connected') {
      setIikoRmsMessage({ type: 'error', text: 'Сначала установите подключение к серверу iiko RMS' });
      return;
    }

    setIsSyncingIikoRms(true);
    setIikoRmsMessage({ type: 'info', text: '🔄 Синхронизация номенклатуры...' });
    
    setIikoRmsConnection(prev => ({
      ...prev,
      sync_status: 'syncing'
    }));
    
    try {
      const response = await axios.post(`${API}/v1/iiko/rms/sync/nomenclature?organization_id=${iikoRmsConnection.organization_id || 'default'}`, {
        force: false
      });

      if (response.data.status === 'completed') {
        const stats = response.data.stats || {};
        const productsCount = stats.products_processed || 0;
        
        setIikoRmsConnection(prev => ({
          ...prev,
          sync_status: 'completed',
          products_count: productsCount,
          last_sync: new Date().toISOString(),
          error_message: ''
        }));
        
        setIikoRmsMessage({ 
          type: 'success', 
          text: `✅ Синхронизация завершена! Получено продуктов: ${productsCount}` 
        });
      } else if (response.data.status === 'already_running') {
        setIikoRmsMessage({ 
          type: 'info', 
          text: '⏳ Синхронизация уже выполняется...' 
        });
        
        // Poll for completion
        setTimeout(() => checkIikoRmsStatus(), 2000);
      } else {
        throw new Error(response.data.error || 'Неизвестная ошибка синхронизации');
      }
    } catch (error) {
      console.error('iiko RMS sync error:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Ошибка синхронизации номенклатуры';
      
      setIikoRmsConnection(prev => ({
        ...prev,
        sync_status: 'failed',
        error_message: errorMsg
      }));
      
      setIikoRmsMessage({ type: 'error', text: `❌ ${errorMsg}` });
    } finally {
      setIsSyncingIikoRms(false);
    }
  };

  const checkIikoRmsStatus = async (attemptRestore = true) => {
    // Определяем правильный user_id для запроса (демо пользователь или реальный)
    const userId = currentUser?.id || 'demo_user';
    
    try {
      const response = await axios.get(`${API}/v1/iiko/rms/connection/status?user_id=${userId}`);
      
      if (response.data.status === 'connected') {
        setIikoRmsConnection(prev => ({
          ...prev,
          status: 'connected',
          host: response.data.host || prev.host,
          login: response.data.login || prev.login,
          organization_name: response.data.organization_name || prev.organization_name,
          last_connection: response.data.last_connection || prev.last_connection
        }));
        
        // Статус подключения теперь управляется через бэкенд
        console.log('🔗 Статус подключения обновлён через бэкенд');
        
        // Also get sync status
        try {
          const syncResponse = await axios.get(`${API}/v1/iiko/rms/sync/status?organization_id=${iikoRmsConnection.organization_id || 'default'}&user_id=${userId}`);
          if (syncResponse.data.status) {
            setIikoRmsConnection(prev => ({
              ...prev,
              sync_status: syncResponse.data.status,
              products_count: syncResponse.data.stats?.products_processed || 0,
              last_sync: syncResponse.data.completed_at || prev.last_sync
            }));
          }
        } catch (syncError) {
          // Пользователь не имеет доступа к данным синхронизации или нет подключения
          console.log('ℹ️ Нет доступа к данным синхронизации для текущего пользователя');
          setIikoRmsConnection(prev => ({
            ...prev,
            sync_status: null,
            products_count: 0,
            last_sync: null
          }));
        }
      } else if (response.data.status === 'demo_mode') {
        // КРИТИЧЕСКИ ВАЖНО: полная изоляция для demo пользователей
        console.log('🧪 Demo пользователь - изоляция данных активна');
        setIikoRmsConnection(prev => ({
          ...prev,
          status: 'not_connected',
          host: null,
          login: null,
          organization_name: null,
          last_connection: null,
          sync_status: null,
          products_count: 0,
          last_sync: null
        }));
      } else if (response.data.status === 'needs_reconnection') {
        setIikoRmsConnection(prev => ({
          ...prev,
          status: 'needs_reconnection',
          host: response.data.host || prev.host,
          login: response.data.login || prev.login,
          error_message: 'Требуется повторная авторизация'
        }));
        
        setIikoRmsMessage({ 
          type: 'warning', 
          text: '⚠️ Подключение к iiko требует повторной авторизации' 
        });
      } else if (response.data.status === 'not_connected') {
        // Используем бэкенд для автоматического восстановления подключения
        // вместо проверки localStorage
        const restoreResponse = await axios.post(`${API}/v1/iiko/rms/restore-connection`, null, {
          params: { user_id: currentUserOrDemo.id }
        });
        
        if (restoreResponse.data.status === 'connected') {
          console.log('✅ Подключение автоматически восстановлено через бэкенд');
          setIikoRmsConnection(prev => ({
            ...prev,
            status: 'connected',
            organization_id: restoreResponse.data.organization_id,
            organization_name: restoreResponse.data.organization_name,
            last_connection: new Date().toISOString()
          }));
        }
      } else {
        // Статус управляется через бэкенд
        console.log('ℹ️ Статус подключения управляется через бэкенд');
      }
    } catch (error) {
      console.error('Error checking iiko RMS status:', error);
      
      // If we get 401/403, show needs reconnection
      if (error.response?.status === 401 || error.response?.status === 403) {
        setIikoRmsConnection(prev => ({
          ...prev,
          status: 'needs_reconnection',
          error_message: 'Сессия истекла, требуется повторная авторизация'
        }));
        
        setIikoRmsMessage({ 
          type: 'warning', 
          text: '⚠️ Сессия истекла. Нужно переподключиться к iiko' 
        });
      }
    }
  };

  // ============== P0: INGREDIENT MODAL SEARCH - wire to iiko ==============
  
  // P0: RU input normalization function
  const normalizeRuInput = (input) => {
    if (!input) return '';
    
    return input
      .trim()                    // Remove spaces
      .toLowerCase()             // Convert to lowercase  
      .replace(/ё/g, 'е')        // ё→е normalization
      .replace(/\s+/g, ' ')      // Collapse multiple spaces
      .trim();                   // Final trim
  };
  
  // P0: Unified iiko search hook
  const useIikoSearch = (orgId = 'default') => {
    const performSearch = async (query, options = {}) => {
      const startTime = Date.now();
      
      if (!query.trim()) {
        return {
          success: true,
          items: [],
          badge: { count: 0, latency: 0, orgId }
        };
      }

      try {
        // P0: Normalize input on frontend
        const normalizedQuery = normalizeRuInput(query);
        
        const response = await axios.get(`${API}/v1/techcards.v2/catalog-search`, {
          params: {
            q: normalizedQuery,
            source: 'iiko',          // P0: Always use iiko source
            orgId: orgId,            // P0: Always send orgId
            limit: options.limit || 5,
            user_id: currentUser?.id || 'demo_user'  // КРИТИЧЕСКИ ВАЖНО: передаем user_id для изоляции данных
          }
        });

        const latency = Date.now() - startTime;

        if (response.data.status === 'success') {
          // P0: Sanitize response - filter elements without name/productId
          const sanitizedItems = (response.data.items || []).filter(item => 
            item && 
            item.name && 
            item.name.trim() && 
            (item.sku_id || item.canonical_id) // Require ID
          );
          
          return {
            success: true,
            items: sanitizedItems,
            badge: {
              count: response.data.iiko_count || 0,
              total_found: response.data.total_found || 0,
              latency,
              orgId,
              connection_status: response.data.iiko_badge?.connection_status || 'unknown'
            },
            raw_response: response.data
          };
        } else {
          console.warn('Search API returned error status:', response.data);
          return {
            success: false,
            items: [],
            badge: { count: 0, latency, orgId },
            error: response.data.message || 'API error'
          };
        }
      } catch (error) {
        const latency = Date.now() - startTime;
        console.error('iiko search error:', error);
        
        return {
          success: false,
          items: [],
          badge: { count: 0, latency, orgId },
          error: error.message
        };
      }
    };
    
    return { performSearch };
  };

  // P0: Enhanced performIikoSearch using unified hook
  const performIikoSearch = async (query) => {
    if (!query.trim()) {
      setIikoSearchResults([]);
      setIikoSearchBadge({ count: 0, latency: 0, orgId: 'default', connection_status: 'not_connected' });
      return;
    }

    setIsSearchingIiko(true);
    
    try {
      // Phase 3: Check if query is article number (4-6 digits)
      const isArticleQuery = /^[0-9]{4,6}$/.test(query);
      
      if (isArticleQuery) {
        // Search by exact article match
        const response = await fetch(`${API}/v1/techcards.v2/catalog-search?q=${encodeURIComponent(query)}&search_by=article&source=iiko&limit=10&user_id=${currentUser?.id || 'demo_user'}`);
        const data = await response.json();
        
        if (data.status === 'success' && data.items.length > 0) {
          setIikoSearchResults(data.items);
          setIikoSearchBadge({
            count: data.items.length,
            latency: data.latency || 0,
            orgId: 'default',
            connection_status: 'connected',
            search_type: 'article_exact'
          });
          return;
        }
      }
      
      // Default text search
      const { performSearch } = useIikoSearch('default');
      const result = await performSearch(query, { limit: 5 });
      
      if (result.success) {
        setIikoSearchResults(result.items);
        setIikoSearchBadge(result.badge);
      } else {
        // P0: Show empty-state on error
        setIikoSearchResults([]);
        setIikoSearchBadge({
          count: 0,
          latency: result.badge.latency,
          orgId: 'default',
          connection_status: 'error',
          error: result.error
        });
      }
    } catch (error) {
      console.error('Unified iiko search error:', error);
      setIikoSearchResults([]);
      setIikoSearchBadge({ 
        count: 0, 
        latency: 0, 
        orgId: 'default', 
        connection_status: 'error',
        error: error.message 
      });
    } finally {
      setIsSearchingIiko(false);
    }
  };

  // ============== ENHANCED AUTO-MAPPING FUNCTIONS (GX-02) ==============
  
  // P1: Advanced actions dropdown with click-outside handling
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showAdvancedActions && !event.target.closest('.advanced-actions-dropdown')) {
        setShowAdvancedActions(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showAdvancedActions]);
  
  // Phase 3: Keyboard shortcut for export (E key)
  useEffect(() => {
    const handleKeyPress = (event) => {
      // Only trigger if not typing in an input field and modal is not open
      if (event.target.tagName !== 'INPUT' && event.target.tagName !== 'TEXTAREA' && 
          !showPhase3ExportModal && !mappingModalOpen && !showExportWizard) {
        if (event.key.toLowerCase() === 'e' && tcV2) {
          event.preventDefault();
          startPhase3Export();
        }
      }
    };
    
    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [tcV2, showPhase3ExportModal, mappingModalOpen, showExportWizard]);
  
  // P0-2: Debounced auto-mapping with 600ms delay
  const [autoMappingDebounceTimer, setAutoMappingDebounceTimer] = useState(null);
  
  const debouncedStartAutoMapping = useCallback(() => {
    // P0-2: Clear existing timer
    if (autoMappingDebounceTimer) {
      clearTimeout(autoMappingDebounceTimer);
    }
    
    // P0-2: Set new 600ms debounce timer
    const timer = setTimeout(() => {
      startEnhancedAutoMapping();
    }, 600);
    
    setAutoMappingDebounceTimer(timer);
  }, [autoMappingDebounceTimer]); // CRITICAL FIX: Remove cleanup function that caused issues
  
  const startEnhancedAutoMapping = async () => {
    if (!tcV2 || !tcV2.ingredients || tcV2.ingredients.length === 0) {
      setAutoMappingMessage({ type: 'error', text: 'Нет ингредиентов для автомаппинга' });
      return;
    }

    // Check iiko RMS connection для реальных пользователей
    if (currentUser && iikoRmsConnection.status !== 'connected') {
      setAutoMappingMessage({ 
        type: 'error', 
        text: '🔗 Требуется подключение к iiko RMS для автомаппинга. Перейдите в МОЕ ЗАВЕДЕНИЕ → IIKO Подключение.' 
      });
      return;
    }

    // Для демо-пользователей разрешаем автомаппинг без подключения
    const userId = currentUser?.id || 'demo_user';

    // P0-2: Block buttons during request (disable state)
    setIsAutoMapping(true);
    setAutoMappingMessage({ type: 'info', text: '🔄 Запуск безопасного автомаппинга с санитизацией...' });

    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/techcards.v2/mapping/enhanced`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          techcard: tcV2,
          organization_id: iikoRmsConnection.organization_id || 'default',
          auto_apply: false,
          user_id: userId  // КРИТИЧЕСКИ ВАЖНО: передаем user_id для изоляции данных
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (result.status === 'success' && result.mapping_results) {
        const mappingData = result.mapping_results;
        
        // P0-2: COMPREHENSIVE SANITIZATION - ignore null/objects without name/productId
        const sanitizedResults = (mappingData.results || [])
          .filter(result => {
            // P0-2: Filter out null, undefined, or non-object results
            if (!result || typeof result !== 'object') {
              console.warn('P0-2: Filtered out invalid result:', result);
              return false;
            }
            
            // P0-2: Require ingredient_name to exist and be non-empty
            if (!result.ingredient_name || !result.ingredient_name.trim()) {
              console.warn('P0-2: Filtered out result without ingredient_name:', result);
              return false;
            }
            
            // P0-2: If suggestion exists, ensure it has name and ID
            if (result.suggestion) {
              if (!result.suggestion.name || !result.suggestion.name.trim()) {
                console.warn('P0-2: Filtered out suggestion without name:', result.suggestion);
                return false;
              }
              if (!result.suggestion.sku_id && !result.suggestion.canonical_id) {
                console.warn('P0-2: Filtered out suggestion without ID:', result.suggestion);
                return false;
              }
            }
            
            return true;
          })
          .map((result, index) => {
            // CRITICAL FIX: Find the ingredient index in tcV2 by name matching
            const ingredientIndex = tcV2.ingredients.findIndex(ing => 
              ing.name && ing.name.toLowerCase().trim() === result.ingredient_name.toLowerCase().trim()
            );
            
            return {
              ingredient_name: result.ingredient_name,
              original_unit: result.original_unit || 'г',
              status: result.status || 'no_match',
              confidence: Math.round((result.confidence || 0) * 100),
              match_type: result.match_type || 'unknown',
              index: ingredientIndex, // CRITICAL FIX: Add ingredient index for applying changes
              suggestion: result.suggestion ? {
                sku_id: result.suggestion.sku_id,
                name: result.suggestion.name || 'Unnamed Product',
                article: result.suggestion.article || '',
                unit: result.suggestion.unit || 'г',
                price_per_unit: result.suggestion.price_per_unit || 0,
                currency: result.suggestion.currency || 'RUB',
                group_name: result.suggestion.group_name || '',
                source: result.suggestion.source || 'iiko',
                // P0-2: Unit mismatch handling - don't hide, show with label
                unit_mismatch: result.original_unit !== result.suggestion.unit
              } : null,
              alternatives: Array.isArray(result.alternatives) ? result.alternatives.filter(alt => 
                alt && alt.name && alt.name.trim() && (alt.sku_id || alt.canonical_id)
              ) : []
            };
          })
          .filter(result => result.index >= 0); // CRITICAL FIX: Only keep results with valid ingredient index

        // P0-2: Check for empty results and provide guidance
        const stats = mappingData.stats || { auto_accept: 0, review: 0, no_match: 0 };
        const coverage = mappingData.coverage || { potential_coverage_pct: 0 };
        
        // P0-2: Enhanced empty-state logic
        if (stats.auto_accept === 0 && stats.review === 0) {
          setAutoMappingMessage({ 
            type: 'warning', 
            text: '📋 Нет позиций ≥90%. Попробуйте: уточнить жирность, заменить "зелень" на "петрушка/укроп", проверить единицы.' 
          });
          
          setAutoMappingResults([]);
          setShowAutoMappingModal(true);
          
          // P0-2: Log mapping_empty event (without UI crash)
          console.log('📊 mapping_empty:', {
            ingredients_count: tcV2.ingredients.length,
            organization: 'default',
            timestamp: new Date().toISOString(),
            empty_reason: 'no_high_confidence_matches'
          });
          
        } else {
          setAutoMappingResults(sanitizedResults);
          setAutoMappingMessage({ 
            type: 'success', 
            text: `✅ Найдено ${sanitizedResults.length} совпадений. ` +
                  `Автопринятие: ${stats.auto_accept}, На проверку: ${stats.review}. ` +
                  `Потенциальное покрытие: ${coverage.potential_coverage_pct}%`
          });
          setShowAutoMappingModal(true);
        }

        console.log('P0-2: Safe auto-mapping completed:', stats);
        
      } else if (result.status === 'no_products') {
        // P0-2: Handle no products scenario gracefully
        setAutoMappingMessage({ 
          type: 'warning', 
          text: '📋 Номенклатура iiko не найдена. Выполните синхронизацию.' 
        });
        setAutoMappingResults([]);
        setShowAutoMappingModal(true);
        
        // P0-2: Log mapping_empty event
        console.log('📊 mapping_empty:', {
          ingredients_count: tcV2?.ingredients?.length || 0,
          organization: 'default',
          timestamp: new Date().toISOString(),
          empty_reason: 'no_products_in_catalog'
        });
        
      } else {
        throw new Error(result.mapping_results?.message || result.message || 'Unknown mapping error');
      }

    } catch (error) {
      console.error('Enhanced auto-mapping error:', error);
      
      // P0-2: Log mapping_failed event (without crashing UI)
      console.log('📊 mapping_failed:', {
        error: error.message,
        ingredients_count: tcV2?.ingredients?.length || 0,
        timestamp: new Date().toISOString(),
        stack: error.stack
      });
      
      setAutoMappingMessage({ 
        type: 'error', 
        text: `❌ Ошибка автомаппинга: ${error.message}` 
      });
      
      // P0-2: Set empty results to prevent crashes
      setAutoMappingResults([]);
      
    } finally {
      // P0-2: Always re-enable buttons
      setIsAutoMapping(false);
    }
  };

  // ============== LEGACY AUTO-MAPPING FUNCTIONS (IK-02B-FE/02) ==============
  
  const startAutoMapping = async () => {
    // CRITICAL FIX: Check if tcV2 is ready
    if (!tcV2Ready || !tcV2 || !tcV2.ingredients || tcV2.ingredients.length === 0) {
      setAutoMappingMessage({ type: 'error', text: 'Нет ингредиентов для автомаппинга. Сначала сгенерируйте техкарту.' });
      return;
    }

    // CRITICAL FIX: Wait for IIKO connection if needed
    if (iikoRmsConnection.status !== 'connected' || !iikoRmsConnection.products_count) {
      setAutoMappingMessage({ 
        type: 'info', 
        text: '🔄 Ожидание подключения к IIKO RMS...' 
      });
      
      // Wait for IIKO connection with retry
      let retryCount = 0;
      const maxRetries = 10; // 5 seconds total
      
      while (retryCount < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // CRITICAL FIX: Check connection status via API
        try {
          const response = await axios.get(`${API}/v1/iiko/rms/connection/status?user_id=${currentUser?.id || 'demo_user'}`);
          if (response.data.status === 'connected' && response.data.products_count > 0) {
            break; // Connection is ready
          }
        } catch (error) {
          console.warn('Failed to check IIKO status:', error);
        }
        
        retryCount++;
      }
      
      // Final check
      if (iikoRmsConnection.status !== 'connected' || !iikoRmsConnection.products_count) {
        setAutoMappingMessage({ 
          type: 'error', 
          text: 'Подключитесь к iiko RMS и выполните синхронизацию номенклатуры' 
        });
        return;
      }
    }

    // Create backup for undo
    setTcV2Backup(JSON.parse(JSON.stringify(tcV2)));
    
    setIsAutoMapping(true);
    setAutoMappingMessage({ type: 'info', text: '🔄 Поиск совпадений в номенклатуре iiko...' });
    
    const mappingResults = [];
    
    try {
      for (let i = 0; i < tcV2.ingredients.length; i++) {
        const ingredient = tcV2.ingredients[i];
        
        // Skip if preserve existing product code is enabled and ingredient already has product code
        if (preserveExistingProductCode && (ingredient.skuId || ingredient.product_code)) {
          mappingResults.push({
            index: i,
            ingredient: ingredient,
            currentSku: ingredient.skuId,
            currentProductCode: ingredient.product_code,
            currentSource: ingredient.source || 'unknown',
            suggestion: null,
            confidence: 0,
            status: 'skipped',
            reason: 'Уже есть SKU'
          });
          continue;
        }
        
        // Search for candidates
        try {
          const response = await axios.get(`${API}/v1/techcards.v2/catalog-search`, {
            params: {
              q: ingredient.name,
              source: 'rms',
              limit: 5,
              user_id: currentUser?.id || 'demo_user'
            }
          });
          
          const candidates = response.data.items || [];
          
          if (candidates.length > 0) {
            const bestCandidate = candidates[0];
            const confidence = Math.round((bestCandidate.match_score || 0) * 100);
            
            // Check for unit mismatch
            const unitMismatch = ingredient.unit !== bestCandidate.unit;
            
            mappingResults.push({
              index: i,
              ingredient: ingredient,
              currentSku: ingredient.skuId || null,
              currentProductCode: ingredient.product_code || null,
              currentSource: ingredient.source || null,
              suggestion: bestCandidate,
              confidence: confidence,
              status: confidence >= 90 ? 'auto_accept' : confidence >= 75 ? 'review' : 'low_confidence',
              unitMismatch: unitMismatch,
              issues: unitMismatch ? ['unitMismatch'] : []
            });
          } else {
            mappingResults.push({
              index: i,
              ingredient: ingredient,
              currentSku: ingredient.skuId || null,
              currentProductCode: ingredient.product_code || null,
              currentSource: ingredient.source || null,
              suggestion: null,
              confidence: 0,
              status: 'no_match',
              reason: 'Совпадения не найдены'
            });
          }
        } catch (error) {
          console.error(`Error searching for ${ingredient.name}:`, error);
          mappingResults.push({
            index: i,
            ingredient: ingredient,
            currentSku: ingredient.skuId || null,
            currentProductCode: ingredient.product_code || null,
            currentSource: ingredient.source || null,
            suggestion: null,
            confidence: 0,
            status: 'error',
            reason: 'Ошибка поиска'
          });
        }
      }
      
      setAutoMappingResults(mappingResults);
      
      // Calculate stats
      const autoAcceptCount = mappingResults.filter(r => r.status === 'auto_accept').length;
      const reviewCount = mappingResults.filter(r => r.status === 'review').length;
      const noMatchCount = mappingResults.filter(r => r.status === 'no_match').length;
      
      setAutoMappingMessage({ 
        type: 'success', 
        text: `✅ Анализ завершен: ${autoAcceptCount} автоматических, ${reviewCount} на проверку, ${noMatchCount} без совпадений` 
      });
      
      setShowAutoMappingModal(true);
      
    } catch (error) {
      console.error('Auto-mapping error:', error);
      setAutoMappingMessage({ 
        type: 'error', 
        text: `❌ Ошибка автомаппинга: ${error.message}` 
      });
    } finally {
      setIsAutoMapping(false);
    }
  };

  const acceptAutoMappingSuggestion = (resultIndex, accept = true) => {
    try {
      // CRITICAL FIX: Validate input parameters
      if (!Array.isArray(autoMappingResults) || 
          typeof resultIndex !== 'number' || 
          resultIndex < 0 || 
          resultIndex >= autoMappingResults.length) {
        console.error('Invalid resultIndex or autoMappingResults:', { resultIndex, autoMappingResults });
        return;
      }
      
      const updatedResults = [...autoMappingResults];
      
      // CRITICAL FIX: Validate the result object exists
      if (!updatedResults[resultIndex]) {
        console.error('Result at index does not exist:', resultIndex);
        return;
      }
      
      if (accept && updatedResults[resultIndex].suggestion) {
        updatedResults[resultIndex].status = 'accepted';
      } else {
        updatedResults[resultIndex].status = 'rejected';
      }
      
      setAutoMappingResults(updatedResults);
      
    } catch (error) {
      console.error('Error in acceptAutoMappingSuggestion:', error);
      setAutoMappingMessage({ 
        type: 'error', 
        text: '❌ Ошибка при обработке выбора' 
      });
    }
  };

  const applyAutoMappingChanges = async () => {
    const acceptedResults = autoMappingResults.filter(r => r.status === 'accepted' || r.status === 'auto_accept');
    
    if (acceptedResults.length === 0) {
      setAutoMappingMessage({ type: 'error', text: 'Нет изменений для применения' });
      return;
    }

    setAutoMappingMessage({ type: 'info', text: '🔄 Применение изменений...' });
    
    try {
      // CRITICAL FIX: Validate tcV2 and ingredients before processing
      if (!tcV2 || !tcV2.ingredients || !Array.isArray(tcV2.ingredients)) {
        throw new Error('Техкарта не найдена или повреждена');
      }
      
      // Update tcV2 with new SKUs and product codes
      const updatedTcV2 = { ...tcV2 };
      let changesCount = 0;
      
      // MAP-01: Enhanced processing with article lookup and fallback
      for (const result of acceptedResults) {
        // CRITICAL FIX: Validate result data before applying
        if (result.suggestion && 
            typeof result.index === 'number' && 
            result.index >= 0 && 
            result.index < updatedTcV2.ingredients.length &&
            updatedTcV2.ingredients[result.index]) {
          
          const suggestion = result.suggestion;
          let productCode = null;
          
          // MAP-01: Extract article with priority: article > code (but avoid GUID)
          if (suggestion.article) {
            productCode = String(suggestion.article).padStart(5, '0');
          } else if (suggestion.product_code) {
            productCode = suggestion.product_code;
          } else if (suggestion.code && !suggestion.code.includes('-')) {
            // Only use code if it's not a GUID (no hyphens)
            productCode = suggestion.code;
          } else if (suggestion.sku_id && !suggestion.article) {
            // MAP-01: If article missing, make additional request for article by id
            try {
              console.log(`MAP-01: Looking up article for skuId: ${suggestion.sku_id}`);
              const response = await fetch(`${API}/v1/techcards.v2/catalog-search?q=${encodeURIComponent(suggestion.sku_id)}&search_by=id&source=iiko&limit=1`);
              const data = await response.json();
              
              if (data.status === 'success' && data.items.length > 0 && data.items[0].article) {
                productCode = String(data.items[0].article).padStart(5, '0');
                console.log(`MAP-01: Found article ${productCode} for skuId ${suggestion.sku_id}`);
              }
            } catch (error) {
              console.warn('MAP-01: Could not lookup article by skuId:', error);
            }
          }
          
          // Apply mapping with product_code
          updatedTcV2.ingredients[result.index] = {
            ...updatedTcV2.ingredients[result.index],
            skuId: suggestion.sku_id,
            product_code: productCode, // MAP-01: Always save article when available
            source: 'rms'
          };
          changesCount++;
          
          console.log(`MAP-01: Applied mapping for ${result.ingredient_name}: skuId=${suggestion.sku_id}, product_code=${productCode}`);
        } else {
          console.warn('Skipped invalid result:', result);
        }
      }
      
      if (changesCount === 0) {
        throw new Error('Не удалось применить изменения - некорректные данные');
      }
      
      // Apply changes and recalculate
      setTcV2(updatedTcV2);
      
      // Use the existing recalculation function
      await performRecalculation(updatedTcV2);
      
      // 🔥 FIX: Save to MongoDB via PUT API
      try {
        const saveResponse = await axios.put(`${API}/v1/techcards.v2/${currentTechCardId}`, updatedTcV2);
        console.log('✅ Techcard saved to MongoDB:', saveResponse.data);
      } catch (saveError) {
        console.error('❌ Save to MongoDB failed:', saveError);
        setAutoMappingMessage({ 
          type: 'warning', 
          text: `✅ Изменения применены локально, но не сохранены в базе данных. Перезагрузите страницу для сохранения.` 
        });
        return; // Don't show success message if save failed
      }
      
      setAutoMappingMessage({ 
        type: 'success', 
        text: `✅ Применено ${changesCount} изменений с артикулами. Покрытие цен обновлено!` 
      });
      
    } catch (error) {
      console.error('Apply auto-mapping changes error:', error);
      setAutoMappingMessage({ 
        type: 'error', 
        text: `❌ Ошибка применения изменений: ${error.message}` 
      });
    }
    
    setShowAutoMappingModal(false);
    setAutoMappingResults([]);
  };

  const undoAutoMappingChanges = async () => {
    if (!tcV2Backup) {
      setAutoMappingMessage({ type: 'error', text: 'Нет данных для отката' });
      return;
    }

    setAutoMappingMessage({ type: 'info', text: '🔄 Откат изменений...' });
    
    setTcV2(tcV2Backup);
    await performRecalculation(tcV2Backup);
    
    setAutoMappingMessage({ 
      type: 'success', 
      text: '✅ Изменения отменены. Техкарта восстановлена.' 
    });
    
    setTcV2Backup(null);
  };

  const getFilteredAutoMappingResults = () => {
    let filtered = autoMappingResults;
    
    // Filter out invalid results - исправляем структуру данных
    filtered = filtered.filter(r => r && (r.ingredient_name || (r.ingredient && r.ingredient.name)));
    
    // Apply filter
    switch (autoMappingFilter) {
      case 'no_product_code':
        filtered = filtered.filter(r => !r.currentSku && !r.currentProductCode);
        break;
      case 'low_confidence':
        filtered = filtered.filter(r => r.confidence > 0 && r.confidence < 90);
        break;
      default:
        break;
    }
    
    // Apply search - исправляем доступ к имени ингредиента
    if (autoMappingSearch) {
      filtered = filtered.filter(r => {
        const ingredientName = r.ingredient_name || (r.ingredient && r.ingredient.name) || '';
        return ingredientName.toLowerCase().includes(autoMappingSearch.toLowerCase());
      });
    }
    
    console.log('Filtered auto-mapping results:', filtered);
    
    return filtered;
  };

  // GX-02: Quality Validation Functions
  const validateTechCardQuality = async (techcard = null) => {
    setIsValidatingQuality(true);
    const cardToValidate = techcard || tcV2;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/techcards.v2/validate/quality`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ techcard: cardToValidate })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const result = await response.json();
      
      setQualityScore(result.quality_score);
      setQualityBanners(result.fix_banners || []);
      
      // Auto-normalize if enabled and needed
      if (autoNormalize && result.normalized_techcard && !result.is_production_ready) {
        const normalizationIssues = result.validation_issues.filter(i => i.type === 'rangeNormalized');
        if (normalizationIssues.length > 0) {
          setTcV2(result.normalized_techcard);
          console.log('GX-02: Auto-normalized', normalizationIssues.length, 'range values');
        }
      }
      
      return result;
      
    } catch (error) {
      console.error('Quality validation error:', error);
      setQualityBanners([{
        type: 'error',
        title: 'Ошибка валидации',
        icon: '🚨',
        color: 'red',
        messages: [`Не удалось проверить качество: ${error.message}`],
        action: 'Повторить попытку'
      }]);
    } finally {
      setIsValidatingQuality(false);
    }
  };

  const normalizeTechCardRanges = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/techcards.v2/normalize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ techcard: tcV2 })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.normalized_techcard) {
        setTcV2(result.normalized_techcard);
        
        const normalizedCount = result.normalization_issues?.length || 0;
        if (normalizedCount > 0) {
          // Show success message
          const message = `✅ Нормализовано ${normalizedCount} значений диапазонов`;
          // You can add a success banner here
          console.log('GX-02:', message);
        }
      }
      
      return result;
      
    } catch (error) {
      console.error('Normalization error:', error);
      throw error;
    }
  };

  const getQualityScoreOnly = async (techcard = null) => {
    const cardToValidate = techcard || tcV2;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/techcards.v2/quality/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ techcard: cardToValidate })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const result = await response.json();
      return result;
      
    } catch (error) {
      console.error('Quality score error:', error);
      throw error;
    }
  };

  // Auto-validate quality when tcV2 changes
  React.useEffect(() => {
    if (tcV2 && tcV2.ingredients && tcV2.ingredients.length > 0) {
      // Mark tcV2 as ready
      setTcV2Ready(true);
      
      // Debounced quality validation
      const timer = setTimeout(() => {
        validateTechCardQuality();
      }, 1000); // 1 second delay to avoid too frequent calls
      
      return () => clearTimeout(timer);
    } else {
      setTcV2Ready(false);
    }
  }, [tcV2]);

  // P0-2: Safe "Принять ≥90%" with comprehensive protection
  const acceptAllHighConfidence = () => {
    // P0-2: Block if already processing
    if (isAutoMapping) {
      console.warn('P0-2: Auto-mapping already in progress, ignoring accept request');
      return;
    }
    
    if (!autoMappingResults || autoMappingResults.length === 0) {
      setAutoMappingMessage({ 
        type: 'warning', 
        text: '⚠️ Нет результатов автомаппинга для принятия' 
      });
      return;
    }
    
    // P0-2: Comprehensive sanitization and filtering
    const highConfidenceResults = autoMappingResults.filter(result => {
      // P0-2: Sanitize - ensure result exists and has required fields
      if (!result || typeof result !== 'object') {
        console.warn('P0-2: Filtered invalid result in accept:', result);
        return false;
      }
      if (!result.suggestion || !result.suggestion.sku_id || !result.suggestion.name) {
        console.warn('P0-2: Filtered result without valid suggestion:', result);
        return false;
      }
      
      return (result.status === 'auto_accept' || result.confidence >= 90) && 
             result.status !== 'accepted';
    });
    
    if (highConfidenceResults.length === 0) {
      // P0-2: Show specific empty-state toast
      setAutoMappingMessage({ 
        type: 'info', 
        text: '📋 Нет позиций ≥90% или все высоко-уверенные совпадения уже приняты' 
      });
      return;
    }
    
    // P0-2: Block buttons during processing
    setIsAutoMapping(true);
    
    try {
      // P0-2: Enhanced logging for audit
      const mappingAction = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        action: 'accept_high_confidence',
        user: 'user@example.com',
        techcard: tcV2?.meta?.title || 'untitled',
        ingredients_count: highConfidenceResults.length,
        ingredients: highConfidenceResults.map(r => ({
          name: r.ingredient_name,
          sku_id: r.suggestion?.sku_id,
          confidence: r.confidence,
          unit_mismatch: r.suggestion?.unit_mismatch || false
        })),
        undoable: true
      };
      
      // P0-2: Safe state updates with error handling
      try {
        setMappingActionLog(prev => [mappingAction, ...prev.slice(0, 9)]);
        setLastMappingAction(mappingAction);
        
        // Update results to accepted status
        const updatedResults = autoMappingResults.map(result => {
          if (highConfidenceResults.some(hr => hr.ingredient_name === result.ingredient_name)) {
            return { ...result, status: 'accepted' };
          }
          return result;
        });
        
        setAutoMappingResults(updatedResults);
        
        // P0-2: Success toast with unit mismatch info
        const unitMismatchCount = highConfidenceResults.filter(r => r.suggestion?.unit_mismatch).length;
        let successText = `✅ Принято ${highConfidenceResults.length} высоко-уверенных совпадений (≥90%)`;
        
        if (unitMismatchCount > 0) {
          successText += ` (⚠️ ${unitMismatchCount} с несовпадением единиц)`;
        }
        
        setAutoMappingMessage({ 
          type: 'success', 
          text: successText
        });
        
        // P0-2: Safe localStorage update
        try {
          localStorage.setItem('lastMappingAction', JSON.stringify({
            timestamp: mappingAction.timestamp,
            count: highConfidenceResults.length,
            techcard: tcV2?.meta?.title
          }));
        } catch (storageError) {
          console.warn('P0-2: localStorage save failed:', storageError);
        }
        
        console.log(`🎯 P0-2: Safely accepted ${highConfidenceResults.length} high-confidence mappings`);
        
      } catch (stateError) {
        console.error('P0-2: State update error:', stateError);
        setAutoMappingMessage({ 
          type: 'error', 
          text: `❌ Ошибка обновления состояния: ${stateError.message}` 
        });
      }
      
    } catch (error) {
      console.error('P0-2: Error in acceptAllHighConfidence:', error);
      
      // P0-2: Log accept_failed event
      console.log('📊 accept_failed:', {
        error: error.message,
        results_count: highConfidenceResults.length,
        timestamp: new Date().toISOString()
      });
      
      setAutoMappingMessage({ 
        type: 'error', 
        text: `❌ Ошибка принятия совпадений: ${error.message}` 
      });
    } finally {
      // P0-2: Always re-enable buttons
      setIsAutoMapping(false);
    }
  };

  // UX-Polish: Undo last mapping action
  const undoLastMappingAction = () => {
    if (!lastMappingAction || !lastMappingAction.undoable) {
      setAutoMappingMessage({ 
        type: 'warning', 
        text: '⚠️ Нет действий для отмены' 
      });
      return;
    }
    
    // Find ingredients from last action and revert their status
    const ingredientsToUndo = lastMappingAction.ingredients.map(ing => ing.name);
    
    const updatedResults = autoMappingResults.map(result => {
      if (ingredientsToUndo.includes(result.ingredient_name) && result.status === 'accepted') {
        // Revert to original status based on confidence
        const originalStatus = result.confidence >= 90 ? 'auto_accept' : 'review';
        return { ...result, status: originalStatus };
      }
      return result;
    });
    
    setAutoMappingResults(updatedResults);
    
    // Mark action as undone
    setLastMappingAction({ ...lastMappingAction, undoable: false });
    
    setAutoMappingMessage({ 
      type: 'info', 
      text: `↩️ Отменено принятие ${lastMappingAction.ingredients_count} ингредиентов` 
    });
    
    console.log('🔄 UX-Polish: Undid last mapping action:', lastMappingAction.ingredients_count);
  };

  // ============== EXPORT WIZARD FUNCTIONS (IK-02B-FE/03) ==============
  
  const startExportWizard = async () => {
    if (!tcV2) {
      setExportMessage({ type: 'error', text: 'Нет техкарты для экспорта' });
      return;
    }

    // Create backup for undo
    setTcV2Backup(JSON.parse(JSON.stringify(tcV2)));
    
    // Reset wizard state
    setExportWizardStep(1);
    setExportWizardData({
      preCheckResults: null,
      autoMappingResults: null,
      coverageBefore: null,
      coverageAfter: null,
      exportUrl: null,
      stepTimings: { start: Date.now() },
      lastExport: null
    });
    setExportMessage({ type: '', text: '' });
    
    // Fetch last export info and perform pre-checks
    await fetchLastExportInfo();
    performPreChecks();
    
    setShowExportWizard(true);
  };

  const fetchLastExportInfo = async () => {
    try {
      const response = await fetch(`${API}/v1/techcards.v2/export/last?organization_id=${iikoRmsConnection.organization_id || 'default'}&techcard_id=${tcV2?.meta?.id || 'temp'}`);
      if (response.ok) {
        const data = await response.json();
        setExportWizardData(prev => ({
          ...prev,
          lastExport: data.last_export
        }));
      }
    } catch (error) {
      console.error('Failed to fetch last export info:', error);
    }
  };

  const performPreChecks = () => {
    const startTime = Date.now();
    
    try {
      const results = {
        iikoConnected: iikoRmsConnection.status === 'connected',
        iikoItemsCount: iikoRmsConnection.products_count || 0,
        priceCoverage: tcV2.costMeta?.coveragePct || 0,
        nutritionCoverage: tcV2.nutritionMeta?.coveragePct || 0,
        issuesCount: tcV2.issues?.length || 0,
        ingredientsCount: tcV2.ingredients?.length || 0,
        ingredientsWithoutSku: tcV2.ingredients?.filter(ing => !ing.skuId).length || 0,
        blockers: [],
        warnings: []
      };
      
      // Check for blockers
      if (!results.iikoConnected) {
        results.blockers.push('Нет подключения к iiko RMS');
      }
      
      if (tcV2.status !== 'success' && tcV2.status !== 'READY' && tcV2.issues?.some(issue => 
        issue.type === 'ruleError' || issue.type === 'missingAnchor'
      )) {
        results.blockers.push('Критические ошибки в техкарте');
      }
      
      // Check for warnings
      if (tcV2.ingredients?.some(ing => ing.unit !== ing.expectedUnit)) {
        results.warnings.push('Несоответствие единиц измерения');
      }
      
      if (results.priceCoverage < 90) {
        results.warnings.push(`Низкое покрытие цен: ${results.priceCoverage}%`);
      }
      
      if (results.nutritionCoverage < 90) {
        results.warnings.push(`Низкое покрытие БЖУ: ${results.nutritionCoverage}%`);
      }
      
      setExportWizardData(prev => ({
        ...prev,
        preCheckResults: results,
        coverageBefore: {
          price: results.priceCoverage,
          nutrition: results.nutritionCoverage
        },
        stepTimings: { 
          ...prev.stepTimings, 
          preCheck: Date.now() - startTime 
        }
      }));
      
    } catch (error) {
      console.error('Pre-check error:', error);
      setExportMessage({ 
        type: 'error', 
        text: `Ошибка предпроверки: ${error.message}` 
      });
    }
  };

  const runExportAutoMapping = async () => {
    setIsExportProcessing(true);
    setExportMessage({ type: 'info', text: '🔄 Выполняется автомаппинг...' });
    
    const startTime = Date.now();
    
    try {
      // Reuse auto-mapping logic from IK-02B-FE/02
      const mappingResults = [];
      
      for (let i = 0; i < tcV2.ingredients.length; i++) {
        const ingredient = tcV2.ingredients[i];
        
        // Skip if ingredient already has SKU (preserve existing)
        if (ingredient.skuId) {
          mappingResults.push({
            index: i,
            ingredient: ingredient,
            currentSku: ingredient.skuId,
            currentProductCode: ingredient.product_code,
            suggestion: null,
            confidence: 0,
            status: 'skipped',
            reason: 'Уже есть SKU'
          });
          continue;
        }
        
        try {
          const response = await axios.get(`${API}/v1/techcards.v2/catalog-search`, {
            params: {
              q: ingredient.name,
              source: 'rms',
              limit: 5
            }
          });
          
          const candidates = response.data.items || [];
          
          if (candidates.length > 0) {
            const bestCandidate = candidates[0];
            const confidence = Math.round((bestCandidate.match_score || 0) * 100);
            
            mappingResults.push({
              index: i,
              ingredient: ingredient,
              suggestion: bestCandidate,
              confidence: confidence,
              status: confidence >= 90 ? 'auto_accept' : 'low_confidence',
              unitMismatch: ingredient.unit !== bestCandidate.unit
            });
          } else {
            mappingResults.push({
              index: i,
              ingredient: ingredient,
              suggestion: null,
              confidence: 0,
              status: 'no_match'
            });
          }
        } catch (error) {
          mappingResults.push({
            index: i,
            ingredient: ingredient,
            suggestion: null,
            confidence: 0,
            status: 'error'
          });
        }
      }
      
      // Apply auto-accepted mappings
      const autoAcceptedResults = mappingResults.filter(r => r.status === 'auto_accept');
      
      if (autoAcceptedResults.length > 0) {
        const updatedTcV2 = { ...tcV2 };
        
        autoAcceptedResults.forEach(result => {
          if (result.suggestion) {
            updatedTcV2.ingredients[result.index] = {
              ...updatedTcV2.ingredients[result.index],
              skuId: result.suggestion.sku_id,
              source: 'rms'
            };
          }
        });
        
        setTcV2(updatedTcV2);
        
        // Perform recalculation
        await performRecalculation(updatedTcV2);
        
        // Update coverage after mapping
        const coverageAfter = {
          price: updatedTcV2.costMeta?.coveragePct || 0,
          nutrition: updatedTcV2.nutritionMeta?.coveragePct || 0
        };
        
        setExportWizardData(prev => ({
          ...prev,
          autoMappingResults: mappingResults,
          coverageAfter: coverageAfter,
          stepTimings: { 
            ...prev.stepTimings, 
            autoMapping: Date.now() - startTime 
          }
        }));
        
        setExportMessage({ 
          type: 'success', 
          text: `✅ Автомаппинг завершен: ${autoAcceptedResults.length} позиций замаплено` 
        });
      } else {
        setExportWizardData(prev => ({
          ...prev,
          autoMappingResults: mappingResults,
          coverageAfter: prev.coverageBefore,
          stepTimings: { 
            ...prev.stepTimings, 
            autoMapping: Date.now() - startTime 
          }
        }));
        
        setExportMessage({ 
          type: 'warning', 
          text: '⚠ Автомаппинг не нашел подходящих совпадений' 
        });
      }
      
      // Auto-advance to next step
      setExportWizardStep(3);
      
    } catch (error) {
      console.error('Export auto-mapping error:', error);
      setExportMessage({ 
        type: 'error', 
        text: `❌ Ошибка автомаппинга: ${error.message}` 
      });
    } finally {
      setIsExportProcessing(false);
    }
  };

  const openGostPreview = async () => {
    const startTime = Date.now();
    
    try {
      setExportMessage({ type: 'info', text: '🔄 Подготовка ГОСТ-превью...' });
      
      const response = await fetch(`${API}/v1/techcards.v2/print`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tcV2)
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank');
        
        setExportWizardData(prev => ({
          ...prev,
          stepTimings: { 
            ...prev.stepTimings, 
            gostPreview: Date.now() - startTime 
          }
        }));
        
        setExportMessage({ 
          type: 'success', 
          text: '✅ ГОСТ-превью открыто в новой вкладке' 
        });
      } else {
        throw new Error('Ошибка генерации ГОСТ-превью');
      }
      
    } catch (error) {
      console.error('GOST preview error:', error);
      setExportMessage({ 
        type: 'error', 
        text: `❌ Ошибка ГОСТ-превью: ${error.message}` 
      });
    }
  };

  const performIikoExport = async () => {
    const startTime = Date.now();
    
    try {
      setIsExportProcessing(true);
      setExportMessage({ type: 'info', text: '🔄 Создание файла для iiko...' });
      
      const response = await fetch(`${API}/v1/techcards.v2/export/iiko.xlsx`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tcV2)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      
      // Trigger download
      const link = document.createElement('a');
      link.href = url;
      link.download = `iiko_ttk_${(tcV2?.meta?.title || 'techcard').replace(/[^\wа-яё\s-]/gi, '').replace(/\s+/g, '_')}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Refresh last export info
      await fetchLastExportInfo();
      
      setExportWizardData(prev => ({
        ...prev,
        exportUrl: url,
        stepTimings: { 
          ...prev.stepTimings, 
          export: Date.now() - startTime 
        }
      }));
      
      setExportMessage({ 
        type: 'success', 
        text: '✅ Файл экспортирован! Импортируйте его в iikoWeb → Технологические карты → Импорт' 
      });
      
      // Auto-advance to final step
      setExportWizardStep(4);
      
    } catch (error) {
      console.error('iiko export error:', error);
      setExportMessage({ 
        type: 'error', 
        text: `❌ Ошибка экспорта: ${error.message}` 
      });
    } finally {
      setIsExportProcessing(false);
    }
  };

  const undoExportChanges = async () => {
    if (!tcV2Backup) {
      setExportMessage({ type: 'error', text: 'Нет данных для отката' });
      return;
    }

    setExportMessage({ type: 'info', text: '🔄 Откат изменений...' });
    
    try {
      setTcV2(tcV2Backup);
      await performRecalculation(tcV2Backup);
      
      setExportMessage({ 
        type: 'success', 
        text: '✅ Изменения отменены' 
      });
      
    } catch (error) {
      console.error('Export undo error:', error);
      setExportMessage({ 
        type: 'error', 
        text: `❌ Ошибка отката: ${error.message}` 
      });
    }
  };

  // ============== NEW CATEGORY MANAGEMENT FUNCTIONS ==============
  
  const fetchAllIikoCategories = async (organizationId) => {
    if (!organizationId) {
      alert('Выберите организацию для просмотра категорий');
      return;
    }

    setIsLoadingCategories(true);
    try {
      const response = await axios.get(`${API}/iiko/categories/${organizationId}`);
      
      if (response.data.success) {
        setIikoCategories(response.data.categories || []);
        return response.data;
      } else {
        setIikoCategories([]);
        alert('Не удалось загрузить категории: ' + response.data.error);
        return null;
      }
    } catch (error) {
      console.error('Error fetching IIKo categories:', error);
      alert('Ошибка получения категорий: ' + (error.response?.data?.detail || error.message));
      setIikoCategories([]);
      return null;
    } finally {
      setIsLoadingCategories(false);
    }
  };

  const createAIMenuDesignerCategory = async () => {
    if (!selectedOrganization?.id) {
      alert('Сначала выберите организацию IIKo');
      return;
    }

    setIsCreatingCategory(true);
    setCategoryCreationResult(null);

    try {
      console.log('Creating AI Menu Designer category for organization:', selectedOrganization.id);
      
      const categoryData = {
        name: 'AI Menu Designer',
        organization_id: selectedOrganization.id
      };

      const response = await axios.post(`${API}/iiko/categories/create`, categoryData);
      
      console.log('Category creation response:', response.data);

      if (response.data.success) {
        setCategoryCreationResult({
          success: true,
          message: response.data.message || 'Категория "AI Menu Designer" создана успешно!',
          category: response.data.category,
          already_exists: response.data.already_exists
        });
        
        // Refresh categories list if modal is open
        if (showAllCategoriesModal) {
          await fetchAllIikoCategories(selectedOrganization.id);
        }
        
        // Show success message
        const alertMessage = response.data.already_exists 
          ? '✅ Категория "AI Menu Designer" уже существует в вашей системе IIKo'
          : '✅ Категория "AI Menu Designer" успешно создана в IIKo!';
        alert(alertMessage);
        
      } else {
        setCategoryCreationResult({
          success: false,
          error: response.data.error || 'Неизвестная ошибка при создании категории'
        });
        alert('❌ Ошибка создания категории: ' + (response.data.error || 'Неизвестная ошибка'));
      }
    } catch (error) {
      console.error('Error creating category:', error);
      const errorMessage = error.response?.data?.detail || error.message;
      setCategoryCreationResult({
        success: false,
        error: errorMessage
      });
      alert('❌ Ошибка создания категории: ' + errorMessage);
    } finally {
      setIsCreatingCategory(false);
    }
  };

  const viewAllIikoCategories = async () => {
    if (!selectedOrganization?.id) {
      alert('Сначала выберите организацию IIKo');
      return;
    }

    setShowAllCategoriesModal(true);
    await fetchAllIikoCategories(selectedOrganization.id);
  };

  // ============== NEW TECH CARDS (ASSEMBLY CHARTS) MANAGEMENT FUNCTIONS ==============
  
  const fetchAllAssemblyCharts = async (organizationId) => {
    if (!organizationId) {
      alert('Выберите организацию для просмотра техкарт');
      return;
    }

    setIsLoadingAssemblyCharts(true);
    try {
      const response = await axios.get(`${API}/iiko/assembly-charts/all/${organizationId}`);
      
      if (response.data.success) {
        setAssemblyCharts(response.data.assembly_charts || []);
        return response.data;
      } else {
        setAssemblyCharts([]);
        alert('Не удалось загрузить техкарты: ' + response.data.error);
        return null;
      }
    } catch (error) {
      console.error('Error fetching assembly charts:', error);
      alert('Ошибка получения техкарт: ' + (error.response?.data?.detail || error.message));
      setAssemblyCharts([]);
      return null;
    } finally {
      setIsLoadingAssemblyCharts(false);
    }
  };

  const createAssemblyChart = async (techCardData) => {
    if (!selectedOrganization?.id) {
      alert('Выберите организацию для создания техкарты');
      return null;
    }

    setIsCreatingAssemblyChart(true);
    try {
      // Parse existing tech card or use provided data
      const requestData = {
        name: techCardData.name || assemblyChartData.name,
        description: techCardData.description || assemblyChartData.description,
        ingredients: techCardData.ingredients || assemblyChartData.ingredients,
        preparation_steps: techCardData.preparation_steps || assemblyChartData.preparation_steps,
        organization_id: selectedOrganization.id,
        weight: techCardData.weight || 0,
        price: techCardData.price || 0,
        category_id: techCardData.category_id || ''
      };

      const response = await axios.post(`${API}/iiko/assembly-charts/create`, requestData);
      
      if (response.data.success) {
        alert(`✅ ${response.data.message}`);
        
        // Refresh assembly charts list
        await fetchAllAssemblyCharts(selectedOrganization.id);
        
        // Reset form data
        setAssemblyChartData({
          name: '',
          description: '',
          ingredients: [],
          preparation_steps: []
        });
        
        return response.data;
      } else {
        alert('Ошибка создания техкарты: ' + response.data.error);
        return null;
      }
    } catch (error) {
      console.error('Error creating assembly chart:', error);
      alert('Ошибка создания техкарты: ' + (error.response?.data?.detail || error.message));
      return null;
    } finally {
      setIsCreatingAssemblyChart(false);
    }
  };

  const deleteAssemblyChart = async (chartId) => {
    if (!window.confirm('Вы уверены, что хотите удалить эту техкарту из IIKo?')) {
      return;
    }

    try {
      const response = await axios.delete(`${API}/iiko/assembly-charts/${chartId}`);
      
      if (response.data.success) {
        alert(`✅ ${response.data.message}`);
        
        // Refresh assembly charts list
        if (selectedOrganization?.id) {
          await fetchAllAssemblyCharts(selectedOrganization.id);
        }
      } else {
        alert('Ошибка удаления техкарты: ' + response.data.error);
      }
    } catch (error) {
      console.error('Error deleting assembly chart:', error);
      alert('Ошибка удаления техкарты: ' + (error.response?.data?.detail || error.message));
    }
  };

  const fetchSyncStatus = async () => {
    try {
      const response = await axios.get(`${API}/iiko/tech-cards/sync-status`);
      
      if (response.data.success) {
        setSyncStatus(response.data);
        setShowSyncStatusModal(true);
      } else {
        alert('Ошибка получения статуса синхронизации');
      }
    } catch (error) {
      console.error('Error fetching sync status:', error);
      alert('Ошибка получения статуса: ' + (error.response?.data?.detail || error.message));
    }
  };

  const uploadTechCardAsAssemblyChart = async (techCard) => {
    if (!selectedOrganization?.id) {
      alert('Выберите организацию в модальном окне IIKo');
      return;
    }

    // Parse tech card content to extract structured data
    const parsedData = parseTechCardForUpload(techCard);
    
    const result = await createAssemblyChart({
      name: parsedData.name,
      description: parsedData.description,
      ingredients: parsedData.ingredients,
      preparation_steps: parsedData.steps,
      weight: parsedData.weight,
      price: parsedData.price
    });

    return result;
  };

  const parseTechCardForUpload = (techCard) => {
    // Extract structured data from tech card content
    const content = techCard.content || '';
    const lines = content.split('\n');
    
    let name = techCard.dish_name || 'Новая техкарта';
    let description = '';
    let ingredients = [];
    let steps = [];
    let weight = 0;
    let price = 0;

    let currentSection = '';
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      
      if (trimmedLine.includes('ИНГРЕДИЕНТЫ') || trimmedLine.includes('🥬')) {
        currentSection = 'ingredients';
        continue;
      } else if (trimmedLine.includes('РЕЦЕПТ') || trimmedLine.includes('👨‍🍳')) {
        currentSection = 'steps';
        continue;
      } else if (trimmedLine.includes('ОПИСАНИЕ') || trimmedLine.includes('📝')) {
        currentSection = 'description';
        continue;
      }
      
      if (currentSection === 'ingredients' && trimmedLine && !trimmedLine.includes('💰') && !trimmedLine.includes('⏰')) {
        if (trimmedLine.includes('—') || trimmedLine.includes('-')) {
          const parts = trimmedLine.replace('—', '|').replace('-', '|').split('|');
          if (parts.length >= 2) {
            const ingredientName = parts[0].replace('•', '').trim();
            const amountPart = parts[1].trim();
            
            // Extract amount and unit
            const amountMatch = amountPart.match(/(\d+(?:\.\d+)?)\s*([а-яёa-z]*)/i);
            if (amountMatch) {
              ingredients.push({
                name: ingredientName,
                quantity: parseFloat(amountMatch[1]),
                unit: amountMatch[2] || 'г',
                price: 0
              });
            }
          }
        }
      } else if (currentSection === 'steps' && trimmedLine && !trimmedLine.includes('💡')) {
        if (trimmedLine.match(/^\d+\./)) {
          steps.push(trimmedLine);
        }
      } else if (currentSection === 'description' && trimmedLine) {
        description += (description ? ' ' : '') + trimmedLine;
      }
    }

    return {
      name,
      description: description || `Блюдо создано с помощью AI-Menu-Designer`,
      ingredients,
      steps,
      weight,
      price
    };
  };

  const openAssemblyChartsManager = async () => {
    if (!selectedOrganization?.id) {
      // First open IIKo modal to select organization
      await openIikoIntegration();
      return;
    }

    setShowAssemblyChartsModal(true);
    await fetchAllAssemblyCharts(selectedOrganization.id);
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
        alert('Настройки заведения обновлены успешно!');
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
  // AI Kitchen V1 Recipe Generation
  const generateAiKitchenRecipe = async () => {
    if (!aiKitchenDishName.trim()) {
      alert('Введите название блюда для создания рецепта');
      return;
    }
    
    if (!currentUserOrDemo?.id) {
      alert('Ошибка авторизации пользователя');
      return;
    }
    
    setIsGenerating(true);
    setLoadingType('recipe');
    const progressInterval = simulateProgress('recipe', 120000); // 2 минуты для V1 GPT-4o
    
    try {
      console.log('🍳 [AI-Kitchen] Generating V1 Recipe for:', aiKitchenDishName);
      
      const response = await axios.post(`${API}/v1/generate-recipe`, {
        dish_name: aiKitchenDishName.trim(),
        cuisine: venueProfile?.cuisine || 'европейская',
        restaurant_type: venueProfile?.venueType || 'casual',
        user_id: (currentUser || { id: 'demo_user' }).id
      }, {
        timeout: 90000 // 90 seconds timeout
      });
      
      if (response.data.recipe) {
        // Сохраняем рецепт для AI-кухни
        setAiKitchenRecipe({
          content: response.data.recipe,
          id: response.data.meta?.id || 'temp-id',
          name: aiKitchenDishName.trim(),
          created_at: new Date().toISOString()
        });
        
        console.log('🍳 [AI-Kitchen] V1 Recipe generated successfully');
        
        // Завершаем анимацию
        clearInterval(progressInterval);
        setLoadingProgress(100);
        setLoadingMessage('🍳 Рецепт готов для экспериментов!');
        
        setTimeout(() => {
          setIsGenerating(false);
          setLoadingProgress(0);
          setLoadingMessage('');
          setLoadingType('');
        }, 2000);
        
      } else {
        throw new Error('Пустой ответ от сервера');
      }
      
    } catch (error) {
      console.error('🍳 [AI-Kitchen] Error generating recipe:', error);
      clearInterval(progressInterval);
      setIsGenerating(false);
      setLoadingProgress(0);
      setLoadingMessage('');
      setLoadingType('');
      alert('Ошибка генерации рецепта: ' + (error.response?.data?.detail || error.message));
    }
  };

  const generateRecipeV1 = async () => {
    // Generate V1 Recipe from dish name or existing tech card
    const dishInput = wizardData.dishName || (tcV2?.name) || (techCard?.name);
    const userToUse = currentUser || { id: 'demo_user' };
    if (!dishInput?.trim() || !userToUse?.id) {
      alert('Введите название блюда для создания рецепта V1');
      return;
    }
    
    setIsGenerating(true);
    setLoadingType('recipe');
    const progressInterval = simulateProgress('recipe', 15000);
    
    try {
      console.log('🍳 Generating V1 Recipe for:', dishInput);
      
      const response = await axios.post(`${API}/v1/generate-recipe`, {
        dish_name: dishInput.trim(),
        cuisine: venueProfile?.cuisine || 'европейская',
        restaurant_type: venueProfile?.venue_type || 'casual',
        user_id: userToUse.id
      }, {
        timeout: 90000 // 90 seconds timeout
      });
      
      // Clear any existing tech cards
      setTechCard(response.data.recipe);
      setTcV2(null); // Clear V2 card to show V1
      
      // Завершаем анимацию
      clearInterval(progressInterval);
      setLoadingProgress(100);
      setLoadingMessage('🍳 Рецепт V1 готов!');
      
      setTimeout(() => {
        setIsGenerating(false);
        setLoadingProgress(0);
        setLoadingMessage('');
        setLoadingType('');
        alert('✨ Красивый рецепт V1 создан! Теперь можно использовать AI функции для экспериментов.');
      }, 2000);
      
    } catch (error) {
      console.error('Error generating V1 recipe:', error);
      clearInterval(progressInterval);
      setIsGenerating(false);
      setLoadingProgress(0);
      setLoadingMessage('');
      setLoadingType('');
      alert('Ошибка генерации рецепта V1: ' + (error.response?.data?.detail || error.message));
    }
  };

  const generateSalesScript = async () => {
    // Support V1 recipes, V1 tech cards, V2 tech cards, and AI Kitchen recipes
    const hasCard = techCard || tcV2 || aiKitchenRecipe;
    const userToUse = currentUser || { id: 'demo_user' };
    if (!hasCard || !userToUse?.id) return;
    
    setIsGenerating(true);
    setLoadingType('sales');
    const progressInterval = simulateProgress('sales', 12000);
    
    try {
      // Выбираем данные для анализа - приоритет: AI Kitchen -> V2 -> V1
      const cardData = aiKitchenRecipe ? {
        name: aiKitchenRecipe.name || 'рецепт',
        content: aiKitchenRecipe.content || ''
      } : (tcV2 || techCard);
      console.log('🔍 Sales script request:', { user_id: userToUse.id, tech_card_name: cardData.name });
      const response = await axios.post(`${API}/generate-sales-script`, {
        tech_card: cardData,
        user_id: userToUse.id
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
      alert('Ошибка генерации скрипта продаж');
    }
  };

  const generateFoodPairing = async () => {
    // Support V1 recipes, V1 tech cards, V2 tech cards, and AI Kitchen recipes
    const hasCard = techCard || tcV2 || aiKitchenRecipe;
    if (!hasCard) return;
    
    const userToUse = currentUser || { id: 'demo_user' };
    if (!userToUse?.id) return;
    
    setIsGenerating(true);
    setLoadingType('pairing');
    const progressInterval = simulateProgress('pairing', 12000);
    
    try {
      // Выбираем данные для анализа - приоритет: AI Kitchen -> V2 -> V1
      const cardData = aiKitchenRecipe ? {
        name: aiKitchenRecipe.name || 'рецепт',
        content: aiKitchenRecipe.content || ''
      } : (tcV2 || techCard);
      console.log('🔍 Food pairing request:', { user_id: userToUse.id, tech_card_name: cardData.name });
      const response = await axios.post(`${API}/generate-food-pairing`, {
        tech_card: cardData,
        user_id: userToUse.id
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
    // Support V1 recipes, V1 tech cards, V2 tech cards, and AI Kitchen recipes
    const hasCard = techCard || tcV2 || aiKitchenRecipe;
    const userToUse = currentUser || { id: 'demo_user' };
    if (!hasCard || !userToUse?.id) return;
    
    setIsGenerating(true);
    setLoadingType('photo');
    const progressInterval = simulateProgress('photo', 10000);
    
    try {
      // Выбираем данные для анализа - приоритет: AI Kitchen -> V2 -> V1
      const cardData = aiKitchenRecipe ? {
        name: aiKitchenRecipe.name || 'рецепт',
        content: aiKitchenRecipe.content || ''
      } : (tcV2 || techCard);
      const response = await axios.post(`${API}/generate-photo-tips`, {
        user_id: userToUse.id,
        tech_card: cardData
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
    // Support V1 recipes, V1 tech cards, V2 tech cards, and AI Kitchen recipes
    const hasCard = techCard || tcV2 || aiKitchenRecipe;
    const userToUse = currentUser || { id: 'demo_user' };
    if (!hasCard || !userToUse?.id) return;
    
    setIsGenerating(true);
    setLoadingType('inspiration');
    const progressInterval = simulateProgress('inspiration', 15000);
    
    try {
      // Выбираем данные для анализа - приоритет: AI Kitchen -> V2 -> V1
      const cardData = aiKitchenRecipe ? {
        name: aiKitchenRecipe.name || 'рецепт',
        content: aiKitchenRecipe.content || ''
      } : (tcV2 || techCard);
      
      const response = await axios.post(`${API}/generate-inspiration`, {
        user_id: userToUse.id,
        tech_card: cardData,
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
    // Support V1 recipes, V1 tech cards, V2 tech cards, and AI Kitchen recipes
    const hasCard = techCard || tcV2 || aiKitchenRecipe;
    const userToUse = currentUser || { id: 'demo_user' };
    if (!hasCard || !userToUse?.id) return;
    
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
      // Выбираем данные для анализа - приоритет: AI Kitchen -> V2 -> V1
      const cardData = aiKitchenRecipe ? {
        name: aiKitchenRecipe.name || 'рецепт',
        content: aiKitchenRecipe.content || ''
      } : (tcV2 || techCard);
      const response = await axios.post(`${API}/analyze-finances`, {
        user_id: userToUse.id,
        tech_card: cardData
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
    // Support V1 recipes, V1 tech cards, V2 tech cards, and AI Kitchen recipes
    const hasCard = techCard || tcV2 || aiKitchenRecipe;
    const userToUse = currentUser || { id: 'demo_user' };
    if (!hasCard || !userToUse?.id) return;
    
    setIsImprovingDish(true);
    setLoadingType('improve');
    setLoadingMessage(getImproveDishLoadingMessage());
    setLoadingProgress(0);
    
    const progressInterval = simulateProgress('improve', 6000); // 6 секунд загрузки
    
    try {
      // Выбираем данные для анализа - приоритет: AI Kitchen -> V2 -> V1
      const cardData = aiKitchenRecipe ? {
        name: aiKitchenRecipe.name || 'рецепт',
        content: aiKitchenRecipe.content || ''
      } : (tcV2 || techCard);
      const response = await axios.post(`${API}/improve-dish`, {
        user_id: userToUse.id,
        tech_card: cardData
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
    // Support V1 recipes, V1 tech cards, V2 tech cards, and AI Kitchen recipes
    const hasCard = techCard || tcV2 || aiKitchenRecipe;
    if (!hasCard || !currentUserOrDemo?.id) return;

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

  // Универсальная функция для сохранения AI-результатов как V1 рецепты
  const saveAIResultAsV1 = async (resultContent, resultName, sourceType) => {
    try {
      const response = await axios.post(`${API}/v1/user/save-recipe`, {
        recipe_content: resultContent,
        recipe_name: resultName,
        recipe_type: 'v1',
        source_type: sourceType, // 'inspiration', 'food_pairing', 'sales_script', etc.
        user_id: (currentUser || { id: 'demo_user' }).id
      });
      
      if (response.data.success) {
        alert('Результат успешно сохранен как V1 рецепт в историю! 🎉');
        loadUserTechCards(); // Обновляем историю
        return true;
      } else {
        alert('Ошибка сохранения: ' + (response.data.message || 'Неизвестная ошибка'));
        return false;
      }
    } catch (error) {
      console.error('Error saving AI result as V1:', error);
      alert('Ошибка сохранения: ' + (error.response?.data?.detail || error.message));
      return false;
    }
  };


  // РЕВОЛЮЦИОННОЕ РЕШЕНИЕ: ИНТЕРАКТИВНАЯ ТАБЛИЦА ИНГРЕДИЕНТОВ
  const renderIngredientsTable = (content) => {
    if (isDebugMode) {
      console.log('=== INGREDIENTS TABLE DEBUG ===');
      console.log('tcV2 available:', !!tcV2);
      console.log('tcV2.ingredients available:', tcV2?.ingredients?.length);
    }
    
    // КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Используем tcV2.ingredients вместо парсинга старого текста
    if (tcV2 && tcV2.ingredients && tcV2.ingredients.length > 0) {
      if (isDebugMode) {
        console.log('Using tcV2.ingredients:', tcV2.ingredients);
      }
      
      // Преобразуем tcV2.ingredients в формат для отображения
      const parsedIngredients = tcV2.ingredients.map((ingredient, index) => {
        return {
          id: index,
          name: ingredient.name || 'Неизвестный ингредиент',
          quantity: `${ingredient.brutto_g || ingredient.netto_g || 0} ${ingredient.unit || 'г'}`,
          price: '~0 ₽', // Цену можно добавить позже
          numericPrice: 0,
          // Добавляем данные из tcV2 для автомаппинга
          skuId: ingredient.skuId || null,
          product_code: ingredient.product_code || null,
          canonical_id: ingredient.canonical_id || null
        };
      });
      
      console.log('Parsed tcV2 ingredients:', parsedIngredients);
      
      // Используем parsedIngredients напрямую
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
                        <div className="space-y-1">
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
                          {/* Source badges */}
                          <div className="flex flex-wrap gap-1">
                            {ingredient.skuId ? (
                              // Determine source from skuId pattern or ingredient metadata
                              ingredient.source === 'rms' || ingredient.skuId.includes('rms_') ? (
                                <span className="bg-purple-600 text-white px-1.5 py-0.5 rounded text-xs font-medium">
                                  iiko
                                </span>
                              ) : ingredient.source === 'usda' || ingredient.canonical_id ? (
                                <span className="bg-green-600 text-white px-1.5 py-0.5 rounded text-xs font-medium">
                                  USDA
                                </span>
                              ) : ingredient.source === 'user' ? (
                                <span className="bg-blue-600 text-white px-1.5 py-0.5 rounded text-xs font-medium">
                                  USER
                                </span>
                              ) : ingredient.source === 'catalog' ? (
                                <span className="bg-yellow-600 text-white px-1.5 py-0.5 rounded text-xs font-medium">
                                  CAT
                                </span>
                              ) : (
                                <span className="bg-gray-600 text-white px-1.5 py-0.5 rounded text-xs font-medium">
                                  BOOT
                                </span>
                              )
                            ) : (
                              <span className="bg-red-600 text-white px-1.5 py-0.5 rounded text-xs font-medium">
                                ⚠ no map
                              </span>
                            )}
                          </div>
                        </div>
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
                        <div className="flex justify-center gap-2">
                          <button
                            onClick={() => handleOpenIngredientMapping(index)}
                            className="text-blue-400 hover:text-blue-300 text-sm"
                            title="Редактировать сопоставление"
                          >
                            ✏️
                          </button>
                          <button
                            onClick={() => {
                              const newIngredients = displayIngredients.filter((_, i) => i !== index);
                              setCurrentIngredients(newIngredients);
                            }}
                            className="text-red-400 hover:text-red-300 text-sm"
                            title="Удалить ингредиент"
                          >
                            🗑️
                          </button>
                        </div>
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
      console.log('No ingredients found in tcV2');
      return (
        <div key="ingredients-error" className="bg-gradient-to-r from-red-600/20 to-orange-600/20 border border-red-400/30 rounded-lg p-6 mb-6">
          <h3 className="text-xl font-bold text-red-300 mb-4">ИНГРЕДИЕНТЫ</h3>
          <p className="text-red-300">Ингредиенты не найдены в техкарте. Попробуйте сгенерировать заново.</p>
        </div>
      );
    }
  };

  // V2 Tech Card Editing with AI
  const handleEditTechCardV2 = async () => {
    if (!editInstruction.trim() || !tcV2?.meta?.id) return;

    setIsEditingAI(true);
    try {
      const response = await axios.post(`${API}/edit-tech-card`, {
        tech_card_id: tcV2.meta.id,
        edit_instruction: editInstruction,
        user_id: currentUser?.id || 'demo_user'
      });
      
      if (response.data.success) {
        // Parse the tech_card string back to object for V2 cards
        try {
          const updatedCard = JSON.parse(response.data.tech_card);
          setTcV2(updatedCard);
          setEditInstruction('');
          
          alert('✅ Техкарта обновлена успешно через AI!');
          
          // Update user tech cards list
          await fetchUserHistory();
        } catch (parseError) {
          console.error('Error parsing updated tech card:', parseError);
          alert('✅ Техкарта обновлена, но произошла ошибка при обновлении интерфейса. Перезагрузите страницу.');
        }
      } else {
        alert(`Ошибка редактирования: ${response.data.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error editing V2 tech card:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Неизвестная ошибка';
      alert(`Ошибка при редактировании техкарты: ${errorMessage}`);
    } finally {
      setIsEditingAI(false);
    }
  };

  // Get AI suggestions for improvements
  const getAISuggestions = async () => {
    if (!tcV2?.meta?.id) {
      alert('Нет техкарты для анализа');
      return;
    }

    try {
      setLoadingMessage('Генерирую предложения по улучшению...');
      
      const response = await axios.post(`${API}/techcards.v2/suggest-improvements`, {
        tech_card_id: tcV2.meta.id,
        suggestion_type: 'all'
      });
      
      if (response.data.status === 'success' && response.data.suggestions.length > 0) {
        const suggestionsText = response.data.suggestions.map((s, i) => 
          `${i + 1}. ${s.title}\n${s.suggestion}\nВлияние: ${s.impact}`
        ).join('\n\n');
        
        alert(`🤖 AI ПРЕДЛОЖЕНИЯ ПО УЛУЧШЕНИЮ:\n\n${suggestionsText}`);
      } else {
        alert('AI не смог найти предложений по улучшению для этой техкарты');
      }
    } catch (error) {
      console.error('Error getting AI suggestions:', error);
      alert('Ошибка при получении предложений от AI');
    } finally {
      setLoadingMessage('');
    }
  };

  // V1 Tech Card Editing (existing functionality)
  const handleEditTechCard = async () => {
    if (!editInstruction.trim() || !currentTechCardId) return;

    setIsEditingAI(true);
    try {
      const response = await axios.post(`${API}/edit-tech-card`, {
        tech_card_id: currentTechCardId,
        edit_instruction: editInstruction,
        user_id: currentUser?.id || 'demo_user'
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
      
      // УПРОЩЕНИЕ: Убрали setEditableIngredients и setEditableSteps - функция не используется
      // setEditableIngredients(ingredients);
      // setEditableSteps(steps);
      
    } catch (error) {
      console.error('Error editing tech card:', error);
      alert('Ошибка при редактировании техкарты');
    } finally {
      setIsEditingAI(false);
    }
  };

  // УПРОЩЕНИЕ: Убрали функцию saveIngredientsChanges - редактор ингредиентов не используется
  // const saveIngredientsChanges = () => {
  //   // Rebuild tech card with new ingredients
  //   const lines = techCard.split('\n');
  //   const newLines = [];
  //   let inIngredientsSection = false;
  //   let ingredientIndex = 0;
  //   
  //   for (let i = 0; i < lines.length; i++) {
  //     const line = lines[i];
  //     
  //     if (line.includes('**Ингредиенты:**')) {
  //       inIngredientsSection = true;
  //       newLines.push(line);
  //       
  //       // Add updated ingredients
  //       editableIngredients.forEach(ing => {
  //         newLines.push(`- ${ing.name} — ${ing.quantity} — ${ing.price}`);
  //       });
  //       
  //       // Skip original ingredients
  //       continue;
  //     }
  //     
  //     if (inIngredientsSection && line.startsWith('- ') && line.includes('₽')) {
  //       // Skip original ingredient lines
  //       continue;
  //     }
  //     
  //     if (inIngredientsSection && line.startsWith('**') && line !== '**Ингредиенты:**') {
  //       inIngredientsSection = false;
  //     }
  //     
  //     newLines.push(line);
  //   }
  //   
  //   setTechCard(newLines.join('\n'));
  //   setIsEditingIngredients(false);
  // };

  // УПРОЩЕНИЕ: Убрали функцию saveStepsChanges - редактор этапов не используется
  // const saveStepsChanges = () => {
  //   // Rebuild tech card with new steps
  //   const lines = techCard.split('\n');
  //   const newLines = [];
  //   let inStepsSection = false;
  //   
  //   for (let i = 0; i < lines.length; i++) {
  //     const line = lines[i];
  //     
  //     if (line.includes('**Пошаговый рецепт:**')) {
  //       inStepsSection = true;
  //       newLines.push(line);
  //       newLines.push('');
  //       
  //       // Add updated steps
  //       editableSteps.forEach((step, index) => {
  //         newLines.push(`${index + 1}. ${step}`);
  //       });
  //       
  //       continue;
  //     }
  //     
  //     if (inStepsSection && line.match(/^\d+\./)) {
  //       // Skip original step lines
  //       continue;
  //     }
  //     
  //     if (inStepsSection && line.startsWith('**') && !line.includes('Пошаговый рецепт')) {
  //       inStepsSection = false;
  //     }
  //     
  //     newLines.push(line);
  //   }
  //   
  //   setTechCard(newLines.join('\n'));
  //   setIsEditingSteps(false);
  // };

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
    
    // Check if password is provided (for email/password registration)
    if (!registrationData.password) {
      alert('Пожалуйста, введите пароль (минимум 6 символов)');
      return;
    }
    
    try {
      console.log('Attempting registration with data:', registrationData);
      const response = await axios.post(`${API}/register`, {
        email: registrationData.email,
        name: registrationData.name,
        city: registrationData.city,
        password: registrationData.password
      });
      console.log('Registration successful:', response.data);
      
      // After registration, try to login automatically
      try {
        const loginResponse = await axios.post(`${API}/login`, {
          email: registrationData.email,
          password: registrationData.password
        });
        
        if (loginResponse.data.success) {
          // Save user and token
          setCurrentUser(loginResponse.data.user);
          localStorage.setItem('receptor_user', JSON.stringify(loginResponse.data.user));
          localStorage.setItem('receptor_token', loginResponse.data.token);
          
          // Reset form
          setShowRegistration(false);
          setRegistrationData({ email: '', name: '', city: '', password: '' });
          
          alert('✅ Регистрация выполнена успешно! Добро пожаловать!');
        }
      } catch (loginError) {
        console.error('Auto-login error:', loginError);
        // Registration successful but auto-login failed
        setShowRegistration(false);
        setRegistrationData({ email: '', name: '', city: '', password: '' });
        alert('✅ Регистрация выполнена успешно! Пожалуйста, войдите в систему.');
      }
      
    } catch (error) {
      console.error('Registration error:', error);
      if (error.response?.data?.detail) {
        alert(`Ошибка: ${error.response.data.detail}`);
      } else {
        alert('Ошибка регистрации. Попробуйте еще раз.');
      }
    }
  };

  // Old handleGenerateTechCard removed - using simplified version now

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
    const userToFetch = currentUser || { id: 'demo_user' };
    if (!userToFetch?.id) {
      return;
    }
    
    try {
      const response = await axios.get(`${API}/user-history/${userToFetch.id}`);
      setUserHistory(response.data.history || []);
      
      // Update dashboard stats
      const historyData = response.data.history || [];
      const totalTechCards = historyData.filter(item => !item.is_menu).length;
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
        tokensUsed: userToFetch.monthly_tech_cards_used || 0,
        thisMonthCards
      });
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  // Simple alias for fetchUserHistory to maintain compatibility
  const loadUserTechCards = () => {
    fetchUserHistory();
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('receptor_user');
    setTechCard(null);
    setUserTechCards([]);
  };

  const handlePrintTechCard = async () => {
    if (!tcV2) {
      setGenerationError('Сначала создайте техкарту');
      setGenerationStatus('error');
      return;
    }

    try {
      console.log('[V2] Exporting PDF via GOST template from V2 endpoint');
      const response = await fetch(`${API}/v1/techcards.v2/print`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(tcV2)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const htmlContent = await response.text(); // Get HTML directly instead of JSON
      console.log('[V2] PDF export HTML content received (same as GOST print)');

      if (htmlContent) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(htmlContent);
        printWindow.document.close();
        
        // This is the same GOST template as GOST-print button
        console.log('[V2] PDF export using identical GOST template as GOST-print');
        
        // Wait for content to load then print
        setTimeout(() => {
          printWindow.print();
        }, 500);
      } else {
        throw new Error('No HTML content received');
      }

    } catch (error) {
      console.error('Error printing tech card:', error);
      setGenerationError('Ошибка при печати техкарты: ' + error.message);
      setGenerationStatus('error');
    }
  };

  const handleGostPrint = async () => {
    if (!tcV2) {
      setGenerationError('Сначала создайте техкарту');
      setGenerationStatus('error');
      return;
    }

    try {
      console.log('[V2] Sending GOST print request to V2 endpoint');
      const response = await fetch(`${API}/v1/techcards.v2/print`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(tcV2)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const htmlContent = await response.text(); // Get HTML directly instead of JSON
      console.log('[V2] GOST print HTML content received');

      if (htmlContent) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(htmlContent);
        printWindow.document.close();
        
        // Show draft watermark if status is draft
        if (tcV2.status === 'draft') {
          console.log('[V2] DRAFT watermark should be visible');
        }
        
        console.log('[V2] GOST print using official V2 template');
        
        // Wait for content to load then trigger print dialog
        setTimeout(() => {
          printWindow.print();
        }, 500);
      } else {
        throw new Error('No HTML content received');
      }

    } catch (error) {
      console.error('Error printing GOST tech card:', error);
      setGenerationError('Ошибка при ГОСТ-печати: ' + error.message);
      setGenerationStatus('error');
    }
  };

  const handleIikoExport = async () => {
    if (!tcV2) {
      setGenerationError('Сначала создайте техкарту');
      setGenerationStatus('error');
      return;
    }

    try {
      console.log('Sending IIKo export request to V2 endpoint');
      const response = await fetch(`${API}/v1/techcards.v2/export/iiko`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(tcV2)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Handle file download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `iiko_export_${(tcV2.meta?.title || 'techcard').replace(/[^\wа-яё\s-]/gi, '').replace(/\s+/g, '_')}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      console.log('IIKo export file downloaded successfully');
      // Success feedback - could add a success banner here

    } catch (error) {
      console.error('Error exporting to IIKo:', error);
      setGenerationError('Ошибка при экспорте в iiko: ' + error.message);
      setGenerationStatus('error');
    }
  };

  const handleIikoCsvExport = async () => {
    if (!tcV2) {
      setGenerationError('Сначала создайте техкарту');
      setGenerationStatus('error');
      return;
    }

    try {
      console.log('Sending IIKo CSV export request to V2 endpoint');
      const response = await fetch(`${API}/v1/techcards.v2/export/iiko.csv`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(tcV2)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Handle ZIP file download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `iiko_export_${(tcV2.meta?.title || 'techcard').replace(/[^\wа-яё\s-]/gi, '').replace(/\s+/g, '_')}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      console.log('IIKo CSV export ZIP file downloaded successfully');
      
      // Show success message
      setGenerationError(null);
      setGenerationStatus('success');

    } catch (error) {
      console.error('Error exporting to IIKo CSV:', error);
      setGenerationError('Ошибка при экспорте CSV в iiko: ' + error.message);
      setGenerationStatus('error');
    }
  };

  const handleIikoTtkXlsxExport = async () => {
    if (!tcV2) {
      setGenerationError('Сначала создайте техкарту');
      setGenerationStatus('error');
      return;
    }

    setGenerationError(null);
    setGenerationStatus('success');

    try {
      console.log('[ALT EXPORT XLSX] Starting iiko TTK XLSX export');
      const response = await fetch(`${API}/v1/techcards.v2/export/iiko.xlsx`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(tcV2)
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        
        // Create safe filename with Cyrillic support
        const safeTitle = tcV2.meta?.title?.replace(/[^\wа-яё\s-]/gi, '').replace(/\s+/g, '_') || 'techcard';
        a.href = url;
        a.download = `iiko_ttk_${safeTitle}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        console.log('[ALT EXPORT XLSX] Successfully exported XLSX');
        setGenerationStatus('success');
      } else {
        const errorText = await response.text();
        console.error('[ALT EXPORT XLSX] Export failed:', response.status, errorText);
        setGenerationError(`Ошибка экспорта: ${response.status} ${errorText}`);
        setGenerationStatus('error');
      }
    } catch (error) {
      console.error('[ALT EXPORT XLSX] Export error:', error);
      setGenerationError(`Ошибка экспорта: ${error.message}`);
      setGenerationStatus('error');
    }
  };

  // CREATE EXPORT WIZARD UI: Unified export functions
  const resetExportWizard = () => {
    setSelectedExportType(null);
    setExportProgress(0);
    setExportStatus('idle');
    setCurrentExportStep('');
    setExportResults([]);
  };

  const openExportWizard = () => {
    if (isDebugMode) {
      console.log('🚀 DEBUG: openExportWizard called');
    }
    resetExportWizard();
    if (isDebugMode) {
      console.log('🚀 DEBUG: setting showUnifiedExportWizard to true');
    }
    setShowUnifiedExportWizard(true);
    
    // FIX JS MODAL SCROLL & OPEN BUG: Prevent body scroll when modal opens
    document.body.style.overflow = 'hidden';
    if (isDebugMode) {
      console.log('🚀 DEBUG: body overflow set to hidden');
    }
  };
  
  const closeExportWizard = () => {
    setShowUnifiedExportWizard(false);
    resetExportWizard();
    
    // FIX JS MODAL SCROLL & OPEN BUG: Restore body scroll when modal closes
    document.body.style.overflow = 'unset';
  };

  // FIX JS MODAL SCROLL & OPEN BUG: Handle escape key and focus management
  useEffect(() => {
    const handleEscapeKey = (event) => {
      if (event.key === 'Escape' && showUnifiedExportWizard) {
        closeExportWizard();
      }
    };

    if (showUnifiedExportWizard) {
      document.addEventListener('keydown', handleEscapeKey);
      
      // Focus trap - focus first focusable element in modal
      const modal = document.querySelector('[data-export-wizard-modal]');
      if (modal) {
        const focusableElements = modal.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusableElements.length > 0) {
          focusableElements[0].focus();
        }
      }
    }

    return () => {
      document.removeEventListener('keydown', handleEscapeKey);
      // Cleanup body scroll on unmount
      document.body.style.overflow = 'unset';
    };
  }, [showUnifiedExportWizard]);

  const executeExport = async (exportType) => {
    if (!tcV2) {
      setGenerationError('Сначала создайте техкарту');
      return;
    }

    // FIX JS MODAL SCROLL & OPEN BUG: Prevent multiple simultaneous exports
    if (exportStatus === 'processing') {
      return;
    }

    setSelectedExportType(exportType);
    setExportStatus('processing');
    setExportProgress(10);
    setExportResults([]);
    setGenerationError(null);

    try {
      switch (exportType) {
        case 'xlsx':
          await executeXlsxExport();
          break;
        case 'zip':
          await executeZipExport();
          break;
        case 'pdf':
          await executePdfExport();
          break;
        case 'full_package':
          await executeFullPackageExport();
          break;
        default:
          throw new Error('Unknown export type');
      }
      
      setExportStatus('success');
      setExportProgress(100);
      setCurrentExportStep('Экспорт завершен');
      
    } catch (error) {
      console.error('Export error:', error);
      setExportStatus('error');
      setCurrentExportStep(`Ошибка: ${error.message}`);
      setGenerationError(error.message);
    }
  };

  const executeXlsxExport = async () => {
    try {
      setCurrentExportStep('Создание XLSX файла...');
      setExportProgress(30);
      
      const response = await fetch(`${API}/v1/techcards.v2/export/iiko.xlsx`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tcV2)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Ошибка сервера: ${response.status} ${errorText}`);
      }

      setExportProgress(70);
      const blob = await response.blob();
      
      if (blob.size === 0) {
        throw new Error('Получен пустой файл от сервера');
      }

      const url = window.URL.createObjectURL(blob);
      
      const safeTitle = tcV2.meta?.title?.replace(/[^\w\s-]/g, '').replace(/\s+/g, '_') || 'techcard';
      const filename = `iiko_ttk_${safeTitle}.xlsx`;
      
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setExportResults([{
        type: 'xlsx',
        filename: filename,
        size: blob.size,
        description: 'Техкарта для импорта в iiko'
      }]);
      
    } catch (error) {
      console.error('XLSX export error:', error);
      throw new Error(`XLSX экспорт: ${error.message}`);
    }
  };

  const executeZipExport = async () => {
    try {
      setCurrentExportStep('Запуск префлайт проверки...');
      setExportProgress(20);

      // Run preflight first
      const preflightResponse = await fetch(`${API}/v1/export/preflight`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ techcardIds: [tcV2.meta.id] })
      });

      if (!preflightResponse.ok) {
        const errorText = await preflightResponse.text();
        throw new Error(`Preflight ошибка: ${preflightResponse.status} ${errorText}`);
      }
      
      const preflight = await preflightResponse.json();
      
      // DEBUG: Log preflight result
      console.log('🔍 Preflight result for ZIP export:', preflight);
      console.log('🔍 Missing products:', preflight?.missing_products?.length || 0);
      console.log('🔍 Missing dishes:', preflight?.missing_dishes?.length || 0);

      setCurrentExportStep('Создание ZIP архива...');
      setExportProgress(60);

      const zipPayload = {
        techcardIds: [tcV2.meta.id],
        preflight_result: preflight
      };
      
      console.log('🔍 ZIP export payload:', zipPayload);

      const zipResponse = await fetch(`${API}/v1/export/zip`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(zipPayload)
      });

      if (!zipResponse.ok) {
        const errorText = await zipResponse.text();
        throw new Error(`ZIP ошибка: ${zipResponse.status} ${errorText}`);
      }

      setExportProgress(80);
      const blob = await zipResponse.blob();
      
      if (blob.size === 0) {
        throw new Error('Получен пустой ZIP архив');
      }

      const url = window.URL.createObjectURL(blob);
      
      // Use dish name instead of timestamp for meaningful filename  
      const dishName = tcV2?.meta?.title || 'techcard';
      // Support Cyrillic characters in filename
      const safeTitle = dishName.replace(/[^\wа-яё\s-]/gi, '').replace(/\s+/g, '_');
      const filename = `iiko_export_${safeTitle}.zip`;
      
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setExportResults([{
        type: 'zip',
        filename: filename,
        size: blob.size,
        description: `Номенклатуры для iiko (${preflight.counts?.dishSkeletons || 0} блюд, ${preflight.counts?.productSkeletons || 0} продуктов)`
      }]);
      
    } catch (error) {
      console.error('ZIP export error:', error);
      throw new Error(`ZIP экспорт: ${error.message}`);
    }
  };

  const executePdfExport = async () => {
    try {
      setCurrentExportStep('Генерация PDF файла...');
      setExportProgress(40);

      const response = await fetch(`${API}/v1/techcards.v2/print`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tcV2)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`PDF ошибка: ${response.status} ${errorText}`);
      }

      setExportProgress(70);
      const htmlContent = await response.text();
      
      if (!htmlContent || htmlContent.trim().length === 0) {
        throw new Error('Получен пустой HTML контент');
      }
      
      // Open in new window for printing
      const printWindow = window.open('', '_blank');
      if (!printWindow) {
        throw new Error('Не удалось открыть окно для печати (возможно заблокировано браузером)');
      }
      
      printWindow.document.write(htmlContent);
      printWindow.document.close();
      
      // Trigger print after content loads
      setTimeout(() => {
        try {
          printWindow.print();
        } catch (e) {
          console.warn('Print dialog error:', e);
        }
      }, 1000);

      setExportResults([{
        type: 'pdf',
        filename: `${(tcV2?.meta?.title || 'techcard').replace(/[^\wа-яё\s-]/gi, '').replace(/\s+/g, '_')}.pdf`,
        size: htmlContent.length,
        description: 'Техкарта в PDF формате (без цен для персонала)'
      }]);
      
    } catch (error) {
      console.error('PDF export error:', error);
      throw new Error(`PDF экспорт: ${error.message}`);
    }
  };

  const executeFullPackageExport = async () => {
    try {
      setCurrentExportStep('Подготовка полного пакета...');
      setExportProgress(10);
      
      const results = [];

      // 1. XLSX Export
      setCurrentExportStep('Создание XLSX файла...');
      setExportProgress(25);
      await executeXlsxExport();
      if (exportResults.length > 0) {
        results.push(...exportResults);
      }

      // 2. ZIP Export  
      setCurrentExportStep('Создание ZIP архива...');
      setExportProgress(50);
      await executeZipExport();
      if (exportResults.length > results.length) {
        results.push(...exportResults.slice(results.length));
      }

      // 3. PDF Export (temporarily disabled due to popup blocker issues)
      // setCurrentExportStep('Генерация PDF...');
      // setExportProgress(75);
      // await executePdfExport();
      // if (exportResults.length > results.length) {
      //   results.push(...exportResults.slice(results.length));
      // }

      setExportResults(results);
      setCurrentExportStep('Полный пакет готов');
      
    } catch (error) {
      console.error('Full package export error:', error);
      throw new Error(`Полный пакет: ${error.message}`);
    }
  };

  // Phase 3: FE-04-min Export to iiko (2 steps) functions
  const startPhase3Export = async () => {
    if (!tcV2) return;
    
    setShowPhase3ExportModal(true);
    setPhase3ExportState('running_preflight');
    setPhase3ExportMessage({ type: 'info', text: '🔄 Запуск префлайта...' });
    
    try {
      // Step 1: Run preflight
      await runPreflight();
    } catch (error) {
      console.error('Phase 3 export error:', error);
      setPhase3ExportState('error');
      setPhase3ErrorDetails({
        type: 'NETWORK',
        message: error.message,
        hint: 'Сеть недоступна. Повторите попытку.'
      });
      setPhase3ExportMessage({ 
        type: 'error', 
        text: '❌ Ошибка при запуске экспорта'
      });
    }
  };
  
  const runPreflight = async () => {
    try {
      const response = await fetch(`${API}/v1/export/preflight`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          techcardIds: [currentTechCardId || 'current'],
          organization_id: 'default'
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Preflight result:', data);
      
      setPreflightResult(data);
      setPhase3ExportState('ready_zip');
      
      // Show preflight completion message
      const dishCount = data.counts?.dishSkeletons || 0;
      const productCount = data.counts?.productSkeletons || 0;
      
      setPhase3ExportMessage({
        type: 'success',
        text: `✅ Preflight завершён: скелетов блюд ${dishCount}, товаров ${productCount}`
      });
      
    } catch (error) {
      console.error('Preflight error:', error);
      throw error;
    }
  };
  
  const generateZipExport = async () => {
    if (!preflightResult) return;
    
    setPhase3ExportState('running_preflight'); // Show loading state
    setPhase3ExportMessage({ type: 'info', text: '🔄 Создание ZIP файла...' });
    
    try {
      const response = await fetch(`${API}/v1/export/zip`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          techcardIds: [currentTechCardId || 'current'],
          operational_rounding: true,
          organization_id: iikoRmsConnection.organization_id || 'default',
          preflight_result: preflightResult
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Handle ZIP download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      
      // Extract filename from response headers or create smart filename
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `iiko_export_${(tcV2?.meta?.title || 'techcard').replace(/[^\wа-яё\s-]/gi, '').replace(/\s+/g, '_')}.zip`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
          if (isDebugMode) {
            console.log('🎯 ZIP FILENAME DEBUG: Using server filename:', filename);
          }
        }
      }
      
      // Create download link
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setPhase3ExportState('ready_zip');
      setPhase3ExportMessage({
        type: 'success',
        text: '✅ ZIP готов к скачиванию'
      });
      
      // Claim articles (fire and forget)
      await claimArticles();
      
    } catch (error) {
      console.error('ZIP export error:', error);
      setPhase3ExportState('error');
      setPhase3ErrorDetails({
        type: 'NETWORK',
        message: error.message,
        hint: 'Ошибка создания ZIP файла. Повторите попытку.'
      });
      setPhase3ExportMessage({
        type: 'error',
        text: '❌ Ошибка создания ZIP файла'
      });
    }
  };
  
  const claimArticles = async () => {
    if (!preflightResult) return;
    
    try {
      const allArticles = [
        ...(preflightResult.generated?.dishArticles || []),
        ...(preflightResult.generated?.productArticles || [])
      ];
      
      if (allArticles.length === 0) return;
      
      const response = await fetch(`${API}/v1/techcards.v2/articles/claim`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          articles: allArticles,
          organization_id: 'default'
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Articles claimed:', data);
      }
      
    } catch (error) {
      console.warn('Error claiming articles:', error);
      // Don't throw - this is a background operation
    }
  };
  
  const resetPhase3Export = () => {
    setPhase3ExportState('idle');
    setPreflightResult(null);
    setPhase3ExportMessage({ type: '', text: '' });
    setZipDownloadUrl(null);
    setPhase3ErrorDetails(null);
  };
  
  const closePhase3ExportModal = () => {
    setShowPhase3ExportModal(false);
    resetPhase3Export();
  };
  
  const downloadTtkOnly = async () => {
    if (!preflightResult) return;
    
    // Guard — dish-first rule: Double-check no dish skeletons needed
    if (preflightResult.counts?.dishSkeletons > 0) {
      setPhase3ErrorDetails({
        type: 'DISH_GUARD_VIOLATION',
        message: 'TTK-only экспорт заблокирован',
        hint: 'Сначала импортируйте скелеты блюд в iiko, затем попробуйте снова'
      });
      setPhase3ExportState('error');
      return;
    }
    
    setPhase3ExportMessage({ type: 'info', text: '🔄 Создание TTK файла...' });
    
    try {
      const response = await fetch(`${API}/v1/export/ttk-only`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          techcardIds: [currentTechCardId || 'current'],
          operational_rounding: true,
          organization_id: 'default'
        })
      });
      
      if (!response.ok) {
        // Handle guard response
        if (response.status === 403) {
          const errorData = await response.json();
          if (errorData.error === 'PRE_FLIGHT_REQUIRED') {
            setPhase3ErrorDetails({
              type: 'PRE_FLIGHT_REQUIRED',
              message: errorData.message,
              hint: errorData.details || 'Используйте ZIP экспорт для получения скелетов блюд'
            });
            setPhase3ExportState('error');
            return;
          }
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Handle TTK file download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      
      // Extract filename from response headers or create smart filename
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `iiko_TTK_${(tcV2?.meta?.title || 'techcard').replace(/[^\wа-яё\s-]/gi, '').replace(/\s+/g, '_')}.xlsx`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
          if (isDebugMode) {
            console.log('🎯 TTK FILENAME DEBUG: Using server filename:', filename);
          }
        }
      }
      
      // Create download link
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setPhase3ExportMessage({
        type: 'success',
        text: '✅ TTK файл скачан успешно'
      });
      
    } catch (error) {
      console.error('TTK-only export error:', error);
      setPhase3ErrorDetails({
        type: 'NETWORK',
        message: error.message,
        hint: 'Ошибка скачивания TTK файла. Попробуйте ZIP экспорт.'
      });
      setPhase3ExportState('error');
      setPhase3ExportMessage({
        type: 'error',
        text: '❌ Ошибка скачивания TTK файла'
      });
    }
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
        setWizardData(prev => ({...prev, dishName: transcript}));
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
    // fetchCities(); // УПРОЩЕНИЕ: Убрали - город больше не нужен
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
    
    // Load HACCP Pro setting
    const savedHaccpPro = localStorage.getItem('haccp_pro_enabled');
    if (savedHaccpPro) {
      setHaccpProEnabled(JSON.parse(savedHaccpPro));
    }
  }, []);

  // Fetch subscription data when user changes
  useEffect(() => {
    if (currentUser?.id) {
      fetchUserSubscription();
      fetchUserHistory();
      fetchUserPrices();
      fetchVenueProfile();
    }
  }, [currentUser?.id]);

  useEffect(() => {
    if (currentUserOrDemo && currentView === 'dashboard') {
      fetchUserHistory();
    }
    // Load projects when user is available
    if (currentUserOrDemo && menuProjects.length === 0) {
      fetchMenuProjects();
    }
  }, [currentView, currentUser]);

  // Save HACCP Pro setting to localStorage
  useEffect(() => {
    localStorage.setItem('haccp_pro_enabled', JSON.stringify(haccpProEnabled));
  }, [haccpProEnabled]);

  // Auto HACCP generation hook - ОТКЛЮЧЕНО
  useEffect(() => {
    return; // ПОЛНОСТЬЮ ОТКЛЮЧЕНО
    if (!FEATURE_HACCP) return;
    if (!haccpProEnabled || !techCard || isAutoGeneratingHaccp) return;
    
    // Debounce HACCP generation by 2 seconds after tech card changes
    const timeout = setTimeout(async () => {
      try {
        console.log('Auto-generating HACCP...');
        setIsAutoGeneratingHaccp(true);
        
        // Parse tech card content to create a simple structure for the API
        const cardData = {
          meta: {
            name: techCard.match(/\*\*Название:\*\*\s*(.*?)(?=\n|$)/)?.[1]?.trim() || "Блюдо",
            category: techCard.match(/\*\*Категория:\*\*\s*(.*?)(?=\n|$)/)?.[1]?.trim() || "Основные блюда",
            cuisine: "международная"
          },
          ingredients: [], // Simplified for now
          process: [], // Simplified for now
          yield: {
            portions: 4,
            per_portion_g: 250,
            total_net_g: 1000
          },
          haccp: {
            hazards: [],
            ccp: [],
            storage: null
          },
          allergens: []
        };

        const response = await fetch(`${API}/v1/haccp.v2/generate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(cardData),
        });

        if (response.ok) {
          const haccpData = await response.json();
          setCurrentTechCardHaccp(haccpData.haccp);
          console.log('HACCP auto-generated successfully:', haccpData.haccp);
        } else {
          console.log('HACCP auto-generation failed:', response.statusText);
        }
      } catch (error) {
        console.error('Error auto-generating HACCP:', error);
      } finally {
        setIsAutoGeneratingHaccp(false);
      }
    }, 2000);

    return () => clearTimeout(timeout);
  }, [FEATURE_HACCP, haccpProEnabled, techCard, isAutoGeneratingHaccp]);

  // IK-04/02: XLSX Import Functions
  const handleXlsxFileDrop = async (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = e.dataTransfer ? e.dataTransfer.files : e.target.files;
    if (files.length > 0) {
      const file = files[0];
      
      // Validate file type
      if (!file.name.toLowerCase().endsWith('.xlsx') && !file.name.toLowerCase().endsWith('.xls')) {
        alert('Пожалуйста, выберите XLSX файл');
        return;
      }
      
      setXlsxFile(file);
      await generateXlsxPreview(file);
    }
  };

  const generateXlsxPreview = async (file) => {
    try {
      // Simple preview - just show file info for now
      // Full XLSX parsing would require additional libraries
      setXlsxPreview({
        fileName: file.name,
        fileSize: (file.size / 1024).toFixed(1) + ' KB',
        lastModified: new Date(file.lastModified).toLocaleDateString(),
        type: 'Excel файл техкарты iiko'
      });
    } catch (error) {
      console.error('Error generating XLSX preview:', error);
      setXlsxPreview({
        fileName: file.name,
        fileSize: (file.size / 1024).toFixed(1) + ' KB',
        error: 'Не удалось создать предпросмотр'
      });
    }
  };

  const importXlsxTechcard = async () => {
    if (!xlsxFile) return;
    
    // UX-Polish: Reset states and start progress tracking
    setXlsxImportProgress(true);
    setXlsxImportResults(null);
    setXlsxImportErrors([]);
    setXlsxImportWarnings([]);
    
    try {
      // Stage 1: Parsing XLSX
      setXlsxImportStage('parsing');
      await new Promise(resolve => setTimeout(resolve, 500)); // UI feedback delay
      
      const formData = new FormData();
      formData.append('file', xlsxFile);
      
      // Stage 2: Validation
      setXlsxImportStage('validation');
      await new Promise(resolve => setTimeout(resolve, 300));
      
      const response = await fetch(`${BACKEND_URL}/api/v1/iiko/import/ttk.xlsx`, {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      // Stage 3: Conversions  
      setXlsxImportStage('conversions');
      await new Promise(resolve => setTimeout(resolve, 300));
      
      const result = await response.json();
      
      // Stage 4: Tech extraction
      setXlsxImportStage('extraction');
      await new Promise(resolve => setTimeout(resolve, 400));
      
      // Process issues into errors and warnings
      const issues = result.issues || [];
      const errors = issues.filter(issue => issue.level === 'error');
      const warnings = issues.filter(issue => issue.level === 'warning');
      
      setXlsxImportErrors(errors);
      setXlsxImportWarnings(warnings);
      
      // Stage 5: Done
      setXlsxImportStage('done');
      setXlsxImportResults(result);
      
      if (result.status === 'success' || result.status === 'draft' || result.status === 'READY') {
        // Success - set the imported techcard
        setTcV2(result.techcard);
        
        // Auto-mapping if enabled
        if (xlsxAutoMapping && result.status === 'success') {
          try {
            await performRecalculation();
          } catch (recalcError) {
            console.warn('Auto recalculation after import failed:', recalcError);
          }
        }
        
        // Close modal after showing results
        setTimeout(() => {
          setShowXlsxImportModal(false);
          resetXlsxImport();
        }, 3000);
        
      } else {
        // Handle error status
        console.error('XLSX import failed:', result);
      }
      
    } catch (error) {
      console.error('XLSX import error:', error);
      setXlsxImportStage('error');
      
      // Create user-friendly error message
      let errorMessage = `Ошибка импорта: ${error.message}`;
      let errorSuggestion = '';
      
      if (error.message.includes('HTTP 413') || error.message.includes('too large')) {
        errorMessage = 'Файл слишком большой';
        errorSuggestion = 'Попробуйте файл размером менее 10 МБ';
      } else if (error.message.includes('HTTP 415') || error.message.includes('Unsupported')) {
        errorMessage = 'Неподдерживаемый формат файла';
        errorSuggestion = 'Убедитесь что файл имеет расширение .xlsx';
      } else if (error.message.includes('HTTP 422')) {
        errorMessage = 'Некорректная структура файла';
        errorSuggestion = 'Проверьте что файл содержит данные техкарты в правильном формате';
      }
      
      setXlsxImportResults({
        status: 'error',
        issues: [{
          code: 'importFailed',
          level: 'error',
          msg: errorMessage,
          suggestion: errorSuggestion
        }],
        meta: { source: 'error' }
      });
      
      setXlsxImportErrors([{
        code: 'importFailed',
        level: 'error', 
        msg: errorMessage,
        suggestion: errorSuggestion
      }]);
      
    } finally {
      setXlsxImportProgress(false);
    }
  };

  const resetXlsxImport = () => {
    setXlsxFile(null);
    setXlsxPreview(null);
    setXlsxImportProgress(false);
    setXlsxImportResults(null);
    setXlsxAutoMapping(false);
    setIsDragOver(false);
    
    // UX-Polish: Reset enhanced states
    setXlsxImportStage('idle');
    setXlsxImportErrors([]);
    setXlsxImportWarnings([]);
  };

  // централизованная функция закрытия модалок
  const closeAllModals = React.useCallback(() => {
    if (isDebugMode) {
      console.log('closeAllModals called');
    }
    setShowRegistration(false);
    setShowPricingModal(false);
    setShowEquipmentModal(false);

    setShowPriceModal(false);
    setShowInstructions(false);
    setShowProAIModal(false);
    setShowSalesScriptModal(false);
    setShowFoodPairingModal(false);
    setShowPhotoTipsModal(false);
    setShowInspirationModal(false);
    setShowFinancesModal(false);
    setShowImproveDishModal(false);
    setShowLaboratoryModal(false);
    setShowVenueProfileModal(false);
    setShowMenuWizard(false);
    setShowMassGenerationModal(false);
    setShowMenuGenerationModal(false);
    setShowSimpleMenuModal(false);
    setShowProjectsModal(false);
    setShowCreateProjectModal(false);
    setShowProjectContentModal(false);
    setShowAnalyticsModal(false);
    setShowIikoModal(false);
    setShowUploadTechCardModal(false);
    setShowSyncMenuModal(false);
    setShowCategoryViewer(false);
    setShowAllCategoriesModal(false);
    setShowAssemblyChartsModal(false);
    // IK-04/02: Close XLSX import modal
    setShowXlsxImportModal(false);
    setShowCreateAssemblyChartModal(false);
  }, []);

  // ESC listener который не черствеет
  useEffect(() => {
    const onKey = (e) => { 
      if (isDebugMode) {
        console.log('Key pressed:', e.key);
      }
      if (e.key === 'Escape') {
        if (isDebugMode) {
          console.log('ESC pressed, closing modals');
        }
        e.preventDefault();
        e.stopPropagation();
        closeAllModals(); 
      }
    };
    document.addEventListener('keydown', onKey, { capture: true });
    return () => document.removeEventListener('keydown', onKey, { capture: true });
  }, [closeAllModals]);

  // Load user history when switching to techcards view
  useEffect(() => {
    const userToCheck = currentUser || { id: 'demo_user' };
    if (currentView === 'techcards' && userToCheck?.id) {
      fetchUserHistory();
    }
  }, [currentView, currentUser?.id]);

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
    
    // Запускаем анимацию прогресса с увеличенным временем для большего количества этапов
    const progressInterval = simulateProgress('menu', 35000); // 35 секунд анимации
    
    // Запускаем смену меню лайфхаков каждые 2.5 секунды (чаще, чем раньше)
    setCurrentMenuTipIndex(0);
    const tipInterval = setInterval(() => {
      setCurrentMenuTipIndex(prev => (prev + 1) % menuGenerationTips.length);
    }, 2500);
    
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
        clearInterval(tipInterval);
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
      clearInterval(tipInterval);
      
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
        setMenuProjects(response.data.projects || []);
      } else {
        // Graceful fallback - just set empty array
        console.warn('Menu projects response not successful, using empty array');
        setMenuProjects([]);
      }
    } catch (error) {
      console.error('Error fetching menu projects:', error);
      // Graceful fallback instead of alert
      console.warn('Failed to load projects, using empty array');
      setMenuProjects([]);
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
        alert('Проект успешно создан!');
        
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

  // NEW: Enhanced project content and analytics functions
  const viewProjectContent = async (project) => {
    setSelectedProject(project);
    setShowProjectContentModal(true);
    setProjectContent(null);
    setProjectAnalytics(null);
    
    // Load project content
    setIsLoadingProjectContent(true);
    try {
      const response = await axios.get(`${API}/menu-project/${project.id}/content`);
      if (response.data.success) {
        setProjectContent(response.data);
      } else {
        throw new Error('Failed to load project content');
      }
    } catch (error) {
      console.error('Error loading project content:', error);
      alert('Ошибка загрузки содержимого проекта');
    } finally {
      setIsLoadingProjectContent(false);
    }
    
    // Load analytics if IIKo is available
    if (iikoOrganizations.length > 0) {
      setIsLoadingProjectAnalytics(true);
      try {
        const orgId = iikoOrganizations[0].id; // Use first available organization
        const analyticsResponse = await axios.get(`${API}/menu-project/${project.id}/analytics?organization_id=${orgId}`);
        if (analyticsResponse.data.success) {
          setProjectAnalytics(analyticsResponse.data);
        }
      } catch (error) {
        console.error('Error loading project analytics:', error);
        // Don't show alert for analytics errors - they're optional
      } finally {
        setIsLoadingProjectAnalytics(false);
      }
    }
  };

  const exportProject = async (projectId, format = 'excel') => {
    setIsExportingProject(true);
    try {
      const response = await axios.post(`${API}/menu-project/${projectId}/export?export_format=${format}`);
      
      if (response.data.success) {
        alert(`Проект экспортирован в ${format.toUpperCase()}! Ссылка для скачивания: ${response.data.download_url}`);
        
        // In a real implementation, you would handle the file download
        console.log('Export URL:', response.data.download_url);
      } else {
        throw new Error('Export failed');
      }
    } catch (error) {
      console.error('Error exporting project:', error);
      alert('Ошибка при экспорте проекта: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsExportingProject(false);
    }
  };

  const renderProjectStats = (stats) => {
    if (!stats) return null;
    
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-900/20 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-blue-300">{stats.creation_time_saved}</div>
          <div className="text-xs text-gray-400">минут сэкономлено</div>
        </div>
        <div className="bg-green-900/20 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-green-300">{stats.estimated_cost_savings}</div>
          <div className="text-xs text-gray-400">₽ экономия</div>
        </div>
        <div className="bg-purple-900/20 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-purple-300">{stats.total_dishes}</div>
          <div className="text-xs text-gray-400">всего блюд</div>
        </div>
        <div className="bg-orange-900/20 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-orange-300">{stats.complexity_score}%</div>
          <div className="text-xs text-gray-400">сложность</div>
        </div>
      </div>
    );
  };

  const renderProjectAnalytics = (analytics) => {
    if (!analytics) return null;
    
    const salesPerformance = analytics.sales_performance;
    const recommendations = analytics.recommendations || [];
    
    return (
      <div className="space-y-6">
        {/* Sales Performance */}
        {salesPerformance && salesPerformance.status === 'success' && (
          <div className="bg-gray-800/50 rounded-lg p-4">
            <h4 className="text-lg font-bold text-green-300 mb-3">📈 ПРОДАЖИ IIKo</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="text-center">
                <div className="text-xl font-bold text-green-400">
                  {Math.round(salesPerformance.project_performance?.total_revenue || 0)} ₽
                </div>
                <div className="text-sm text-gray-400">Выручка проекта</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-blue-400">
                  {salesPerformance.project_performance?.total_quantity || 0}
                </div>
                <div className="text-sm text-gray-400">Блюд продано</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-purple-400">
                  {Math.round((salesPerformance.project_performance?.match_rate || 0) * 100)}%
                </div>
                <div className="text-sm text-gray-400">Найдено в продажах</div>
              </div>
            </div>
            
            {/* Market Share */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-green-900/20 rounded p-3">
                <div className="text-sm text-gray-400">Доля в выручке</div>
                <div className="text-lg font-bold text-green-300">
                  {Math.round(salesPerformance.market_share?.project_revenue_share || 0)}%
                </div>
              </div>
              <div className="bg-blue-900/20 rounded p-3">
                <div className="text-sm text-gray-400">Доля в продажах</div>
                <div className="text-lg font-bold text-blue-300">
                  {Math.round(salesPerformance.market_share?.project_quantity_share || 0)}%
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div className="bg-gray-800/50 rounded-lg p-4">
            <h4 className="text-lg font-bold text-yellow-300 mb-3">💡 РЕКОМЕНДАЦИИ</h4>
            <div className="space-y-3">
              {recommendations.slice(0, 3).map((rec, index) => (
                <div key={index} className={`p-3 rounded border-l-4 ${
                  rec.priority === 'high' ? 'border-red-400 bg-red-900/20' :
                  rec.priority === 'medium' ? 'border-yellow-400 bg-yellow-900/20' :
                  'border-green-400 bg-green-900/20'
                }`}>
                  <div className="font-bold text-sm mb-1">{rec.title}</div>
                  <div className="text-xs text-gray-300">{rec.description}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // NEW: Analytics and OLAP functions
  const loadAnalyticsOverview = async () => {
    if (!currentUser?.id) return;
    
    setIsLoadingAnalytics(true);
    try {
      // Load overall analytics data
      const [historyResponse, projectsResponse] = await Promise.all([
        axios.get(`${API}/user-history/${currentUser.id}`),
        axios.get(`${API}/menu-projects/${currentUser.id}`)
      ]);
      
      const history = historyResponse.data.history || []; // TC-003: API возвращает {history: [...]}
      const projects = projectsResponse.data.projects || [];
      
      // Calculate overall statistics
      const totalTechCards = history.filter(item => !item.is_menu).length;
      const totalMenus = history.filter(item => item.is_menu).length;
      const totalProjects = projects.length;
      
      // Time savings calculation
      const totalTimeSaved = totalMenus * 15 + totalTechCards * 45; // минуты
      const totalCostSaved = totalMenus * 5000 + totalTechCards * 2000; // рубли
      
      // Last activity
      const sortedHistory = history.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      const lastActivity = sortedHistory[0]?.created_at;
      
      // Most productive day
      const activityByDate = {};
      history.forEach(item => {
        const date = new Date(item.created_at).toDateString();
        activityByDate[date] = (activityByDate[date] || 0) + 1;
      });
      
      const mostProductiveDay = Object.entries(activityByDate)
        .sort(([,a], [,b]) => b - a)[0];
      
      setAnalyticsData({
        overview: {
          totalTechCards,
          totalMenus,
          totalProjects,
          totalTimeSaved,
          totalCostSaved,
          lastActivity,
          mostProductiveDay: mostProductiveDay ? {
            date: mostProductiveDay[0],
            count: mostProductiveDay[1]
          } : null
        },
        recentActivity: sortedHistory.slice(0, 10),
        projects: projects.map(project => ({
          ...project,
          productivity_score: (project.menus_count * 15 + project.tech_cards_count * 45) / 60 // hours
        })).sort((a, b) => b.productivity_score - a.productivity_score)
      });
      
    } catch (error) {
      console.error('Error loading analytics overview:', error);
      setAnalyticsData(null);
    } finally {
      setIsLoadingAnalytics(false);
    }
  };

  const loadOLAPReport = async () => {
    if (iikoOrganizations.length === 0) {
      alert('Сначала настройте интеграцию с IIKo');
      return;
    }
    
    setIsLoadingAnalytics(true);
    try {
      const orgId = iikoOrganizations[0].id;
      const response = await axios.get(`${API}/iiko/sales-report?organization_id=${orgId}`);
      
      if (response.data.success) {
        setOlapReportData(response.data);
      } else {
        throw new Error(response.data.error || 'Failed to load OLAP report');
      }
    } catch (error) {
      console.error('Error loading OLAP report:', error);
      alert('Ошибка загрузки OLAP отчета: ' + (error.response?.data?.detail || error.message));
      setOlapReportData(null);
    } finally {
      setIsLoadingAnalytics(false);
    }
  };

  const renderAnalyticsOverview = () => {
    if (!analyticsData) return null;
    
    const { overview, recentActivity, projects } = analyticsData;
    
    return (
      <div className="space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-blue-900/30 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-blue-300">{overview.totalTechCards}</div>
            <div className="text-sm text-gray-400">Техкарт создано</div>
          </div>
          <div className="bg-green-900/30 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-green-300">{overview.totalMenus}</div>
            <div className="text-sm text-gray-400">Меню создано</div>
          </div>
          <div className="bg-purple-900/30 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-purple-300">{overview.totalProjects}</div>
            <div className="text-sm text-gray-400">Проектов</div>
          </div>
          <div className="bg-orange-900/30 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-orange-300">{Math.round(overview.totalTimeSaved / 60)}</div>
            <div className="text-sm text-gray-400">Часов сэкономлено</div>
          </div>
        </div>
        
        {/* Savings Highlight */}
        <div className="bg-green-900/20 rounded-lg p-6 border border-green-500/30">
          <h3 className="text-xl font-bold text-green-300 mb-3">💰 ЭКОНОМИЯ</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="text-2xl font-bold text-green-400">{overview.totalTimeSaved} минут</div>
              <div className="text-sm text-gray-300">Времени сэкономлено</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-400">{overview.totalCostSaved.toLocaleString()} ₽</div>
              <div className="text-sm text-gray-300">Стоимость работы разработчика</div>
            </div>
          </div>
        </div>
        
        {/* Top Projects */}
        {projects.length > 0 && (
          <div className="bg-gray-800/50 rounded-lg p-4">
            <h3 className="text-lg font-bold text-purple-300 mb-3">🏆 ТОП ПРОЕКТЫ</h3>
            <div className="space-y-3">
              {projects.slice(0, 5).map((project, index) => (
                <div key={project.id} className="flex justify-between items-center bg-gray-700/50 rounded p-3">
                  <div>
                    <div className="font-bold text-sm">{project.project_name}</div>
                    <div className="text-xs text-gray-400">{project.menus_count} меню, {project.tech_cards_count} техкарт</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-purple-300">{project.productivity_score.toFixed(1)}ч</div>
                    <div className="text-xs text-gray-400">продуктивности</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Recent Activity */}
        {recentActivity.length > 0 && (
          <div className="bg-gray-800/50 rounded-lg p-4">
            <h3 className="text-lg font-bold text-blue-300 mb-3">🕒 ПОСЛЕДНЯЯ АКТИВНОСТЬ</h3>
            <div className="space-y-2">
              {recentActivity.slice(0, 5).map((item, index) => (
                <div key={item.id || index} className="flex justify-between items-center text-sm">
                  <div className="flex items-center gap-2">
                    <span className={item.is_menu ? '🍽️' : '📋'} />
                    <span>{item.dish_name || item.menu_type || 'Неизвестно'}</span>
                  </div>
                  <div className="text-gray-400">
                    {new Date(item.created_at).toLocaleDateString('ru-RU')}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderOLAPReport = () => {
    if (!olapReportData) return null;
    
    const { summary, top_dishes, period } = olapReportData;
    
    return (
      <div className="space-y-6">
        {/* Report Period */}
        <div className="bg-blue-900/20 rounded-lg p-4">
          <h3 className="text-lg font-bold text-blue-300 mb-2">📊 ПЕРИОД ОТЧЕТА</h3>
          <div className="text-sm text-gray-300">
            {period?.from ? `${period.from} - ${period.to}` : 'Последние 7 дней'}
          </div>
        </div>
        
        {/* Summary Stats */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-green-900/30 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-green-300">{Math.round(summary.total_revenue || 0)}</div>
              <div className="text-sm text-gray-400">₽ Общая выручка</div>
            </div>
            <div className="bg-blue-900/30 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-blue-300">{summary.total_items_sold || 0}</div>
              <div className="text-sm text-gray-400">Блюд продано</div>
            </div>
            <div className="bg-purple-900/30 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-purple-300">{Math.round(summary.average_check || 0)}</div>
              <div className="text-sm text-gray-400">₽ Средний чек</div>
            </div>
            <div className="bg-orange-900/30 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-orange-300">{summary.unique_dishes || 0}</div>
              <div className="text-sm text-gray-400">Уникальных блюд</div>
            </div>
          </div>
        )}
        
        {/* Top Dishes */}
        {top_dishes && top_dishes.length > 0 && (
          <div className="bg-gray-800/50 rounded-lg p-4">
            <h3 className="text-lg font-bold text-yellow-300 mb-3">🏆 ТОП БЛЮДА ПО ПРОДАЖАМ</h3>
            <div className="space-y-3">
              {top_dishes.slice(0, 10).map((dish, index) => (
                <div key={index} className="flex justify-between items-center bg-gray-700/50 rounded p-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-yellow-600 rounded-full flex items-center justify-center text-sm font-bold">
                      {index + 1}
                    </div>
                    <div>
                      <div className="font-bold text-sm">{dish.name}</div>
                      <div className="text-xs text-gray-400">{dish.category}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-green-300">{Math.round(dish.revenue || 0)} ₽</div>
                    <div className="text-xs text-gray-400">{dish.quantity || 0} шт</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const loadUserPrices = async (userId) => {
    try {
      const response = await axios.get(`${API}/user-prices/${userId}`);
      setUserPrices(response.data.prices || []);
    } catch (error) {
      console.error('Error loading user prices:', error);
    }
  };

  // РЕВОЛЮЦИЯ UX: Убираем принудительную регистрацию!
  // Теперь пользователи сразу могут создавать техкарты в демо-режиме
  // Регистрация нужна только для сохранения результатов
  
  // Создаем демо-пользователя если нет текущего (с PRO планом для доступа к AI)
  const currentUserOrDemo = currentUser || {
    id: 'demo_user',
    name: 'Демо пользователь', 
    email: 'demo@receptor.pro',
    subscription_plan: 'pro',  // PRO план для доступа к AI-дополнениям
    monthly_tech_cards_used: 0,
    demo_mode: true
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white font-['Montserrat']">
      {/* Hero Section - hidden in demo mode */}
      {false && (
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
      <header className="border-b border-purple-500/20 bg-gray-900/80 backdrop-blur-xl shadow-2xl">
        <div className="max-w-7xl mx-auto px-6 py-5">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-3 sm:space-y-0">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 via-purple-600 to-purple-700 rounded-xl flex items-center justify-center shadow-lg ring-2 ring-purple-400/20">
                <span className="text-white font-bold text-xl">R</span>
              </div>
              <div className="flex flex-col">
                <h1 className="text-2xl sm:text-3xl font-semibold bg-gradient-to-r from-purple-300 via-purple-200 to-purple-100 bg-clip-text text-transparent tracking-tight">
                  RECEPTOR PRO
                </h1>
                <div className="flex items-center space-x-3">
                  <span className="text-xs text-purple-400/80 font-medium tracking-widest uppercase">
                    Restaurant Tech Platform
                  </span>

                </div>
              </div>
            </div>
            
            {/* Subscription Info */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-4 w-full sm:w-auto">
              <div className="text-center sm:text-left">
                <div className="text-sm text-purple-300 font-bold">
                  {currentUserOrDemo.subscription_plan?.toUpperCase() || 'FREE'}
                </div>
                {currentUserOrDemo.subscription_plan === 'free' && (
                  <div className="text-xs text-gray-400">
                    {currentUserOrDemo.monthly_tech_cards_used || 0}/3 техкарт
                  </div>
                )}
                {currentUserOrDemo.subscription_plan === 'starter' && (
                  <div className="text-xs text-gray-400">
                    {currentUserOrDemo.monthly_tech_cards_used || 0}/25 техкарт
                  </div>
                )}
                {(currentUserOrDemo.subscription_plan === 'pro' || currentUserOrDemo.subscription_plan === 'business') && (
                  <div className="text-xs text-gray-400">
                    {currentUserOrDemo.monthly_tech_cards_used || 0} техкарт
                  </div>
                )}
              </div>
              
              <nav className="flex items-center space-x-1">
                {/* УПРОЩЕННАЯ НАВИГАЦИЯ: только основные разделы */}
                <button
                  onClick={() => setCurrentView('dashboard')}
                  className={`px-4 py-2.5 rounded-lg font-medium text-sm transition-all duration-200 ${
                    currentView === 'dashboard' 
                      ? 'bg-purple-600/20 text-purple-200 shadow-lg border border-purple-500/30 backdrop-blur-sm' 
                      : 'text-purple-300/80 hover:text-purple-200 hover:bg-purple-600/10 hover:backdrop-blur-sm'
                  }`}
                  title="Главная страница с ассистентом"
                >
                  <span className="flex items-center space-x-1.5">
                    <span>ГЛАВНАЯ</span>
                  </span>
                </button>
                <button
                  onClick={() => setCurrentView('techcards')}
                  className={`px-4 py-2.5 rounded-lg font-medium text-sm transition-all duration-200 ${
                    currentView === 'techcards' 
                      ? 'bg-purple-600/20 text-purple-200 shadow-lg border border-purple-500/30 backdrop-blur-sm' 
                      : 'text-purple-300/80 hover:text-purple-200 hover:bg-purple-600/10 hover:backdrop-blur-sm'
                  }`}
                  title="Просмотр всех техкарт"
                >
                  ТЕХКАРТЫ
                </button>
                <button
                  onClick={() => setCurrentView('ai-kitchen')}
                  className={`px-4 py-2.5 rounded-lg font-medium text-sm transition-all duration-200 ${
                    currentView === 'ai-kitchen' 
                      ? 'bg-purple-600/20 text-purple-200 shadow-lg border border-purple-500/30 backdrop-blur-sm' 
                      : 'text-purple-300/80 hover:text-purple-200 hover:bg-purple-600/10 hover:backdrop-blur-sm'
                  }`}
                  title="AI-Кухня: фудпейринг, генерация меню, AI рекомендации"
                >
                  <span className="flex items-center space-x-1.5">
                    <span>AI-КУХНЯ</span>
                    <span className="bg-gradient-to-r from-pink-500 to-violet-500 text-white px-1.5 py-0.5 rounded text-xs font-bold">AI</span>
                  </span>
                </button>
                
                {/* PRO ФУНКЦИИ - скрыты до PRO версии */}
                {false && (
                  <>
                    <button
                      onClick={() => setShowProjectsModal(true)}
                      className="px-4 py-2.5 rounded-lg font-medium text-sm text-purple-300/80 hover:text-purple-200 hover:bg-purple-600/10 hover:backdrop-blur-sm transition-all duration-200"
                      title="📁 Project Management (PRO)"
                    >
                      <span className="flex items-center space-x-1.5">
                        <span className="text-xs">📁</span>
                        <span>Projects</span>
                      </span>
                    </button>
                    <button
                      onClick={() => setShowAnalyticsModal(true)}
                      className="px-4 py-2.5 rounded-lg font-medium text-sm text-purple-300/80 hover:text-purple-200 hover:bg-purple-600/10 hover:backdrop-blur-sm transition-all duration-200"
                      title="📊 Business Analytics (PRO)"
                    >
                      <span className="flex items-center space-x-1.5">
                        <span className="text-xs">📊</span>
                        <span>Analytics</span>
                      </span>
                    </button>
                  </>
                )}
              </nav>
              {/* IIKo кнопка убрана - больше не нужна */}
              <div className="flex items-center space-x-4">
                {/* ДАННЫЕ перенесены в настройки профиля - упрощаем интерфейс */}
                {false && (
                  <button
                    onClick={() => setShowDataModal(true)}
                    className="text-yellow-300 hover:text-yellow-200 font-semibold text-sm sm:text-base transition-colors"
                    title="📂 Загрузить прайсы и данные по БЖУ (PRO)"
                  >
                    ДАННЫЕ
                  </button>
                )}
                
                {/* Показываем разные элементы для демо и зарегистрированных пользователей */}
                {currentUserOrDemo.demo_mode ? (
                  // Демо режим - показываем Login/Signup
                  <>
                    {/* 🎯 Кнопка помощи для demo пользователей */}
                    <button
                      onClick={() => setActiveTour('welcome')}
                      className="text-blue-400 hover:text-blue-300 text-xl transition-all duration-200 hover:scale-110"
                      title="❓ Помощь - Пройти тур по функциям"
                    >
                      ❓
                    </button>
                    <button
                      onClick={() => setShowModernAuth(true)}
                      className="bg-gray-800 hover:bg-gray-700 text-white font-medium px-6 py-2 rounded-lg text-sm transition-all border border-gray-600 hover:border-gray-500"
                      title="Войти или зарегистрироваться"
                    >
                      Войти
                    </button>
                    <span className="text-gray-400 text-sm hidden sm:inline">|</span>
                    <button
                      onClick={() => setShowVenueProfileModal(true)}
                      className="text-purple-300 hover:text-purple-200 font-bold text-sm sm:text-base transition-colors flex items-center space-x-2"
                      title="Личный кабинет: настройки заведения, подключение iiko"
                    >
                      <span>{currentUserOrDemo.name}</span>
                    </button>
                  </>
                ) : (
                  // Зарегистрированный пользователь - личный кабинет + выход
                  <>
                    {/* 🎯 Кнопка помощи - повторить онбординг */}
                    <button
                      onClick={() => setActiveTour('welcome')}
                      className="text-blue-400 hover:text-blue-300 text-xl transition-all duration-200 hover:scale-110"
                      title="❓ Помощь - Повторить тур по функциям"
                    >
                      ❓
                    </button>
                    <button
                      onClick={() => setCurrentView('personal-cabinet')}
                      className="text-purple-300 hover:text-purple-200 font-bold text-sm sm:text-base transition-colors flex items-center space-x-2"
                      title="Личный кабинет: настройки профиля, подписка, iiko, тарифы"
                    >
                      <span>{currentUserOrDemo.name}</span>
                    </button>
                    <button
                      onClick={handleLogout}
                      className="text-purple-300 hover:text-purple-200 font-semibold text-sm sm:text-base"
                      title="🚪 Выйти из аккаунта и очистить данные сессии"
                    >
                      ВЫЙТИ
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:py-12">
        {/* Dashboard View */}
        {currentView === 'dashboard' && (
          <div className="space-y-8">
            {/* Culinary Assistant - Center Mode (Main Feature) */}
            <div className="mb-8">
              <CulinaryAssistant 
                userId={currentUserOrDemo?.id || 'demo_user'}
                mode="center"
                onTechCardRequest={(data) => {
                  console.log('TechCard request from chat:', data);
                  // Если техкарта создана через чат, переключаемся на страницу создания и показываем её
                  if (data && data.techCard) {
                    // Переключаемся на страницу создания техкарт
                    setCurrentView('create');
                    // Устанавливаем техкарту
                    setTcV2(data.techCard);
                    setTechCard(null);
                    if (data.techCard?.meta?.id) {
                      setCurrentTechCardId(data.techCard.meta.id);
                    }
                    // Парсим ингредиенты из V2 формата
                    const parsedIngredients = data.techCard.ingredients?.map((ing, index) => ({
                      id: index + 1,
                      name: ing.name,
                      quantity: ing.netto_g?.toString() || '0',
                      unit: ing.unit || 'г',
                      unitPrice: '0',
                      totalPrice: '0',
                      originalQuantity: ing.netto_g?.toString() || '0',
                      originalPrice: '0'
                    })) || [];
                    setCurrentIngredients(parsedIngredients);
                  } else if (data && data.dishName) {
                    // Если только название блюда, переключаемся и заполняем форму
                    setCurrentView('create');
                    setDishName(data.dishName);
                    updateWizardData(1, { dishName: data.dishName });
                    setTcV2(null);
                    setTechCard(null);
                  }
                }}
              />
            </div>

            {/* Welcome Section */}
            <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 border border-purple-400/30 rounded-xl p-6 sm:p-8">
              <h2 className="text-2xl sm:text-3xl font-bold text-purple-300 mb-4">
                Добро пожаловать, {currentUserOrDemo.name}!
              </h2>
              
              {/* Demo Mode Banner */}
              {currentUserOrDemo.demo_mode && (
                <div className="bg-yellow-900/30 border border-yellow-400/50 rounded-lg p-4 mb-4">
                  <div className="flex items-center gap-3">
                    <div>
                      <div className="font-bold text-yellow-300">Демо режим</div>
                      <div className="text-yellow-400 text-sm">
                        Создавайте техкарты бесплатно! Для сохранения результатов зарегистрируйтесь.
                      </div>
                    </div>
                    <button
                      onClick={() => setShowRegistrationModal(true)}
                      className="ml-auto bg-yellow-600 hover:bg-yellow-700 text-black px-3 py-1 rounded text-sm font-bold transition-colors"
                    >
                      Регистрация
                    </button>
                  </div>
                </div>
              )}
              
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
                    {currentUserOrDemo.subscription_plan?.toUpperCase() || 'FREE'}
                  </div>
                  <div className="text-sm text-gray-400">Ваш план</div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div 
                className="bg-gradient-to-br from-purple-600/20 to-pink-600/20 border border-purple-400/30 rounded-xl p-6 cursor-pointer hover:scale-105 transition-transform"
                onClick={() => setCurrentView('create')}
              >
                <h3 className="text-xl font-bold text-purple-300 mb-2">Создать техкарту</h3>
                <p className="text-gray-400 text-sm">Сгенерируйте детальную техкарту для любого блюда</p>
              </div>

              <div 
                className="bg-gradient-to-br from-orange-600/20 to-red-600/20 border border-orange-400/30 rounded-xl p-6 cursor-pointer hover:scale-105 transition-transform"
                onClick={() => setShowVenueProfileModal(true)}
              >
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
                        <div className="w-2 h-2 rounded-full bg-purple-500"></div>
                        <div>
                          <div className="font-semibold text-gray-200">{item.dish_name}</div>
                          <div className="text-xs text-gray-400">
                            {new Date(item.created_at).toLocaleDateString('ru-RU')}
                          </div>
                        </div>
                      </div>
                      <button 
                        onClick={() => {
                          // Unified loading logic for both V1 and V2 formats
                          const isV2 = item.techcard_v2_data || (item.content && item.content.includes('"meta"'));
                          
                          if (isV2 && item.techcard_v2_data) {
                            setTcV2(item.techcard_v2_data);
                            setTechCard(null);
                            setGenerationStatus('success');
                            setCurrentTechCardId(item.id);
                            setCurrentView('create');
                          } else if (item.content) {
                            try {
                              const parsedContent = JSON.parse(item.content);
                              if (parsedContent.ingredients) {
                                setTcV2(parsedContent);
                                setTechCard(null);
                                setGenerationStatus('success');
                                setCurrentTechCardId(item.id);
                                setCurrentView('create');
                              } else {
                                throw new Error('Not V2 format');
                              }
                            } catch (e) {
                              // V1 tech card - only clear tcV2 if not forced to V2
                              if (!FORCE_TECHCARD_V2) {
                                setTechCard(item.content);
                                setTcV2(null);
                              }
                              setGenerationStatus('success');
                              setCurrentTechCardId(item.id);
                              setCurrentView('create');
                            }
                          }
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

        {/* Generated Menu View - в AI-Kitchen */}
        {currentView === 'ai-kitchen' && generatedMenu && !showMenuWizard && (
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
                                    setWizardData(prev => ({...prev, dishName: `${dish.name} (из меню "${generatedMenu.menu_name || 'Сгенерированное меню'}")}`}));
                                    
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
                                  setWizardData(prev => ({...prev, dishName: `${dish.name} (из меню "${generatedMenu.menu_name || 'Сгенерированное меню'}")}`}));
                                  
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

        {/* AI-Kitchen View - AI-дополнения: Лаборатория, Вдохновение и т.д. */}
        {currentView === 'ai-kitchen' && (
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-8">
              <div className="bg-gradient-to-r from-pink-600/20 to-violet-600/20 border border-pink-400/30 rounded-2xl p-8 sm:p-12 mb-8">
                <div className="text-6xl sm:text-8xl mb-6"></div>
                <div className="flex items-center justify-center gap-4 mb-6">
                  <h2 className="text-3xl sm:text-5xl font-bold bg-gradient-to-r from-pink-400 to-violet-400 bg-clip-text text-transparent">
                    AI-КУХНЯ
                  </h2>
                  <button
                    onClick={() => setActiveTour('aiKitchen')}
                    className="bg-pink-600/30 hover:bg-pink-600/50 text-pink-300 font-bold py-2 px-4 rounded-lg transition-all hover:scale-110"
                    title="Пройти обучающий тур по AI-Кухне"
                  >
                    ❓
                  </button>
                </div>
                <p className="text-xl sm:text-2xl text-gray-300 mb-4 max-w-4xl mx-auto">
                  Творческие <span className="text-pink-400 font-bold">AI-дополнения</span> для создания уникальных блюд
                </p>
                <div className="flex flex-wrap justify-center gap-2 text-sm">
                  <span className="bg-pink-600 px-3 py-1 rounded-full text-white">Лаборатория</span>
                  <span className="bg-violet-600 px-3 py-1 rounded-full text-white">Вдохновение</span>
                  <span className="bg-blue-600 px-3 py-1 rounded-full text-white">Фудпейринг</span>
                  <span className="bg-green-600 px-3 py-1 rounded-full text-white">Прокачка блюд</span>
                </div>
              </div>
            </div>

            {/* Central V1 Recipe Generator */}
            <div className="mb-8">
              <div className="bg-gradient-to-br from-purple-600/20 to-pink-600/20 border border-purple-400/30 rounded-2xl p-6 sm:p-8">
                <div className="text-center mb-8">
                  <h3 className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-4">
                    Генератор Рецептов
                  </h3>
                  <p className="text-gray-300 text-xl max-w-3xl mx-auto leading-relaxed">
                    Создайте детальный рецепт с пошаговыми инструкциями, а затем используйте AI-инструменты для его профессионального развития
                  </p>
                </div>
                
                {!aiKitchenRecipe && !techCard ? (
                  /* Recipe Creation Form */
                  <div className="max-w-3xl mx-auto space-y-6">
                    <div className="relative">
                      <input
                        type="text"
                        value={aiKitchenDishName}
                        onChange={(e) => setAiKitchenDishName(e.target.value)}
                        placeholder="Введите название блюда для создания рецепта..."
                        className="w-full bg-gray-800/30 border-2 border-gray-600/30 rounded-2xl px-8 py-6 pr-20 text-xl text-white placeholder-gray-400 focus:border-purple-400/60 focus:outline-none focus:ring-4 focus:ring-purple-500/20 transition-all duration-300 backdrop-blur-sm"
                        onKeyPress={(e) => {
                          if (e.key === 'Enter' && !isGenerating && aiKitchenDishName.trim()) {
                            generateAiKitchenRecipe();
                          }
                        }}
                      />
                      {/* Voice Input Button for AI Kitchen */}
                      <button
                        type="button"
                        onClick={() => {
                          // Voice input for AI Kitchen
                          if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                            const SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition;
                            const recognition = new SpeechRecognition();
                            
                            recognition.continuous = false;
                            recognition.interimResults = false;
                            recognition.lang = 'ru-RU';
                            
                            setVoiceStatus('Слушаю...');
                            setShowVoiceModal(true);
                            
                            recognition.onresult = (event) => {
                              const transcript = event.results[0][0].transcript;
                              setAiKitchenDishName(transcript);
                              setVoiceStatus('Распознано: ' + transcript);
                              setTimeout(() => {
                                setShowVoiceModal(false);
                              }, 1500);
                            };
                            
                            recognition.onerror = () => {
                              setVoiceStatus('Ошибка распознавания голоса');
                              setTimeout(() => {
                                setShowVoiceModal(false);
                              }, 2000);
                            };
                            
                            recognition.start();
                          } else {
                            alert('Ваш браузер не поддерживает голосовой ввод');
                          }
                        }}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 p-3 rounded-xl bg-purple-600/20 hover:bg-purple-600/40 text-purple-300 hover:text-purple-200 transition-all duration-300 border border-purple-500/30 hover:border-purple-400/50"
                        title="Голосовой ввод"
                      >
                        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 0 1 5 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </div>
                    <button 
                      onClick={generateAiKitchenRecipe}
                      disabled={isGenerating || !aiKitchenDishName.trim()}
                      className={`w-full ${(isGenerating || !aiKitchenDishName.trim()) ? 'bg-gray-600/50 cursor-not-allowed' : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 hover:shadow-2xl hover:shadow-purple-500/30'} text-white font-bold py-5 px-12 rounded-2xl transition-all duration-300 transform hover:scale-[1.02] text-xl shadow-xl shadow-purple-500/20 border border-purple-500/20`}
                      title="Создать детальный рецепт с пошаговыми инструкциями для дальнейших экспериментов"
                    >
                      {isGenerating && loadingType === 'recipe' ? 
                        <span className="flex items-center justify-center">
                          <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          СОЗДАНИЕ РЕЦЕПТА...
                        </span>
                        : 'СОЗДАТЬ РЕЦЕПТ'
                      }
                    </button>
                  </div>
                ) : (
                  /* Generated Recipe Display */
                  <div className="max-w-5xl mx-auto">
                    <div className="bg-gradient-to-br from-gray-800/40 to-gray-900/40 border border-purple-400/40 rounded-2xl p-8 backdrop-blur-sm">
                      <div className="flex items-center justify-between mb-6">
                        <h4 className="text-purple-300 font-bold text-2xl">
                          {aiKitchenRecipe?.name || techCard?.name || 'Рецепт'}
                        </h4>
                        <div className="flex flex-wrap gap-4">
                          <button 
                            onClick={async () => {
                              try {
                                const recipeToSave = aiKitchenRecipe || techCard;
                                const response = await axios.post(`${API}/v1/user/save-recipe`, {
                                  recipe_content: recipeToSave.content,
                                  recipe_name: recipeToSave.name,
                                  recipe_type: 'v1',
                                  user_id: (currentUser || { id: 'demo_user' }).id
                                });
                                
                                if (response.data.success) {
                                  alert('Рецепт успешно сохранен в историю');
                                  loadUserTechCards();
                                } else {
                                  alert('Ошибка сохранения: ' + (response.data.message || 'Неизвестная ошибка'));
                                }
                              } catch (error) {
                                console.error('Error saving V1 recipe:', error);
                                alert('Ошибка сохранения рецепта: ' + (error.response?.data?.detail || error.message));
                              }
                            }}
                            className="bg-gradient-to-r from-green-600/30 to-emerald-600/30 hover:from-green-600/50 hover:to-emerald-600/50 text-green-300 border border-green-500/50 px-6 py-3 rounded-xl hover:border-green-400/70 transition-all duration-300 font-medium"
                          >
                            Сохранить в историю
                          </button>
                          
                          <button 
                            onClick={async () => {
                              // V1→V2 Конвертация
                              setIsGenerating(true);
                              setLoadingType('conversion');
                              setLoadingMessage('Структурируем рецепт в техкарту...');
                              
                              // Запускаем симуляцию прогресса
                              const progressInterval = simulateProgress('conversion', 20000); // 20 секунд
                              
                              // Запускаем автоматическую смену советов
                              setCurrentConversionTipIndex(0);
                              const tipInterval = setInterval(() => {
                                setCurrentConversionTipIndex(prev => (prev + 1) % conversionTips.length);
                              }, 6000); // Смена каждые 6 секунд - чтобы успеть прочитать
                              
                              try {
                                console.log('🔄 Converting V1 recipe to V2 techcard');
                                
                                const recipeToConvert = aiKitchenRecipe || techCard;
                                const response = await axios.post(`${API}/v1/convert-recipe-to-techcard`, {
                                  recipe_content: recipeToConvert.content,
                                  recipe_name: recipeToConvert.name,
                                  user_id: (currentUser || { id: 'demo_user' }).id
                                });
                                
                                if (response.data.techcard) {
                                  // Успешная конвертация - переключаемся на V2
                                  setTcV2(response.data.techcard);
                                  setTechCard(null); // Очищаем V1
                                  setAiKitchenRecipe(null); // Очищаем AI Kitchen
                                  setCurrentTechCardId(response.data.techcard.id || response.data.techcard._id); // 🔥 FIX: Set ID для history navigation!
                                  setWizardData(prev => ({...prev, dishName: aiKitchenRecipe.name}));
                                  setGenerationStatus('success');
                                  setCurrentView('create');
                                  
                                  alert('Рецепт успешно преобразован в профессиональную техкарту V2!');
                                } else {
                                  throw new Error('Пустой ответ от сервера конвертации');
                                }
                                
                              } catch (error) {
                                console.error('Error converting V1 to V2:', error);
                                alert('Ошибка конвертации: ' + (error.response?.data?.detail || error.message));
                              } finally {
                                clearInterval(progressInterval);
                                clearInterval(tipInterval);
                                setIsGenerating(false);
                                setLoadingMessage('');
                                setLoadingType('');
                              }
                            }}
                            disabled={isGenerating}
                            className={`${isGenerating ? 'bg-gray-600/50 cursor-not-allowed' : 'bg-gradient-to-r from-orange-600/30 to-red-600/30 hover:from-orange-600/50 hover:to-red-600/50'} text-orange-300 border border-orange-500/50 px-6 py-3 rounded-xl hover:border-orange-400/70 transition-all duration-300 font-medium`}
                          >
                            {isGenerating && loadingType === 'conversion' ? 'Конвертируем...' : 'Превратить в техкарту'}
                          </button>
                          
                          <button 
                            onClick={() => {
                              setAiKitchenRecipe(null);
                              setTechCard(null);
                              setAiKitchenDishName('');
                            }}
                            className="bg-gradient-to-r from-purple-600/30 to-pink-600/30 hover:from-purple-600/50 hover:to-pink-600/50 text-purple-300 border border-purple-500/50 px-6 py-3 rounded-xl hover:border-purple-400/70 transition-all duration-300 font-medium"
                          >
                            Создать новый рецепт
                          </button>
                          
                          <button 
                            onClick={() => {
                              // Копируем рецепт в буфер обмена
                              const recipeToShare = aiKitchenRecipe || techCard;
                              const recipeText = `📋 ${recipeToShare.name}\n\n${recipeToShare.content}\n\n✨ Создано с помощью Receptor AI | www.receptorai.pro`;
                              
                              navigator.clipboard.writeText(recipeText).then(() => {
                                alert('✅ Рецепт скопирован в буфер обмена! Теперь можно поделиться им в мессенджере или соцсетях.');
                              }).catch(err => {
                                console.error('Error copying recipe:', err);
                                // Fallback для старых браузеров
                                const textArea = document.createElement('textarea');
                                textArea.value = recipeText;
                                textArea.style.position = 'fixed';
                                textArea.style.left = '-999999px';
                                document.body.appendChild(textArea);
                                textArea.select();
                                try {
                                  document.execCommand('copy');
                                  alert('✅ Рецепт скопирован в буфер обмена!');
                                } catch (err) {
                                  alert('❌ Не удалось скопировать рецепт. Попробуйте выделить текст вручную.');
                                }
                                document.body.removeChild(textArea);
                              });
                            }}
                            className="bg-gradient-to-r from-blue-600/30 to-cyan-600/30 hover:from-blue-600/50 hover:to-cyan-600/50 text-blue-300 border border-blue-500/50 px-6 py-3 rounded-xl hover:border-blue-400/70 transition-all duration-300 font-medium flex items-center gap-2"
                            title="Скопировать рецепт для отправки в мессенджер или соцсети"
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                            Поделиться
                          </button>
                        </div>
                      </div>
                      <div className="max-h-80 overflow-y-auto text-gray-300 text-sm leading-relaxed">
                        <div 
                          dangerouslySetInnerHTML={{ 
                            __html: formatProAIContent((aiKitchenRecipe || techCard).content) 
                          }} 
                        />
                      </div>
                    </div>
                    
                    <div className="mt-8 text-center">
                      <p className="text-purple-300 text-xl font-medium mb-4">
                        Используйте AI-инструменты ниже для профессионального развития рецепта
                      </p>
                      
                      {/* ТЕСТОВАЯ КНОПКА ВДОХНОВЕНИЯ */}
                      <div className="mb-4">
                        <button
                          onClick={() => {
                            console.log('🎯 Testing inspiration with aiKitchenRecipe:', aiKitchenRecipe?.name);
                            if (aiKitchenRecipe) {
                              generateInspiration();
                            } else {
                              alert('Сначала создайте рецепт выше');
                            }
                          }}
                          disabled={!aiKitchenRecipe || isGenerating}
                          className={`${!aiKitchenRecipe || isGenerating ? 'bg-gray-600/50' : 'bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700'} text-white px-6 py-3 rounded-xl font-medium transition-all`}
                        >
                          {isGenerating && loadingType === 'inspiration' ? 'Создаю твист...' : '💡 ТЕСТ: Творческий твист'}
                        </button>
                      </div>
                      <div className="flex flex-wrap justify-center gap-3 text-sm">
                        <span className="bg-gradient-to-r from-cyan-600/20 to-cyan-700/20 border border-cyan-500/30 px-4 py-2 rounded-xl text-cyan-300">Лабораторные эксперименты</span>
                        <span className="bg-gradient-to-r from-orange-600/20 to-orange-700/20 border border-orange-500/30 px-4 py-2 rounded-xl text-orange-300">Творческое вдохновение</span>
                        <span className="bg-gradient-to-r from-blue-600/20 to-blue-700/20 border border-blue-500/30 px-4 py-2 rounded-xl text-blue-300">Фудпейринг</span>
                        <span className="bg-gradient-to-r from-green-600/20 to-green-700/20 border border-green-500/30 px-4 py-2 rounded-xl text-green-300">Фотопрезентация</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* AI Functions Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              
              {/* 1. Лаборатория с V1 Рецептами */}
              <div className="bg-gradient-to-br from-cyan-600/20 to-blue-600/20 border border-cyan-400/30 rounded-xl p-6 hover:border-cyan-300/50 transition-all duration-300 group">
                <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">🧪</div>
                <h3 className="text-xl font-bold text-cyan-300 mb-3">Лаборатория</h3>
                <p className="text-gray-300 text-sm mb-4">
                  Создавайте красивые рецепты V1 для экспериментов и проводите кулинарные эксперименты с AI
                </p>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-cyan-400 text-xs font-semibold">⚗️ Эксперименты</span>
                  <span className="text-cyan-400 text-xs">🧪 Исследования</span>
                </div>
                
                {/* Laboratory Experiment Button */}
                <button 
                  onClick={() => conductExperiment()}
                  disabled={isGenerating || isExperimenting}
                  className={`w-full ${(isGenerating || isExperimenting) ? 'bg-gray-600 cursor-not-allowed' : 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-sm`}
                >
                  {isExperimenting ? 'ЭКСПЕРИМЕНТИРУЮ...' : '🧪 Провести эксперимент'}
                </button>
                
                {/* Раздел экспериментов - теперь без генерации рецептов */}
              </div>

              {/* 2. Вдохновение */}
              <div className="bg-gradient-to-br from-orange-600/20 to-red-600/20 border border-orange-400/30 rounded-xl p-6 hover:border-orange-300/50 transition-all duration-300 cursor-pointer group">
                <div className="text-4xl mb-4 group-hover:scale-110 transition-transform"></div>
                <h3 className="text-xl font-bold text-orange-300 mb-3">Вдохновение</h3>
                <p className="text-gray-300 text-sm mb-4">
                  Креативные твисты на блюда, используя техники и ингредиенты кухонь других стран
                </p>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-orange-400 text-xs font-semibold">✨ Твисты</span>
                  <span className="text-orange-300 group-hover:translate-x-1 transition-transform">→</span>
                </div>
                <button
                  onClick={generateInspiration}
                  disabled={isGenerating || !(techCard || tcV2 || aiKitchenRecipe)}
                  className={`w-full ${
                    isGenerating || !(techCard || tcV2 || aiKitchenRecipe)
                      ? 'bg-gray-600 cursor-not-allowed' 
                      : 'btn-inspiration'
                  } text-white font-bold py-3 px-4 rounded-lg transition-colors text-sm`}
                >
                  {isGenerating ? 'ГЕНЕРИРУЮ...' : 'ЗАПУСТИТЬ'}
                </button>
              </div>

              {/* 3. Фудпейринг */}
              <div className="bg-gradient-to-br from-green-600/20 to-emerald-600/20 border border-green-400/30 rounded-xl p-6 hover:border-green-300/50 transition-all duration-300 cursor-pointer group">
                <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">🍷</div>
                <h3 className="text-xl font-bold text-green-300 mb-3">Фудпейринг</h3>
                <p className="text-gray-300 text-sm mb-4">
                  AI подберет идеальные сочетания вкусов, напитков и ингредиентов для ваших блюд
                </p>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-green-400 text-xs font-semibold">🧠 Smart Pairing</span>
                  <span className="text-green-300 group-hover:translate-x-1 transition-transform">→</span>
                </div>
                <button
                  onClick={generateFoodPairing}
                  disabled={isGenerating || !(techCard || tcV2 || aiKitchenRecipe)}
                  className={`w-full ${
                    isGenerating || !(techCard || tcV2 || aiKitchenRecipe)
                      ? 'bg-gray-600 cursor-not-allowed' 
                      : 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700'
                  } text-white font-bold py-3 px-4 rounded-lg transition-colors text-sm`}
                >
                  {isGenerating ? 'ПОДБИРАЮ...' : 'ЗАПУСТИТЬ'}
                </button>
              </div>

              {/* 4. Прокачать блюдо */}
              <div className="bg-gradient-to-br from-purple-600/20 to-pink-600/20 border border-purple-400/30 rounded-xl p-6 hover:border-purple-300/50 transition-all duration-300 cursor-pointer group">
                <div className="text-4xl mb-4 group-hover:scale-110 transition-transform"></div>
                <h3 className="text-xl font-bold text-purple-300 mb-3">Прокачать блюдо</h3>
                <p className="text-gray-300 text-sm mb-4">
                  Улучшите существующие техкарты: сократите время, снизите себестоимость, улучшите вкус
                </p>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-purple-400 text-xs font-semibold">💪 Upgrade</span>
                  <span className="text-purple-300 group-hover:translate-x-1 transition-transform">→</span>
                </div>
                <button
                  onClick={improveDish}
                  disabled={isImprovingDish || !(techCard || tcV2 || aiKitchenRecipe)}
                  className={`w-full ${
                    isImprovingDish || !(techCard || tcV2 || aiKitchenRecipe)
                      ? 'bg-gray-600 cursor-not-allowed' 
                      : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700'
                  } text-white font-bold py-3 px-4 rounded-lg transition-colors text-sm`}
                >
                  {isImprovingDish ? 'ПРОКАЧИВАЮ...' : 'ЗАПУСТИТЬ'}
                </button>
              </div>

              {/* 5. Скрипт продаж */}
              <div className="bg-gradient-to-br from-yellow-600/20 to-orange-600/20 border border-yellow-400/30 rounded-xl p-6 hover:border-yellow-300/50 transition-all duration-300 cursor-pointer group">
                <div className="text-4xl mb-4 group-hover:scale-110 transition-transform"></div>
                <h3 className="text-xl font-bold text-yellow-300 mb-3">Скрипт продаж</h3>
                <p className="text-gray-300 text-sm mb-4">
                  Создавайте убедительные тексты для официантов и продвижения блюд в соцсетях
                </p>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-yellow-400 text-xs font-semibold">💰 Sales</span>
                  <span className="text-yellow-300 group-hover:translate-x-1 transition-transform">→</span>
                </div>
                <button
                  onClick={generateSalesScript}
                  disabled={isGenerating || !(techCard || tcV2 || aiKitchenRecipe)}
                  className={`w-full ${
                    isGenerating || !(techCard || tcV2 || aiKitchenRecipe)
                      ? 'bg-gray-600 cursor-not-allowed' 
                      : 'bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700'
                  } text-white font-bold py-3 px-4 rounded-lg transition-colors text-sm`}
                >
                  {isGenerating ? 'СОЗДАЮ...' : 'ЗАПУСТИТЬ'}
                </button>
              </div>

              {/* 6. Финансовый анализ */}
              <div className="bg-gradient-to-br from-indigo-600/20 to-blue-600/20 border border-indigo-400/30 rounded-xl p-6 hover:border-indigo-300/50 transition-all duration-300 cursor-pointer group">
                <div className="text-4xl mb-4 group-hover:scale-110 transition-transform"></div>
                <h3 className="text-xl font-bold text-indigo-300 mb-3">Финансовый анализ</h3>
                <p className="text-gray-300 text-sm mb-4">
                  Детальный анализ рентабельности блюда с советами по оптимизации затрат
                </p>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-indigo-400 text-xs font-semibold">📊 Analytics</span>
                  <span className="text-indigo-300 group-hover:translate-x-1 transition-transform">→</span>
                </div>
                <button
                  onClick={analyzeFinances}
                  disabled={isAnalyzingFinances || !(techCard || tcV2 || aiKitchenRecipe)}
                  className={`w-full ${
                    isAnalyzingFinances || !(techCard || tcV2 || aiKitchenRecipe)
                      ? 'bg-gray-600 cursor-not-allowed' 
                      : 'bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700'
                  } text-white font-bold py-3 px-4 rounded-lg transition-colors text-sm`}
                >
                  {isAnalyzingFinances ? 'АНАЛИЗИРУЮ...' : 'ЗАПУСТИТЬ'}
                </button>
              </div>

            </div>

            {/* Requirement: Need tech card or recipe */}
            {!(techCard || tcV2 || aiKitchenRecipe) && (
              <div className="mt-8 bg-yellow-600/20 border border-yellow-400/30 rounded-xl p-6 text-center">
                <div className="text-3xl mb-4">📝</div>
                <h3 className="text-lg font-bold text-yellow-300 mb-2">Сначала создайте рецепт</h3>
                <p className="text-gray-300 text-sm mb-4">
                  Для использования AI-функций создайте рецепт V1 выше или техкарту
                </p>
                <button
                  onClick={() => setCurrentView('create')}
                  className="bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700 text-white font-bold px-6 py-3 rounded-lg transition-all"
                >
                  Создать техкарту
                </button>
              </div>
            )}

          </div>
        )}

        {/* Menu Wizard - Placeholder for now */}
        {showMenuWizard && (
          <div className="max-w-4xl mx-auto text-center py-20">
            <div className="bg-gradient-to-r from-cyan-600/20 to-blue-600/20 border border-cyan-400/30 rounded-2xl p-12">
              <div className="text-8xl mb-6">🎯</div>
              <h2 className="text-5xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent mb-6">
                ГЕНЕРАТОР МЕНЮ
              </h2>
              <p className="text-2xl text-gray-300 mb-8">
                Мастер создания меню временно недоступен
              </p>
              <button 
                onClick={() => setShowMenuWizard(false)}
                className="bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-700 hover:to-gray-800 text-white font-bold px-8 py-4 rounded-lg text-lg transition-all"
              >
                ← Назад
              </button>
            </div>
          </div>
        )}

        {/* Placeholder for future wizard content - removed for now */}

        {/* TC-002: TechCards History View */}
        {currentView === 'techcards' && (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-purple-300 mb-2">📋 МОИ ТЕХКАРТЫ</h2>
              <p className="text-gray-400">Все созданные техкарты и их статусы</p>
            </div>
            
            {userHistory && userHistory.length > 0 ? (
              <div className="grid gap-4">
                {userHistory.filter(item => !item.is_menu).map((techcard, index) => {
                  const isV1Recipe = techcard.is_recipe === true || techcard.type === 'v1';
                  const isV2 = !isV1Recipe && (techcard.techcard_v2_data || techcard.status === 'READY');
                  return (
                    <div 
                      key={techcard.id || index}
                      className="bg-gray-800/50 rounded-xl p-6 border border-gray-700 hover:border-purple-500/50 transition-all cursor-pointer"
                      onClick={() => {
                        // Правильная загрузка V1 рецептов и V2 техкарт
                        
                        if (isV1Recipe) {
                          // Загружаем V1 рецепт в AI-Kitchen
                          console.log('📋 Opening V1 recipe in AI Kitchen:', techcard.dish_name || techcard.name);
                          setAiKitchenRecipe({
                            content: techcard.content,
                            id: techcard.id,
                            name: techcard.dish_name || techcard.name || 'Рецепт из истории',
                            created_at: techcard.created_at || new Date().toISOString()
                          });
                          setTechCard(null);
                          setTcV2(null);
                          setCurrentTechCardId(techcard.id);
                          
                          console.log('🔄 Switching to ai-kitchen view');
                          setCurrentView('ai-kitchen');
                          
                          // Скроллим вверх чтобы было видно AI Kitchen
                          setTimeout(() => {
                            console.log('📜 Scrolling to top');
                            window.scrollTo({ top: 0, behavior: 'smooth' });
                          }, 100);
                        } else if (isV2 && techcard.techcard_v2_data) {
                          // Загружаем V2 техкарту
                          setTcV2(techcard.techcard_v2_data);
                          setTechCard(null);
                          setWizardData(prev => ({...prev, dishName: techcard.name || techcard.techcard_v2_data?.meta?.title || 'Техкарта из истории'}));
                          setGenerationStatus('success');
                          setCurrentTechCardId(techcard.id);
                          setCurrentView('create');
                        } else if (techcard.content) {
                          // Попытка парсинга контента
                          try {
                            const parsedContent = JSON.parse(techcard.content);
                            setTcV2(parsedContent);
                            setTechCard(null);
                            setWizardData(prev => ({...prev, dishName: techcard.name || parsedContent?.meta?.title || 'Техкарта из истории'}));
                            setGenerationStatus('success');
                            setCurrentTechCardId(techcard.id);
                            setCurrentView('create');
                          } catch (e) {
                            // Если парсинг не удался, это V1 - открываем в AI-Kitchen
                            setAiKitchenRecipe({
                              content: techcard.content,
                              id: techcard.id,
                              name: techcard.dish_name || techcard.name || 'Рецепт из истории',
                              created_at: techcard.created_at || new Date().toISOString()
                            });
                            setTechCard(null);
                            setTcV2(null);
                            setCurrentTechCardId(techcard.id);
                            setCurrentView('aiKitchen');
                          }
                        }
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-white mb-2">
                            {techcard.dish_name || 'Без названия'}
                          </h3>
                          <div className="flex items-center space-x-4 text-sm text-gray-400">
                            <span>
                              📅 {new Date(techcard.created_at).toLocaleDateString('ru-RU')}
                            </span>
                            <span className={`px-2 py-1 rounded text-xs font-bold ${
                              (techcard.status === 'READY' || techcard.status === 'success') ? 'bg-green-600 text-white' : 
                              'bg-yellow-600 text-black'
                            }`}>
                              {techcard.status === 'READY' ? 'ГОТОВО' : (techcard.status || 'draft')}
                            </span>
                            <span className={`text-xs ${isV2 ? 'text-purple-400' : isV1Recipe ? 'text-pink-400' : 'text-gray-500'}`}>
                              {isV2 ? 'V2 Техкарта' : isV1Recipe ? 'V1 Рецепт' : 'V1'}
                            </span>
                          </div>
                        </div>
                        <div className="text-purple-400">
                          👁️
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-400">
                <div className="text-6xl mb-4">📝</div>
                <p className="text-xl">Техкарты не найдены</p>
                <p className="text-gray-500 mt-2">Создайте свою первую техkарту!</p>
                <button
                  onClick={() => setCurrentView('create')}
                  className="mt-6 bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-bold transition-colors"
                >
                  Создать техkарту
                </button>
              </div>
            )}
          </div>
        )}

        {/* Personal Cabinet View - Only for authenticated users */}
        {currentView === 'personal-cabinet' && (
          <>
            {currentUser && currentUser.id !== 'demo_user' ? (
              <div className="min-h-screen">
            {/* Modern SaaS-style Personal Cabinet with Sidebar */}
            <div className="flex flex-col lg:flex-row gap-6">
              
              {/* Sidebar Navigation */}
              <div className="lg:w-64 flex-shrink-0">
                <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-6 border border-gray-700 sticky top-6">
                  <div className="mb-6">
                    <h2 className="text-xl font-bold text-purple-300 mb-2">Личный кабинет</h2>
                    <p className="text-gray-400 text-sm truncate">{currentUser?.email}</p>
                  </div>
                  
                  <nav className="space-y-2">
                    <button
                      onClick={() => setPersonalCabinetTab('profile')}
                      className={`w-full text-left px-4 py-3 rounded-lg transition-all ${
                        personalCabinetTab === 'profile' 
                          ? 'bg-purple-600 text-white shadow-lg' 
                          : 'text-gray-300 hover:bg-gray-700/50'
                      }`}
                    >
                      Профиль
                    </button>
                    
                    <button
                      onClick={() => setPersonalCabinetTab('subscription')}
                      className={`w-full text-left px-4 py-3 rounded-lg transition-all ${
                        personalCabinetTab === 'subscription' 
                          ? 'bg-purple-600 text-white shadow-lg' 
                          : 'text-gray-300 hover:bg-gray-700/50'
                      }`}
                    >
                      Подписка
                    </button>
                    
                    <button
                      onClick={() => setPersonalCabinetTab('venue')}
                      className={`w-full text-left px-4 py-3 rounded-lg transition-all ${
                        personalCabinetTab === 'venue' 
                          ? 'bg-purple-600 text-white shadow-lg' 
                          : 'text-gray-300 hover:bg-gray-700/50'
                      }`}
                    >
                      Заведение
                    </button>
                    
                    <button
                      onClick={() => setPersonalCabinetTab('integrations')}
                      className={`w-full text-left px-4 py-3 rounded-lg transition-all ${
                        personalCabinetTab === 'integrations' 
                          ? 'bg-purple-600 text-white shadow-lg' 
                          : 'text-gray-300 hover:bg-gray-700/50'
                      }`}
                    >
                      Интеграции
                    </button>
                    
                    <button
                      onClick={() => setPersonalCabinetTab('settings')}
                      className={`w-full text-left px-4 py-3 rounded-lg transition-all ${
                        personalCabinetTab === 'settings' 
                          ? 'bg-purple-600 text-white shadow-lg' 
                          : 'text-gray-300 hover:bg-gray-700/50'
                      }`}
                    >
                      Настройки
                    </button>
                  </nav>
                  
                  <div className="mt-6 pt-6 border-t border-gray-700">
                    <button
                      onClick={() => setCurrentView('create')}
                      className="w-full text-left px-4 py-2 rounded-lg text-gray-300 hover:bg-gray-700/50 transition-all"
                    >
                      Вернуться
                    </button>
                  </div>
                </div>
              </div>

              {/* Main Content Area */}
              <div className="flex-1 min-w-0">
                <div className="space-y-6">
                  {/* Tab Content */}
                  {personalCabinetTab === 'profile' && (
                    <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-6 border border-gray-700">
                      <h3 className="text-2xl font-bold text-gray-200 mb-6">Профиль</h3>
                      
                      <div className="space-y-6">
                        {/* User Avatar & Info */}
                        <div className="bg-gray-700/30 rounded-xl p-6 border border-gray-600/30">
                          <div className="flex items-center gap-6">
                            <div className="w-20 h-20 rounded-full bg-gradient-to-r from-purple-600 to-purple-500 flex items-center justify-center text-3xl font-bold text-white">
                              {currentUser?.name?.charAt(0)?.toUpperCase() || 'U'}
                            </div>
                            <div className="flex-1">
                              <h4 className="text-xl font-bold text-white mb-1">{currentUser?.name || 'Пользователь'}</h4>
                              <p className="text-gray-400">{currentUser?.email || 'Email не указан'}</p>
                              {currentUser?.city && (
                                <p className="text-gray-400 text-sm mt-1">{currentUser.city}</p>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        {/* Profile Details */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="bg-gray-700/30 rounded-lg p-4 border border-gray-600/30">
                            <div className="text-gray-400 text-sm mb-1">Имя</div>
                            <div className="text-white font-medium">{currentUser?.name || 'Не указано'}</div>
                          </div>
                          <div className="bg-gray-700/30 rounded-lg p-4 border border-gray-600/30">
                            <div className="text-gray-400 text-sm mb-1">Email</div>
                            <div className="text-white font-medium">{currentUser?.email || 'Не указано'}</div>
                          </div>
                          <div className="bg-gray-700/30 rounded-lg p-4 border border-gray-600/30">
                            <div className="text-gray-400 text-sm mb-1">Город</div>
                            <div className="text-white font-medium">{currentUser?.city || 'Не указано'}</div>
                          </div>
                          <div className="bg-gray-700/30 rounded-lg p-4 border border-gray-600/30">
                            <div className="text-gray-400 text-sm mb-1">Дата регистрации</div>
                            <div className="text-white font-medium">
                              {currentUser?.created_at ? new Date(currentUser.created_at).toLocaleDateString('ru-RU') : 'Не указано'}
                            </div>
                          </div>
                        </div>
                        
                        {/* Actions */}
                        <div className="flex gap-3">
                          <button
                            onClick={() => {
                              setEditProfileData({
                                name: currentUser?.name || '',
                                email: currentUser?.email || '',
                                city: currentUser?.city || ''
                              });
                              setShowProfileEditModal(true);
                            }}
                            className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
                          >
                            Редактировать профиль
                          </button>
                          
                          {currentUser && !currentUser.password_hash && (
                            <button
                              onClick={() => {
                                setSetPasswordData({ password: '', confirmPassword: '' });
                                setShowSetPasswordModal(true);
                              }}
                              className="flex-1 bg-purple-500 hover:bg-purple-600 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
                            >
                              Установить пароль
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {personalCabinetTab === 'subscription' && (
                    <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-6 border border-gray-700">
                      <h3 className="text-2xl font-bold text-gray-200 mb-6">Подписка</h3>
                      
                      <div className="space-y-6">
                        {/* Current Plan */}
                        <div className="bg-gray-700/30 rounded-xl p-6 border border-gray-600/30">
                          <div className="flex items-center justify-between mb-4">
                            <div>
                              <h4 className="text-xl font-bold text-white mb-2">
                                {currentUser?.subscription_plan === 'pro' ? 'PRO План' : 'Базовый план'}
                              </h4>
                              <p className="text-gray-400">
                                {currentUser?.subscription_plan === 'pro' 
                                  ? 'Полный доступ ко всем функциям' 
                                  : 'Создание техкарт, экспорт в IIKO'}
                              </p>
                            </div>
                          </div>
                          
                          {currentUser?.subscription_plan === 'pro' && currentUser?.subscription_expires_at && (
                            <div className="mt-4 pt-4 border-t border-gray-600/30">
                              <div className="text-gray-400 text-sm">
                                Действует до: <span className="font-semibold text-white">
                                  {new Date(currentUser.subscription_expires_at).toLocaleDateString('ru-RU')}
                                </span>
                              </div>
                            </div>
                          )}
                        </div>
                        
                        {/* Upgrade Button */}
                        {currentUser?.subscription_plan !== 'pro' && (
                          <div className="text-center">
                            <button
                              onClick={() => {
                                console.log('🔵 Opening pricing page, currentUser:', currentUser);
                                setShowPricingPage(true);
                              }}
                              className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-8 rounded-lg transition-colors"
                            >
                              Улучшить до PRO
                            </button>
                          </div>
                        )}
                        
                        {/* Features Comparison */}
                        <div className="bg-gray-700/30 rounded-xl p-6 border border-gray-600/30">
                          <h5 className="text-lg font-semibold text-white mb-4">Что включено:</h5>
                          <div className="space-y-3">
                            <div className="flex items-center gap-3">
                              <div className="w-1.5 h-1.5 rounded-full bg-purple-500"></div>
                              <span className="text-gray-300">Создание неограниченного количества техкарт</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="w-1.5 h-1.5 rounded-full bg-purple-500"></div>
                              <span className="text-gray-300">Экспорт в IIKO RMS</span>
                            </div>
                            {currentUser?.subscription_plan === 'pro' ? (
                              <>
                                <div className="flex items-center gap-3">
                                  <div className="w-1.5 h-1.5 rounded-full bg-purple-500"></div>
                                  <span className="text-gray-300">AI-Кухня и Лаборатория</span>
                                </div>
                                <div className="flex items-center gap-3">
                                  <div className="w-1.5 h-1.5 rounded-full bg-purple-500"></div>
                                  <span className="text-gray-300">Финансовый анализ</span>
                                </div>
                                <div className="flex items-center gap-3">
                                  <div className="w-1.5 h-1.5 rounded-full bg-purple-500"></div>
                                  <span className="text-gray-300">Скрипты продаж и фудпейринг</span>
                                </div>
                              </>
                            ) : (
                              <>
                                <div className="flex items-center gap-3">
                                  <div className="w-1.5 h-1.5 rounded-full bg-gray-600"></div>
                                  <span className="text-gray-500">AI-Кухня и Лаборатория (PRO)</span>
                                </div>
                                <div className="flex items-center gap-3">
                                  <div className="w-1.5 h-1.5 rounded-full bg-gray-600"></div>
                                  <span className="text-gray-500">Финансовый анализ (PRO)</span>
                                </div>
                                <div className="flex items-center gap-3">
                                  <div className="w-1.5 h-1.5 rounded-full bg-gray-600"></div>
                                  <span className="text-gray-500">Скрипты продаж и фудпейринг (PRO)</span>
                                </div>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {personalCabinetTab === 'venue' && (
                    <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-6 border border-gray-700">
                      <h3 className="text-2xl font-bold text-gray-200 mb-6">Профиль заведения</h3>
                      
                      {venueProfile.venue_name ? (
                        <div className="space-y-6">
                          <div className="bg-gray-700/30 rounded-xl p-6 border border-gray-600/30">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                              <div>
                                <div className="text-gray-400 text-sm mb-1">Название</div>
                                <div className="text-white font-semibold text-lg">{venueProfile.venue_name}</div>
                              </div>
                              {venueProfile.venue_type && (
                                <div>
                                  <div className="text-gray-400 text-sm mb-1">Тип заведения</div>
                                  <div className="text-white font-medium">{venueTypes[venueProfile.venue_type]?.name}</div>
                                </div>
                              )}
                              {venueProfile.cuisine_focus && venueProfile.cuisine_focus.length > 0 && (
                                <div>
                                  <div className="text-gray-400 text-sm mb-1">Кухня</div>
                                  <div className="text-white font-medium">
                                    {venueProfile.cuisine_focus.map(c => cuisineTypes[c]?.name).join(', ')}
                                  </div>
                                </div>
                              )}
                              {venueProfile.average_check && (
                                <div>
                                  <div className="text-gray-400 text-sm mb-1">Средний чек</div>
                                  <div className="text-white font-medium">{venueProfile.average_check}₽</div>
                                </div>
                              )}
                            </div>
                          </div>
                          
                          <button
                            onClick={() => setShowVenueProfileModal(true)}
                            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
                          >
                            Редактировать профиль
                          </button>
                        </div>
                      ) : (
                        <div className="text-center py-12">
                          <h4 className="text-xl font-semibold text-gray-300 mb-2">Профиль заведения не настроен</h4>
                          <p className="text-gray-400 mb-6">Настройте профиль для персонализации функций</p>
                          <button
                            onClick={() => setShowVenueProfileModal(true)}
                            className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
                          >
                            Настроить профиль
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {personalCabinetTab === 'integrations' && (
                    <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-6 border border-gray-700">
                      <h3 className="text-2xl font-bold text-gray-200 mb-6">Интеграции</h3>
                      
                      <div className="space-y-6">
                        {/* IIKO RMS Integration */}
                        <div className="bg-gray-700/30 rounded-xl p-6 border border-gray-600/30">
                          <div className="flex items-center justify-between mb-4">
                            <div>
                              <h4 className="text-lg font-semibold text-white mb-1">IIKO RMS</h4>
                              <p className="text-gray-400 text-sm">Синхронизация номенклатуры и экспорт техкарт</p>
                            </div>
                            <div className={`px-4 py-2 rounded-full text-sm font-semibold ${
                              iikoRmsConnection.status === 'connected' 
                                ? 'bg-purple-600/20 text-purple-300 border border-purple-400/30' 
                                : 'bg-gray-600/20 text-gray-400 border border-gray-500/30'
                            }`}>
                              {iikoRmsConnection.status === 'connected' ? 'Подключено' : 'Не подключено'}
                            </div>
                          </div>
                          
                          {iikoRmsConnection.status === 'connected' ? (
                            <div className="space-y-4">
                              <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                  <div className="text-gray-400">Организация</div>
                                  <div className="text-white font-medium">{iikoRmsConnection.organization_name || 'N/A'}</div>
                                </div>
                                <div>
                                  <div className="text-gray-400">Товаров синхронизировано</div>
                                  <div className="text-white font-medium">{iikoRmsConnection.products_count || 0}</div>
                                </div>
                                <div>
                                  <div className="text-gray-400">Последняя синхронизация</div>
                                  <div className="text-white font-medium">
                                    {iikoRmsConnection.last_sync ? new Date(iikoRmsConnection.last_sync).toLocaleDateString('ru-RU') : 'Никогда'}
                                  </div>
                                </div>
                              </div>
                              
                              <div className="flex gap-3">
                                <button
                                  onClick={() => setShowIikoRmsModal(true)}
                                  className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
                                >
                                  Настройки
                                </button>
                                <button
                                  onClick={syncIikoRmsNomenclature}
                                  disabled={isSyncingIikoRms}
                                  className="flex-1 bg-purple-500 hover:bg-purple-600 disabled:bg-gray-600 disabled:text-gray-400 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
                                >
                                  {isSyncingIikoRms ? 'Синхронизация...' : 'Синхронизация'}
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="text-center py-4">
                              <button
                                onClick={() => setShowIikoRmsModal(true)}
                                className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
                              >
                                Подключить IIKO RMS
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {personalCabinetTab === 'settings' && (
                    <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-6 border border-gray-700">
                      <h3 className="text-2xl font-bold text-gray-200 mb-6">Настройки</h3>
                      
                      <div className="space-y-6">
                        <div className="bg-gray-700/30 rounded-xl p-6 border border-gray-600/30">
                          <h4 className="text-lg font-semibold text-white mb-4">Безопасность</h4>
                          <div className="space-y-4">
                            {currentUser && !currentUser.password_hash && (
                              <div className="bg-gray-600/20 border border-gray-500/30 rounded-lg p-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <div className="text-white font-medium mb-1">Пароль не установлен</div>
                                    <div className="text-gray-400 text-sm">Установите пароль для безопасности аккаунта</div>
                                  </div>
                                  <button
                                    onClick={() => {
                                      setSetPasswordData({ password: '', confirmPassword: '' });
                                      setShowSetPasswordModal(true);
                                    }}
                                    className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                                  >
                                    Установить
                                  </button>
                                </div>
                              </div>
                            )}
                            
                            <div className="bg-gray-600/20 rounded-lg p-4">
                              <div className="text-white font-medium mb-1">Метод входа</div>
                              <div className="text-gray-400 text-sm">
                                {currentUser?.provider === 'google' ? 'Google OAuth' : currentUser?.provider === 'email' ? 'Email/Пароль' : 'Не указано'}
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        <div className="bg-gray-700/30 rounded-xl p-6 border border-gray-600/30">
                          <h4 className="text-lg font-semibold text-white mb-4">Аккаунт</h4>
                          <div className="space-y-3">
                            <button
                              onClick={handleLogout}
                              className="w-full bg-gray-600 hover:bg-gray-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
                            >
                              Выйти из аккаунта
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
            ) : (
              // Demo user fallback - redirect to create view with message
              <div className="text-center py-12">
                <div className="bg-yellow-900/20 border border-yellow-400/30 rounded-xl p-8 max-w-md mx-auto">
                  <div className="text-6xl mb-4">🔒</div>
                  <h3 className="text-xl font-bold text-yellow-300 mb-3">Личный кабинет недоступен</h3>
                  <p className="text-gray-400 mb-6">
                    Для доступа к личному кабинету необходимо зарегистрироваться или войти в систему
                  </p>
                  <div className="space-y-3">
                    <button
                      onClick={() => setCurrentView('create')}
                      className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-4 rounded-lg transition-colors"
                    >
                      ← Вернуться к созданию техкарт
                    </button>
                    <button
                      onClick={() => setShowRegistrationModal(true)}
                      className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg transition-colors"
                    >
                      📝 Зарегистрироваться
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {/* Create Tech Card View (existing content) */}
        {currentView === 'create' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-10">
          {/* Left Panel - Chat when techcard exists, Form when not */}
          <div className="lg:col-span-1">
            {tcV2 || techCard ? (
              /* Culinary Assistant - Sidebar Mode */
              <div className="h-[calc(100vh-200px)]">
                <CulinaryAssistant 
                  userId={currentUserOrDemo?.id || 'demo_user'}
                  mode="sidebar"
                  onTechCardRequest={(data) => {
                    // Если пользователь просит создать техкарту из чата
                    if (typeof data === 'string') {
                      // Старый формат - только название
                      setDishName(data);
                      setTcV2(null);
                      setTechCard(null);
                    } else if (data && data.techCard) {
                      // Новый формат - техкарта уже создана через tool call
                      setTcV2(data.techCard);
                      setTechCard(null);
                      setCurrentTechCardId(data.techCard?.meta?.id || null);
                    } else if (data && data.dishName) {
                      // Формат с названием блюда
                      setDishName(data.dishName);
                      setTcV2(null);
                      setTechCard(null);
                    }
                  }}
                />
              </div>
            ) : (
              <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-4 sm:p-8 border border-gray-700 space-y-6 sm:space-y-8">
              <div>
                <div className="flex items-center justify-between mb-4 sm:mb-6">
                  <h2 className="text-xl sm:text-2xl font-semibold text-gray-200">СОЗДАТЬ ТЕХКАРТУ</h2>
                  <button
                    onClick={() => window.startTour_createTechcard && window.startTour_createTechcard()}
                    className="text-gray-400 hover:text-gray-300 transition-colors text-sm font-medium"
                    title="Показать тур: как создать техкарту"
                  >
                    Помощь
                  </button>
                </div>
                
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
                            <p>• <strong>📋 ТЕХКАРТЫ</strong> - все созданные техкарты сохраняются автоматически</p>
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
                        value={wizardData.dishName}
                        onChange={(e) => updateWizardData(1, { dishName: e.target.value })}
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
                            <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 0 1 5 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                          </svg>
                        )}
                      </button>
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={!wizardData.dishName.trim() || isGenerating}
                    className={`w-full ${isGenerating ? 'bg-gray-600 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'} text-white font-semibold py-3 sm:py-4 px-6 rounded-lg transition-colors flex items-center justify-center text-sm sm:text-base min-h-[48px] sm:min-h-[56px]`}
                    title="Создать профессиональную техническую карту с ингредиентами и процессом приготовления"
                  >
                    {isGenerating ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-3 h-4 w-4 sm:h-5 sm:w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        СОЗДАЮ РЕЦЕПТ...
                      </>
                    ) : 'СОЗДАТЬ ТЕХКАРТУ'}
                  </button>
                </form>
                
                {/* DEBUG INFO */}
                {isDebugMode && (
                  <div className="mt-4 bg-gray-800/50 border border-gray-600/50 rounded-lg p-3">
                    <h4 className="text-gray-300 font-bold text-xs mb-2">🐛 DEBUG INFO (?debug=1)</h4>
                    <div className="space-y-1 text-xs text-gray-400">
                      <div><strong>Status:</strong> {generationStatus || 'none'}</div>
                      <div><strong>First Issue:</strong> {generationIssues[0] || 'none'}</div>
                      <div><strong>Last Request:</strong> {
                        typeof window !== 'undefined' && window.__lastGenerationDebug ? 
                        `${window.__lastGenerationDebug.requestTime}ms at ${window.__lastGenerationDebug.timestamp}` : 
                        'none'
                      }</div>
                      <div><strong>TcV2 Present:</strong> {tcV2 ? 'yes' : 'no'}</div>
                    </div>
                  </div>
                )}
                
                {/* PRO Price Management - ВРЕМЕННО СКРЫТО ДЛЯ ПРОДАКШНА */}
                {false && (currentUserOrDemo.subscription_plan === 'pro' || currentUserOrDemo.subscription_plan === 'business' || currentUserOrDemo.demo_mode) && (
                  <div className="border-t border-purple-400/30 pt-4 sm:pt-6">
                    <h3 className="text-base sm:text-lg font-bold text-purple-300 mb-3 sm:mb-4">PRO ФУНКЦИИ</h3>
                    
                    {/* Venue Profile and Price Management moved to Personal Cabinet */}
                    {/* 
                    <button
                      onClick={() => setShowVenueProfileModal(true)}
                      className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold py-3 sm:py-4 px-4 sm:px-6 rounded-lg transition-all transform hover:scale-105 mb-3 sm:mb-4 text-sm sm:text-base min-h-[48px] shadow-lg"
                      title="🏢 Настройте тип заведения, кухню и средний чек для персонализации всех функций"
                    >
                      🏪 МОЕ ЗАВЕДЕНИЕ
                    </button>
                    */}
                    
                    {/* Show venue info if configured */}
                    {venueProfile.venue_type && (
                      <div className="text-xs sm:text-sm text-purple-300 text-center mb-3 sm:mb-4 p-2 bg-purple-900/20 rounded">
                        📍 {venueTypes[venueProfile.venue_type]?.name} • {venueProfile.cuisine_focus?.map(c => cuisineTypes[c]?.name).join(', ')} • {venueProfile.average_check}₽
                      </div>
                    )}
                    {userEquipment.length > 0 && (
                      <div className="text-xs sm:text-sm text-purple-400 text-center mb-3 sm:mb-4">
                        🔧 Выбрано {userEquipment.length} единиц оборудования
                      </div>
                    )}
                    
                    {/* Price Management moved to Personal Cabinet */}
                    {/* 
                    <button
                      onClick={() => setShowPriceModal(true)}
                      className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 sm:py-4 px-4 sm:px-6 rounded-lg transition-colors mb-3 sm:mb-4 text-sm sm:text-base min-h-[48px]"
                      title="📊 Загрузите Excel/CSV файлы с ценами поставщиков для точного расчета себестоимости"
                    >
                      УПРАВЛЕНИЕ ПРАЙСАМИ
                    </button>
                    */}
                    {/* TEMPORARILY HIDDEN - Price info
                    {userPrices.length > 0 && (
                      <div className="text-xs sm:text-sm text-green-400 text-center mb-3 sm:mb-4">
                        💰 Загружено {userPrices.length} позиций
                      </div>
                    )}
                    <div className="text-xs sm:text-sm text-green-400 text-center mb-3 sm:mb-4 p-2 bg-green-900/20 rounded">
                      ✅ Загрузка Excel/CSV прайс-листов полностью готова!
                    </div>
                    */}
                    
                    {/* Personal Cabinet Button - ВРЕМЕННО СКРЫТО ДЛЯ ПРОДАКШНА */}
                    {false && currentUser && currentUser.id !== 'demo_user' && (
                      <button
                        onClick={() => setCurrentView('personal-cabinet')}
                        className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold py-3 sm:py-4 px-4 sm:px-6 rounded-lg transition-all transform hover:scale-105 mb-4 text-sm sm:text-base min-h-[48px] shadow-lg"
                        title="👤 Личный кабинет: Настройки профиля и подключение IIKO"
                      >
                        👤 ЛИЧНЫЙ КАБИНЕТ
                      </button>
                    )}
                    
                    {/* ПРО AI функции - ВРЕМЕННО СКРЫТЫ ДЛЯ ПРОДАКШНА */}
                    {false && currentUser && currentUser.id !== 'demo_user' && (
                      <div className="border-t border-purple-400/20 pt-3 sm:pt-4">
                        <h4 className="text-sm sm:text-base font-bold text-purple-200 mb-3">AI ДОПОЛНЕНИЯ</h4>
                        
                        <div className="grid grid-cols-1 gap-2 sm:gap-3">
                        {/* V1 Recipe Creation moved to AI-Kitchen -> Laboratory */}
                        <button
                          onClick={() => generateSalesScript()}
                          disabled={isGenerating || !(techCard || tcV2 || aiKitchenRecipe)}
                          className={`w-full ${isGenerating || !(techCard || tcV2 || aiKitchenRecipe) ? 'bg-gray-600 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px]`}
                          title="💬 СКРИПТ ПРОДАЖ: Генерирует профессиональные тексты для официантов с аргументами и техниками продаж"
                        >
                          СКРИПТ ПРОДАЖ
                        </button>
                        
                        <button
                          onClick={generateFoodPairing}
                          disabled={isGenerating || !(techCard || tcV2 || aiKitchenRecipe)}
                          className={`w-full ${isGenerating || !(techCard || tcV2 || aiKitchenRecipe) ? 'bg-gray-600 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px]`}
                          title="🍷 ФУДПЕЙРИНГ: Подбирает идеальные напитки, гарниры и закуски к вашему блюду с объяснением сочетаний"
                        >
                          ФУДПЕЙРИНГ
                        </button>
                        
                        <button
                          onClick={generateInspiration}
                          disabled={isGenerating || !(techCard || tcV2 || aiKitchenRecipe)}
                          className={`w-full ${isGenerating || !(techCard || tcV2 || aiKitchenRecipe) ? 'bg-gray-600 cursor-not-allowed' : 'btn-inspiration'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px]`}
                          title="ВДОХНОВЕНИЕ: Создает креативный твист на ваше блюдо, используя техники и ингредиенты кухонь других стран"
                        >
                          ВДОХНОВЕНИЕ
                        </button>
                        
                        <button
                          onClick={conductExperiment}
                          disabled={isExperimenting}
                          className={`w-full ${isExperimenting ? 'bg-gray-600 cursor-not-allowed' : 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px] laboratory-button`}
                          title="ЛАБОРАТОРИЯ: Создает экспериментальные блюда с неожиданными сочетаниями ингредиентов и генерирует изображение результата"
                        >
                          {isExperimenting ? 'ЭКСПЕРИМЕНТИРУЮ...' : 'ЛАБОРАТОРИЯ'}
                        </button>
                        
                        <button
                          onClick={generatePhotoTips}
                          disabled={isGenerating || !(techCard || tcV2 || aiKitchenRecipe)}
                          className={`w-full ${isGenerating || !(techCard || tcV2 || aiKitchenRecipe) ? 'bg-gray-600 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px]`}
                          title="📸 СОВЕТЫ ПО ФОТО: Профессиональные рекомендации по фотографии блюд для социальных сетей и меню"
                        >
                          СОВЕТЫ ПО ФОТО
                        </button>
                        
                        <button
                          onClick={improveDish}
                          disabled={isImprovingDish || !(techCard || tcV2 || aiKitchenRecipe)}
                          className={`w-full ${isImprovingDish || !(techCard || tcV2 || aiKitchenRecipe) ? 'bg-gray-600 cursor-not-allowed' : 'bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px]`}
                          title="⚡ ПРОКАЧАТЬ БЛЮДО: Улучшает ваш рецепт профессиональными техниками и секретами шеф-поваров до версии 2.0"
                        >
                          {isImprovingDish ? 'УЛУЧШАЮ...' : '⚡ ПРОКАЧАТЬ БЛЮДО'}
                        </button>
                        
                        <button
                          onClick={analyzeFinances}
                          disabled={isAnalyzingFinances || !(techCard || tcV2 || aiKitchenRecipe)}
                          className={`w-full ${isAnalyzingFinances || !(techCard || tcV2 || aiKitchenRecipe) ? 'bg-gray-600 cursor-not-allowed' : 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700'} text-white font-bold py-3 px-4 rounded-lg transition-colors text-xs sm:text-sm min-h-[44px]`}
                          title="💼 ФИНАНСОВЫЙ АНАЛИЗ: Анализирует рентабельность блюда и дает конкретные советы по оптимизации затрат и увеличению прибыли"
                        >
                          {isAnalyzingFinances ? 'АНАЛИЗИРУЮ...' : '💼 ФИНАНСЫ'}
                        </button>
                        
                        {/* Убрали нерабочие iiko кнопки: "ЗАГРУЗИТЬ В IIKo" и "СОЗДАТЬ ТЕХKАРТУ В IIKo" */}
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Upgrade prompt for Free users */}
                {currentUserOrDemo.subscription_plan === 'free' && currentUserOrDemo.monthly_tech_cards_used >= 3 && (
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
              {(techCard || tcV2) && (
                <div className="border-t border-gray-700 pt-6 sm:pt-8">
                  <h3 className="text-lg sm:text-xl font-semibold text-gray-200 mb-4 sm:mb-6">
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
                      onClick={tcV2 ? handleEditTechCardV2 : handleEditTechCard}
                      disabled={!editInstruction.trim() || isEditingAI}
                      className="w-full bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-semibold py-3 sm:py-4 px-6 rounded-lg transition-colors flex items-center justify-center text-sm sm:text-base min-h-[48px] sm:min-h-[56px]"
                      title="Изменить техкарту с помощью ИИ на основе ваших инструкций"
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
                    
                    {/* AI Suggestions Button - СКРЫТО: endpoint не реализован на backend */}
                    {false && tcV2 && (
                      <button
                        onClick={getAISuggestions}
                        disabled={loadingMessage.includes('предложения')}
                        className="w-full bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-bold py-2 px-4 rounded-lg transition-colors flex items-center justify-center text-sm min-h-[40px] mt-2"
                        title="💡 Получить предложения AI по улучшению техкарты"
                      >
                        {loadingMessage.includes('предложения') ? (
                          <>
                            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            АНАЛИЗИРУЮ...
                          </>
                        ) : '💡 AI ПРЕДЛОЖЕНИЯ'}
                      </button>
                    )}
                  </div>
                  
                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    className="w-full mt-4 bg-gray-600 hover:bg-gray-700 text-white font-semibold py-3 sm:py-4 px-6 rounded-lg transition-colors text-sm sm:text-base min-h-[48px] sm:min-h-[56px]"
                    title="Открыть режим ручного редактирования техкарты в текстовом поле"
                  >
                    {isEditing ? 'ЗАКРЫТЬ РЕДАКТОР' : 'РУЧНОЕ РЕДАКТИРОВАНИЕ'}
                  </button>
                </div>
              )}

              {/* Manual Editing */}
              {isEditing && techCard && (
                <div className="border-t border-gray-700 pt-6 sm:pt-8">
                  <h3 className="text-lg sm:text-xl font-semibold text-gray-200 mb-4 sm:mb-6">
                    РУЧНОЕ РЕДАКТИРОВАНИЕ
                  </h3>
                  <div className="space-y-4">
                    {/* УПРОЩЕНИЕ: Убрали кнопки редактирования ингредиентов и этапов - функционал не используется */}
                    {/* 
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
                    */}
                    <div className="text-center text-gray-400 py-8">
                      <p>Ручное редактирование временно недоступно</p>
                      <p className="text-sm mt-2">Используйте ИИ-редактирование выше</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
            )}
          </div>

          {/* Right Panel */}
          <div className="lg:col-span-2">
            {techCard || tcV2 ? (
              <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-4 sm:p-8 border border-gray-700">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 sm:mb-8 gap-4">
                  <div>
                    <h2 className="text-xl sm:text-2xl font-bold text-purple-300">ТЕХНОЛОГИЧЕСКАЯ КАРТА</h2>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">
                      💡 Кликните на любой текст для редактирования
                    </p>
                  </div>
                  <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4 w-full sm:w-auto">
                    {/* P1: Enhanced iiko Connection Header */}
                    <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                      iikoRmsConnection.status === 'connected' ? 'bg-green-600/20 text-green-300 border border-green-400/30' :
                      iikoRmsConnection.status === 'needs_reconnection' ? 'bg-yellow-600/20 text-yellow-300 border border-yellow-400/30' :
                      iikoRmsConnection.status === 'error' ? 'bg-red-600/20 text-red-300 border border-red-400/30' :
                      'bg-gray-600/20 text-gray-300 border border-gray-400/30'
                    }`}>
                      {iikoRmsConnection.status === 'connected' ? (
                        <span>
                          ✅ Подключено к iiko
                          {localStorage.getItem('lastMappingAction') && (() => {
                            try {
                              const lastAction = JSON.parse(localStorage.getItem('lastMappingAction'));
                              const time = new Date(lastAction.timestamp).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
                              return ` · Последний экспорт ${time}`;
                            } catch {
                              return '';
                            }
                          })()}
                        </span>
                      ) : iikoRmsConnection.status === 'needs_reconnection' ? '⚠️ Нужно переподключиться' :
                        iikoRmsConnection.status === 'error' ? '❌ Ошибка iiko' :
                        '🔧 Настройка iiko'}
                    </div>
                  </div>
                  
                  {/* P1: Basic Mode - 5 Core Actions Only */}
                  <div className="flex flex-wrap gap-3 mt-4">
                    {/* 1. Автомаппинг (iiko) */}
                    <button 
                      onClick={debouncedStartAutoMapping}
                      disabled={isAutoMapping || (currentUser && iikoRmsConnection.status !== 'connected')}
                      className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-bold transition-colors text-sm min-h-[44px] flex items-center"
                      title={currentUser ? "Связать ингредиенты техкарты с товарами в вашей IIKO системе" : "Демо-автомаппинг доступен без подключения"}
                    >
                      {isAutoMapping ? '⏳ Анализ...' : '🔗 Связать с IIKO'}
                    </button>
                    
                    {/* УПРОЩЕНИЕ UI: Убрали дублирующуюся кнопку "Экспорт номенклатур" - функция есть в мастере экспорта */}
                    
                    {/* CREATE EXPORT WIZARD UI - Unified Export Button */}
                    <button 
                      onClick={() => { openExportWizard(); }}
                      disabled={!tcV2}
                      className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-8 py-4 rounded-lg font-semibold transition-colors text-lg min-h-[64px] flex items-center justify-center"
                      title="Экспорт техкарты в разные форматы - PDF, XLSX, ZIP для IIKO"
                    >
                      ЭКСПОРТ
                    </button>
                    
                    {/* СКРЫТО: Кнопка импорта TTK временно недоступна */}
                    {/*
                    <button 
                      onClick={() => setShowXlsxImportModal(true)}
                      className="bg-gradient-to-r from-orange-600 to-orange-700 hover:from-orange-700 hover:to-orange-800 text-white px-4 py-2 rounded-lg font-bold transition-colors text-sm min-h-[44px] flex items-center"
                      title="Импорт технологической карты из XLSX файла"
                    >
                      📥 Импорт TTK
                    </button>
                    */}
                    
                    {/* УДАЛЕНО: Кнопка синхронизации перенесена в МОЕ ЗАВЕДЕНИЕ */}
                    {/* 
                    <button 
                      onClick={() => setShowIikoRmsModal(true)}
                      className="bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white px-4 py-2 rounded-lg font-bold transition-colors text-sm min-h-[44px] flex items-center"
                      title="Синхронизация цен и номенклатуры с iiko RMS"
                    >
                      🔄 Синхронизация
                    </button>
                    */}
                    
                    {/* УДАЛЕНО: Кнопка дополнительно с legacy функциями */}
                    {/*
                    <div className="relative advanced-actions-dropdown">
                      <button 
                        onClick={() => setShowAdvancedActions(!showAdvancedActions)}
                        className="bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-700 hover:to-gray-800 text-white px-4 py-2 rounded-lg font-bold transition-colors text-sm min-h-[44px] flex items-center"
                        title="Дополнительные действия и экспорты"
                      >
                        ⚙️ Дополнительно ▾
                      </button>
                      
                      {showAdvancedActions && (
                        <div className="absolute right-0 top-full mt-2 w-64 bg-gray-800 border border-gray-600 rounded-lg shadow-xl z-50">
                          <div className="p-2 space-y-1">
                            <button 
                              onClick={() => { navigator.clipboard.writeText(techCard); setShowAdvancedActions(false); }}
                              disabled={!techCard}
                              className="w-full text-left px-3 py-2 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm text-white transition-colors"
                              title="Скопировать техкарту в буфер обмена"
                            >
                              📋 Копировать техкарту
                            </button>
                            <button 
                              onClick={() => { handlePrintTechCard(); setShowAdvancedActions(false); }}
                              disabled={!tcV2}
                              className="w-full text-left px-3 py-2 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm text-white transition-colors"
                              title="Экспорт в PDF для печати"
                            >
                              📄 Экспорт в PDF
                            </button>
                            <button 
                              onClick={() => { handleGostPrint(); setShowAdvancedActions(false); }}
                              disabled={!tcV2}
                              className="w-full text-left px-3 py-2 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm text-white transition-colors"
                              title="ГОСТ-печать A4"
                            >
                              🏛️ ГОСТ-печать
                            </button>
                            <hr className="border-gray-600 my-1" />
                            <button 
                              onClick={() => { handleIikoExport(); setShowAdvancedActions(false); }}
                              disabled={!tcV2}
                              className="w-full text-left px-3 py-2 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm text-white transition-colors"
                              title="Legacy экспорт в iiko"
                            >
                              📊 Legacy iiko Export
                            </button>
                            <button 
                              onClick={() => { handleIikoCsvExport(); setShowAdvancedActions(false); }}
                              disabled={!tcV2}
                              className="w-full text-left px-3 py-2 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm text-white transition-colors"
                              title="iiko CSV для импорта"
                            >
                              📄 iiko CSV (ZIP)
                            </button>

                          </div>
                        </div>
                      )}
                    </div>
                    */}
                  </div>
                </div>
                
                {/* AUTO-MAPPING STATUS BANNER (IK-02B-FE/02) */}
                {autoMappingMessage.text && (
                  <div className={`mb-4 p-4 rounded-lg border ${
                    autoMappingMessage.type === 'success' ? 'bg-green-900/30 border-green-400/30 text-green-300' :
                    autoMappingMessage.type === 'error' ? 'bg-red-900/30 border-red-400/30 text-red-300' :
                    'bg-blue-900/30 border-blue-400/30 text-blue-300'
                  }`}>
                    <div className="flex items-center justify-between">
                      <span>{autoMappingMessage.text}</span>
                      {tcV2Backup && (
                        <button
                          onClick={undoAutoMappingChanges}
                          className="ml-4 bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors"
                        >
                          ↶ Отменить изменения
                        </button>
                      )}
                    </div>
                  </div>
                )}
                
                {/* COVERAGE SUMMARY BANNER */}
                {tcV2 && (tcV2.costMeta || tcV2.nutritionMeta || tcV2.ingredients) && (
                  <div className="mb-4 bg-gray-800/50 border border-gray-600/50 rounded-lg p-4">
                    <div className="flex flex-wrap items-center gap-4 text-sm">
                      {tcV2.costMeta && (
                        <div className="flex items-center space-x-2">
                          <span className="text-gray-400">💰 Покрытие цен:</span>
                          <span className={`font-bold ${tcV2.costMeta.coveragePct >= 80 ? 'text-green-300' : tcV2.costMeta.coveragePct >= 50 ? 'text-yellow-300' : 'text-red-300'}`}>
                            {tcV2.costMeta.coveragePct}%
                          </span>
                          <span className="text-gray-500">({tcV2.costMeta.source})</span>
                        </div>
                      )}
                      {tcV2.nutritionMeta && (
                        <div className="flex items-center space-x-2">
                          <span className="text-gray-400">📊 Покрытие БЖУ:</span>
                          <span className={`font-bold ${tcV2.nutritionMeta.coveragePct >= 80 ? 'text-green-300' : tcV2.nutritionMeta.coveragePct >= 50 ? 'text-yellow-300' : 'text-red-300'}`}>
                            {tcV2.nutritionMeta.coveragePct}%
                          </span>
                        </div>
                      )}
                      {tcV2.ingredients && Array.isArray(tcV2.ingredients) && (
                        <div className="flex items-center space-x-2">
                          <span className="text-gray-400">⚠ Без SKU:</span>
                          <span className="text-orange-300 font-bold">
                            {tcV2.ingredients.filter(ing => !ing.skuId).length}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* STATUS BANNERS */}
                {generationStatus === 'error' && generationError && (
                  <div className="mb-6 bg-red-900/30 border border-red-500/50 rounded-lg p-4">
                    <div className="flex items-start space-x-3">
                      <div className="text-red-400 text-xl">❌</div>
                      <div>
                        <h4 className="text-red-300 font-bold mb-1">Не удалось сгенерировать</h4>
                        <p className="text-red-200 text-sm">{generationError}</p>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* CLEANUP TECH CARD DATA & UI: Убираем отображение проблем генерации */}
                
                <div className="prose prose-invert max-w-none">
                  {/* DEBUG INFO */}
                  {isDebugMode && (
                    <div className="bg-yellow-900/20 border border-yellow-600 p-2 mb-4 text-xs">
                      <p>DEBUG: tcV2 = {tcV2 ? 'YES' : 'NO'}, techCard = {techCard ? 'YES' : 'NO'}</p>
                      <p>TechCard length: {techCard?.length || 0}</p>
                      <p>TechCard type: {typeof techCard}</p>
                      <p>Preview: {techCard ? techCard.substring(0, 50) + '...' : 'null'}</p>
                    </div>
                  )}
                  
                  {/* Support both V1 Recipes/Tech Cards and V2 Tech Cards */}
                  {tcV2 ? (
                    renderTechCardV2(tcV2)
                  ) : techCard ? (
                    <div className="bg-gradient-to-r from-pink-900/20 to-rose-900/20 border border-pink-400/30 rounded-xl p-4 mb-6">
                      <div className="flex items-center gap-3 mb-4">
                        <span className="text-pink-300 text-2xl">🍳</span>
                        <div>
                          <h3 className="text-pink-300 font-bold">Рецепт V1</h3>
                          <p className="text-pink-400/70 text-sm">Красивый рецепт для экспериментов и обучения</p>
                        </div>
                      </div>
                      {formatTechCard(techCard)}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-gray-400 space-y-4">
                      <div>
                        <p className="text-xl font-semibold text-gray-300">ТЕХКАРТА ПОЯВИТСЯ ЗДЕСЬ</p>
                        <p className="text-lg">После создания техкарты или рецепта</p>
                        <div className="flex gap-4 justify-center mt-6">
                          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-3">
                            <div className="text-gray-200 font-medium">Техкарты V2</div>
                            <div className="text-gray-400 text-sm">Для бизнеса и IIKO</div>
                          </div>
                          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-3">
                            <div className="text-gray-200 font-medium">Рецепты V1</div>
                            <div className="text-gray-400 text-sm">Для экспериментов</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* УПРОЩЕНИЕ UI: Убрали встроенный редактор ингредиентов - он не работал и перегружал интерфейс */}

              </div>
            ) : (
              <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-12 border border-gray-700 text-center">
                <h3 className="text-2xl font-semibold text-gray-300 mb-4">ТЕХКАРТА ПОЯВИТСЯ ЗДЕСЬ</h3>
                <p className="text-gray-400">Введите название блюда слева и нажмите "СОЗДАТЬ ТЕХКАРТУ"</p>
              </div>
            )}
          </div>
        </div>
        )}
      </main>

      {/* Voice Recognition Modal */}
      {showVoiceModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={(e)=>{ if (e.target===e.currentTarget) closeAllModals(); }}>
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

      {/* УПРОЩЕНИЕ UI: Убрали модальное окно редактора ингредиентов - не использовалось */}

      {/* УПРОЩЕНИЕ UI: Убрали модальное окно редактора этапов - не использовалось */}

      {/* Price Management Modal - PRO only */}
      {showPriceModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={(e)=>{ if (e.target===e.currentTarget) closeAllModals(); }}>
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
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={(e)=>{ if (e.target===e.currentTarget) closeAllModals(); }}>
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
          <div className="bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 rounded-3xl p-10 max-w-lg w-full mx-4 border border-purple-500/30 shadow-2xl animate-in slide-in-from-bottom duration-500">
            <div className="text-center">
              {/* Enhanced Animated Icon */}
              <div className="mb-8 relative">
                <div className="w-24 h-24 mx-auto relative">
                  {/* Rotating outer ring */}
                  <div className="absolute inset-0 border-4 border-purple-500/30 rounded-full animate-spin"></div>
                  <div className="absolute inset-2 border-4 border-t-purple-500 border-r-pink-500 border-b-purple-500/20 border-l-pink-500/20 rounded-full animate-spin" style={{animationDuration: '2s', animationDirection: 'reverse'}}></div>
                  
                  {/* Central pulsating core */}
                  <div className="absolute inset-4 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full animate-pulse"></div>
                  <div className="absolute inset-6 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full animate-ping opacity-75"></div>
                  
                  {/* Dynamic emoji center */}
                  <div className="absolute inset-0 flex items-center justify-center text-2xl animate-bounce">
                    {loadingType === 'menu' ? '🍽️' : '📋'}
                  </div>
                </div>
                
                {/* Floating particles */}
                <div className="absolute -top-2 -left-2 w-2 h-2 bg-purple-400 rounded-full animate-bounce opacity-60" style={{animationDelay: '0.5s'}}></div>
                <div className="absolute -top-4 right-4 w-1.5 h-1.5 bg-pink-400 rounded-full animate-bounce opacity-60" style={{animationDelay: '1s'}}></div>
                <div className="absolute bottom-0 -left-4 w-1 h-1 bg-purple-300 rounded-full animate-bounce opacity-60" style={{animationDelay: '1.5s'}}></div>
              </div>
              
              {/* Enhanced Loading Message */}
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-300 to-pink-300 mb-3">
                  {loadingType === 'techcard' && '✨ Генерирую техкарту'}
                  {loadingType === 'menu' && '🎯 Создаю идеальное меню'}
                  {loadingType === 'sales' && '🎭 Создаю скрипт продаж'}
                  {loadingType === 'pairing' && '🍷 Подбираю сочетания'}
                  {loadingType === 'photo' && '📸 Готовлю советы по фото'}
                  {loadingType === 'inspiration' && '🌟 Создаю вдохновение'}
                  {loadingType === 'conversion' && '🔄 Конвертирую V1 → V2'}
                </h3>
                <p className="text-purple-300 text-base animate-pulse font-medium">
                  {loadingMessage}
                </p>
              </div>
              
              {/* Enhanced Progress Bar */}
              <div className="mb-8">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-purple-300 text-sm font-medium">Прогресс</span>
                  <span className="text-purple-300 text-sm font-bold">{Math.round(loadingProgress)}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-3 mb-2 overflow-hidden shadow-inner">
                  <div 
                    className="bg-gradient-to-r from-purple-500 via-pink-500 to-purple-400 h-full rounded-full transition-all duration-500 ease-out relative"
                    style={{ width: `${loadingProgress}%` }}
                  >
                    {/* Animated glow effect */}
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
                    {/* Moving highlight */}
                    <div className="absolute top-0 left-0 h-full w-8 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-ping"></div>
                  </div>
                </div>
              </div>
              
              {/* Enhanced Fun Animation */}
              <div className="flex justify-center space-x-1 mb-8">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-2 h-2 rounded-full animate-bounce ${
                      i % 2 === 0 ? 'bg-purple-400' : 'bg-pink-400'
                    }`}
                    style={{ animationDelay: `${i * 0.15}s` }}
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

              {/* Tips and Lifehacks for V1 to V2 Conversion */}
              {loadingType === 'conversion' && (
                <div className="mt-8 p-4 bg-gradient-to-br from-orange-900/20 to-purple-900/20 rounded-xl border border-orange-400/30">
                  <div className="flex items-start space-x-3">
                    <div className="text-3xl flex-shrink-0 animate-bounce">
                      {conversionTips[currentConversionTipIndex]?.icon}
                    </div>
                    <div className="text-left">
                      <h4 className="text-orange-300 font-bold text-sm mb-2">
                        {conversionTips[currentConversionTipIndex]?.title}
                      </h4>
                      <p className="text-gray-300 text-xs leading-relaxed">
                        {conversionTips[currentConversionTipIndex]?.text}
                      </p>
                    </div>
                  </div>
                  <div className="mt-3 flex justify-center space-x-1">
                    {conversionTips.map((_, index) => (
                      <div
                        key={index}
                        className={`w-1.5 h-1.5 rounded-full transition-all ${
                          index === currentConversionTipIndex ? 'bg-orange-400' : 'bg-gray-600'
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
                onClick={async () => {
                  // Извлекаем название блюда из результата
                  const lines = inspirationResult.split('\n');
                  const nameMatch = lines.find(line => line.includes('Название:'));
                  const dishName = nameMatch ? nameMatch.replace(/\*\*Название:\*\*|Название:/, '').trim() : 'Вдохновение';
                  
                  const saved = await saveAIResultAsV1(inspirationResult, dishName, 'inspiration');
                  if (saved) {
                    setShowInspirationModal(false);
                  }
                }}
                className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white px-6 py-2 rounded-lg"
              >
                💾 СОХРАНИТЬ КАК V1
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
            
            {/* Статистика точности расчета */}
            {financesResult.price_accuracy && (
              <div className="mb-6 p-4 bg-gradient-to-r from-blue-900/20 to-purple-900/20 rounded-xl border border-blue-400/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="text-3xl">🎯</div>
                    <div>
                      <div className="text-blue-300 font-bold">Точность расчета: {financesResult.price_accuracy.accuracy_percent}%</div>
                      <div className="text-gray-400 text-sm">
                        {financesResult.price_accuracy.iiko_matched} из {financesResult.price_accuracy.total_ingredients} ингредиентов - цены из вашего IIKO каталога
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-green-400 font-bold text-lg">✓ {financesResult.price_accuracy.iiko_matched} точных</div>
                    <div className="text-yellow-400 text-sm">≈ {financesResult.price_accuracy.market_estimated} оценочных</div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Краткая сводка */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
              <div className="bg-gradient-to-r from-green-600/20 to-emerald-600/20 rounded-xl p-6 text-center border border-green-500/30 shadow-lg">
                <div className="text-green-300 text-sm font-bold uppercase tracking-wider">Себестоимость</div>
                <div className="text-3xl font-bold text-white mt-2">{financesResult.total_cost}₽</div>
                <div className="text-green-400 text-xs mt-1">на 1 порцию</div>
              </div>
              <div className="bg-gradient-to-r from-blue-600/20 to-cyan-600/20 rounded-xl p-6 text-center border border-blue-500/30 shadow-lg">
                <div className="text-blue-300 text-sm font-bold uppercase tracking-wider">💰 Поставьте в меню</div>
                <div className="text-3xl font-bold text-white mt-2">{financesResult.recommended_price}₽</div>
                <div className="text-blue-400 text-xs mt-1">
                  {financesResult.price_reasoning ? (
                    <span title={`${financesResult.price_reasoning.final_recommendation}`}>
                      × {((financesResult.recommended_price / financesResult.total_cost) || 3).toFixed(1)} коэффициент
                    </span>
                  ) : (
                    `× ${((financesResult.recommended_price / financesResult.total_cost) || 3).toFixed(1)} коэффициент`
                  )}
                </div>
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
            
            {/* Детализация рекомендуемой цены */}
            {financesResult.price_reasoning && (
              <div className="mb-8 bg-gradient-to-r from-indigo-900/20 to-blue-900/20 rounded-xl p-6 border border-indigo-400/30">
                <h3 className="text-xl font-bold text-indigo-300 mb-4 flex items-center">
                  💡 Как мы рассчитали рекомендуемую цену
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
                    <span className="text-gray-300">Себестоимость блюда:</span>
                    <span className="text-white font-bold">{financesResult.price_reasoning.cost_base || financesResult.total_cost}₽</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
                    <span className="text-gray-300">
                      Типичная наценка для вашего типа заведения ({financesResult.price_reasoning.venue_markup || '3.0x'}):
                    </span>
                    <span className="text-blue-300 font-bold">{financesResult.price_reasoning.suggested_by_markup}₽</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
                    <span className="text-gray-300">Средняя цена у конкурентов:</span>
                    <span className="text-purple-300 font-bold">{financesResult.price_reasoning.competitor_average}₽</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gradient-to-r from-indigo-600/20 to-blue-600/20 rounded-lg border border-indigo-400/30">
                    <span className="text-indigo-200 font-bold">✨ Итоговая рекомендация:</span>
                    <span className="text-white font-bold text-xl">{financesResult.recommended_price}₽</span>
                  </div>
                  <div className="mt-3 p-3 bg-blue-900/20 rounded-lg border-l-4 border-blue-400">
                    <p className="text-blue-200 text-sm">{financesResult.price_reasoning.final_recommendation}</p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Разбор ингредиентов с актуальными ценами */}
            {financesResult.ingredient_breakdown && financesResult.ingredient_breakdown.length > 0 && (
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-green-300 mb-6 flex items-center">
                  🛒 ДЕТАЛИЗАЦИЯ СТОИМОСТИ ИНГРЕДИЕНТОВ
                  <span className="ml-3 text-sm text-gray-400 font-normal">с указанием источников цен</span>
                </h3>
                <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl p-6 border border-gray-600/30">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-600">
                          <th className="text-left py-3 px-4 text-green-300 font-bold">ИНГРЕДИЕНТ</th>
                          <th className="text-center py-3 px-4 text-blue-300 font-bold">СТОИМОСТЬ</th>
                          <th className="text-center py-3 px-4 text-purple-300 font-bold">% ОТ ОБЩЕЙ</th>
                          <th className="text-center py-3 px-4 text-orange-300 font-bold">ИСТОЧНИК</th>
                          <th className="text-left py-3 px-4 text-yellow-300 font-bold">ОПТИМИЗАЦИЯ</th>
                        </tr>
                      </thead>
                      <tbody>
                        {financesResult.ingredient_breakdown.map((item, index) => (
                          <tr key={index} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                            <td className="py-3 px-4 text-white font-medium">{item.ingredient}</td>
                            <td className="py-3 px-4 text-center text-blue-200 font-bold">{item.cost}</td>
                            <td className="py-3 px-4 text-center text-purple-200">{item.percent_of_total}</td>
                            <td className="py-3 px-4 text-center">
                              {item.price_source === 'iiko' ? (
                                <span className="inline-flex items-center px-2 py-1 rounded text-xs font-bold bg-green-600/20 text-green-300 border border-green-400/30" title="Точная цена из вашего IIKO каталога">
                                  ✓ IIKO
                                </span>
                              ) : (
                                <span className="inline-flex items-center px-2 py-1 rounded text-xs font-bold bg-yellow-600/20 text-yellow-300 border border-yellow-400/30" title="Рыночная оценка на основе поиска">
                                  ≈ Оценка
                                </span>
                              )}
                            </td>
                            <td className="py-3 px-4 text-gray-300 text-xs">{item.optimization_tip || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
            
            {/* Старая версия таблицы (fallback если нет ingredient_breakdown) */}
            {!financesResult.ingredient_breakdown && financesResult.ingredient_costs && (
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
                onClick={async () => {
                  const dishName = improveDishResult.split('\n')[0]?.replace(/\*\*/g, '').replace('Название:', '').trim() || 'Прокачанное блюдо';
                  
                  const saved = await saveAIResultAsV1(improveDishResult, dishName, 'improved_dish');
                  if (saved) {
                    setShowImproveDishModal(false);
                  }
                }}
                className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white px-6 py-3 rounded-lg font-bold transition-colors"
              >
                💾 СОХРАНИТЬ КАК V1
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
              <h2 className="text-2xl font-bold text-cyan-300">ЛАБОРАТОРИЯ: ЭКСПЕРИМЕНТ ЗАВЕРШЕН!</h2>
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
                  const dishName = `Эксперимент: ${laboratoryResult.experiment_type}`;
                  
                  const saved = await saveAIResultAsV1(laboratoryResult.experiment, dishName, 'laboratory_experiment');
                  if (saved) {
                    setShowLaboratoryModal(false);
                  }
                }}
                className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white px-6 py-3 rounded-lg font-bold transition-colors"
                title="💾 Сохранить эксперимент как V1 рецепт"
              >
                💾 СОХРАНИТЬ КАК V1
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
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50" onClick={(e)=>{ if (e.target===e.currentTarget) closeAllModals(); }}>
          <div className="bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 rounded-xl p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto border border-purple-400/30">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-purple-300 flex items-center gap-3">
                Профиль заведения
                {profileStep > 1 && (
                  <span className="text-sm bg-purple-600 text-white px-3 py-1 rounded-full">
                    Шаг {profileStep}/4
                  </span>
                )}
              </h2>
              <button
                onClick={() => {
                  setShowVenueProfileModal(false);
                  setProfileStep(0); // Reset to IIKO tab
                }}
                className="text-gray-400 hover:text-white transition-colors text-2xl"
              >
                ✕
              </button>
            </div>

            {/* Navigation Tabs */}
            <div className="flex space-x-4 mb-6 border-b border-gray-600">
              <button
                onClick={() => setProfileStep(0)}
                className={`px-4 py-2 font-medium transition-colors ${
                  profileStep === 0 
                    ? 'border-b-2 border-purple-400 text-purple-300' 
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                IIKO Подключение
              </button>
              <button
                onClick={() => setProfileStep(1)}
                className={`px-4 py-2 font-medium transition-colors ${
                  profileStep >= 1 
                    ? 'border-b-2 border-purple-400 text-purple-300' 
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Профиль заведения
              </button>
              <button
                onClick={() => setProfileStep(5)}
                className={`px-4 py-2 font-medium transition-colors ${
                  profileStep >= 5 
                    ? 'border-b-2 border-purple-400 text-purple-300' 
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Глубокое исследование
              </button>
            </div>

            {/* IIKO Connection Tab */}
            {profileStep === 0 && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <h3 className="text-xl font-bold text-purple-200 mb-2">Подключение к IIKO</h3>
                  <p className="text-gray-300">Введите данные вашей IIKO системы для экспорта техкарт</p>
                  <p className="text-sm text-yellow-300 mt-2">⚠️ Эти данные нужны только для экспорта в IIKO. Создание техкарт работает без подключения.</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-gradient-to-br from-blue-900/20 to-blue-800/20 border border-blue-400/30 rounded-xl p-6">
                    <h4 className="text-lg font-bold text-blue-300 mb-4">Данные для подключения</h4>
                    
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Адрес сервера IIKO
                        </label>
                        <input
                          type="text"
                          value={iikoRmsCredentials.host}
                          onChange={(e) => setIikoRmsCredentials(prev => ({ ...prev, host: e.target.value }))}
                          placeholder="Например: ваше-заведение.iiko.it"
                          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Логин
                        </label>
                        <input
                          type="text"
                          value={iikoRmsCredentials.login}
                          onChange={(e) => setIikoRmsCredentials(prev => ({ ...prev, login: e.target.value }))}
                          placeholder="Ваш логин IIKO"
                          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Пароль
                        </label>
                        <input
                          type="password"
                          value={iikoRmsCredentials.password}
                          onChange={(e) => setIikoRmsCredentials(prev => ({ ...prev, password: e.target.value }))}
                          placeholder="Ваш пароль IIKO"
                          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      
                      {iikoRmsCredentials.host && iikoRmsCredentials.login && iikoRmsCredentials.password && (
                        <button
                          onClick={connectToIikoRms}
                          disabled={isConnectingIikoRms}
                          className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-600 disabled:to-gray-700 text-white px-4 py-3 rounded-lg font-bold transition-colors"
                        >
                          {isConnectingIikoRms ? 'Подключаюсь...' : 'Проверить подключение'}
                        </button>
                      )}
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-br from-green-900/20 to-green-800/20 border border-green-400/30 rounded-xl p-6">
                    <h4 className="text-lg font-bold text-green-300 mb-4">Как получить данные?</h4>
                    
                    <div className="space-y-3 text-sm text-gray-300">
                      <div>
                        <span className="font-bold text-green-400">Адрес сервера:</span>
                        <p>Обычно имеет вид: ваше-заведение.iiko.it</p>
                      </div>
                      
                      <div>
                        <span className="font-bold text-green-400">Логин и пароль:</span>
                        <p>Те же, что вы используете для входа в IIKO Office</p>
                      </div>
                      
                      <div className="bg-yellow-900/20 border border-yellow-400/30 rounded-lg p-3 mt-4">
                        <p className="text-yellow-200 text-xs">
                          Если не знаете данные, обратитесь к системному администратору IIKO в вашем заведении
                        </p>
                      </div>
                    </div>
                    
                    {iikoRmsConnection.status === 'connected' && (
                      <div className="bg-green-900/20 border border-green-400/30 rounded-lg p-3 mt-4">
                        <p className="text-green-200 text-sm font-bold">Подключение активно</p>
                        <p className="text-green-300 text-xs">
                          {iikoRmsConnection.organization_name} • {iikoRmsConnection.products_count} товаров
                        </p>
                      </div>
                    )}
                  </div>
                </div>
                
                {iikoRmsMessage.text && (
                  <div className={`p-4 rounded-lg ${
                    iikoRmsMessage.type === 'success' ? 'bg-green-900/20 border border-green-400/30 text-green-200' :
                    iikoRmsMessage.type === 'error' ? 'bg-red-900/20 border border-red-400/30 text-red-200' :
                    'bg-blue-900/20 border border-blue-400/30 text-blue-200'
                  }`}>
                    {iikoRmsMessage.text}
                  </div>
                )}
                
                <div className="text-center">
                  <button
                    onClick={() => setProfileStep(1)}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-bold transition-colors"
                  >
                    НАСТРОИТЬ ПРОФИЛЬ ЗАВЕДЕНИЯ →
                  </button>
                </div>
              </div>
            )}

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
                          <div>Сложность: {venue.complexity_level === 'high' ? 'Высокая' : venue.complexity_level === 'medium' ? 'Средняя' : 'Низкая'}</div>
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

                {/* City */}
                <div>
                  <label className="block text-purple-200 font-bold mb-2">Город</label>
                  <input
                    type="text"
                    value={venueProfile.city || ''}
                    onChange={(e) => setVenueProfile(prev => ({ ...prev, city: e.target.value }))}
                    placeholder="Например: Москва"
                    className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white"
                  />
                </div>

                {/* Staff Count, Working Hours, Seating Capacity */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-purple-200 font-bold mb-2">Количество сотрудников</label>
                    <input
                      type="number"
                      value={venueProfile.staff_count || ''}
                      onChange={(e) => setVenueProfile(prev => ({ ...prev, staff_count: parseInt(e.target.value) || 0 }))}
                      placeholder="Например: 15"
                      className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-purple-200 font-bold mb-2">Режим работы</label>
                    <input
                      type="text"
                      value={venueProfile.working_hours || ''}
                      onChange={(e) => setVenueProfile(prev => ({ ...prev, working_hours: e.target.value }))}
                      placeholder="Например: 10:00-22:00"
                      className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-purple-200 font-bold mb-2">Вместимость (мест)</label>
                    <input
                      type="number"
                      value={venueProfile.seating_capacity || ''}
                      onChange={(e) => setVenueProfile(prev => ({ ...prev, seating_capacity: parseInt(e.target.value) || 0 }))}
                      placeholder="Например: 50"
                      className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white"
                    />
                  </div>
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
                
                {/* HACCP Pro Settings - ОТКЛЮЧЕНО */}
                {false && (currentUser?.subscription_plan === 'pro' || currentUser?.subscription_plan === 'business') && (
                  <div className="pt-6 border-t border-purple-400/30">
                    <h4 className="text-lg font-bold text-orange-300 mb-4 flex items-center space-x-2">
                      <span>🛡️</span>
                      <span>HACCP Pro</span>
                      <span className="bg-orange-600 px-2 py-1 rounded text-xs">PRO</span>
                    </h4>
                    <label className="flex items-center space-x-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={haccpProEnabled}
                        onChange={(e) => setHaccpProEnabled(e.target.checked)}
                        className="w-5 h-5 text-orange-600 bg-gray-700 border-gray-600 rounded focus:ring-orange-500 focus:ring-2"
                      />
                      <div className="text-gray-300">
                        <div className="font-medium">Включить HACCP Pro модуль</div>
                        <div className="text-sm text-gray-400">
                          Автоматическая генерация и аудит HACCP протоколов для соблюдения требований безопасности пищевых продуктов
                        </div>
                      </div>
                    </label>
                  </div>
                )}
                
                {/* iiko RMS Integration Section */}
                <div className="pt-6 border-t border-purple-400/30">
                  <h4 className="text-lg font-bold text-blue-300 mb-4 flex items-center space-x-2">
                    <span>🔗</span>
                    <span>iiko RMS подключение</span>
                    <span className="bg-blue-600 px-2 py-1 rounded text-xs">ИНТЕГРАЦИЯ</span>
                  </h4>
                  
                  {iikoRmsConnection.status === 'connected' ? (
                    <div className="bg-green-900/30 border border-green-400/30 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-green-300 font-semibold flex items-center gap-2">
                            ✅ Подключено к {iikoRmsConnection.host}
                          </div>
                          <div className="text-green-400 text-sm mt-1">
                            Логин: {iikoRmsConnection.login} | Организация: {iikoRmsConnection.organization_name}
                          </div>
                          <div className="text-green-500 text-xs mt-1">
                            Сессия до: {iikoRmsConnection.session_expires_at ? new Date(iikoRmsConnection.session_expires_at).toLocaleString() : 'N/A'}
                          </div>
                        </div>
                        <button
                          onClick={() => setShowIikoRmsModal(true)}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors"
                        >
                          ⚙️ Настроить
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-gray-800/30 border border-gray-600/30 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-gray-300 font-semibold">
                            iiko RMS не подключен
                          </div>
                          <div className="text-gray-400 text-sm mt-1">
                            Подключите для экспорта техкарт в iiko
                          </div>
                        </div>
                        <button
                          onClick={() => setShowIikoRmsModal(true)}
                          className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors"
                        >
                          Подключить
                        </button>
                      </div>
                    </div>
                  )}
                  
                  <div className="text-gray-400 text-xs mt-2">
                    После подключения пароль будет сохранен для автоматического входа
                  </div>
                </div>
                
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
                    {isUpdatingProfile ? 'СОХРАНЕНИЕ...' : 'СОХРАНИТЬ ПРОФИЛЬ'}
                  </button>
                </div>
              </div>
            )}

            {/* Wizard Step 5: Deep Research */}
            {profileStep === 5 && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <h3 className="text-xl font-bold text-purple-200 mb-2">Глубокое исследование заведения</h3>
                  <p className="text-gray-300">AI проанализирует ваше заведение в интернете и предоставит рекомендации</p>
                </div>

                {!deepResearchData && !isResearching && (
                  <div className="bg-gradient-to-br from-purple-900/20 to-pink-900/20 border border-purple-400/30 rounded-xl p-6">
                    <div className="space-y-4">
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
                      <div>
                        <label className="block text-purple-200 font-bold mb-2">Город</label>
                        <input
                          type="text"
                          value={venueProfile.city || ''}
                          onChange={(e) => setVenueProfile(prev => ({ ...prev, city: e.target.value }))}
                          placeholder="Например: Москва"
                          className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white"
                        />
                      </div>
                      <div>
                        <label className="block text-purple-200 font-bold mb-2">Дополнительная информация (необязательно)</label>
                        <textarea
                          value={venueProfile.venue_description || ''}
                          onChange={(e) => setVenueProfile(prev => ({ ...prev, venue_description: e.target.value }))}
                          placeholder="Расскажите о вашем заведении..."
                          rows={4}
                          className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white resize-none"
                        />
                      </div>
                      <button
                        onClick={startDeepResearch}
                        disabled={!venueProfile.venue_name || isResearching}
                        className={`w-full px-6 py-3 rounded-lg font-bold transition-colors ${
                          !venueProfile.venue_name || isResearching
                            ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                            : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white'
                        }`}
                      >
                        Начать исследование
                      </button>
                    </div>
                  </div>
                )}

                {isResearching && (
                  <div className="bg-gradient-to-br from-purple-900/20 to-pink-900/20 border border-purple-400/30 rounded-xl p-8">
                    <div className="text-center">
                      <div className="text-4xl mb-4">🔍</div>
                      <h4 className="text-xl font-bold text-purple-300 mb-4">{currentResearchMessage}</h4>
                      <div className="w-full bg-gray-700 rounded-full h-3 mb-2">
                        <div 
                          className="bg-gradient-to-r from-purple-600 to-pink-600 h-3 rounded-full transition-all duration-300"
                          style={{ width: `${researchProgress}%` }}
                        ></div>
                      </div>
                      <div className="text-purple-200 text-sm font-bold">{researchProgress}%</div>
                    </div>
                  </div>
                )}

                {deepResearchData && !isResearching && (
                  <div className="space-y-4">
                    <div className="bg-gradient-to-br from-green-900/20 to-emerald-900/20 border border-green-400/30 rounded-xl p-6">
                      <h4 className="text-lg font-bold text-green-300 mb-4">Результаты исследования</h4>
                      {deepResearchData.competitor_analysis && (
                        <div className="mb-4">
                          <h5 className="font-bold text-green-200 mb-2">Анализ конкурентов</h5>
                          <p className="text-gray-300 text-sm">{deepResearchData.competitor_analysis}</p>
                        </div>
                      )}
                      {deepResearchData.customer_reviews_summary && (
                        <div className="mb-4">
                          <h5 className="font-bold text-green-200 mb-2">Отзывы клиентов</h5>
                          <p className="text-gray-300 text-sm">{deepResearchData.customer_reviews_summary}</p>
                        </div>
                      )}
                      {deepResearchData.recommendations && (
                        <div>
                          <h5 className="font-bold text-green-200 mb-2">Рекомендации</h5>
                          <p className="text-gray-300 text-sm">{deepResearchData.recommendations}</p>
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => {
                        setDeepResearchData(null);
                        startDeepResearch();
                      }}
                      className="w-full px-6 py-3 rounded-lg font-bold bg-purple-600 hover:bg-purple-700 text-white transition-colors"
                    >
                      Обновить исследование
                    </button>
                  </div>
                )}

                <div className="flex justify-between pt-6 border-t border-purple-400/30">
                  <button
                    onClick={() => setProfileStep(4)}
                    className="px-6 py-3 rounded-lg font-bold bg-gray-600 hover:bg-gray-700 text-white transition-colors"
                  >
                    ← НАЗАД
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
                            onClick={() => viewProjectContent(project)}
                            className="flex-1 bg-gray-600 hover:bg-gray-700 text-white text-xs py-2 px-3 rounded transition-colors"
                            title="Просмотр содержимого и аналитики проекта"
                          >
                            📂 Открыть
                          </button>
                          <button
                            onClick={() => exportProject(project.id, 'excel')}
                            disabled={isExportingProject}
                            className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white text-xs py-2 px-2 rounded transition-colors"
                            title="Экспорт проекта в Excel"
                          >
                            {isExportingProject ? '⏳' : '📊'}
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

      {/* IIKo Integration Modal */}
      {showIikoModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 border border-purple-400/30 rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center gap-3">
                <h3 className="text-xl font-bold text-purple-200">
                  🏢 Интеграция с IIKo
                </h3>
                <button
                  onClick={() => {
                    setActiveTour('iiko');
                    setShowIikoModal(false);
                  }}
                  className="bg-purple-600/30 hover:bg-purple-600/50 text-purple-300 font-bold py-1 px-3 rounded-lg transition-all hover:scale-110"
                  title="Пройти обучающий тур по IIKO интеграции"
                >
                  ❓
                </button>
              </div>
              <button
                onClick={() => setShowIikoModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            {/* IIKo Health Status */}
            {iikoHealthStatus && (
              <div className={`mb-6 p-4 rounded-lg border ${
                iikoHealthStatus.status === 'healthy' 
                  ? 'bg-green-900/20 border-green-400/30'
                  : iikoHealthStatus.status === 'unhealthy'
                  ? 'bg-red-900/20 border-red-400/30'
                  : 'bg-yellow-900/20 border-yellow-400/30'
              }`}>
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-lg">
                    {iikoHealthStatus.status === 'healthy' ? '✅' : 
                     iikoHealthStatus.status === 'unhealthy' ? '❌' : '⚠️'}
                  </span>
                  <span className={`font-semibold ${
                    iikoHealthStatus.status === 'healthy' ? 'text-green-200' :
                    iikoHealthStatus.status === 'unhealthy' ? 'text-red-200' : 'text-yellow-200'
                  }`}>
                    Статус подключения: {iikoHealthStatus.iiko_connection}
                  </span>
                </div>
                {iikoHealthStatus.error && (
                  <p className="text-red-200 text-sm">
                    Ошибка: {iikoHealthStatus.error}
                  </p>
                )}
              </div>
            )}

            {/* Organizations List */}
            <div className="mb-6">
              <h4 className="text-lg font-semibold text-purple-200 mb-3">
                Доступные организации
              </h4>
              {isLoadingIiko ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400"></div>
                  <p className="text-purple-300 mt-2">Загружаем организации...</p>
                </div>
              ) : iikoOrganizations.length > 0 ? (
                <div className="space-y-3">
                  {iikoOrganizations.map((org) => (
                    <div
                      key={org.id}
                      className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                        selectedOrganization?.id === org.id
                          ? 'bg-purple-600/30 border-purple-400'
                          : 'bg-gray-700/50 border-gray-600 hover:bg-gray-700/70'
                      }`}
                      onClick={() => {
                        setSelectedOrganization(org);
                        fetchIikoMenu(org.id);
                      }}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <h5 className="font-semibold text-white">{org.name}</h5>
                          <p className="text-gray-400 text-sm">ID: {org.id}</p>
                          {org.address && (
                            <p className="text-gray-400 text-sm">📍 {org.address}</p>
                          )}
                        </div>
                        <span className={`px-2 py-1 rounded text-xs ${
                          org.active ? 'bg-green-600 text-green-100' : 'bg-gray-600 text-gray-100'
                        }`}>
                          {org.active ? 'Активна' : 'Неактивна'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-400">
                  <p>Организации не найдены или произошла ошибка подключения</p>
                </div>
              )}
            </div>

            {/* Menu Information */}
            {selectedOrganization && (
              <div className="mb-6">
                <h4 className="text-lg font-semibold text-purple-200 mb-3">
                  Меню организации: {selectedOrganization.name}
                </h4>
                {isLoadingIiko ? (
                  <div className="text-center py-4">
                    <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-purple-400"></div>
                    <p className="text-purple-300 mt-2">Загружаем меню...</p>
                  </div>
                ) : iikoMenu ? (
                  <div className="bg-gray-700/50 rounded-lg p-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                      <div>
                        <div className="text-2xl font-bold text-blue-300">{iikoMenu.categories?.length || 0}</div>
                        <div className="text-sm text-gray-400">Категории</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-green-300">{iikoMenu.items?.length || 0}</div>
                        <div className="text-sm text-gray-400">Блюда</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-yellow-300">{iikoMenu.modifiers?.length || 0}</div>
                        <div className="text-sm text-gray-400">Модификаторы</div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-400">Обновлено</div>
                        <div className="text-xs text-gray-300">
                          {iikoMenu.last_updated ? new Date(iikoMenu.last_updated).toLocaleDateString('ru-RU') : 'N/A'}
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-400 text-center py-4">Выберите организацию для загрузки меню</p>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col gap-3">
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => setShowSyncMenuModal(true)}
                  disabled={!selectedOrganization}
                  className={`${
                    !selectedOrganization 
                      ? 'bg-gray-600 cursor-not-allowed' 
                      : 'bg-blue-600 hover:bg-blue-700'
                  } text-white font-bold py-3 px-6 rounded-lg transition-colors`}
                  title="Синхронизировать меню между системами"
                >
                  🔄 Синхронизировать меню
                </button>
                
                <button
                  onClick={async () => {
                    const diagnostics = await axios.get(`${API}/iiko/diagnostics`);
                    alert(`Диагностика IIKo:\n\n${JSON.stringify(diagnostics.data, null, 2)}`);
                  }}
                  className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                  title="Запустить диагностику подключения"
                >
                  🔧 Диагностика
                </button>
              </div>

              {/* NEW - Category Management */}
              <div className="mt-4">
                <h4 className="text-lg font-semibold text-purple-200 mb-3">
                  📂 Управление категориями
                </h4>
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <button
                    onClick={createAIMenuDesignerCategory}
                    disabled={!selectedOrganization}
                    className={`${
                      !selectedOrganization 
                        ? 'bg-gray-600 cursor-not-allowed' 
                        : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700'
                    } text-white font-bold py-3 px-6 rounded-lg transition-colors`}
                    title="Создать специальную категорию для AI Menu Designer"
                  >
                    ✨ Создать категорию "AI Menu Designer"
                  </button>
                  
                  <button
                    onClick={viewAllIikoCategories}
                    disabled={!selectedOrganization}
                    className={`${
                      !selectedOrganization 
                        ? 'bg-gray-600 cursor-not-allowed' 
                        : 'bg-indigo-600 hover:bg-indigo-700'
                    } text-white font-bold py-3 px-6 rounded-lg transition-colors`}
                    title="Посмотреть все категории в IIKo"
                  >
                    📋 Просмотр всех категорий
                  </button>
                </div>
              </div>

              {/* NEW - Category Viewing Buttons */}
              <div className="mt-4">
                <h4 className="text-lg font-semibold text-purple-200 mb-3">
                  🍽️ Просмотр категорий меню
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  <button
                    onClick={() => viewIikoCategory('салаты')}
                    disabled={!selectedOrganization}
                    className={`${
                      !selectedOrganization 
                        ? 'bg-gray-600 cursor-not-allowed' 
                        : 'bg-green-600 hover:bg-green-700'
                    } text-white font-bold py-2 px-4 rounded-lg transition-colors text-sm`}
                    title="Посмотреть все салаты из меню"
                  >
                    🥗 Салаты
                  </button>
                  
                  <button
                    onClick={() => viewIikoCategory('горячее')}
                    disabled={!selectedOrganization}
                    className={`${
                      !selectedOrganization 
                        ? 'bg-gray-600 cursor-not-allowed' 
                        : 'bg-red-600 hover:bg-red-700'
                    } text-white font-bold py-2 px-4 rounded-lg transition-colors text-sm`}
                    title="Посмотреть горячие блюда"
                  >
                    🔥 Горячее
                  </button>
                  
                  <button
                    onClick={() => viewIikoCategory('напитки')}
                    disabled={!selectedOrganization}
                    className={`${
                      !selectedOrganization 
                        ? 'bg-gray-600 cursor-not-allowed' 
                        : 'bg-blue-500 hover:bg-blue-600'
                    } text-white font-bold py-2 px-4 rounded-lg transition-colors text-sm`}
                    title="Посмотреть напитки"
                  >
                    🥤 Напитки
                  </button>
                  
                  <button
                    onClick={() => viewIikoCategory('десерты')}
                    disabled={!selectedOrganization}
                    className={`${
                      !selectedOrganization 
                        ? 'bg-gray-600 cursor-not-allowed' 
                        : 'bg-pink-600 hover:bg-pink-700'
                    } text-white font-bold py-2 px-4 rounded-lg transition-colors text-sm`}
                    title="Посмотреть десерты"
                  >
                    🍰 Десерты
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Убрали нерабочий модал загрузки техkарт в IIKo */}

      {/* Sync Menu Modal */}
      {showSyncMenuModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 border border-purple-400/30 rounded-lg p-6 max-w-2xl w-full">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-purple-200">
                🔄 Синхронизация меню с IIKo
              </h3>
              <button
                onClick={() => {
                  setShowSyncMenuModal(false);
                  setSyncProgress(null);
                }}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            {!isSyncing && !syncProgress ? (
              <>
                <div className="mb-6">
                  <h4 className="text-lg font-semibold text-white mb-2">
                    Настройки синхронизации
                  </h4>
                  <p className="text-gray-400 text-sm mb-4">
                    Выберите что синхронизировать между AI-Menu-Designer и IIKo
                  </p>

                  <div className="space-y-3">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={syncSettings.syncPrices}
                        onChange={(e) => setSyncSettings(prev => ({...prev, syncPrices: e.target.checked}))}
                        className="mr-3"
                      />
                      <span className="text-white">Синхронизировать цены</span>
                    </label>
                    
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={syncSettings.syncCategories}
                        onChange={(e) => setSyncSettings(prev => ({...prev, syncCategories: e.target.checked}))}
                        className="mr-3"
                      />
                      <span className="text-white">Синхронизировать категории</span>
                    </label>
                  </div>
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={() => setShowSyncMenuModal(false)}
                    className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                  >
                    ❌ Отменить
                  </button>
                  <button
                    onClick={() => syncMenuWithIiko([selectedOrganization.id], syncSettings)}
                    disabled={!selectedOrganization}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-3 px-6 rounded-lg transition-colors"
                  >
                    🔄 Начать синхронизацию
                  </button>
                </div>
              </>
            ) : (
              <>
                {/* Sync Progress */}
                <div className="mb-6">
                  <h4 className="text-lg font-semibold text-white mb-2">
                    Прогресс синхронизации
                  </h4>
                  
                  <div className="bg-gray-700/50 rounded-lg p-4">
                    <div className="flex items-center gap-3 mb-2">
                      <div className={`w-4 h-4 rounded-full ${
                        isSyncing ? 'bg-yellow-400 animate-pulse' : 
                        syncProgress?.status === 'completed' ? 'bg-green-400' :
                        syncProgress?.status === 'error' ? 'bg-red-400' : 'bg-gray-400'
                      }`}></div>
                      <span className="text-white font-medium">
                        {syncProgress?.message || 'Подготовка к синхронизации...'}
                      </span>
                    </div>
                    
                    {syncProgress?.syncJobId && (
                      <p className="text-gray-400 text-xs">
                        ID задачи: {syncProgress.syncJobId}
                      </p>
                    )}
                    
                    {syncProgress?.results && (
                      <div className="mt-4 text-sm">
                        <p className="text-green-300">
                          ✅ Организаций обработано: {syncProgress.results.organizations_synced?.length || 0}
                        </p>
                        <p className="text-blue-300">
                          📋 Элементов меню: {syncProgress.results.items_updated || 0}
                        </p>
                        <p className="text-purple-300">
                          🗂 Категорий: {syncProgress.results.categories_updated || 0}
                        </p>
                        {syncProgress.results.errors?.length > 0 && (
                          <p className="text-red-300">
                            ❌ Ошибок: {syncProgress.results.errors.length}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {!isSyncing && (
                  <button
                    onClick={() => {
                      setShowSyncMenuModal(false);
                      setSyncProgress(null);
                    }}
                    className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                  >
                    ✅ Закрыть
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* IIKo Category Viewer Modal - КРАСИВЫЙ ПРОСМОТР КАТЕГОРИЙ */}
      {showCategoryViewer && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 border border-purple-400/30 rounded-2xl p-6 max-w-6xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center gap-3">
                <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-300 to-pink-300">
                  {categoryData?.success !== false ? 
                    `🍽️ ${categoryData?.category?.name || categoryData?.searchedFor}` : 
                    `🔍 Поиск категории: ${categoryData?.searchedFor}`
                  }
                </h3>
                {selectedOrganization && (
                  <span className="text-purple-400 text-sm">
                    📍 {selectedOrganization.name}
                  </span>
                )}
              </div>
              <button
                onClick={() => {
                  setShowCategoryViewer(false);
                  setCategoryData(null);
                }}
                className="text-gray-400 hover:text-white text-3xl font-bold transition-colors"
              >
                ×
              </button>
            </div>

            {/* Loading State */}
            {isLoadingCategory && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent"></div>
                <p className="text-purple-300 mt-4 text-lg">
                  🔍 Загружаем категорию из IIKo...
                </p>
              </div>
            )}

            {/* Success - Category Found */}
            {!isLoadingCategory && categoryData?.success !== false && categoryData?.category && (
              <div>
                {/* Category Info */}
                <div className="bg-gradient-to-r from-purple-800/30 to-pink-800/30 rounded-xl p-4 mb-6 border border-purple-400/20">
                  <div className="flex flex-wrap justify-between items-center gap-4">
                    <div>
                      <h4 className="text-xl font-semibold text-white">
                        {categoryData.category.name}
                      </h4>
                      <p className="text-purple-300 text-sm">
                        ID: {categoryData.category.id}
                      </p>
                      {categoryData.category.description && (
                        <p className="text-gray-300 text-sm mt-1">
                          {categoryData.category.description}
                        </p>
                      )}
                    </div>
                    
                    <div className="flex gap-6 text-center">
                      <div>
                        <div className="text-3xl font-bold text-green-400">
                          {categoryData.summary?.total_in_category || 0}
                        </div>
                        <div className="text-sm text-gray-400">Всего блюд</div>
                      </div>
                      <div>
                        <div className="text-3xl font-bold text-blue-400">
                          {categoryData.summary?.shown || 0}
                        </div>
                        <div className="text-sm text-gray-400">Показано</div>
                      </div>
                      <div>
                        <div className="text-3xl font-bold text-purple-400">
                          {categoryData.summary?.has_descriptions || 0}
                        </div>
                        <div className="text-sm text-gray-400">С описаниями</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Items Grid */}
                {categoryData.items && categoryData.items.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {categoryData.items.map((item, index) => (
                      <div
                        key={item.id || index}
                        className="bg-gray-800/50 border border-gray-600/50 rounded-xl p-4 hover:bg-gray-800/70 hover:border-purple-400/50 transition-all duration-300 group"
                      >
                        <div className="flex justify-between items-start mb-3">
                          <h5 className="font-semibold text-white text-sm group-hover:text-purple-200 transition-colors">
                            {item.name}
                          </h5>
                          <div className={`w-3 h-3 rounded-full ${
                            item.active ? 'bg-green-500' : 'bg-red-500'
                          }`} title={item.active ? 'Активно' : 'Неактивно'}></div>
                        </div>
                        
                        {item.description && item.description !== 'Без описания' && (
                          <p className="text-gray-400 text-xs leading-relaxed mb-3">
                            {item.description}
                          </p>
                        )}
                        
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-purple-400">
                            ID: {item.id?.substring(0, 8)}...
                          </span>
                          <span className={`px-2 py-1 rounded ${
                            item.active 
                              ? 'bg-green-600/20 text-green-300' 
                              : 'bg-red-600/20 text-red-300'
                          }`}>
                            {item.active ? '✅ Активно' : '❌ Неактивно'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <div className="text-6xl mb-4">📭</div>
                    <p className="text-xl text-gray-400">
                      В этой категории пока нет блюд
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Error - Category Not Found */}
            {!isLoadingCategory && categoryData?.success === false && (
              <div className="text-center py-8">
                <div className="text-6xl mb-4">🔍</div>
                <h4 className="text-xl font-semibold text-red-300 mb-2">
                  {categoryData.error}
                </h4>
                <p className="text-gray-400 mb-6">
                  Попробуйте другое название или выберите из доступных категорий
                </p>

                {/* Similar Categories */}
                {categoryData.similarCategories && categoryData.similarCategories.length > 0 && (
                  <div className="mb-6">
                    <h5 className="text-lg font-semibold text-purple-300 mb-3">
                      Похожие категории:
                    </h5>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {categoryData.similarCategories.map((catName, index) => (
                        <button
                          key={index}
                          onClick={() => viewIikoCategory(catName.toLowerCase())}
                          className="bg-purple-600 hover:bg-purple-700 text-white py-2 px-4 rounded-lg text-sm transition-colors"
                        >
                          {catName}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* All Categories */}
                {categoryData.allCategories && categoryData.allCategories.length > 0 && (
                  <div>
                    <h5 className="text-lg font-semibold text-purple-300 mb-3">
                      Все доступные категории:
                    </h5>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 max-h-40 overflow-y-auto">
                      {categoryData.allCategories.map((catName, index) => (
                        <button
                          key={index}
                          onClick={() => viewIikoCategory(catName.toLowerCase())}
                          className="bg-gray-600 hover:bg-gray-700 text-white py-1 px-3 rounded text-xs transition-colors"
                        >
                          {catName}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Bottom Actions */}
            {!isLoadingCategory && categoryData && categoryData.success !== false && (
              <div className="flex justify-center mt-6 gap-3">
                <button
                  onClick={() => {
                    setShowCategoryViewer(false);
                    setCategoryData(null);
                  }}
                  className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-6 rounded-lg transition-colors"
                >
                  ✅ Закрыть
                </button>
                
                <button
                  onClick={() => viewIikoCategory('салаты')}
                  className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded-lg transition-colors"
                  title="Обновить категорию"
                >
                  🔄 Обновить
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Project Content Modal - NEW! */}
      {showProjectContentModal && selectedProject && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800/95 backdrop-blur-lg rounded-2xl w-full max-w-7xl max-h-[90vh] overflow-y-auto border border-purple-400/20">
            {/* Header */}
            <div className="sticky top-0 bg-gray-800/95 backdrop-blur-lg border-b border-purple-400/20 p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-3xl font-bold text-purple-300 mb-2">
                    📁 {selectedProject.project_name}
                  </h2>
                  <p className="text-gray-400">
                    {selectedProject.project_type} • Создан {new Date(selectedProject.created_at).toLocaleDateString('ru-RU')}
                  </p>
                  {selectedProject.description && (
                    <p className="text-sm text-gray-300 mt-2">{selectedProject.description}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => exportProject(selectedProject.id, 'excel')}
                    disabled={isExportingProject}
                    className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    {isExportingProject ? '⏳ Экспорт...' : '📊 Экспорт Excel'}
                  </button>
                  <button
                    onClick={() => {
                      setShowProjectContentModal(false);
                      setSelectedProject(null);
                      setProjectContent(null);
                      setProjectAnalytics(null);
                    }}
                    className="text-gray-400 hover:text-white text-3xl font-bold transition-colors"
                  >
                    ×
                  </button>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              {isLoadingProjectContent ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="animate-spin text-6xl mb-4">⚡</div>
                  <div className="text-xl text-purple-300 font-bold mb-2">Загружаем содержимое проекта...</div>
                  <div className="text-gray-400">Анализируем меню и техкарты</div>
                </div>
              ) : projectContent ? (
                <div className="space-y-8">
                  {/* Project Statistics */}
                  {projectContent.project_stats && renderProjectStats(projectContent.project_stats)}
                  
                  {/* Analytics Section */}
                  {isLoadingProjectAnalytics ? (
                    <div className="bg-gray-800/50 rounded-lg p-6 text-center">
                      <div className="animate-spin text-3xl mb-2">📊</div>
                      <div className="text-lg text-purple-300">Загружаем аналитику IIKo...</div>
                    </div>
                  ) : (
                    projectAnalytics && renderProjectAnalytics(projectAnalytics.analytics)
                  )}

                  {/* Content Tabs */}
                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <div className="flex gap-4 mb-4">
                      <h3 className="text-2xl font-bold text-purple-300">📂 СОДЕРЖИМОЕ ПРОЕКТА</h3>
                    </div>
                    
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Menus Section */}
                      <div className="bg-gray-700/50 rounded-lg p-4">
                        <h4 className="text-lg font-bold text-green-300 mb-3 flex items-center gap-2">
                          🍽️ МЕНЮ ({projectContent.menus_count})
                        </h4>
                        
                        {projectContent.menus.length === 0 ? (
                          <div className="text-gray-400 text-center py-8">
                            <div className="text-4xl mb-2">📋</div>
                            <div>Меню в проекте пока нет</div>
                          </div>
                        ) : (
                          <div className="space-y-3 max-h-96 overflow-y-auto">
                            {projectContent.menus.map((menu, index) => (
                              <div key={index} className="bg-gray-800/50 rounded p-3 border-l-4 border-green-400">
                                <div className="font-bold text-sm text-green-300 mb-1">
                                  {menu.menu_type} • {menu.dishes?.length || 0} блюд
                                </div>
                                <div className="text-xs text-gray-400 mb-2">
                                  {new Date(menu.created_at).toLocaleDateString('ru-RU')}
                                </div>
                                {menu.expectations && (
                                  <div className="text-xs text-gray-300 line-clamp-2">
                                    {menu.expectations.substring(0, 100)}...
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Tech Cards Section */}
                      <div className="bg-gray-700/50 rounded-lg p-4">
                        <h4 className="text-lg font-bold text-blue-300 mb-3 flex items-center gap-2">
                          📋 ТЕХКАРТЫ ({projectContent.tech_cards_count})
                        </h4>
                        
                        {projectContent.tech_cards.length === 0 ? (
                          <div className="text-gray-400 text-center py-8">
                            <div className="text-4xl mb-2">📄</div>
                            <div>Техкарты в проекте пока нет</div>
                          </div>
                        ) : (
                          <div className="space-y-3 max-h-96 overflow-y-auto">
                            {projectContent.tech_cards.slice(0, 20).map((card, index) => (
                              <div key={index} className="bg-gray-800/50 rounded p-3 border-l-4 border-blue-400">
                                <div className="font-bold text-sm text-blue-300 mb-1">
                                  {card.dish_name}
                                </div>
                                <div className="text-xs text-gray-400 mb-2">
                                  {new Date(card.created_at).toLocaleDateString('ru-RU')}
                                  {card.is_inspiration && (
                                    <span className="ml-2 bg-orange-600 text-white px-2 py-0.5 rounded text-xs">
                                      ВДОХНОВЕНИЕ
                                    </span>
                                  )}
                                </div>
                                <button
                                  onClick={() => {
                                    setTechCard(card.content);
                                    setCurrentTechCardId(card.id);
                                    setShowProjectContentModal(false);
                                  }}
                                  className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded transition-colors"
                                >
                                  👁️ Открыть
                                </button>
                              </div>
                            ))}
                            {projectContent.tech_cards.length > 20 && (
                              <div className="text-center text-gray-400 text-sm py-2">
                                ... и еще {projectContent.tech_cards.length - 20} техкарт
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Categories Coverage */}
                  {projectContent.project_stats?.categories_covered && projectContent.project_stats.categories_covered.length > 0 && (
                    <div className="bg-gray-800/50 rounded-lg p-4">
                      <h4 className="text-lg font-bold text-yellow-300 mb-3">🏷️ ПОКРЫТЫЕ КАТЕГОРИИ</h4>
                      <div className="flex flex-wrap gap-2">
                        {projectContent.project_stats.categories_covered.map((category, index) => (
                          <span 
                            key={index}
                            className="bg-yellow-600/20 text-yellow-300 px-3 py-1 rounded-full text-sm"
                          >
                            {category}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">❌</div>
                  <div className="text-xl text-red-300 font-bold mb-2">Ошибка загрузки</div>
                  <div className="text-gray-400">Не удалось загрузить содержимое проекта</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Analytics Modal - NEW! */}
      {showAnalyticsModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800/95 backdrop-blur-lg rounded-2xl w-full max-w-6xl max-h-[90vh] overflow-y-auto border border-purple-400/20">
            {/* Header */}
            <div className="sticky top-0 bg-gray-800/95 backdrop-blur-lg border-b border-purple-400/20 p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-3xl font-bold text-purple-300 mb-2">📊 АНАЛИТИКА И ОТЧЕТЫ</h2>
                  <p className="text-gray-400">Статистика использования и OLAP отчеты из IIKo</p>
                </div>
                <button
                  onClick={() => {
                    setShowAnalyticsModal(false);
                    setSelectedAnalyticsType('overview');
                    setAnalyticsData(null);
                    setOlapReportData(null);
                  }}
                  className="text-gray-400 hover:text-white text-3xl font-bold transition-colors"
                >
                  ×
                </button>
              </div>
              
              {/* Analytics Type Tabs */}
              <div className="flex gap-2 mt-4">
                <button
                  onClick={() => {
                    setSelectedAnalyticsType('overview');
                    loadAnalyticsOverview();
                  }}
                  className={`px-4 py-2 rounded-lg font-bold text-sm transition-colors ${
                    selectedAnalyticsType === 'overview'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  📈 Общая аналитика
                </button>
                <button
                  onClick={() => {
                    setSelectedAnalyticsType('olap');
                    loadOLAPReport();
                  }}
                  className={`px-4 py-2 rounded-lg font-bold text-sm transition-colors ${
                    selectedAnalyticsType === 'olap'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                  disabled={iikoOrganizations.length === 0}
                  title={iikoOrganizations.length === 0 ? 'Требуется интеграция с IIKo' : 'OLAP отчеты из IIKo'}
                >
                  📊 OLAP отчеты
                </button>
                <button
                  onClick={() => setSelectedAnalyticsType('projects')}
                  className={`px-4 py-2 rounded-lg font-bold text-sm transition-colors ${
                    selectedAnalyticsType === 'projects'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  📁 Аналитика проектов
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              {isLoadingAnalytics ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="animate-spin text-6xl mb-4">📊</div>
                  <div className="text-xl text-purple-300 font-bold mb-2">Загружаем аналитику...</div>
                  <div className="text-gray-400">
                    {selectedAnalyticsType === 'overview' && 'Анализируем вашу активность'}
                    {selectedAnalyticsType === 'olap' && 'Загружаем данные из IIKo'}
                    {selectedAnalyticsType === 'projects' && 'Обрабатываем данные проектов'}
                  </div>
                </div>
              ) : (
                <div>
                  {selectedAnalyticsType === 'overview' && renderAnalyticsOverview()}
                  {selectedAnalyticsType === 'olap' && (
                    olapReportData ? renderOLAPReport() : (
                      <div className="text-center py-12">
                        <div className="text-6xl mb-4">📊</div>
                        <div className="text-xl text-gray-300 font-bold mb-2">OLAP отчеты</div>
                        <div className="text-gray-400 mb-6">
                          {iikoOrganizations.length === 0 
                            ? 'Для просмотра OLAP отчетов сначала настройте интеграцию с IIKo'
                            : 'Нажмите кнопку "📊 OLAP отчеты" для загрузки данных'
                          }
                        </div>
                        {iikoOrganizations.length === 0 && (
                          <button
                            onClick={() => {
                              setShowAnalyticsModal(false);
                              openIikoIntegration();
                            }}
                            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-lg"
                          >
                            🏢 Настроить IIKo
                          </button>
                        )}
                      </div>
                    )
                  )}
                  {selectedAnalyticsType === 'projects' && (
                    <div className="text-center py-12">
                      <div className="text-6xl mb-4">📁</div>
                      <div className="text-xl text-gray-300 font-bold mb-2">Аналитика проектов</div>
                      <div className="text-gray-400 mb-6">
                        Детальную аналитику проектов можно посмотреть, открыв конкретный проект
                      </div>
                      <button
                        onClick={() => {
                          setShowAnalyticsModal(false);
                          setShowProjectsModal(true);
                        }}
                        className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-6 rounded-lg"
                      >
                        📁 Открыть проекты
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ============== NEW ASSEMBLY CHARTS MODAL ============== */}
      {showAssemblyChartsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-green-300">🔨 ТЕХКАРТЫ В IIKo</h2>
              <button
                onClick={() => setShowAssemblyChartsModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            {selectedOrganization && (
              <div className="mb-4 p-3 bg-blue-900/30 rounded-lg border border-blue-400/30">
                <div className="text-sm text-blue-300">
                  🏢 Организация: <span className="font-bold">{selectedOrganization.name}</span>
                </div>
              </div>
            )}

            <div className="flex gap-4 mb-6">
              <button
                onClick={() => setShowCreateAssemblyChartModal(true)}
                className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded transition-colors"
              >
                ➕ Создать техкарту
              </button>
              
              <button
                onClick={() => selectedOrganization?.id && fetchAllAssemblyCharts(selectedOrganization.id)}
                disabled={isLoadingAssemblyCharts}
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition-colors disabled:bg-gray-600"
              >
                {isLoadingAssemblyCharts ? '⏳ Обновляем...' : '🔄 Обновить'}
              </button>

              <button
                onClick={() => fetchSyncStatus()}
                className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded transition-colors"
              >
                📊 Статус синхронизации
              </button>
            </div>

            {isLoadingAssemblyCharts ? (
              <div className="text-center py-12">
                <div className="animate-spin text-4xl mb-4">🔄</div>
                <div className="text-gray-300">Загружаем техкарты из IIKo...</div>
              </div>
            ) : assemblyCharts.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📋</div>
                <div className="text-xl text-gray-300 mb-2">Техкарт пока нет</div>
                <div className="text-gray-400 mb-6">
                  Создайте первую техкарту или загрузите из AI-Menu-Designer
                </div>
                <button
                  onClick={() => setShowCreateAssemblyChartModal(true)}
                  className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded"
                >
                  ➕ Создать техкарту
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {assemblyCharts.map((chart, index) => (
                  <div key={index} className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="font-bold text-green-300">{chart.name || `Техкарта ${index + 1}`}</h3>
                      <button
                        onClick={() => deleteAssemblyChart(chart.id)}
                        className="text-red-400 hover:text-red-300 text-sm"
                        title="Удалить техкарту"
                      >
                        🗑️
                      </button>
                    </div>
                    
                    {chart.description && (
                      <div className="text-sm text-gray-300 mb-3">
                        {chart.description.substring(0, 100)}
                        {chart.description.length > 100 && '...'}
                      </div>
                    )}
                    
                    <div className="flex flex-wrap gap-2 text-xs">
                      {chart.ingredients && chart.ingredients.length > 0 && (
                        <span className="bg-blue-900/30 text-blue-300 px-2 py-1 rounded">
                          🥬 {chart.ingredients.length} ингредиентов
                        </span>
                      )}
                      {chart.ai_generated && (
                        <span className="bg-purple-900/30 text-purple-300 px-2 py-1 rounded">
                          🤖 AI
                        </span>
                      )}
                      {chart.active && (
                        <span className="bg-green-900/30 text-green-300 px-2 py-1 rounded">
                          ✅ Активна
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* CREATE ASSEMBLY CHART MODAL */}
      {showCreateAssemblyChartModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-green-300">➕ СОЗДАТЬ ТЕХКАРТУ</h2>
              <button
                onClick={() => {
                  setShowCreateAssemblyChartModal(false);
                  setAssemblyChartData({
                    name: '',
                    description: '',
                    ingredients: [],
                    preparation_steps: []
                  });
                }}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-gray-300 mb-2">
                  Название техкарты *
                </label>
                <input
                  type="text"
                  value={assemblyChartData.name}
                  onChange={(e) => setAssemblyChartData({...assemblyChartData, name: e.target.value})}
                  className="w-full p-3 border border-gray-600 rounded bg-gray-700 text-white"
                  placeholder="Например: Паста Карбонара"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-300 mb-2">
                  Описание
                </label>
                <textarea
                  value={assemblyChartData.description}
                  onChange={(e) => setAssemblyChartData({...assemblyChartData, description: e.target.value})}
                  className="w-full p-3 border border-gray-600 rounded bg-gray-700 text-white h-24"
                  placeholder="Краткое описание блюда..."
                />
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-300 mb-2">
                  Ингредиенты
                </label>
                <div className="text-sm text-gray-400 mb-2">
                  Добавьте ингредиенты в формате: название, количество, единица измерения
                </div>
                <div className="space-y-2">
                  {assemblyChartData.ingredients.map((ingredient, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="text"
                        value={ingredient.name || ''}
                        onChange={(e) => {
                          const newIngredients = [...assemblyChartData.ingredients];
                          newIngredients[index] = {...ingredient, name: e.target.value};
                          setAssemblyChartData({...assemblyChartData, ingredients: newIngredients});
                        }}
                        className="flex-1 p-2 border border-gray-600 rounded bg-gray-700 text-white text-sm"
                        placeholder="Название ингредиента"
                      />
                      <input
                        type="number"
                        value={ingredient.quantity || ''}
                        onChange={(e) => {
                          const newIngredients = [...assemblyChartData.ingredients];
                          newIngredients[index] = {...ingredient, quantity: parseFloat(e.target.value) || 0};
                          setAssemblyChartData({...assemblyChartData, ingredients: newIngredients});
                        }}
                        className="w-20 p-2 border border-gray-600 rounded bg-gray-700 text-white text-sm"
                        placeholder="100"
                      />
                      <input
                        type="text"
                        value={ingredient.unit || ''}
                        onChange={(e) => {
                          const newIngredients = [...assemblyChartData.ingredients];
                          newIngredients[index] = {...ingredient, unit: e.target.value};
                          setAssemblyChartData({...assemblyChartData, ingredients: newIngredients});
                        }}
                        className="w-16 p-2 border border-gray-600 rounded bg-gray-700 text-white text-sm"
                        placeholder="г"
                      />
                      <button
                        onClick={() => {
                          const newIngredients = assemblyChartData.ingredients.filter((_, i) => i !== index);
                          setAssemblyChartData({...assemblyChartData, ingredients: newIngredients});
                        }}
                        className="text-red-400 hover:text-red-300 px-2"
                      >
                        🗑️
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={() => {
                      setAssemblyChartData({
                        ...assemblyChartData,
                        ingredients: [...assemblyChartData.ingredients, {name: '', quantity: 0, unit: 'г', price: 0}]
                      });
                    }}
                    className="text-green-400 hover:text-green-300 text-sm"
                  >
                    ➕ Добавить ингредиент
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-bold text-gray-300 mb-2">
                  Этапы приготовления
                </label>
                <div className="space-y-2">
                  {assemblyChartData.preparation_steps.map((step, index) => (
                    <div key={index} className="flex gap-2">
                      <span className="text-gray-400 text-sm mt-2">{index + 1}.</span>
                      <textarea
                        value={step}
                        onChange={(e) => {
                          const newSteps = [...assemblyChartData.preparation_steps];
                          newSteps[index] = e.target.value;
                          setAssemblyChartData({...assemblyChartData, preparation_steps: newSteps});
                        }}
                        className="flex-1 p-2 border border-gray-600 rounded bg-gray-700 text-white text-sm"
                        placeholder="Описание этапа приготовления..."
                        rows="2"
                      />
                      <button
                        onClick={() => {
                          const newSteps = assemblyChartData.preparation_steps.filter((_, i) => i !== index);
                          setAssemblyChartData({...assemblyChartData, preparation_steps: newSteps});
                        }}
                        className="text-red-400 hover:text-red-300 px-2"
                      >
                        🗑️
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={() => {
                      setAssemblyChartData({
                        ...assemblyChartData,
                        preparation_steps: [...assemblyChartData.preparation_steps, '']
                      });
                    }}
                    className="text-green-400 hover:text-green-300 text-sm"
                  >
                    ➕ Добавить этап
                  </button>
                </div>
              </div>
            </div>

            <div className="flex gap-4 mt-6">
              <button
                onClick={() => createAssemblyChart(assemblyChartData)}
                disabled={!assemblyChartData.name || isCreatingAssemblyChart}
                className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white font-bold py-2 px-6 rounded transition-colors"
              >
                {isCreatingAssemblyChart ? '⏳ Создаем...' : '✅ Создать техкарту'}
              </button>
              
              <button
                onClick={() => {
                  setShowCreateAssemblyChartModal(false);
                  setAssemblyChartData({
                    name: '',
                    description: '',
                    ingredients: [],
                    preparation_steps: []
                  });
                }}
                className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-6 rounded transition-colors"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SYNC STATUS MODAL */}
      {showSyncStatusModal && syncStatus && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-purple-300">📊 СТАТУС СИНХРОНИЗАЦИИ</h2>
              <button
                onClick={() => setShowSyncStatusModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {Object.entries(syncStatus.status_summary).map(([status, count]) => (
                <div key={status} className="bg-gray-700 rounded-lg p-4">
                  <div className="text-lg font-bold text-blue-300">{count}</div>
                  <div className="text-sm text-gray-300 capitalize">{status.replace('_', ' ')}</div>
                </div>
              ))}
            </div>

            <div className="space-y-4 max-h-96 overflow-y-auto">
              {syncStatus.sync_records.map((record, index) => (
                <div key={index} className="bg-gray-700 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div className="font-bold text-green-300">{record.tech_card_name}</div>
                    <div className={`text-xs px-2 py-1 rounded ${
                      record.sync_status === 'created_as_assembly_chart' 
                        ? 'bg-green-900/30 text-green-300'
                        : record.sync_status === 'upload_failed'
                        ? 'bg-red-900/30 text-red-300'
                        : 'bg-yellow-900/30 text-yellow-300'
                    }`}>
                      {record.sync_status}
                    </div>
                  </div>
                  
                  <div className="text-xs text-gray-400 mb-2">
                    {new Date(record.created_at).toLocaleString('ru-RU')}
                    {record.assembly_chart_id && (
                      <span className="ml-2">ID: {record.assembly_chart_id}</span>
                    )}
                  </div>

                  {record.upload_error && (
                    <div className="text-xs text-red-300 mt-2 p-2 bg-red-900/20 rounded">
                      Ошибка: {record.upload_error}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* All IIKo Categories Modal */}
      {showAllCategoriesModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 border border-purple-400/30 rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-purple-200">
                📂 Категории в IIKo: {selectedOrganization?.name}
              </h3>
              <button
                onClick={() => {
                  setShowAllCategoriesModal(false);
                  setIikoCategories([]);
                }}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            {isLoadingCategories ? (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400"></div>
                <p className="text-purple-300 mt-2">Загружаем категории из IIKo...</p>
              </div>
            ) : iikoCategories.length > 0 ? (
              <div>
                <div className="mb-4 text-center">
                  <span className="text-gray-300">
                    Найдено категорий: <span className="font-bold text-white">{iikoCategories.length}</span>
                  </span>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-96 overflow-y-auto">
                  {iikoCategories.map((category, index) => (
                    <div
                      key={category.id || index}
                      className={`p-3 rounded-lg border transition-colors ${
                        category.name === 'AI Menu Designer'
                          ? 'bg-gradient-to-r from-purple-600/30 to-pink-600/30 border-purple-400'
                          : category.deleted
                          ? 'bg-red-900/20 border-red-400/30'
                          : 'bg-gray-700/50 border-gray-600 hover:bg-gray-700/70'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h5 className={`font-medium ${
                            category.name === 'AI Menu Designer' ? 'text-purple-200' : 'text-white'
                          }`}>
                            {category.name === 'AI Menu Designer' && '✨ '}
                            {category.name}
                          </h5>
                          <p className="text-gray-400 text-xs mt-1">
                            ID: {category.id}
                          </p>
                          {category.code && (
                            <p className="text-gray-400 text-xs">
                              Код: {category.code}
                            </p>
                          )}
                        </div>
                        <span className={`px-2 py-1 rounded text-xs ${
                          category.deleted 
                            ? 'bg-red-600 text-red-100' 
                            : category.name === 'AI Menu Designer'
                            ? 'bg-purple-600 text-purple-100'
                            : 'bg-green-600 text-green-100'
                        }`}>
                          {category.deleted ? 'Удалена' : 
                           category.name === 'AI Menu Designer' ? 'AI Designer' : 'Активна'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="mt-6 text-center">
                  <button
                    onClick={createAIMenuDesignerCategory}
                    disabled={isCreatingCategory || iikoCategories.some(cat => cat.name === 'AI Menu Designer')}
                    className={`${
                      isCreatingCategory 
                        ? 'bg-gray-600 cursor-not-allowed' 
                        : iikoCategories.some(cat => cat.name === 'AI Menu Designer')
                        ? 'bg-green-600 cursor-default'
                        : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700'
                    } text-white font-bold py-3 px-6 rounded-lg transition-colors`}
                    title={
                      iikoCategories.some(cat => cat.name === 'AI Menu Designer')
                        ? 'Категория AI Menu Designer уже существует'
                        : 'Создать категорию AI Menu Designer'
                    }
                  >
                    {isCreatingCategory ? '⏳ Создаем...' : 
                     iikoCategories.some(cat => cat.name === 'AI Menu Designer') ? '✅ AI Menu Designer уже создана' :
                     '✨ Создать AI Menu Designer'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-400">
                <p className="mb-4">Категории не найдены или произошла ошибка загрузки</p>
                <button
                  onClick={() => fetchAllIikoCategories(selectedOrganization?.id)}
                  className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-lg transition-colors"
                >
                  🔄 Повторить загрузку
                </button>
              </div>
            )}

            <div className="mt-6 text-center">
              <button
                onClick={() => {
                  setShowAllCategoriesModal(false);
                  setIikoCategories([]);
                }}
                className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-6 rounded-lg transition-colors"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}

      {/* HACCP Audit Modal - ОТКЛЮЧЕНО */}
      {false && showHaccpAuditModal && haccpAuditResult && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gradient-to-br from-gray-900 via-orange-900 to-gray-900 rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-orange-400/30">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-orange-300 flex items-center gap-3">
                🛡️ Результаты аудита HACCP
              </h2>
              <button
                onClick={() => setShowHaccpAuditModal(false)}
                className="text-gray-400 hover:text-white transition-colors text-2xl"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              {/* Issues List */}
              <div>
                <h3 className="text-lg font-bold text-orange-300 mb-4">
                  Обнаруженные проблемы ({haccpAuditResult.issues?.length || 0})
                </h3>
                {haccpAuditResult.issues && haccpAuditResult.issues.length > 0 ? (
                  <div className="space-y-3">
                    {haccpAuditResult.issues.map((issue, idx) => (
                      <div key={idx} className="bg-orange-800/30 p-3 rounded-lg flex items-start space-x-3">
                        <span className="text-orange-400 mt-1">⚠️</span>
                        <span className="text-gray-300 flex-1">{issue}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-green-800/30 p-4 rounded-lg text-center">
                    <span className="text-green-300 font-medium">✅ Проблем не обнаружено</span>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex justify-between pt-6 border-t border-orange-400/30">
                <button
                  onClick={() => setShowHaccpAuditModal(false)}
                  className="px-6 py-3 rounded-lg font-bold bg-gray-600 hover:bg-gray-700 text-white transition-colors"
                >
                  Отмена
                </button>
                {haccpAuditResult.issues && haccpAuditResult.issues.length > 0 && (
                  <button
                    onClick={applyHaccpPatch}
                    className="px-6 py-3 rounded-lg font-bold bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 text-white transition-colors"
                  >
                    Применить исправления
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* INGREDIENT MAPPING MODAL */}
      {mappingModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 rounded-lg p-6 max-w-3xl w-full mx-4 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-purple-300">Назначить продукт из каталога</h3>
              <button
                onClick={() => setMappingModalOpen(false)}
                className="text-gray-400 hover:text-white text-xl"
              >
                ✕
              </button>
            </div>
            
            {mappingIngredientIndex !== null && tcV2.ingredients[mappingIngredientIndex] && (
              <div className="mb-4 p-3 bg-gray-800 rounded">
                <p className="text-gray-300">
                  <strong>Ингредиент:</strong> {tcV2.ingredients[mappingIngredientIndex].name}
                </p>
              </div>
            )}

            {/* Tabs */}
            <div className="flex mb-4 bg-gray-800 rounded-lg p-1">
              <button
                onClick={() => setMappingActiveTab('all')}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  mappingActiveTab === 'all' 
                    ? 'bg-purple-600 text-white' 
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Все каталоги
              </button>
              <button
                onClick={() => setMappingActiveTab('usda')}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  mappingActiveTab === 'usda' 
                    ? 'bg-green-600 text-white' 
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                🇺🇸 USDA
              </button>
              <button
                onClick={() => setMappingActiveTab('price')}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  mappingActiveTab === 'price' 
                    ? 'bg-yellow-600 text-white' 
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                💰 Цены
              </button>
              <button
                onClick={() => setMappingActiveTab('iiko')}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors relative ${
                  mappingActiveTab === 'iiko' 
                    ? 'bg-purple-600 text-white' 
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                🏪 iiko
                {/* P0: iiko badge with count and update timestamp */}
                {iikoSearchBadge.count > 0 && (
                  <div className="absolute -top-1 -right-1 bg-green-500 text-white text-xs rounded-full px-1 min-w-[18px] h-4 flex items-center justify-center">
                    {iikoSearchBadge.count > 999 ? '999+' : iikoSearchBadge.count}
                  </div>
                )}
              </button>
              <button
                onClick={() => setMappingActiveTab('catalog')}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  mappingActiveTab === 'catalog' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Каталоги
              </button>
            </div>
            
            {/* P0: iiko badge info display */}
            {mappingActiveTab === 'iiko' && iikoSearchBadge.count > 0 && (
              <div className="mb-3 text-xs text-gray-400 text-center">
                iiko · {iikoSearchBadge.count.toLocaleString('ru-RU')} позиций · обновлено {
                  iikoSearchBadge.last_sync ? 
                    new Date(iikoSearchBadge.last_sync).toLocaleString('ru-RU', {
                      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                    }) : 
                    'никогда'
                }
              </div>
            )}

            {/* Search Input */}
            <div className="mb-4">
              {mappingActiveTab === 'usda' ? (
                <input
                  type="text"
                  value={usdaSearchQuery}
                  onChange={(e) => {
                    setUsdaSearchQuery(e.target.value);
                    debouncedUsdaSearch(e.target.value);
                  }}
                  placeholder="Поиск в USDA FoodData Central..."
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white placeholder-gray-400"
                />
              ) : mappingActiveTab === 'price' ? (
                <input
                  type="text"
                  value={priceSearchQuery}
                  onChange={(e) => {
                    setPriceSearchQuery(e.target.value);
                    debouncedPriceSearch(e.target.value);
                  }}
                  placeholder="Поиск цен в каталогах..."
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white placeholder-gray-400"
                />
              ) : mappingActiveTab === 'iiko' ? (
                <div>
                  <input
                    type="text"
                    value={iikoSearchQuery}
                    onChange={(e) => {
                      setIikoSearchQuery(e.target.value);
                      debouncedIikoSearch(e.target.value);
                    }}
                    onCompositionEnd={(e) => {
                      // P0: Handle RU input composition (IME)
                      debouncedIikoSearch(e.target.value);
                    }}
                    placeholder="Поиск в iiko: название или артикул (02684)..."
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white placeholder-gray-400"
                  />
                  
                  {/* P0: Debug badge under input */}
                  {(iikoSearchQuery || iikoSearchBadge.count > 0) && (
                    <div className="mt-2 text-xs text-gray-500 text-center">
                      iiko · {iikoSearchBadge.count || 0} · org={iikoSearchBadge.orgId || 'default'} · 
                      t={iikoSearchBadge.latency || 0}ms
                      {iikoSearchBadge.connection_status && ` · ${iikoSearchBadge.connection_status}`}
                      {iikoSearchBadge.error && ` · ERROR: ${iikoSearchBadge.error}`}
                    </div>
                  )}
                </div>
              ) : (
                <input
                  type="text"
                  value={catalogSearchQuery}
                  onChange={(e) => {
                    setCatalogSearchQuery(e.target.value);
                    performCatalogSearch(e.target.value);
                  }}
                  placeholder="Поиск в каталоге продуктов..."
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white placeholder-gray-400"
                />
              )}
            </div>
            
            {/* Loading State */}
            {((mappingActiveTab === 'usda' && isSearchingUsda) || 
              (mappingActiveTab === 'price' && isSearchingPrice) ||
              (mappingActiveTab === 'iiko' && isSearchingIiko) ||
              (mappingActiveTab !== 'usda' && mappingActiveTab !== 'price' && mappingActiveTab !== 'iiko' && isSearching)) && (
              <div className="text-center py-4 text-gray-400">
                🔍 Поиск...
              </div>
            )}
            
            {/* Results */}
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {mappingActiveTab === 'usda' ? (
                // USDA Results
                <>
                  {usdaSearchResults.map((item, index) => (
                    <div
                      key={index}
                      className="p-3 bg-gray-800 hover:bg-gray-700 rounded cursor-pointer transition-colors border-l-4 border-green-500"
                      onClick={() => handleAssignIngredientMapping(item)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="font-bold text-white">{item.name}</div>
                          <div className="text-sm text-gray-400">
                            <span className="bg-green-600 text-white px-2 py-0.5 rounded text-xs mr-2">USDA</span>
                            {item.nutrition_preview && (
                              <span className="text-green-300">{item.nutrition_preview}</span>
                            )}
                          </div>
                          {item.fdc_id && (
                            <div className="text-xs text-gray-500 mt-1">
                              FDC ID: {item.fdc_id}
                            </div>
                          )}
                          {/* Show portions if available */}
                          {item.portions && item.portions.length > 0 && (
                            <div className="text-xs text-blue-300 mt-1">
                              Порции: {item.portions.slice(0, 2).map(p => `${p.desc} (${p.g}г)`).join(', ')}
                              {item.portions.length > 2 && ` +${item.portions.length - 2} еще`}
                            </div>
                          )}
                        </div>
                        <div className="text-green-400 text-xs">
                          📊 БЖУ
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {!isSearchingUsda && usdaSearchQuery && usdaSearchResults.length === 0 && (
                    <div className="text-center py-6 text-gray-400">
                      <div className="text-2xl mb-2">🔍</div>
                      <div>Ничего не найдено в USDA для "{usdaSearchQuery}"</div>
                      <button
                        onClick={() => setMappingModalOpen(false)}
                        className="mt-2 text-sm text-blue-400 hover:text-blue-300"
                      >
                        Сообщить о пропуске
                      </button>
                    </div>
                  )}
                </>
              ) : mappingActiveTab === 'price' ? (
                // Price Results
                <>
                  {priceSearchResults.map((item, index) => (
                    <div
                      key={index}
                      className={`p-3 bg-gray-800 hover:bg-gray-700 rounded cursor-pointer transition-colors border-l-4 ${
                        item.source === 'user' ? 'border-purple-500' : 
                        item.source === 'catalog' ? 'border-blue-500' : 'border-orange-500'
                      }`}
                      onClick={() => handleAssignIngredientMapping(item)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="font-bold text-white">{item.name}</div>
                          <div className="text-sm text-gray-400">
                            <span className={`px-2 py-0.5 rounded text-xs mr-2 text-white ${
                              item.source === 'user' ? 'bg-purple-600' : 
                              item.source === 'catalog' ? 'bg-blue-600' : 'bg-orange-600'
                            }`}>
                              {item.source === 'user' ? 'USER' : 
                               item.source === 'catalog' ? 'CAT' : 'BOOT'}
                            </span>
                            <span className="text-green-300 font-bold">
                              {item.price_per_unit}₽/{item.unit}
                            </span>
                            {item.currency && item.currency !== 'RUB' && (
                              <span className="text-gray-400 text-xs ml-1">({item.currency})</span>
                            )}
                          </div>
                          {item.sku_id && (
                            <div className="text-xs text-gray-500 mt-1">
                              SKU: {item.sku_id}
                            </div>
                          )}
                          {item.asOf && (
                            <div className="text-xs text-blue-300 mt-1">
                              Обновлено: {item.asOf}
                            </div>
                          )}
                        </div>
                        <div className="text-yellow-400 text-xs">
                          💰 Цена
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {!isSearchingPrice && priceSearchQuery && priceSearchResults.length === 0 && (
                    <div className="text-center py-6 text-gray-400">
                      <div className="text-2xl mb-2">🔍</div>
                      <div>Цены не найдены для "{priceSearchQuery}"</div>
                      <button
                        onClick={() => setMappingModalOpen(false)}
                        className="mt-2 text-sm text-blue-400 hover:text-blue-300"
                      >
                        Закрыть
                      </button>
                    </div>
                  )}
                </>
              ) : mappingActiveTab === 'iiko' ? (
                // P0: iiko RMS Results - Enhanced format {name · unit · score%}
                <>
                  {iikoSearchResults.map((item, index) => (
                    <div
                      key={index}
                      className="p-3 bg-gray-800 hover:bg-gray-700 rounded cursor-pointer transition-colors border-l-4 border-purple-500"
                      onClick={() => handleAssignIngredientMapping(item)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          {/* P0: Enhanced display format {name · unit · score%} */}
                          <div className="font-bold text-white">
                            {item.name}
                            <span className="text-gray-400 font-normal text-sm ml-2">
                              · {item.unit} · {Math.round((item.match_score || 0) * 100)}%
                            </span>
                          </div>
                          
                          <div className="text-sm text-gray-400 mt-1">
                            <span className="bg-purple-600 text-white px-2 py-0.5 rounded text-xs mr-2">iiko</span>
                            {item.price > 0 && (
                              <span className="text-green-300 font-bold">
                                {item.price}₽/{item.unit}
                              </span>
                            )}
                            {item.category && (
                              <span className="text-gray-400 ml-2">{item.category}</span>
                            )}
                          </div>
                          
                          {/* Additional metadata */}
                          <div className="text-xs text-gray-500 mt-1 space-y-0.5">
                            {item.article && (
                              <div className="text-green-400 font-mono">
                                Артикул (iiko): {String(item.article).padStart(5, '0')}
                              </div>
                            )}
                            {item.sku_id && !item.article && (
                              <div className="text-gray-500" title="Код быстрого набора iikoFront (не используется в ТТК)">
                                ID: {item.sku_id.substring(0, 8)}...
                              </div>
                            )}
                            {item.product_type && (
                              <div className="text-purple-300">
                                Тип: {item.product_type === 'DISH' ? 'Блюдо' : 
                                     item.product_type === 'GOODS' ? 'Товар' : 
                                     item.product_type === 'PREPARED' ? 'Заготовка' : 
                                     item.product_type}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="text-purple-400 text-xs flex flex-col items-center">
                          <div>🏪 iiko</div>
                          {item.match_score && (
                            <div className="text-yellow-300 font-bold mt-1">
                              {Math.round(item.match_score * 100)}%
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {/* P0: Enhanced empty-state with specific suggestions */}
                  {!isSearchingIiko && iikoSearchQuery && iikoSearchResults.length === 0 && (
                    <div className="text-center py-6 text-gray-400">
                      <div className="text-2xl mb-2">🔍</div>
                      <div>Ничего не найдено в iiko для "{iikoSearchQuery}"</div>
                      <div className="text-sm text-gray-500 mt-2">
                        {iikoRmsConnection.status !== 'connected' ? 
                          'Требуется подключение к iiko RMS' :
                          'Попробуйте: картоф, картофель свежий, картошка'
                        }
                      </div>
                      
                      {/* P0: Debug info in empty state */}
                      {iikoSearchBadge.error && (
                        <div className="mt-2 p-2 bg-red-900/20 rounded text-red-300 text-xs">
                          Ошибка: {iikoSearchBadge.error}
                        </div>
                      )}
                      
                      {/* P0: Enhanced empty-state suggestions */}
                      <div className="mt-4 p-3 bg-blue-900/20 rounded-lg text-left text-xs">
                        <div className="font-medium text-blue-300 mb-2">💡 Советы по поиску:</div>
                        <ul className="text-blue-400 space-y-1">
                          <li>• <strong>02684</strong> → поиск по артикулу (точное совпадение)</li>
                          <li>• <strong>картоф</strong> → найдет "Картофель", "Картошка"</li>
                          <li>• <strong>молоко 3.2</strong> → найдет продукты с жирностью 3,2%</li>
                          <li>• <strong>яйцо</strong> → найдет "Яйцо куриное С1"</li>
                          <li>• <strong>куриный</strong> → найдет "Куриный попкорн", "Фарш куриный"</li>
                        </ul>
                      </div>
                      <button
                        onClick={() => setMappingModalOpen(false)}
                        className="mt-2 text-sm text-blue-400 hover:text-blue-300"
                      >
                        Закрыть
                      </button>
                    </div>
                  )}
                  
                  {/* Connection status hint */}
                  {!iikoSearchQuery && iikoRmsConnection.status !== 'connected' && (
                    <div className="text-center py-6 text-gray-400">
                      <div className="text-2xl mb-2">🏪</div>
                      <div>Подключитесь к серверу iiko RMS</div>
                      <div className="text-sm text-gray-500 mt-2">
                        Для поиска номенклатуры установите подключение в разделе ДАННЫЕ → iiko RMS
                      </div>
                      <button
                        onClick={() => {
                          setMappingModalOpen(false);
                          setShowIikoRmsModal(true);
                        }}
                        className="mt-3 bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded text-sm transition-colors"
                      >
                        🔗 Подключить IIKO RMS
                      </button>
                    </div>
                  )}
                </>
              ) : (
                // All/Catalog Results  
                <>
                  {catalogSearchResults.map((item, index) => (
                    <div
                      key={index}
                      className={`p-3 bg-gray-800 hover:bg-gray-700 rounded cursor-pointer transition-colors border-l-4 ${
                        item.source === 'usda' ? 'border-green-500' : 
                        item.source === 'catalog' ? 'border-blue-500' : 'border-orange-500'
                      }`}
                      onClick={() => handleAssignIngredientMapping(item)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-bold text-white">{item.name}</div>
                          <div className="text-sm text-gray-400">
                            <span className={`px-2 py-0.5 rounded text-xs mr-2 text-white ${
                              item.source === 'usda' ? 'bg-green-600' : 
                              item.source === 'catalog' ? 'bg-blue-600' : 'bg-orange-600'
                            }`}>
                              {item.source === 'usda' ? 'USDA' : 
                               item.source === 'catalog' ? 'CAT' : 'BOOT'}
                            </span>
                            {item.category}
                            {item.price && ` • ${item.price}₽/${item.unit}`}
                            {item.nutrition_preview && ` • ${item.nutrition_preview}`}
                          </div>
                        </div>
                        <div className="flex gap-1">
                          {item.price && <span className="text-green-400 text-xs">💰</span>}
                          {item.has_nutrition && <span className="text-blue-400 text-xs">📊</span>}
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {!isSearching && catalogSearchQuery && catalogSearchResults.length === 0 && (
                    <div className="text-center py-4 text-gray-400">
                      Ничего не найдено для "{catalogSearchQuery}"
                    </div>
                  )}
                </>
              )}
            </div>
            
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setMappingModalOpen(false)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Data Options Modal (IK-02B-FE/01) */}
      {showDataModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800/95 backdrop-blur-lg rounded-2xl w-full max-w-lg border border-purple-400/20">
            {/* Header */}
            <div className="bg-gray-800/95 backdrop-blur-lg border-b border-purple-400/20 p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold text-purple-300 mb-2">📂 ДАННЫЕ</h2>
                  <p className="text-gray-400">Выберите источник данных для техкарт</p>
                </div>
                <button
                  onClick={() => setShowDataModal(false)}
                  className="text-gray-400 hover:text-white text-3xl font-bold transition-colors"
                >
                  ×
                </button>
              </div>
            </div>
            
            {/* Options */}
            <div className="p-6 space-y-4">
              <button
                onClick={() => {
                  setShowDataModal(false);
                  setShowUploadModal(true);
                }}
                className="w-full bg-gradient-to-r from-yellow-600 to-yellow-700 hover:from-yellow-700 hover:to-yellow-800 text-white font-bold py-4 px-6 rounded-xl transition-all duration-300 flex items-center space-x-3"
              >
                <span className="text-2xl">📤</span>
                <div className="text-left">
                  <div className="text-lg">Загрузить файлы</div>
                  <div className="text-sm opacity-90">Прайсы и данные по БЖУ из CSV/JSON</div>
                </div>
              </button>
              
              {/* Нерабочие iiko кнопки убраны для чистоты интерфейса */}
            </div>
          </div>
        </div>
      )}

      {/* Upload Data Modal (Task 1.2) */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800/95 backdrop-blur-lg rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-purple-400/20">
            {/* Header */}
            <div className="sticky top-0 bg-gray-800/95 backdrop-blur-lg border-b border-purple-400/20 p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold text-purple-300 mb-2">📂 ЗАГРУЗИТЬ ДАННЫЕ</h2>
                  <p className="text-gray-400">Импорт прайсов и данных по питанию для лучшего расчёта техкарт</p>
                </div>
                <button
                  onClick={() => setShowUploadModal(false)}
                  className="text-gray-400 hover:text-white text-3xl font-bold transition-colors"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              {!uploadResults ? (
                <div>
                  {/* Type Selection */}
                  <div className="mb-6">
                    <label className="block text-sm font-bold text-gray-300 mb-3">
                      Тип данных для загрузки:
                    </label>
                    <div className="flex gap-4">
                      <button
                        onClick={() => setUploadType('prices')}
                        className={`flex-1 p-4 rounded-lg border-2 text-left transition-all ${
                          uploadType === 'prices'
                            ? 'border-green-400 bg-green-400/10 text-green-300'
                            : 'border-gray-600 bg-gray-700/50 text-gray-300 hover:border-gray-500'
                        }`}
                      >
                        <div className="text-lg font-bold mb-2">💰 Прайс-лист</div>
                        <div className="text-sm text-gray-400">CSV, Excel файлы с ценами на продукты</div>
                      </button>
                      <button
                        onClick={() => setUploadType('nutrition')}
                        className={`flex-1 p-4 rounded-lg border-2 text-left transition-all ${
                          uploadType === 'nutrition'
                            ? 'border-blue-400 bg-blue-400/10 text-blue-300'
                            : 'border-gray-600 bg-gray-700/50 text-gray-300 hover:border-gray-500'
                        }`}
                      >
                        <div className="text-lg font-bold mb-2">📊 БЖУ данные</div>
                        <div className="text-sm text-gray-400">JSON, CSV с данными по питательности</div>
                      </button>
                    </div>
                  </div>

                  {/* File Upload */}
                  <div className="mb-6">
                    <label className="block text-sm font-bold text-gray-300 mb-3">
                      Выберите файл:
                    </label>
                    <input
                      type="file"
                      accept={uploadType === 'prices' ? '.csv,.xlsx,.xls' : '.json,.csv'}
                      onChange={handleFileSelect}
                      className="w-full p-3 border border-gray-600 rounded-lg bg-gray-700 text-white"
                    />
                    <div className="mt-2 text-sm text-gray-400">
                      {uploadType === 'prices' 
                        ? 'Поддерживаются: CSV, Excel (.xlsx, .xls)'
                        : 'Поддерживаются: JSON, CSV'
                      }
                    </div>
                  </div>

                  {/* File Preview */}
                  {uploadPreview && (
                    <div className="mb-6 p-4 bg-gray-700/50 rounded-lg border border-gray-600">
                      <div className="text-sm font-bold text-white mb-2">📋 Предпросмотр файла:</div>
                      <div className="space-y-1 text-sm">
                        <div><span className="text-gray-400">Имя:</span> <span className="text-white">{uploadPreview.name}</span></div>
                        <div><span className="text-gray-400">Размер:</span> <span className="text-white">{uploadPreview.size}</span></div>
                        <div><span className="text-gray-400">Тип:</span> <span className="text-white">{uploadPreview.type}</span></div>
                        <div className="mt-3">
                          <span className="text-gray-400">
                            {uploadType === 'prices' ? 'Ожидаемые колонки:' : 'Ожидаемый формат:'}
                          </span>
                          <div className="text-yellow-300 text-xs mt-1">
                            {uploadPreview.expectedColumns || uploadPreview.expectedFormat}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex justify-end space-x-4">
                    <button
                      onClick={() => setShowUploadModal(false)}
                      className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
                    >
                      Отмена
                    </button>
                    <button
                      onClick={handleUpload}
                      disabled={!uploadFile || isUploading}
                      className={`px-6 py-2 rounded-lg transition-colors font-bold ${
                        !uploadFile || isUploading
                          ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                          : uploadType === 'prices'
                            ? 'bg-green-600 hover:bg-green-700 text-white'
                            : 'bg-blue-600 hover:bg-blue-700 text-white'
                      }`}
                    >
                      {isUploading ? (
                        <>
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Загружаю...
                        </>
                      ) : (
                        `📤 Загрузить ${uploadType === 'prices' ? 'прайсы' : 'БЖУ данные'}`
                      )}
                    </button>
                  </div>
                </div>
              ) : (
                /* Upload Results */
                <div>
                  {uploadResults.success ? (
                    <div>
                      <div className="flex items-center mb-4">
                        <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center mr-4">
                          <span className="text-white text-2xl">✅</span>
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-green-300">Загрузка успешна!</h3>
                          <p className="text-gray-300">{uploadResults.message}</p>
                        </div>
                      </div>

                      <div className="bg-green-900/20 border border-green-600/30 rounded-lg p-4 mb-4">
                        <div className="text-sm font-bold text-green-300 mb-2">
                          📊 Результат: {uploadResults.count} позиций обработано
                        </div>
                        
                        {uploadResults.preview && uploadResults.preview.length > 0 && (
                          <div>
                            <div className="text-xs text-gray-400 mb-2">Примеры загруженных данных:</div>
                            <div className="space-y-1 max-h-32 overflow-y-auto">
                              {uploadResults.preview.map((item, index) => (
                                <div key={index} className="text-xs bg-gray-800/50 rounded p-2">
                                  {uploadType === 'prices' ? (
                                    <div className="flex gap-2">
                                      <span className="text-white">{item.name}</span>
                                      <span className="text-green-300">{item.price}₽</span>
                                      <span className="text-gray-400">{item.unit}</span>
                                    </div>
                                  ) : (
                                    <div className="flex gap-2 text-xs">
                                      <span className="text-white">{item.name}</span>
                                      <span className="text-yellow-300">{item.kcal} ккал</span>
                                      <span className="text-blue-300">Б:{item.proteins_g}г</span>
                                      <span className="text-orange-300">Ж:{item.fats_g}г</span>
                                      <span className="text-green-300">У:{item.carbs_g}г</span>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="bg-blue-900/20 border border-blue-600/30 rounded-lg p-4 mb-6">
                        <div className="text-sm font-bold text-blue-300 mb-2">💡 Что дальше?</div>
                          <div className="text-xs text-gray-300 space-y-1">
                            <div>- Данные сохранены и будут использоваться для расчёта техкарт</div>
                            <div>- Создайте новую техкарту для проверки покрытия данными</div>
                            <div>- Используйте кнопку "Пересчитать" в существующих техкартах</div>
                          </div>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex justify-end space-x-4">
                        <button
                          onClick={() => {
                            setShowUploadModal(false);
                            setUploadResults(null);
                          }}
                          className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
                        >
                          Закрыть
                        </button>
                        {tcV2 && (
                          <button
                            onClick={triggerRecalc}
                            disabled={isRecalculating}
                            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:bg-gray-600"
                          >
                            {isRecalculating ? 'Пересчитываю...' : 'Пересчитать текущую ТК'}
                          </button>
                        )}
                      </div>
                    </div>
                  ) : (
                    /* Error State */
                    <div>
                      <div className="flex items-center mb-4">
                        <div className="w-12 h-12 bg-red-600 rounded-full flex items-center justify-center mr-4">
                          <span className="text-white text-2xl">❌</span>
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-red-300">Ошибка загрузки</h3>
                          <p className="text-gray-300">Не удалось обработать файл</p>
                        </div>
                      </div>

                      <div className="bg-red-900/20 border border-red-600/30 rounded-lg p-4 mb-6">
                        <div className="text-sm text-red-300">
                          {uploadResults.error}
                        </div>
                      </div>

                      <div className="flex justify-end space-x-4">
                        <button
                          onClick={() => setUploadResults(null)}
                          className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
                        >
                          Попробовать снова
                        </button>
                        <button
                          onClick={() => setShowUploadModal(false)}
                          className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                        >
                          Закрыть
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Sub-Recipe Modal */}
      {showSubRecipeModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800/95 backdrop-blur-lg rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-purple-400/20">
            <div className="sticky top-0 bg-gray-800/95 backdrop-blur-lg border-b border-purple-400/20 p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold text-purple-300 mb-2">📋 ВЫБРАТЬ ПОДРЕЦЕПТ</h2>
                  <p className="text-gray-400">Выберите существующую техкарту как подрецепт</p>
                </div>
                <button
                  onClick={() => setShowSubRecipeModal(false)}
                  className="text-gray-400 hover:text-white text-3xl font-bold transition-colors"
                >
                  ×
                </button>
              </div>
            </div>
            
            <div className="p-6">
              {availableSubRecipes.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <div className="text-4xl mb-4">📋</div>
                  <p>Нет доступных техкарт для подрецептов</p>
                  <p className="text-sm mt-2">Создайте больше техкарт, чтобы использовать их как подрецепты</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {availableSubRecipes.map((subRecipe, index) => (
                    <div 
                      key={index}
                      className="bg-gray-700/50 rounded-lg p-4 hover:bg-gray-700/70 transition-colors cursor-pointer border border-gray-600 hover:border-blue-500"
                      onClick={() => assignSubRecipe(subRecipe)}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="text-white font-bold mb-1">{subRecipe.title}</h3>
                          <div className="text-gray-400 text-sm">
                            ID: {subRecipe.id}
                            {subRecipe.created_at && (
                              <span className="ml-4">
                                📅 {new Date(subRecipe.created_at).toLocaleDateString('ru-RU')}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="text-blue-400 font-bold">
                          Выбрать →
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* iiko RMS Integration Modal (IK-02B-FE/01) */}
      {showIikoRmsModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-40 p-4">
          <div className="bg-gray-800/95 backdrop-blur-lg rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-purple-400/20">
            {/* Header */}
            <div className="sticky top-0 bg-gray-800/95 backdrop-blur-lg border-b border-purple-400/20 p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold text-purple-300 mb-2">🏪 iiko RMS</h2>
                  <p className="text-gray-400">Подключение к системе ресторана для синхронизации номенклатуры</p>
                </div>
                <button
                  onClick={() => {
                    setShowIikoRmsModal(false);
                    setIikoRmsMessage({ type: '', text: '' });
                  }}
                  className="text-gray-400 hover:text-white text-3xl font-bold transition-colors"
                >
                  ×
                </button>
              </div>
            </div>
            
            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Message Banner */}
              {iikoRmsMessage.text && (
                <div className={`p-4 rounded-xl border ${
                  iikoRmsMessage.type === 'success' ? 'bg-green-900/50 border-green-400/30 text-green-300' :
                  iikoRmsMessage.type === 'error' ? 'bg-red-900/50 border-red-400/30 text-red-300' :
                  'bg-blue-900/50 border-blue-400/30 text-blue-300'
                }`}>
                  {iikoRmsMessage.text}
                </div>
              )}
              
              {/* Connection Status */}
              <div className="bg-gray-700/50 rounded-xl p-4 border border-gray-600/50">
                <h3 className="text-lg font-semibold text-purple-300 mb-3">📊 Статус подключения</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Статус:</span>
                    <span className={`font-semibold ${
                      iikoRmsConnection.status === 'connected' ? 'text-green-300' :
                      iikoRmsConnection.status === 'needs_reconnection' ? 'text-yellow-300' :
                      iikoRmsConnection.status === 'error' ? 'text-red-300' :
                      'text-gray-300'
                    }`}>
                      {iikoRmsConnection.status === 'connected' ? '✅ Подключено' :
                       iikoRmsConnection.status === 'needs_reconnection' ? '⚠️ Нужно переподключиться' :
                       iikoRmsConnection.status === 'error' ? '❌ Ошибка' :
                       '🔧 Настройка'}
                    </span>
                  </div>
                  {iikoRmsConnection.organization_name && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Организация:</span>
                      <span className="text-white">{iikoRmsConnection.organization_name}</span>
                    </div>
                  )}
                  {iikoRmsConnection.last_connection && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Подключение:</span>
                      <span className="text-white">{new Date(iikoRmsConnection.last_connection).toLocaleString('ru-RU')}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-400">Синхронизация:</span>
                    <span className={`font-semibold ${
                      iikoRmsConnection.sync_status === 'completed' ? 'text-green-300' :
                      iikoRmsConnection.sync_status === 'syncing' ? 'text-yellow-300' :
                      iikoRmsConnection.sync_status === 'failed' ? 'text-red-300' :
                      'text-gray-300'
                    }`}>
                      {iikoRmsConnection.sync_status === 'completed' ? '✅ Завершена' :
                       iikoRmsConnection.sync_status === 'syncing' ? '🔄 Выполняется' :
                       iikoRmsConnection.sync_status === 'failed' ? '❌ Ошибка' :
                       '⚪ Не выполнялась'}
                    </span>
                  </div>
                  {iikoRmsConnection.products_count > 0 && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Позиций в каталоге:</span>
                      <span className="text-white font-semibold">{iikoRmsConnection.products_count.toLocaleString('ru-RU')}</span>
                    </div>
                  )}
                  {iikoRmsConnection.last_sync && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Последняя синхронизация:</span>
                      <span className="text-white">{new Date(iikoRmsConnection.last_sync).toLocaleString('ru-RU')}</span>
                    </div>
                  )}
                </div>
              </div>
              
              {/* Connection Form */}
              <div className="bg-gray-700/50 rounded-xl p-4 border border-gray-600/50">
                <h3 className="text-lg font-semibold text-purple-300 mb-3">🔗 Настройки подключения</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Хост сервера iiko RMS
                    </label>
                    <input
                      type="text"
                      value={iikoRmsCredentials.host}
                      onChange={(e) => setIikoRmsCredentials(prev => ({ ...prev, host: e.target.value }))}
                      placeholder="your-restaurant.iiko.it"
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-purple-400 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Логин
                    </label>
                    <input
                      type="text"
                      value={iikoRmsCredentials.login}
                      onChange={(e) => setIikoRmsCredentials(prev => ({ ...prev, login: e.target.value }))}
                      placeholder="Введите логин"
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-purple-400 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Пароль
                    </label>
                    <input
                      type="password"
                      value={iikoRmsCredentials.password}
                      onChange={(e) => setIikoRmsCredentials(prev => ({ ...prev, password: e.target.value }))}
                      placeholder="Введите пароль"
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-purple-400 focus:outline-none"
                    />
                  </div>
                  
                  <div className="flex space-x-3">
                    {iikoRmsConnection.status === 'connected' || iikoRmsConnection.status === 'needs_reconnection' ? (
                      <>
                        <button
                          onClick={connectToIikoRms}
                          disabled={isConnectingIikoRms || !iikoRmsCredentials.host || !iikoRmsCredentials.login || !iikoRmsCredentials.password}
                          className="flex-1 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-bold py-3 px-6 rounded-xl transition-all duration-300"
                        >
                          {isConnectingIikoRms ? '⏳ Переподключение...' : 
                           iikoRmsConnection.status === 'needs_reconnection' ? '🔄 Переподключить' : '🔗 Обновить'}
                        </button>
                        
                        <button
                          onClick={syncIikoRmsNomenclature}
                          disabled={isSyncingIikoRms || iikoRmsConnection.status !== 'connected'}
                          className="flex-1 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-bold py-3 px-6 rounded-xl transition-all duration-300"
                        >
                          {isSyncingIikoRms ? '⏳ Синхронизация...' : '🔄 Синхронизировать'}
                        </button>
                        
                        <button
                          onClick={disconnectFromIikoRms}
                          className="bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white font-bold py-3 px-4 rounded-xl transition-all duration-300"
                          title="Забыть подключение"
                        >
                          🗑️
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={connectToIikoRms}
                          disabled={isConnectingIikoRms || !iikoRmsCredentials.host || !iikoRmsCredentials.login || !iikoRmsCredentials.password}
                          className="flex-1 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-bold py-3 px-6 rounded-xl transition-all duration-300"
                        >
                          {isConnectingIikoRms ? '⏳ Подключение...' : '🔗 Подключить'}
                        </button>
                        
                        <button
                          onClick={syncIikoRmsNomenclature}
                          disabled={isSyncingIikoRms || iikoRmsConnection.status !== 'connected'}
                          className="flex-1 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-bold py-3 px-6 rounded-xl transition-all duration-300"
                        >
                          {isSyncingIikoRms ? '⏳ Синхронизация...' : '🔄 Синхронизировать'}
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Security Notice */}
              <div className="bg-yellow-900/30 border border-yellow-400/30 rounded-xl p-4">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">🔒</span>
                  <div className="text-sm text-yellow-300">
                    <div className="font-semibold">Безопасность данных</div>
                    <div className="text-yellow-400/80">
                      Пароль не сохраняется в браузере. Подключение происходит напрямую к вашему серверу iiko RMS.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Auto-Mapping Modal (IK-02B-FE/02) */}
      {showAutoMappingModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800/95 backdrop-blur-lg rounded-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden border border-purple-400/20 flex flex-col">
            {/* Header */}
            <div className="bg-gray-800/95 backdrop-blur-lg border-b border-purple-400/20 p-6 shrink-0">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold text-purple-300 mb-2">🏪 Автомаппинг из iiko RMS</h2>
                  <p className="text-gray-400">Сопоставление ингредиентов с номенклатурой ресторана</p>
                </div>
                <button
                  onClick={() => {
                    setShowAutoMappingModal(false);
                    setAutoMappingResults([]);
                    setAutoMappingMessage({ type: '', text: '' });
                  }}
                  className="text-gray-400 hover:text-white text-3xl font-bold transition-colors"
                >
                  ×
                </button>
              </div>
            </div>
            
            {/* Message Banner */}
            {autoMappingMessage.text && (
              <div className={`p-4 border-b border-gray-600/50 ${
                autoMappingMessage.type === 'success' ? 'bg-green-900/30 text-green-300' :
                autoMappingMessage.type === 'error' ? 'bg-red-900/30 text-red-300' :
                'bg-blue-900/30 text-blue-300'
              }`}>
                {autoMappingMessage.text}
              </div>
            )}
            
            {/* Instructions */}
            <div className="p-4 border-b border-gray-600/50 bg-blue-900/20">
              <h4 className="text-blue-300 font-bold mb-2">💡 Как это работает:</h4>
              <ul className="text-sm text-blue-200 space-y-1">
                <li>• <strong>Принять</strong> - использовать найденный товар IIKO</li>
                <li>• <strong>Изменить</strong> - выбрать другой товар вручную</li>
                <li>• <strong>Отклонить</strong> - не связывать с IIKO (артикул не назначится)</li>
              </ul>
            </div>
            
            {/* Filters */}
            <div className="p-4 border-b border-gray-600/50 bg-gray-700/30">
              <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
                <div className="flex space-x-2">
                  <button
                    onClick={() => setAutoMappingFilter('all')}
                    className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                      autoMappingFilter === 'all' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    Все
                  </button>
                  <button
                    onClick={() => setAutoMappingFilter('no_product_code')}
                    className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                      autoMappingFilter === 'no_product_code' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white'
                    }`}
                    title="B. Terminology & UI: Показать только ингредиенты без артикулов iiko"
                  >
                    Только без артикулов
                  </button>
                  <button
                    onClick={() => setAutoMappingFilter('low_confidence')}
                    className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                      autoMappingFilter === 'low_confidence' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    Низкая уверенность (&lt;90%)
                  </button>
                </div>
                
                <input
                  type="text"
                  value={autoMappingSearch}
                  onChange={(e) => setAutoMappingSearch(e.target.value)}
                  placeholder="Поиск по названию ингредиента..."
                  className="flex-1 min-w-0 px-3 py-2 bg-gray-800 border border-gray-600 rounded text-white placeholder-gray-400 focus:border-purple-400 focus:outline-none text-sm"
                />
                
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="preserveExistingProductCode"
                    checked={preserveExistingProductCode}
                    onChange={(e) => setPreserveExistingProductCode(e.target.checked)}
                    className="w-4 h-4 text-purple-600 bg-gray-800 border-gray-600 rounded focus:ring-purple-500 focus:ring-2"
                  />
                  <label htmlFor="preserveExistingProductCode" className="text-sm text-gray-300" title="B. Terminology & UI: Сохранять существующие артикулы продуктов">
                    Не перезаписывать артикулы (iiko)
                  </label>
                </div>
              </div>
            </div>
            
            {/* Results Table */}
            <div className="flex-1 overflow-y-auto max-h-[60vh]">
              <div className="p-4 space-y-2">
                {getFilteredAutoMappingResults().map((result, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg border transition-colors ${
                      result.status === 'accepted' ? 'bg-green-900/20 border-green-500/30' :
                      result.status === 'auto_accept' ? 'bg-blue-900/20 border-blue-500/30' :
                      result.status === 'rejected' ? 'bg-red-900/20 border-red-500/30' :
                      result.status === 'error' ? 'bg-red-900/30 border-red-500/50' :
                      result.status === 'skipped' ? 'bg-gray-900/30 border-gray-600/50' :
                      'bg-gray-800/50 border-gray-600/30'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      {/* P0-2: Ingredient Info with enhanced display */}
                      <div className="flex-1 min-w-0 mr-4">
                        <div className="flex items-center space-x-3 mb-2">
                          <div className="font-medium text-white">
                            {result.ingredient_name}
                            <span className="text-gray-400 ml-2 text-sm">({result.original_unit})</span>
                          </div>
                          {(result.currentSku || result.currentProductCode) && (
                            <span className="bg-gray-600 text-gray-200 px-2 py-1 rounded text-xs" title="B. Terminology & UI: Текущий артикул продукта в iiko">
                              Артикул: {result.currentProductCode || result.currentSku || 'не назначен'}
                            </span>
                          )}
                        </div>
                        
                        {result.suggestion ? (
                          <div className="flex items-center space-x-4 text-sm">
                            <div className="flex-1 min-w-0">
                              <div className="text-purple-300 font-medium">
                                {result.suggestion.name}
                              </div>
                              <div className="text-gray-400">
                                SKU: {result.suggestion.sku_id} • {result.suggestion.unit}
                                {result.suggestion.group_name && (
                                  <span className="ml-2">• {result.suggestion.group_name}</span>
                                )}
                              </div>
                            </div>
                            
                            <div className="flex items-center space-x-2">
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                result.confidence >= 90 ? 'bg-green-600 text-white' :
                                result.confidence >= 75 ? 'bg-yellow-600 text-white' :
                                'bg-red-600 text-white'
                              }`}>
                                {result.confidence}%
                              </span>
                              
                              <span className="bg-purple-600 text-white px-2 py-1 rounded text-xs">
                                iiko
                              </span>
                              
                              {/* P0-2: Unit-mismatch display - не скрывать */}
                              {result.suggestion.unit_mismatch && (
                                <span className="bg-yellow-600 text-white px-2 py-1 rounded text-xs" title="Единица измерения не совпала">
                                  ⚠ единица не совпала
                                </span>
                              )}
                            </div>
                          </div>
                        ) : (
                          <div className="text-gray-500 text-sm">
                            {result.reason || 'Совпадения не найдены'}
                          </div>
                        )}
                      </div>
                      
                      {/* Actions */}
                      <div className="flex space-x-2">
                        {result.suggestion && result.status !== 'skipped' && (
                          <>
                            <button
                              onClick={() => acceptAutoMappingSuggestion(index, true)}
                              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                                result.status === 'accepted' || result.status === 'auto_accept'
                                  ? 'bg-green-600 text-white'
                                  : 'bg-gray-600 hover:bg-green-600 text-gray-200 hover:text-white'
                              }`}
                            >
                              ✓ Принять
                            </button>
                            <button
                              onClick={() => {
                                // Открываем поиск товаров IIKO для этого ингредиента
                                const ingredientIndex = tcV2.ingredients.findIndex(
                                  ing => ing && ing.name === (result.ingredient_name || (result.ingredient && result.ingredient.name))
                                );
                                if (ingredientIndex >= 0) {
                                  handleOpenIngredientMapping(ingredientIndex);
                                  setShowAutoMappingModal(false);
                                }
                              }}
                              className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors"
                              title="Выбрать другой товар из IIKO вручную"
                            >
                              🔍 Изменить
                            </button>
                            <button
                              onClick={() => acceptAutoMappingSuggestion(index, false)}
                              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                                result.status === 'rejected'
                                  ? 'bg-red-600 text-white'
                                  : 'bg-gray-600 hover:bg-red-600 text-gray-200 hover:text-white'
                              }`}
                            >
                              ✗ Отклонить
                            </button>
                          </>
                        )}
                        
                        {/* Если предложения нет, показываем только кнопку ручного поиска */}
                        {!result.suggestion && (
                          <button
                            onClick={() => {
                              const ingredientIndex = tcV2.ingredients.findIndex(
                                ing => ing && ing.name === (result.ingredient_name || (result.ingredient && result.ingredient.name))
                              );
                              if (ingredientIndex >= 0) {
                                handleOpenIngredientMapping(ingredientIndex);
                                setShowAutoMappingModal(false);
                              }
                            }}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors"
                            title="Найти товар в IIKO вручную"
                          >
                            🔍 Найти в IIKO
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                
                {getFilteredAutoMappingResults().length === 0 && (
                  <div className="text-center py-12 text-gray-400">
                    <div className="text-3xl mb-4">🔍</div>
                    <div className="text-lg">Нет результатов для отображения</div>
                    <div className="text-sm text-gray-500 mt-2">
                      Попробуйте изменить фильтры или выполнить автомаппинг
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            {/* Actions Panel */}
            <div className="border-t border-gray-600/50 p-4 bg-gray-700/30">
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-400">
                  {autoMappingResults.filter(r => r.status === 'accepted' || r.status === 'auto_accept').length} из {autoMappingResults.length} позиций будет изменено
                </div>
                
                <div className="flex flex-col sm:flex-row gap-3">
                  <button
                    onClick={acceptAllHighConfidence}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition-colors"
                  >
                    Принять всё (≥90%)
                  </button>

                  {/* UX-Polish: Undo button */}
                  {lastMappingAction && lastMappingAction.undoable && (
                    <button
                      onClick={undoLastMappingAction}
                      className="bg-orange-600 hover:bg-orange-700 text-white font-bold py-2 px-4 rounded transition-colors"
                      title="Отменить последнее массовое принятие"
                    >
                      ↩️ Undo ({lastMappingAction.ingredients_count})
                    </button>
                  )}
                  
                  <button
                    onClick={applyAutoMappingChanges}
                    disabled={autoMappingResults.filter(r => r.status === 'accepted' || r.status === 'auto_accept').length === 0}
                    className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded transition-colors"
                  >
                    Применить выбранное
                  </button>
                  
                  <button
                    onClick={() => {
                      setShowAutoMappingModal(false);
                      setAutoMappingResults([]);
                      setAutoMappingMessage({ type: '', text: '' });
                    }}
                    className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded transition-colors"
                  >
                    Отменить
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Export Wizard Modal (IK-02B-FE/03) */}
      {showExportWizard && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800/95 backdrop-blur-lg rounded-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden border border-emerald-400/20">
            {/* Header with Progress */}
            <div className="bg-gray-800/95 backdrop-blur-lg border-b border-emerald-400/20 p-6">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-emerald-300 mb-2">🚀 Экспорт в iiko (1 клик)</h2>
                  <p className="text-gray-400">Автомаппинг → ГОСТ-превью → XLSX экспорт</p>
                </div>
                <button
                  onClick={() => {
                    setShowExportWizard(false);
                    setExportWizardStep(1);
                    setExportMessage({ type: '', text: '' });
                  }}
                  className="text-gray-400 hover:text-white text-3xl font-bold transition-colors"
                >
                  ×
                </button>
              </div>
              
              {/* Progress Line */}
              <div className="flex items-center space-x-4">
                {[1, 2, 3, 4].map((step) => (
                  <div key={step} className="flex items-center flex-1">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${
                      exportWizardStep > step ? 'bg-emerald-600 text-white' :
                      exportWizardStep === step ? 'bg-emerald-500 text-white' :
                      'bg-gray-600 text-gray-300'
                    }`}>
                      {exportWizardStep > step ? '✓' : step}
                    </div>
                    <div className={`ml-2 text-sm font-medium ${
                      exportWizardStep >= step ? 'text-emerald-300' : 'text-gray-400'
                    }`}>
                      {step === 1 && 'Проверки'}
                      {step === 2 && 'Автомаппинг'}
                      {step === 3 && 'ГОСТ-превью'}
                      {step === 4 && 'Экспорт'}
                    </div>
                    {step < 4 && (
                      <div className={`flex-1 h-0.5 ml-4 ${
                        exportWizardStep > step ? 'bg-emerald-600' : 'bg-gray-600'
                      }`} />
                    )}
                  </div>
                ))}
              </div>
            </div>
            
            {/* Message Banner */}
            {exportMessage.text && (
              <div className={`p-4 border-b border-gray-600/50 ${
                exportMessage.type === 'success' ? 'bg-green-900/30 text-green-300' :
                exportMessage.type === 'error' ? 'bg-red-900/30 text-red-300' :
                exportMessage.type === 'warning' ? 'bg-yellow-900/30 text-yellow-300' :
                'bg-blue-900/30 text-blue-300'
              }`}>
                <div className="flex items-center justify-between">
                  <span>{exportMessage.text}</span>
                  {tcV2Backup && exportWizardStep >= 2 && (
                    <button
                      onClick={undoExportChanges}
                      className="ml-4 bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors"
                    >
                      ↶ Откатить изменения
                    </button>
                  )}
                </div>
              </div>
            )}
            
            {/* Step Content */}
            <div className="flex-1 overflow-auto p-6">
              {/* Step 1: Pre-checks */}
              {exportWizardStep === 1 && (
                <div className="space-y-6">
                  <h3 className="text-xl font-bold text-emerald-300">📋 Предпроверки</h3>
                  
                  {exportWizardData.preCheckResults && (
                    <div className="space-y-4">
                      {/* Status Cards */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-gray-700/50 rounded-lg p-4 border border-gray-600/50">
                          <div className="text-sm text-gray-400">iiko RMS</div>
                          <div className={`font-bold ${exportWizardData.preCheckResults.iikoConnected ? 'text-green-300' : 'text-red-300'}`}>
                            {exportWizardData.preCheckResults.iikoConnected ? '✅ Подключен' : '❌ Не подключен'}
                          </div>
                          <div className="text-xs text-gray-500">
                            {exportWizardData.preCheckResults.iikoItemsCount} позиций
                          </div>
                        </div>
                        
                        <div className="bg-gray-700/50 rounded-lg p-4 border border-gray-600/50">
                          <div className="text-sm text-gray-400">Цены</div>
                          <div className={`font-bold ${exportWizardData.preCheckResults.priceCoverage >= 80 ? 'text-green-300' : 'text-yellow-300'}`}>
                            {exportWizardData.preCheckResults.priceCoverage}%
                          </div>
                          <div className="text-xs text-gray-500">покрытие</div>
                        </div>
                        
                        <div className="bg-gray-700/50 rounded-lg p-4 border border-gray-600/50">
                          <div className="text-sm text-gray-400">БЖУ</div>
                          <div className={`font-bold ${exportWizardData.preCheckResults.nutritionCoverage >= 80 ? 'text-green-300' : 'text-yellow-300'}`}>
                            {exportWizardData.preCheckResults.nutritionCoverage}%
                          </div>
                          <div className="text-xs text-gray-500">покрытие</div>
                        </div>
                        
                        <div className="bg-gray-700/50 rounded-lg p-4 border border-gray-600/50">
                          <div className="text-sm text-gray-400">SKU</div>
                          <div className={`font-bold ${exportWizardData.preCheckResults.ingredientsWithoutSku === 0 ? 'text-green-300' : 'text-orange-300'}`}>
                            {exportWizardData.preCheckResults.ingredientsWithoutSku} без SKU
                          </div>
                          <div className="text-xs text-gray-500">
                            из {exportWizardData.preCheckResults.ingredientsCount}
                          </div>
                        </div>
                      </div>
                      
                      {/* Last Export Info */}
                      {exportWizardData.lastExport && (
                        <div className="bg-gray-700/50 rounded-lg p-4 border border-gray-600/50">
                          <div className="flex items-center justify-between mb-2">
                            <div className="text-sm text-gray-400">📊 Последний экспорт</div>
                            <div className="text-xs text-gray-500">
                              {exportWizardData.lastExport.human_time}
                            </div>
                          </div>
                          <div className="text-sm text-emerald-300">
                            {exportWizardData.lastExport.techcard_title}
                          </div>
                          <div className="text-xs text-gray-400 mt-1">
                            {exportWizardData.lastExport.ingredients_count} ингредиентов • {Math.round(exportWizardData.lastExport.file_size_bytes / 1024)} KB
                          </div>
                        </div>
                      )}
                      
                      {!exportWizardData.lastExport && (
                        <div className="bg-gray-700/50 rounded-lg p-4 border border-gray-600/50">
                          <div className="text-sm text-gray-400">📊 Последний экспорт</div>
                          <div className="text-sm text-gray-500 mt-1">
                            Экспорты ещё не выполнялись
                          </div>
                        </div>
                      )}
                      
                      {/* Blockers */}
                      {exportWizardData.preCheckResults.blockers.length > 0 && (
                        <div className="bg-red-900/30 border border-red-400/30 rounded-lg p-4">
                          <div className="font-bold text-red-300 mb-2">🚫 Блокирующие проблемы:</div>
                          <ul className="text-red-400 space-y-1">
                            {exportWizardData.preCheckResults.blockers.map((blocker, index) => (
                              <li key={index}>• {blocker}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {/* Warnings */}
                      {exportWizardData.preCheckResults.warnings.length > 0 && (
                        <div className="bg-yellow-900/30 border border-yellow-400/30 rounded-lg p-4">
                          <div className="font-bold text-yellow-300 mb-2">⚠ Предупреждения:</div>
                          <ul className="text-yellow-400 space-y-1">
                            {exportWizardData.preCheckResults.warnings.map((warning, index) => (
                              <li key={index}>• {warning}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
              
              {/* Step 2: Auto-mapping */}
              {exportWizardStep === 2 && (
                <div className="space-y-6">
                  <h3 className="text-xl font-bold text-emerald-300">🔄 Автомаппинг</h3>
                  
                  {exportWizardData.autoMappingResults ? (
                    <div className="space-y-4">
                      <div className="bg-gray-700/50 rounded-lg p-4 border border-gray-600/50">
                        <div className="grid grid-cols-3 gap-4 text-center">
                          <div>
                            <div className="text-2xl font-bold text-green-300">
                              {exportWizardData.autoMappingResults.filter(r => r.status === 'auto_accept').length}
                            </div>
                            <div className="text-sm text-gray-400">Автоматически</div>
                          </div>
                          <div>
                            <div className="text-2xl font-bold text-yellow-300">
                              {exportWizardData.autoMappingResults.filter(r => r.status === 'low_confidence').length}
                            </div>
                            <div className="text-sm text-gray-400">Требует проверки</div>
                          </div>
                          <div>
                            <div className="text-2xl font-bold text-red-300">
                              {exportWizardData.autoMappingResults.filter(r => r.status === 'no_match').length}
                            </div>
                            <div className="text-sm text-gray-400">Без совпадений</div>
                          </div>
                        </div>
                      </div>
                      
                      {exportWizardData.coverageAfter && (
                        <div className="bg-blue-900/30 border border-blue-400/30 rounded-lg p-4">
                          <div className="text-blue-300 font-medium mb-2">📊 Изменение покрытия:</div>
                          <div className="flex space-x-6">
                            <div>
                              <span className="text-gray-400">Цены: </span>
                              <span className="text-blue-200">
                                {exportWizardData.coverageBefore?.price || 0}% → {exportWizardData.coverageAfter.price}%
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-400">БЖУ: </span>
                              <span className="text-blue-200">
                                {exportWizardData.coverageBefore?.nutrition || 0}% → {exportWizardData.coverageAfter.nutrition}%
                              </span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <div className="text-3xl mb-4">🔄</div>
                      <div className="text-gray-400">Автомаппинг будет выполнен автоматически</div>
                    </div>
                  )}
                </div>
              )}
              
              {/* Step 3: GOST Preview */}
              {exportWizardStep === 3 && (
                <div className="space-y-6">
                  <h3 className="text-xl font-bold text-emerald-300">📄 ГОСТ-превью</h3>
                  
                  <div className="bg-gray-700/50 rounded-lg p-6 border border-gray-600/50">
                    <div className="text-center space-y-4">
                      <div className="text-6xl">📄</div>
                      <div className="text-lg text-white">Готово к предпросмотру</div>
                      <div className="text-gray-400">
                        Откройте ГОСТ-печать для проверки данных перед экспортом
                      </div>
                      
                      <button
                        onClick={openGostPreview}
                        className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                      >
                        📖 Открыть ГОСТ-печать
                      </button>
                    </div>
                  </div>
                  
                  {/* Data Sources Info */}
                  {tcV2 && (
                    <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-600/50">
                      <div className="text-sm text-gray-400 mb-2">Источники данных:</div>
                      <div className="flex flex-wrap gap-2 text-xs">
                        {tcV2.nutritionMeta && (
                          <span className="bg-green-600 text-white px-2 py-1 rounded">
                            БЖУ: {tcV2.nutritionMeta.source || 'Mixed'}
                          </span>
                        )}
                        {tcV2.costMeta && (
                          <span className="bg-yellow-600 text-white px-2 py-1 rounded">
                            Цены: {tcV2.costMeta.source || 'Mixed'}
                          </span>
                        )}
                        {tcV2.costMeta?.asOf && (
                          <span className="bg-gray-600 text-white px-2 py-1 rounded">
                            Обновлено: {new Date(tcV2.costMeta.asOf).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              {/* Step 4: Export */}
              {exportWizardStep === 4 && (
                <div className="space-y-6">
                  <h3 className="text-xl font-bold text-emerald-300">📦 Экспорт завершен</h3>
                  
                  <div className="bg-green-900/30 border border-green-400/30 rounded-lg p-6">
                    <div className="text-center space-y-4">
                      <div className="text-6xl">✅</div>
                      <div className="text-xl text-green-300 font-bold">Файл готов!</div>
                      <div className="text-green-400">
                        Файл экспортирован и готов к импорту в iikoWeb
                      </div>
                      
                      {/* Updated Last Export Info */}
                      {exportWizardData.lastExport && (
                        <div className="bg-green-800/30 rounded-lg p-3 text-sm">
                          <div className="text-green-300">
                            📊 Последний экспорт: {exportWizardData.lastExport.human_time}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Enhanced iikoWeb Import Instructions */}
                  <div className="bg-blue-900/30 border border-blue-400/30 rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="font-medium text-blue-300">📋 Инструкция по импорту в iikoWeb</div>
                      <button
                        onClick={() => {
                          const instructions = `Импорт техкарты в iikoWeb:

1. Откройте iikoWeb → Администрирование
2. Перейдите в раздел "Технологические карты"
3. Нажмите "Импорт справочника"
4. Выберите скачанный XLSX файл
5. Проверьте результаты импорта
6. Сохраните изменения

Примечания:
- Убедитесь, что все ингредиенты присутствуют в номенклатуре
- При необходимости создайте недостающие позиции в справочнике товаров
- После импорта проверьте корректность расчета себестоимости`;
                          
                          navigator.clipboard.writeText(instructions).then(() => {
                            setExportMessage({ 
                              type: 'success', 
                              text: '📋 Инструкция скопирована в буфер обмена!' 
                            });
                          });
                        }}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors"
                      >
                        📋 Копировать
                      </button>
                    </div>
                    
                    <ol className="text-blue-400 text-sm space-y-2 list-decimal list-inside">
                      <li>Откройте <strong>iikoWeb → Администрирование</strong></li>
                      <li>Перейдите в раздел <strong>"Технологические карты"</strong></li>
                      <li>Нажмите <strong>"Импорт справочника"</strong></li>
                      <li>Выберите скачанный XLSX файл</li>
                      <li>Проверьте результаты импорта</li>
                      <li>Сохраните изменения</li>
                    </ol>
                    
                    <div className="mt-4 p-3 bg-blue-800/30 rounded text-xs text-blue-300">
                      <strong>💡 Важно:</strong> Убедитесь, что все ингредиенты присутствуют в номенклатуре. 
                      При необходимости создайте недостающие позиции в справочнике товаров.
                    </div>
                  </div>
                  
                  {/* Quality Validation Errors (if any) */}
                  {exportWizardData.blockingErrors && exportWizardData.blockingErrors.length > 0 && (
                    <div className="bg-red-900/30 border border-red-400/30 rounded-lg p-4">
                      <div className="font-bold text-red-300 mb-2">🚫 Критические ошибки валидации:</div>
                      <ul className="text-red-400 space-y-1 text-sm">
                        {exportWizardData.blockingErrors.map((error, index) => (
                          <li key={index}>• {error.hint || error.type}</li>
                        ))}
                      </ul>
                      {exportWizardData.canAutoFix && (
                        <button
                          onClick={async () => {
                            try {
                              setExportMessage({ type: 'info', text: '🔄 Автоисправление ошибок...' });
                              
                              const response = await fetch(`${API}/v1/techcards.v2/export/auto-fix`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ 
                                  techcard: tcV2,
                                  issues: exportWizardData.blockingErrors 
                                })
                              });
                              
                              if (response.ok) {
                                const fixedData = await response.json();
                                setTcV2(fixedData.fixed_techcard);
                                setExportMessage({ 
                                  type: 'success', 
                                  text: `✅ ${fixedData.message}` 
                                });
                              } else {
                                throw new Error('Не удалось исправить ошибки');
                              }
                            } catch (error) {
                              setExportMessage({ 
                                type: 'error', 
                                text: `❌ Ошибка автоисправления: ${error.message}` 
                              });
                            }
                          }}
                          className="mt-3 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors"
                        >
                          🔧 Исправить автоматически
                        </button>
                      )}
                    </div>
                  )}
                  
                  <div className="text-center">
                    <button
                      onClick={() => handleIikoCsvExport()}
                      className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition-colors mr-4"
                    >
                      📁 Альтернатива: CSV/ZIP
                    </button>
                  </div>
                </div>
              )}
            </div>
            
            {/* Actions Panel */}
            <div className="border-t border-gray-600/50 p-4 bg-gray-700/30">
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-400">
                  {exportWizardData.stepTimings.start && (
                    <span>Время выполнения: {Math.round((Date.now() - exportWizardData.stepTimings.start) / 1000)}с</span>
                  )}
                </div>
                
                <div className="flex space-x-3">
                  {exportWizardStep > 1 && exportWizardStep < 4 && (
                    <button
                      onClick={() => setExportWizardStep(exportWizardStep - 1)}
                      className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded transition-colors"
                    >
                      ← Назад
                    </button>
                  )}
                  
                  {exportWizardStep === 1 && exportWizardData.preCheckResults?.blockers.length === 0 && (
                    <button
                      onClick={() => {
                        setExportWizardStep(2);
                        runExportAutoMapping();
                      }}
                      disabled={isExportProcessing}
                      className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded transition-colors"
                    >
                      {isExportProcessing ? '⏳ Обработка...' : 'Запустить автомаппинг →'}
                    </button>
                  )}
                  
                  {exportWizardStep === 1 && exportWizardData.preCheckResults?.blockers.length > 0 && (
                    <button
                      onClick={() => setMappingModalOpen(true)}
                      className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition-colors"
                    >
                      Открыть ручной маппинг
                    </button>
                  )}
                  
                  {exportWizardStep === 3 && (
                    <button
                      onClick={performIikoExport}
                      disabled={isExportProcessing}
                      className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded transition-colors"
                    >
                      {isExportProcessing ? '⏳ Создание файла...' : 'Создать XLSX файл →'}
                    </button>
                  )}
                  
                  {exportWizardStep === 4 && (
                    <button
                      onClick={() => {
                        setShowExportWizard(false);
                        setExportWizardStep(1);
                        setExportMessage({ type: '', text: '' });
                      }}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 px-4 rounded transition-colors"
                    >
                      ✅ Готово
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CREATE EXPORT WIZARD UI - Unified Export Wizard Modal */}
      {/* FIX JS MODAL SCROLL & OPEN BUG: Enhanced modal with proper scroll handling */}
      {showUnifiedExportWizard && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto"
          onClick={closeExportWizard}
          role="dialog"
          aria-modal="true"
          aria-labelledby="export-wizard-title"
        >
          <div 
            className="bg-gray-800 rounded-2xl p-6 max-w-4xl w-full shadow-2xl border border-gray-700 my-8 max-h-[90vh] overflow-y-auto" 
            onClick={(e) => e.stopPropagation()}
            data-export-wizard-modal
          >
            {/* Header */}
            <div className="flex justify-between items-center mb-6 sticky top-0 bg-gray-800 pb-4 border-b border-gray-700">
              <div>
                <h2 id="export-wizard-title" className="text-2xl font-bold text-white mb-1">📄 Экспорт техкарты</h2>
                <p className="text-gray-300 text-sm">Выберите формат экспорта для вашей техкарты</p>
              </div>
              <button
                onClick={closeExportWizard}
                className="text-gray-400 hover:text-white text-2xl font-bold w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-700 transition-colors"
                aria-label="Закрыть экспорт"
              >
                ×
              </button>
            </div>

            {/* Scrollable Content Area */}
            <div className="overflow-y-auto max-h-[calc(90vh-200px)]">
              {/* Export Options Grid */}
              {exportStatus === 'idle' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  {/* XLSX Export */}
                  <button 
                    onClick={() => executeExport('xlsx')}
                    className="bg-gradient-to-br from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 rounded-xl p-6 cursor-pointer transition-all transform hover:scale-105 shadow-lg hover:shadow-xl text-left w-full border-none"
                    aria-label="Экспорт XLSX техкарты"
                  >
                    <div className="text-white">
                      <div className="text-4xl mb-3">📊</div>
                      <h3 className="text-xl font-bold mb-2">XLSX Техкарта</h3>
                      <p className="text-green-100 text-sm mb-3">
                        Готовая техкарта для импорта в систему iiko
                      </p>
                      <div className="text-green-200 text-xs">
                        • Полные БЖУ данные<br/>
                        • Корректные артикулы<br/>
                        • Совместимость с iiko RMS
                      </div>
                    </div>
                  </button>

                  {/* ZIP Export */}
                  <button 
                    onClick={() => executeExport('zip')}
                    className="bg-gradient-to-br from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 rounded-xl p-6 cursor-pointer transition-all transform hover:scale-105 shadow-lg hover:shadow-xl text-left w-full border-none"
                    aria-label="Экспорт ZIP номенклатур"
                  >
                    <div className="text-white">
                      <div className="text-4xl mb-3">📦</div>
                      <h3 className="text-xl font-bold mb-2">ZIP Номенклатуры</h3>
                      <p className="text-blue-100 text-sm mb-3">
                        Архив со скелетонами блюд и продуктов
                      </p>
                      <div className="text-blue-200 text-xs">
                        • Dish-Skeletons.xlsx<br/>
                        • Product-Skeletons.xlsx<br/>
                        • Только необходимые файлы
                      </div>
                    </div>
                  </button>

                  {/* PDF Export */}
                  <button 
                    onClick={() => executeExport('pdf')}
                    className="bg-gradient-to-br from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 rounded-xl p-6 cursor-pointer transition-all transform hover:scale-105 shadow-lg hover:shadow-xl text-left w-full border-none"
                    aria-label="Экспорт PDF для персонала"
                  >
                    <div className="text-white">
                      <div className="text-4xl mb-3">📄</div>
                      <h3 className="text-xl font-bold mb-2">PDF для персонала</h3>
                      <p className="text-purple-100 text-sm mb-3">
                        Техкарта для печати на кухню (без цен)
                      </p>
                      <div className="text-purple-200 text-xs">
                        • Готов к печати<br/>
                        • Без коммерческих данных<br/>
                        • ГОСТ формат
                      </div>
                    </div>
                  </button>

                  {/* Full Package Export */}
                  <button 
                    onClick={() => executeExport('full_package')}
                    className="bg-gradient-to-br from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 rounded-xl p-6 cursor-pointer transition-all transform hover:scale-105 shadow-lg hover:shadow-xl text-left w-full border-none"
                    aria-label="Экспорт полного пакета"
                  >
                    <div className="text-white">
                      <div className="text-4xl mb-3">🎁</div>
                      <h3 className="text-xl font-bold mb-2">Полный пакет</h3>
                      <p className="text-orange-100 text-sm mb-3">
                        Все форматы сразу: XLSX + ZIP + PDF
                      </p>
                      <div className="text-orange-200 text-xs">
                        • Техкарта для iiko<br/>
                        • Номенклатуры<br/>
                        • PDF для кухни
                      </div>
                    </div>
                  </button>
                </div>
              )}

              {/* Progress Section */}
              {exportStatus === 'processing' && (
                <div className="mb-6">
                  <div className="bg-gray-700 rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-xl font-bold text-white">Экспорт в процессе...</h3>
                      <div className="text-2xl animate-spin">⚙️</div>
                    </div>
                    
                    {/* Progress Bar */}
                    <div className="w-full bg-gray-600 rounded-full h-4 mb-4">
                      <div 
                        className="bg-gradient-to-r from-blue-500 to-purple-500 h-4 rounded-full transition-all duration-500"
                        style={{ width: `${exportProgress}%` }}
                        role="progressbar"
                        aria-valuenow={exportProgress}
                        aria-valuemin="0"
                        aria-valuemax="100"
                      ></div>
                    </div>
                    
                    {/* Current Step */}
                    <div className="text-gray-300 text-center" aria-live="polite">
                      {currentExportStep}
                    </div>
                  </div>
                </div>
              )}

              {/* Success Section */}
              {exportStatus === 'success' && (
                <div className="mb-6">
                  <div className="bg-green-800 rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-xl font-bold text-white">✅ Экспорт завершен</h3>
                      <div className="text-2xl">🎉</div>
                    </div>
                    
                    {/* Export Results */}
                    <div className="space-y-3 max-h-60 overflow-y-auto">
                      {exportResults.map((result, index) => (
                        <div key={index} className="bg-green-700 rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="font-semibold text-white">{result.filename}</div>
                              <div className="text-green-200 text-sm">{result.description}</div>
                            </div>
                            <div className="text-green-200 text-sm">
                              {(result.size / 1024).toFixed(1)} KB
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Error Section */}
              {exportStatus === 'error' && (
                <div className="mb-6">
                  <div className="bg-red-800 rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-xl font-bold text-white">❌ Ошибка экспорта</h3>
                      <div className="text-2xl">⚠️</div>
                    </div>
                    
                    <div className="text-red-200" role="alert">
                      {currentExportStep}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Footer Actions - Always visible */}
            <div className="flex justify-between items-center pt-4 border-t border-gray-700 sticky bottom-0 bg-gray-800">
              <div className="text-gray-400 text-sm">
                {tcV2 ? `Техкарта: ${tcV2.meta?.title || 'Без названия'}` : 'Техкарта не создана'}
              </div>
              
              <div className="flex space-x-3">
                {exportStatus === 'success' && (
                  <button
                    onClick={() => {
                      resetExportWizard();
                    }}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
                  >
                    Экспортировать еще
                  </button>
                )}
                
                <button
                  onClick={closeExportWizard}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Phase 3: FE-04-min Export to iiko (2 steps) Modal */}
      {showPhase3ExportModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800/95 backdrop-blur-lg rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden border border-emerald-400/20">
            {/* Header */}
            <div className="bg-gray-800/95 backdrop-blur-lg border-b border-emerald-400/20 p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold text-emerald-300 mb-2">🚀 Экспорт номенклатур</h2>
                  <p className="text-gray-400">Префлайт → ZIP (Скелеты + ТТК) → импорт в iiko</p>
                </div>
                <button
                  onClick={closePhase3ExportModal}
                  className="text-gray-400 hover:text-white text-3xl font-bold transition-colors"
                >
                  ×
                </button>
              </div>
              
              {/* State Indicator */}
              <div className="flex items-center space-x-4 mt-4">
                <div className={`w-3 h-3 rounded-full ${
                  phase3ExportState === 'idle' ? 'bg-gray-500' :
                  phase3ExportState === 'running_preflight' ? 'bg-yellow-500 animate-pulse' :
                  phase3ExportState === 'ready_zip' ? 'bg-green-500' :
                  'bg-red-500'
                }`} />
                <span className="text-sm text-gray-300">
                  {phase3ExportState === 'idle' && 'Готов к запуску'}
                  {phase3ExportState === 'running_preflight' && 'Выполнение префлайта...'}
                  {phase3ExportState === 'ready_zip' && 'ZIP готов к скачиванию'}
                  {phase3ExportState === 'error' && 'Ошибка экспорта'}
                </span>
              </div>
            </div>
            
            {/* Message Banner */}
            {phase3ExportMessage.text && (
              <div className={`p-4 border-b border-gray-600/50 ${
                phase3ExportMessage.type === 'success' ? 'bg-green-900/30 text-green-300' :
                phase3ExportMessage.type === 'error' ? 'bg-red-900/30 text-red-300' :
                phase3ExportMessage.type === 'warning' ? 'bg-yellow-900/30 text-yellow-300' :
                'bg-blue-900/30 text-blue-300'
              }`}>
                <div className="flex items-center justify-between">
                  <span>{phase3ExportMessage.text}</span>
                </div>
              </div>
            )}
            
            {/* Content */}
            <div className="flex-1 overflow-auto p-6">
              {/* Preflight Panel */}
              {preflightResult && (
                <div className="space-y-6">
                  <h3 className="text-xl font-bold text-emerald-300">📋 Результаты префлайта</h3>
                  
                  {/* TTK Date & Skeleton Counts */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-blue-900/30 border border-blue-400/30 rounded-lg p-4">
                      <div className="text-sm text-blue-400">Дата ТТК</div>
                      <div className="text-xl font-bold text-blue-300">
                        {preflightResult.ttkDate}
                      </div>
                    </div>
                    
                    <div className="bg-purple-900/30 border border-purple-400/30 rounded-lg p-4">
                      <div className="text-sm text-purple-400">Блюда для скелетов</div>
                      <div className="text-xl font-bold text-purple-300">
                        {preflightResult.counts?.dishSkeletons || 0}
                      </div>
                    </div>
                    
                    <div className="bg-orange-900/30 border border-orange-400/30 rounded-lg p-4">
                      <div className="text-sm text-orange-400">Товары для скелетов</div>
                      <div className="text-xl font-bold text-orange-300">
                        {preflightResult.counts?.productSkeletons || 0}
                      </div>
                    </div>
                  </div>
                  
                  {/* Phase 3.5 + Guard: Enhanced Instruction with Guards */}
                  <div className="bg-gray-700/50 border border-gray-600/50 rounded-lg p-4">
                    <div className="flex items-start space-x-3">
                      <div className="text-2xl">💡</div>
                      <div className="flex-1">
                        <div className="font-bold text-gray-300">Инструкция по импорту:</div>
                        {(preflightResult.counts?.dishSkeletons > 0 || preflightResult.counts?.productSkeletons > 0) ? (
                          <div className="text-yellow-400 text-sm mt-1">
                            <div className="font-bold">⚠️ Требуется двухэтапный импорт:</div>
                            <div className="mt-1">
                              1. Сначала импортируйте скелеты в iikoWeb ({preflightResult.counts?.dishSkeletons || 0} блюд, {preflightResult.counts?.productSkeletons || 0} товаров)
                            </div>
                            <div>2. Затем импортируйте файл ТТК</div>
                            <div className="mt-2 text-yellow-300">
                              ❗ Без предварительного импорта скелетов ТТК не импортируется (ошибка "артикул не найден")
                            </div>
                            {preflightResult.counts?.dishSkeletons > 0 && (
                              <div className="mt-2 p-3 bg-yellow-900/30 border border-yellow-600/50 rounded">
                                <div className="font-bold text-yellow-300">🛡️ Защита "dish-first rule":</div>
                                <div className="text-yellow-400 text-xs">
                                  TTK-only экспорт заблокирован, т.к. блюда отсутствуют в номенклатуре iiko.
                                  Используйте ZIP экспорт для получения скелетов блюд.
                                </div>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="text-green-400 text-sm mt-1">
                            <div className="flex items-center mb-2">
                              <span className="text-green-300">✅ Все артикулы найдены в iiko.</span>
                            </div>
                            <div>Доступны оба варианта экспорта:</div>
                            <div className="ml-4 mt-1">
                              <div>• ZIP файл (полный экспорт)</div>
                              <div>• TTK файл (только техкарта)</div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Generated Articles Preview */}
                  {(preflightResult.generated?.dishArticles?.length > 0 || preflightResult.generated?.productArticles?.length > 0) && (
                    <div className="bg-green-900/20 border border-green-400/30 rounded-lg p-4">
                      <div className="font-bold text-green-300 mb-2">🎯 Сгенерированные артикулы:</div>
                      <div className="text-sm space-y-1">
                        {preflightResult.generated.dishArticles?.length > 0 && (
                          <div className="text-green-400">
                            Блюда: {preflightResult.generated.dishArticles.join(', ')}
                          </div>
                        )}
                        {preflightResult.generated.productArticles?.length > 0 && (
                          <div className="text-green-400">
                            Товары: {preflightResult.generated.productArticles.join(', ')}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              {/* Error Details */}
              {phase3ErrorDetails && (
                <div className="space-y-6">
                  <h3 className="text-xl font-bold text-red-300">❌ Ошибка экспорта</h3>
                  
                  <div className="bg-red-900/30 border border-red-400/30 rounded-lg p-6">
                    <div className="space-y-4">
                      <div>
                        <div className="font-bold text-red-300">Тип ошибки:</div>
                        <div className="text-red-400">{phase3ErrorDetails.type}</div>
                      </div>
                      
                      {phase3ErrorDetails.hint && (
                        <div>
                          <div className="font-bold text-red-300">Рекомендация:</div>
                          <div className="text-red-400">{phase3ErrorDetails.hint}</div>
                        </div>
                      )}
                      
                      {phase3ErrorDetails.message && (
                        <div>
                          <div className="font-bold text-red-300">Детали:</div>
                          <div className="text-red-400 text-sm font-mono bg-red-900/20 p-2 rounded">
                            {phase3ErrorDetails.message}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
              
              {/* ZIP Download Hint */}
              {phase3ExportState === 'ready_zip' && (
                <div className="space-y-6">
                  <div className="bg-green-900/30 border border-green-400/30 rounded-lg p-6">
                    <div className="text-center space-y-4">
                      <div className="text-6xl">📦</div>
                      <div className="text-xl text-green-300 font-bold">ZIP файл создан!</div>
                      <div className="text-green-400">
                        ZIP содержит следующие файлы:
                      </div>
                      
                      <div className="bg-green-800/30 rounded-lg p-4 text-sm">
                        <ul className="text-green-300 space-y-1">
                          <li>• iiko_TTK.xlsx (всегда включён)</li>
                          {preflightResult?.counts?.dishSkeletons > 0 && (
                            <li>• Dish-Skeletons.xlsx ({preflightResult.counts.dishSkeletons} блюд)</li>
                          )}
                          {preflightResult?.counts?.productSkeletons > 0 && (
                            <li>• Product-Skeletons.xlsx ({preflightResult.counts.productSkeletons} товаров)</li>
                          )}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {/* Footer Actions */}
            <div className="bg-gray-800/95 backdrop-blur-lg border-t border-gray-600/50 p-6">
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-400">
                  {phase3ExportState === 'idle' && 'Нажмите "Запустить префлайт" для начала'}
                  {phase3ExportState === 'running_preflight' && 'Выполняется анализ и подготовка артикулов...'}
                  {phase3ExportState === 'ready_zip' && 'Готово! Нажмите "Скачать ZIP" для получения файлов'}
                  {phase3ExportState === 'error' && 'Произошла ошибка. Попробуйте ещё раз'}
                </div>
                
                <div className="flex space-x-3">
                  {phase3ExportState === 'idle' && (
                    <button
                      onClick={runPreflight}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 px-4 rounded transition-colors"
                    >
                      🚀 Запустить префлайт
                    </button>
                  )}
                  
                  {phase3ExportState === 'ready_zip' && (
                    <div className="flex space-x-3">
                      {/* Guard — dish-first rule: Always show ZIP download */}
                      <button
                        onClick={generateZipExport}
                        className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded transition-colors"
                      >
                        📦 Скачать ZIP
                      </button>
                      
                      {/* Guard — dish-first rule: Only show TTK-only if no dish skeletons needed */}
                      {(!preflightResult || preflightResult.counts?.dishSkeletons === 0) && (
                        <button
                          onClick={downloadTtkOnly}
                          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition-colors"
                          title="Скачать только файл ТТК (доступно когда все блюда существуют в iiko)"
                        >
                          📄 Только ТТК
                        </button>
                      )}
                      
                      {/* Guard — dish-first rule: Show warning when TTK-only blocked */}
                      {preflightResult && preflightResult.counts?.dishSkeletons > 0 && (
                        <div className="flex items-center text-yellow-400 text-sm">
                          <span className="mr-2">⚠️</span>
                          <span>TTK-only заблокирован: нужны скелеты блюд</span>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {phase3ExportState === 'error' && (
                    <button
                      onClick={() => {
                        resetPhase3Export();
                        setPhase3ExportState('idle');
                      }}
                      className="bg-yellow-600 hover:bg-yellow-700 text-white font-bold py-2 px-4 rounded transition-colors"
                    >
                      🔄 Попробовать снова
                    </button>
                  )}
                  
                  <button
                    onClick={closePhase3ExportModal}
                    className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded transition-colors"
                  >
                    ✕ Закрыть
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* IK-04/02: XLSX Import Modal */}
      {showXlsxImportModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800/95 backdrop-blur-lg rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-green-400/20">
            {/* Header */}
            <div className="sticky top-0 bg-gray-800/95 backdrop-blur-lg border-b border-green-400/20 p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold text-green-300 mb-2">📊 Импорт ТТК (iiko XLSX)</h2>
                  <p className="text-gray-400">Загрузите XLSX файл техкарты из iiko</p>
                </div>
                <button
                  onClick={() => {
                    setShowXlsxImportModal(false);
                    resetXlsxImport();
                  }}
                  className="text-gray-400 hover:text-white text-3xl font-bold transition-colors"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {!xlsxImportResults ? (
                <>
                  {/* File Drop Zone */}
                  <div
                    className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
                      isDragOver 
                        ? 'border-green-400 bg-green-900/20' 
                        : 'border-gray-600 hover:border-green-400'
                    }`}
                    onDrop={handleXlsxFileDrop}
                    onDragOver={(e) => {
                      e.preventDefault();
                      setIsDragOver(true);
                    }}
                    onDragLeave={() => setIsDragOver(false)}
                  >
                    {!xlsxFile ? (
                      <>
                        <div className="text-4xl mb-4">📊</div>
                        <p className="text-lg font-bold text-green-300 mb-2">
                          Перетащите XLSX файл сюда
                        </p>
                        <p className="text-gray-400 mb-4">
                          или выберите файл техкарты из iiko
                        </p>
                        <label className="inline-block bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded-lg cursor-pointer transition-colors">
                          📁 Выбрать файл
                          <input
                            type="file"
                            accept=".xlsx,.xls"
                            onChange={handleXlsxFileDrop}
                            className="hidden"
                          />
                        </label>
                        <div className="text-xs text-gray-500 mt-2">
                          Поддерживаются форматы: XLSX, XLS
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="text-3xl mb-4">✅</div>
                        <p className="text-lg font-bold text-green-300 mb-2">
                          Файл выбран
                        </p>
                        {xlsxPreview && (
                          <div className="bg-gray-900/50 rounded-lg p-4 text-left">
                            <div className="text-green-300 font-bold mb-2">{xlsxPreview.fileName}</div>
                            <div className="text-gray-400 text-sm space-y-1">
                              <div>Размер: {xlsxPreview.fileSize}</div>
                              <div>Тип: {xlsxPreview.type}</div>
                              <div>Изменён: {xlsxPreview.lastModified}</div>
                            </div>
                            {xlsxPreview.error && (
                              <div className="text-red-400 text-sm mt-2">
                                ⚠️ {xlsxPreview.error}
                              </div>
                            )}
                          </div>
                        )}
                        <button
                          onClick={() => {
                            setXlsxFile(null);
                            setXlsxPreview(null);
                          }}
                          className="mt-4 text-gray-400 hover:text-red-400 underline transition-colors"
                        >
                          Выбрать другой файл
                        </button>
                      </>
                    )}
                  </div>

                  {/* Options */}
                  {xlsxFile && (
                    <div className="bg-gray-900/50 rounded-lg p-4">
                      <h3 className="text-lg font-bold text-green-300 mb-3">⚙️ Опции импорта</h3>
                      
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={xlsxAutoMapping}
                          onChange={(e) => setXlsxAutoMapping(e.target.checked)}
                          className="w-4 h-4 text-green-600 bg-gray-700 border-gray-600 rounded focus:ring-green-500"
                        />
                        <div>
                          <div className="text-white font-medium">Сразу подтянуть цены из iiko</div>
                          <div className="text-gray-400 text-sm">Автоматически выполнить маппинг и пересчёт после импорта</div>
                        </div>
                      </label>
                    </div>
                  )}

                  {/* Import Button */}
                  {xlsxFile && (
                    <div className="flex justify-end space-x-3">
                      <button
                        onClick={() => {
                          setShowXlsxImportModal(false);
                          resetXlsxImport();
                        }}
                        className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                      >
                        Отмена
                      </button>
                      <button
                        onClick={importXlsxTechcard}
                        disabled={xlsxImportProgress}
                        className={`font-bold py-3 px-6 rounded-lg transition-colors ${
                          xlsxImportProgress
                            ? 'bg-gray-600 cursor-not-allowed text-gray-400'
                            : 'bg-green-600 hover:bg-green-700 text-white'
                        }`}
                      >
                        {xlsxImportProgress ? '⏳ Импортирую...' : '📥 Импортировать'}
                      </button>
                    </div>
                  )}

                  {/* UX-Polish: Progress with stages */}
                  {xlsxImportProgress && (
                    <div className="bg-gray-900/50 rounded-lg p-6">
                      <div className="text-lg font-bold text-blue-300 mb-4">🔄 Импорт в процессе...</div>
                      
                      <div className="space-y-3">
                        {/* Stage 1: Parsing */}
                        <div className={`flex items-center space-x-3 ${
                          xlsxImportStage === 'parsing' ? 'text-blue-400' : 
                          ['validation', 'conversions', 'extraction', 'done'].includes(xlsxImportStage) ? 'text-green-400' : 'text-gray-500'
                        }`}>
                          <div className="w-6 h-6 flex items-center justify-center">
                            {xlsxImportStage === 'parsing' ? '⏳' : 
                             ['validation', 'conversions', 'extraction', 'done'].includes(xlsxImportStage) ? '✅' : '⭕'}
                          </div>
                          <span>Parsing XLSX структуры</span>
                        </div>

                        {/* Stage 2: Validation */}
                        <div className={`flex items-center space-x-3 ${
                          xlsxImportStage === 'validation' ? 'text-blue-400' : 
                          ['conversions', 'extraction', 'done'].includes(xlsxImportStage) ? 'text-green-400' : 'text-gray-500'
                        }`}>
                          <div className="w-6 h-6 flex items-center justify-center">
                            {xlsxImportStage === 'validation' ? '⏳' : 
                             ['conversions', 'extraction', 'done'].includes(xlsxImportStage) ? '✅' : '⭕'}
                          </div>
                          <span>Validation данных</span>
                        </div>

                        {/* Stage 3: Conversions */}
                        <div className={`flex items-center space-x-3 ${
                          xlsxImportStage === 'conversions' ? 'text-blue-400' : 
                          ['extraction', 'done'].includes(xlsxImportStage) ? 'text-green-400' : 'text-gray-500'
                        }`}>
                          <div className="w-6 h-6 flex items-center justify-center">
                            {xlsxImportStage === 'conversions' ? '⏳' : 
                             ['extraction', 'done'].includes(xlsxImportStage) ? '✅' : '⭕'}
                          </div>
                          <span>Conversions единиц (кг→г, мл→г)</span>
                        </div>

                        {/* Stage 4: Tech extraction */}
                        <div className={`flex items-center space-x-3 ${
                          xlsxImportStage === 'extraction' ? 'text-blue-400' : 
                          xlsxImportStage === 'done' ? 'text-green-400' : 'text-gray-500'
                        }`}>
                          <div className="w-6 h-6 flex items-center justify-center">
                            {xlsxImportStage === 'extraction' ? '⏳' : 
                             xlsxImportStage === 'done' ? '✅' : '⭕'}
                          </div>
                          <span>Tech extraction (технология, процессы)</span>
                        </div>

                        {/* Stage 5: Done */}
                        <div className={`flex items-center space-x-3 ${
                          xlsxImportStage === 'done' ? 'text-green-400' : 'text-gray-500'
                        }`}>
                          <div className="w-6 h-6 flex items-center justify-center">
                            {xlsxImportStage === 'done' ? '✅' : '⭕'}
                          </div>
                          <span>Done - готово!</span>
                        </div>
                      </div>

                      {xlsxImportStage === 'error' && (
                        <div className="mt-4 text-red-400">
                          ❌ Произошла ошибка при импорте
                        </div>
                      )}
                    </div>
                  )}
                </>
              ) : (
                /* Import Results */
                <div className="space-y-6">
                  {xlsxImportResults.status === 'success' && (
                    <div className="bg-green-900/30 border border-green-400/30 rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="text-2xl">✅</span>
                        <div>
                          <div className="text-lg font-bold text-green-300">
                            Импорт успешно завершён!
                          </div>
                          <div className="text-green-400">
                            Импортировано из iiko XLSX • блюдо: {xlsxImportResults.techcard?.meta?.title} • 
                            SKU: {xlsxImportResults.techcard?.ingredients?.filter(ing => ing.skuId).length || 0} • 
                            ингредиентов: {xlsxImportResults.techcard?.ingredients?.length || 0}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {xlsxImportResults.status === 'draft' && (
                    <div className="bg-yellow-900/30 border border-yellow-400/30 rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="text-2xl">⚠️</span>
                        <div>
                          <div className="text-lg font-bold text-yellow-300">
                            Импорт завершён с предупреждениями
                          </div>
                          <div className="text-yellow-400">
                            Техкарта создана, но требует проверки
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {xlsxImportResults.status === 'error' && (
                    <div className="bg-red-900/30 border border-red-400/30 rounded-lg p-6">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="text-2xl">❌</span>
                        <div>
                          <div className="text-lg font-bold text-red-300">
                            Ошибка импорта
                          </div>
                          <div className="text-red-400">
                            Не удалось импортировать файл
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* UX-Polish: Enhanced Issues Display */}
                  {(xlsxImportErrors.length > 0 || xlsxImportWarnings.length > 0 || (xlsxImportResults.issues && xlsxImportResults.issues.length > 0)) && (
                    <div className="space-y-4">
                      {/* Errors */}
                      {xlsxImportErrors.length > 0 && (
                        <div className="bg-red-900/30 border border-red-400/30 rounded-lg p-4">
                          <div className="flex items-center space-x-2 mb-3">
                            <span className="text-xl">❌</span>
                            <span className="font-bold text-red-300">Критические ошибки ({xlsxImportErrors.length})</span>
                          </div>
                          <div className="space-y-2">
                            {xlsxImportErrors.map((error, index) => (
                              <div key={index} className="bg-red-800/30 rounded p-3">
                                <div className="font-medium text-red-300">
                                  {error.msg || error.message || 'Неизвестная ошибка'}
                                </div>
                                {error.suggestion && (
                                  <div className="text-red-400 text-sm mt-1">
                                    💡 {error.suggestion}
                                  </div>
                                )}
                                {error.row && error.column && (
                                  <div className="text-red-500 text-xs mt-1">
                                    📍 Строка {error.row}, колонка {error.column}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Warnings */}  
                      {xlsxImportWarnings.length > 0 && (
                        <div className="bg-yellow-900/30 border border-yellow-400/30 rounded-lg p-4">
                          <div className="flex items-center space-x-2 mb-3">
                            <span className="text-xl">⚠️</span>
                            <span className="font-bold text-yellow-300">Предупреждения ({xlsxImportWarnings.length})</span>
                          </div>
                          <div className="space-y-2">
                            {xlsxImportWarnings.map((warning, index) => (
                              <div key={index} className="bg-yellow-800/30 rounded p-3">
                                <div className="font-medium text-yellow-300">
                                  {warning.msg || warning.message}
                                </div>
                                {warning.suggestion && (
                                  <div className="text-yellow-400 text-sm mt-1">
                                    💡 {warning.suggestion}
                                  </div>
                                )}
                                {warning.code === 'densityAssumed' && (
                                  <div className="text-yellow-500 text-xs mt-1">
                                    🧪 Плотность: {warning.ingredient} (мл→г конверсия)
                                  </div>
                                )}
                                {warning.code === 'unitHeuristicApplied' && (
                                  <div className="text-yellow-500 text-xs mt-1">
                                    📏 Вес штуки: {warning.ingredient} (шт→г конверсия)
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Legacy issues fallback */}
                      {xlsxImportResults.issues && xlsxImportResults.issues.length > 0 && xlsxImportErrors.length === 0 && xlsxImportWarnings.length === 0 && (
                        <div className="bg-gray-900/50 rounded-lg p-4">
                          <details>
                            <summary className="text-gray-300 font-bold cursor-pointer hover:text-white">
                              Показать детали ({xlsxImportResults.issues.length} {xlsxImportResults.issues.length === 1 ? 'предупреждение' : 'предупреждений'})
                            </summary>
                            <div className="mt-4 space-y-2">
                              {xlsxImportResults.issues.map((issue, index) => (
                                <div 
                                  key={index}
                                  className={`text-sm p-3 rounded ${
                                    issue.level === 'error' ? 'bg-red-900/30 text-red-300' :
                                    issue.level === 'warning' ? 'bg-yellow-900/30 text-yellow-300' :
                                    'bg-blue-900/30 text-blue-300'
                                  }`}
                                >
                                  <span className="font-bold">{issue.code}:</span> {issue.msg}
                                </div>
                              ))}
                            </div>
                          </details>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Meta Information */}
                  {xlsxImportResults.meta && (
                    <div className="bg-gray-900/50 rounded-lg p-4 text-sm text-gray-400">
                      <div>Обработано строк: {xlsxImportResults.meta.parsed_rows}</div>
                      <div>Источник: {xlsxImportResults.meta.source}</div>
                      <div>Файл: {xlsxImportResults.meta.filename}</div>
                    </div>
                  )}

                  {/* Close Button */}
                  <div className="flex justify-end">
                    <button
                      onClick={() => {
                        setShowXlsxImportModal(false);
                        resetXlsxImport();
                      }}
                      className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                    >
                      Готово
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Debug Panel - show if debug=1 in URL */}
      {isDebugMode && (
        <div className="fixed bottom-4 right-4 bg-gray-900/95 backdrop-blur-lg border border-purple-400/30 rounded-lg p-3 text-xs font-mono max-w-sm">
          <div className="text-purple-300 font-bold mb-2">🐛 DEBUG PANEL</div>
          <div className="space-y-1 text-gray-300">
            <div>Status: {generationStatus || 'none'}</div>
            <div>TcV2 Present: {tcV2 ? 'yes' : 'no'}</div>
            <div>Price Coverage: {tcV2?.costMeta?.coveragePct ?? '-'}%</div>
            <div>Price Source: {tcV2?.costMeta?.source ?? '-'}</div>
            <div>Nutrition Coverage: {tcV2?.nutritionMeta?.coveragePct ?? '-'}%</div>
            <div>Issues Count: {generationIssues?.length ?? 0}</div>
            {generationIssues?.length > 0 && (
              <div>First Issue: {generationIssues[0]?.type || generationIssues[0] || 'none'}</div>
            )}
            <div>Last Request: {window.__lastGenerationDebug?.requestTime ? `${window.__lastGenerationDebug.requestTime}ms` : 'none'}</div>
            {/* GX-01: Show timings from TechCard meta */}
            {tcV2?.meta?.timings && (
              <div className="border-t border-gray-700 pt-1 mt-1">
                <div className="text-purple-300 font-bold">⏱️ Timings:</div>
                <div>Draft: {tcV2.meta.timings.llm_draft_ms || '-'}ms</div>
                <div>Normalize: {tcV2.meta.timings.llm_normalize_ms || '-'}ms</div>
                <div>Total: {tcV2.meta.timings.total_ms || '-'}ms</div>
              </div>
            )}
            <div className="border-t border-gray-700 pt-1 mt-1">
              <div>iiko Connected: {iikoRmsConnection.status === 'connected' ? 'yes' : 'no'}</div>
              <div>iiko Items: {iikoRmsConnection.products_count || 0}</div>
              <div>Last Sync: {iikoRmsConnection.last_sync ? new Date(iikoRmsConnection.last_sync).toLocaleTimeString() : 'never'}</div>
              <div>Auto-mapped Count: {autoMappingResults.filter(r => r.status === 'accepted' || r.status === 'auto_accept').length}</div>
              <div>Confidence Stats: {autoMappingResults.length > 0 ? 
                `≥90%: ${autoMappingResults.filter(r => r.confidence >= 90).length}, ` +
                `75-89%: ${autoMappingResults.filter(r => r.confidence >= 75 && r.confidence < 90).length}, ` +
                `<75%: ${autoMappingResults.filter(r => r.confidence > 0 && r.confidence < 75).length}`
                : 'none'}</div>
            </div>
          </div>
        </div>
      )}

      {/* Login Modal */}
      {showLogin && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-white mb-4">Вход в аккаунт</h2>
            
            <form onSubmit={handleLogin}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Введите ваш email"
                  required
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowLogin(false);
                    setLoginEmail('');
                  }}
                  className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
                >
                  Войти
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 🎯 ОНБОРДИНГ для новых пользователей */}
      {(showOnboarding || activeTour === 'welcome') && (
        <OnboardingTour
          isActive={activeTour === 'welcome'}
          onComplete={() => {
            handleOnboardingComplete();
            setActiveTour(null);
          }}
          onSkip={() => {
            handleOnboardingSkip();
            setActiveTour(null);
          }}
        />
      )}

      {/* 🎯 КОНТЕКСТНЫЕ ТУРЫ для каждого раздела */}
      <TourSystem
        tourId="createTechcard"
        steps={tourConfigs.createTechcard}
        isActive={activeTour === 'createTechcard'}
        onComplete={() => {
          console.log('✅ Create Techcard tour completed');
          setActiveTour(null);
        }}
        onSkip={() => {
          console.log('⏭️ Create Techcard tour skipped');
          setActiveTour(null);
        }}
      />
      
      <TourSystem
        tourId="aiKitchen"
        steps={tourConfigs.aiKitchen}
        isActive={activeTour === 'aiKitchen'}
        onComplete={() => {
          console.log('✅ AI Kitchen tour completed');
          setActiveTour(null);
        }}
        onSkip={() => {
          console.log('⏭️ AI Kitchen tour skipped');
          setActiveTour(null);
        }}
      />
      
      <TourSystem
        tourId="iiko"
        steps={tourConfigs.iiko}
        isActive={activeTour === 'iiko'}
        onComplete={() => {
          console.log('✅ IIKO tour completed');
          setActiveTour(null);
        }}
        onSkip={() => {
          console.log('⏭️ IIKO tour skipped');
          setActiveTour(null);
        }}
      />

      {/* Set Password Modal (for users without password) */}
      {showSetPasswordModal && currentUser && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-8 w-full max-w-md">
            <h2 className="text-2xl font-bold text-white mb-6">🔐 Установить пароль</h2>
            <p className="text-gray-400 mb-6">
              Установите пароль для входа через email. Это позволит вам входить в систему без Google OAuth.
            </p>
            
            <form onSubmit={async (e) => {
              e.preventDefault();
              if (!currentUser?.id) return;
              
              // Validation
              if (setPasswordData.password.length < 6) {
                alert('Пароль должен быть не менее 6 символов');
                return;
              }
              
              if (setPasswordData.password !== setPasswordData.confirmPassword) {
                alert('Пароли не совпадают');
                return;
              }
              
              setIsSettingPassword(true);
              try {
                const response = await axios.post(`${API}/user/${currentUser.id}/set-password`, {
                  password: setPasswordData.password
                });
                
                if (response.data.success) {
                  // Update current user
                  const updatedUser = { ...currentUser, password_hash: 'set', provider: 'email' };
                  setCurrentUser(updatedUser);
                  localStorage.setItem('receptor_user', JSON.stringify(updatedUser));
                  
                  // Close modal
                  setShowSetPasswordModal(false);
                  setSetPasswordData({ password: '', confirmPassword: '' });
                  
                  // Show success
                  alert('✅ Пароль установлен успешно! Теперь вы можете входить через email/password.');
                }
              } catch (error) {
                console.error('Set password error:', error);
                const errorMessage = error.response?.data?.detail || 'Ошибка установки пароля. Попробуйте еще раз.';
                alert(errorMessage);
              } finally {
                setIsSettingPassword(false);
              }
            }} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Новый пароль
                </label>
                <input
                  type="password"
                  value={setPasswordData.password}
                  onChange={(e) => setSetPasswordData({...setPasswordData, password: e.target.value})}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-green-500 transition-colors"
                  placeholder="Минимум 6 символов"
                  required
                  minLength={6}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Подтвердите пароль
                </label>
                <input
                  type="password"
                  value={setPasswordData.confirmPassword}
                  onChange={(e) => setSetPasswordData({...setPasswordData, confirmPassword: e.target.value})}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-green-500 transition-colors"
                  placeholder="Повторите пароль"
                  required
                  minLength={6}
                />
              </div>
              
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowSetPasswordModal(false);
                    setSetPasswordData({ password: '', confirmPassword: '' });
                  }}
                  className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 px-4 rounded-lg transition-colors"
                  disabled={isSettingPassword}
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  disabled={isSettingPassword}
                  className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white font-bold py-3 px-4 rounded-lg transition-colors disabled:cursor-not-allowed"
                >
                  {isSettingPassword ? '⏳ Установка...' : '💾 Установить пароль'}
                </button>
              </div>
            </form>
            
            <button
              onClick={() => {
                setShowSetPasswordModal(false);
                setSetPasswordData({ password: '', confirmPassword: '' });
              }}
              className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Profile Edit Modal */}
      {showProfileEditModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-8 w-full max-w-md">
            <h2 className="text-2xl font-bold text-white mb-6">✏️ Редактировать профиль</h2>
            
            <form onSubmit={async (e) => {
              e.preventDefault();
              if (!currentUser?.id) return;
              
              setIsUpdatingUserProfile(true);
              try {
                const response = await axios.put(`${API}/user/${currentUser.id}/update`, editProfileData);
                
                // Update current user
                setCurrentUser(response.data);
                localStorage.setItem('receptor_user', JSON.stringify(response.data));
                
                // Close modal
                setShowProfileEditModal(false);
                
                // Show success
                alert('✅ Профиль обновлен успешно!');
              } catch (error) {
                console.error('Profile update error:', error);
                const errorMessage = error.response?.data?.detail || 'Ошибка обновления профиля. Попробуйте еще раз.';
                alert(errorMessage);
              } finally {
                setIsUpdatingUserProfile(false);
              }
            }} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Имя
                </label>
                <input
                  type="text"
                  value={editProfileData.name}
                  onChange={(e) => setEditProfileData({...editProfileData, name: e.target.value})}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 transition-colors"
                  placeholder="Ваше имя"
                  required
                  minLength={2}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={editProfileData.email}
                  onChange={(e) => setEditProfileData({...editProfileData, email: e.target.value})}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 transition-colors"
                  placeholder="your@email.com"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Город
                </label>
                <input
                  type="text"
                  value={editProfileData.city}
                  onChange={(e) => setEditProfileData({...editProfileData, city: e.target.value})}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 transition-colors"
                  placeholder="Москва"
                  required
                  minLength={2}
                />
              </div>
              
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowProfileEditModal(false)}
                  className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 px-4 rounded-lg transition-colors"
                  disabled={isUpdatingUserProfile}
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  disabled={isUpdatingUserProfile}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-bold py-3 px-4 rounded-lg transition-colors disabled:cursor-not-allowed"
                >
                  {isUpdatingUserProfile ? '⏳ Сохранение...' : '💾 Сохранить'}
                </button>
              </div>
            </form>
            
            <button
              onClick={() => setShowProfileEditModal(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* 💎 Pricing Page Modal */}
      {showPricingPage && (
        <>
          {console.log('🔵 Rendering PricingPage, showPricingPage:', showPricingPage, 'currentUser:', currentUser)}
          <PricingPage
          currentUser={currentUser}
          onClose={() => setShowPricingPage(false)}
          onSubscriptionUpdated={async () => {
            // Reload user data after subscription update
            if (currentUser) {
              try {
                const response = await axios.get(`${API}/user-subscription/${currentUser.id}`);
                if (response.data) {
                  const updatedUser = { ...currentUser, ...response.data };
                  setCurrentUser(updatedUser);
                  localStorage.setItem('receptor_user', JSON.stringify(updatedUser));
                }
              } catch (error) {
                console.error('Failed to refresh user subscription:', error);
              }
            }
          }}
        />
        </>
      )}

      {/* 🚀 Modern Auth Modal */}
      <ModernAuthModal
        isOpen={showModernAuth}
        onClose={() => setShowModernAuth(false)}
        onGoogleSuccess={(user, token) => {
          // Обновляем состояние пользователя сразу после Google авторизации
          setCurrentUser(user);
          
          // Загружаем данные пользователя (subscription, history, prices)
          // Это произойдет автоматически через useEffect при изменении currentUser
          
          // Закрываем модал
          setShowModernAuth(false);
          
          // Показываем сообщение об успехе
          alert('✅ Вход через Google выполнен успешно!');
        }}
        onLogin={async (email, password) => {
          try {
            const response = await axios.post(`${API}/login`, {
              email,
              password
            });
            
            if (response.data.success) {
              // Save user and token
              localStorage.setItem('receptor_user', JSON.stringify(response.data.user));
              localStorage.setItem('receptor_token', response.data.token);
              
              // Update state
              setCurrentUser(response.data.user);
              
              // Close modal
              setShowModernAuth(false);
              
              // Show success message
              alert('✅ Вход выполнен успешно!');
            } else {
              alert('Ошибка авторизации. Попробуйте еще раз.');
            }
          } catch (error) {
            console.error('Login error:', error);
            const errorMessage = error.response?.data?.detail || 'Ошибка авторизации. Попробуйте еще раз.';
            alert(errorMessage);
          }
        }}
        onRegister={async (email, password) => {
          try {
            // Extract name from email (before @)
            const name = email.split('@')[0];
            const city = 'Москва'; // Default city, can be updated later
            
            const response = await axios.post(`${API}/register`, {
              email,
              password,
              name,
              city
            });
            
            if (response.data) {
              // For registration, we need to login after registration
              // Try to login with the same credentials
              try {
                const loginResponse = await axios.post(`${API}/login`, {
                  email,
                  password
                });
                
                if (loginResponse.data.success) {
                  // Save user and token
                  localStorage.setItem('receptor_user', JSON.stringify(loginResponse.data.user));
                  localStorage.setItem('receptor_token', loginResponse.data.token);
                  
                  // Update state
                  setCurrentUser(loginResponse.data.user);
                  
                  // Close modal
                  setShowModernAuth(false);
                  
                  // Show success message
                  alert('✅ Регистрация выполнена успешно! Добро пожаловать!');
                }
              } catch (loginError) {
                console.error('Auto-login error:', loginError);
                alert('✅ Регистрация выполнена успешно! Пожалуйста, войдите в систему.');
                // Switch to login mode
                // This will be handled by the modal itself
              }
            }
          } catch (error) {
            console.error('Registration error:', error);
            const errorMessage = error.response?.data?.detail || 'Ошибка регистрации. Попробуйте еще раз.';
            alert(errorMessage);
          }
        }}
      />

    </div>
  );
}

export default App;