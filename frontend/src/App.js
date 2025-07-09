import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [showRegistration, setShowRegistration] = useState(false);
  const [cities, setCities] = useState([]);
  const [dishName, setDishName] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
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
  const [editableIngredients, setEditableIngredients] = useState([]);
  const [isEditingIngredients, setIsEditingIngredients] = useState(false);
  const [editableSteps, setEditableSteps] = useState([]);
  const [isEditingSteps, setIsEditingSteps] = useState(false);

  // Voice recognition states
  const [isListening, setIsListening] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState('');
  const [showVoiceModal, setShowVoiceModal] = useState(false);
  const [recognition, setRecognition] = useState(null);

  // Login states
  const [showLogin, setShowLogin] = useState(false);
  const [loginEmail, setLoginEmail] = useState('');

  // Registration form state
  const [registrationData, setRegistrationData] = useState({
    email: '',
    name: '',
    city: ''
  });

  // Enhanced tech card formatter with debug
  const formatTechCard = (content) => {
    console.log('=== DEBUG: Full content ===');
    console.log(content);
    console.log('=== END DEBUG ===');
    
    const lines = content.split('\n');
    const result = [];
    
    for (let index = 0; index < lines.length; index++) {
      const line = lines[index].trim();
      
      // Main title - FIXED to show dish name
      if (line.startsWith('**') && line.endsWith('**') && line.includes('Название')) {
        const title = line.replace(/\*\*/g, '').replace('Название:', '').trim();
        console.log('Found title line:', line);
        console.log('Extracted title:', title);
        if (title) {
          result.push(
            <div key={index} className="text-center mb-8">
              <h1 className="text-4xl font-bold text-purple-300 mb-4 animate-pulse">{title}</h1>
            </div>
          );
        }
        continue;
      }
      
      // Section headers - clean format without stars
      if (line.startsWith('**') && line.endsWith('**')) {
        const title = line.replace(/\*\*/g, '').replace(':', '').trim();
        if (title && !title.includes('Название')) {
          result.push(
            <h2 key={index} className="text-2xl font-bold text-purple-400 mt-8 mb-4 border-b-2 border-purple-400 pb-2 uppercase tracking-wide">
              {title}
            </h2>
          );
        }
        continue;
      }
      
      // FORCED INGREDIENTS TABLE - will always show
      if (line.includes('Ингредиенты')) {
        console.log('FORCE CREATING INGREDIENTS TABLE');
        
        // Try to parse real ingredients from content first
        const realIngredients = [];
        const ingredientLines = lines.filter(l => {
          const cleanLine = l.trim();
          return cleanLine.startsWith('- ') && 
                 cleanLine.includes('₽') &&
                 !cleanLine.includes('ингредиентам:') &&
                 !cleanLine.includes('Себестоимость') &&
                 !cleanLine.includes('Рекомендуемая цена') &&
                 !cleanLine.includes('Ужарка');
        });
        
        console.log('Real ingredient lines found:', ingredientLines);
        
        // Parse real ingredients with correct em dash
        ingredientLines.forEach(ingLine => {
          if (ingLine.includes(' — ')) {
            const parts = ingLine.replace('- ', '').split(' — ');
            if (parts.length >= 3) {
              realIngredients.push({
                name: parts[0].trim(),
                quantity: parts[1].trim(),
                price: parts[2].trim()
              });
            }
          }
        });
        
        console.log('Final ingredients for table:', realIngredients);
        
        // Use real ingredients if found, otherwise show placeholder
        const finalIngredients = realIngredients.length > 0 ? realIngredients : [
          { name: 'Ингредиенты загружаются...', quantity: '...', price: '...' }
        ];
        
        console.log('Final ingredients for table:', finalIngredients);
        
        result.push(
          <div key={index} className="my-8">
            <h2 className="text-2xl font-bold text-purple-400 mb-4 border-b-2 border-purple-400 pb-2 uppercase tracking-wide">
              ИНГРЕДИЕНТЫ
            </h2>
            <div className="overflow-x-auto bg-gray-800/50 rounded-lg">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gradient-to-r from-purple-600 to-purple-700">
                    <th className="text-left py-4 px-4 text-white font-bold text-sm uppercase tracking-wide">ИНГРЕДИЕНТ</th>
                    <th className="text-center py-4 px-4 text-white font-bold text-sm uppercase tracking-wide">КОЛИЧЕСТВО</th>
                    <th className="text-right py-4 px-4 text-white font-bold text-sm uppercase tracking-wide">ЦЕНА</th>
                  </tr>
                </thead>
                <tbody>
                  {finalIngredients.map((ing, ingIndex) => (
                    <tr key={`forced-ing-${ingIndex}`} className="hover:bg-gray-700/50 transition-colors">
                      <td className="font-semibold text-purple-200 py-3 px-4 border-b border-purple-400/30">
                        {ing.name}
                      </td>
                      <td className="text-center text-gray-300 py-3 px-4 border-b border-purple-400/30">
                        {ing.quantity}
                      </td>
                      <td className="text-right font-bold text-green-300 py-3 px-4 border-b border-purple-400/30">
                        {ing.price}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
        
        continue;
      }
      
      // Skip ingredient lines that are already rendered
      if (line.startsWith('- ') && 
          (line.includes('₽') || line.includes('руб') || 
           line.includes(' г ') || line.includes(' мл '))) {
        continue;
      }
      
      // Cost information with better formatting
      if (line.includes('Себестоимость') || line.includes('Рекомендуемая цена') || line.includes('По ингредиентам')) {
        result.push(
          <div key={index} className="my-6 p-4 bg-green-900/20 border border-green-500/30 rounded-lg">
            <div className="font-bold text-lg text-green-200">{line}</div>
          </div>
        );
        continue;
      }
      
      // КБЖУ information
      if (line.includes('КБЖУ') || line.includes('Калории')) {
        result.push(
          <div key={index} className="my-6 p-4 bg-blue-900/20 border border-blue-500/30 rounded-lg">
            <div className="font-bold text-blue-200">{line}</div>
          </div>
        );
        continue;
      }
      
      // List items - improved styling
      if (line.startsWith('- ')) {
        result.push(
          <div key={index} className="ml-6 mb-2 text-gray-300 flex items-start">
            <span className="text-purple-400 mr-3 mt-1 text-lg">•</span>
            <span>{line.replace('- ', '')}</span>
          </div>
        );
        continue;
      }
      
      // Numbered steps with better styling
      if (line.match(/^\d+\./)) {
        result.push(
          <div key={index} className="bg-gray-800/50 p-4 rounded-lg mb-4 border-l-4 border-purple-500 hover:bg-gray-800/70 transition-colors">
            <div className="font-medium text-gray-200 leading-relaxed">{line}</div>
          </div>
        );
        continue;
      }
      
      // Regular paragraphs
      if (line && !line.startsWith('─') && !line.startsWith('*')) {
        result.push(
          <p key={index} className="mb-3 text-gray-300 leading-relaxed">
            {line}
          </p>
        );
        continue;
      }
    }
    
    return result;
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
    if (!dishName.trim()) return;

    setIsGenerating(true);
    try {
      const response = await axios.post(`${API}/generate-tech-card`, {
        dish_name: dishName,
        user_id: currentUser.id
      });
      
      setTechCard(response.data.tech_card);
      setCurrentTechCardId(response.data.id);
      setDishName('');
    } catch (error) {
      console.error('Error generating tech card:', error);
      alert('Ошибка при генерации техкарты');
    } finally {
      setIsGenerating(false);
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
      
      // Format headers
      if (line.startsWith('**') && line.endsWith('**')) {
        const title = cleanLine.replace(':', '').trim();
        if (title.includes('Название')) {
          const dishTitle = title.replace('Название', '').trim();
          return `<h1 style="color: #8B5CF6; font-size: 28px; font-weight: 900; text-align: center; margin-bottom: 30px; border-bottom: 3px solid #8B5CF6; padding-bottom: 15px;">${dishTitle}</h1>`;
        }
        return `<h2 style="color: #1A1B23; font-size: 18px; font-weight: 800; text-transform: uppercase; margin-top: 25px; margin-bottom: 15px; border-bottom: 2px solid #C084FC; padding-bottom: 8px;">${title}</h2>`;
      }
      
      // Format ingredients
      if (line.startsWith('- ') && (line.includes('₽') || line.includes('руб'))) {
        return `<p style="margin-left: 20px; margin-bottom: 8px;">• ${cleanLine.replace('- ', '')}</p>`;
      }
      
      // Format numbered steps
      if (line.match(/^\d+\./)) {
        return `<div style="background: #F8FAFC; border-left: 4px solid #8B5CF6; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">${cleanLine}</div>`;
      }
      
      // Format list items
      if (line.startsWith('- ')) {
        return `<p style="margin-left: 20px; margin-bottom: 8px;">• ${cleanLine.replace('- ', '')}</p>`;
      }
      
      // Cost information
      if (line.includes('Себестоимость') || line.includes('Рекомендуемая цена')) {
        return `<div style="background: #F0FDF4; border: 2px solid #10B981; border-radius: 8px; padding: 15px; margin: 15px 0; font-weight: 700;">${cleanLine}</div>`;
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
            <p><strong>Сгенерировано RECEPTOR AI</strong></p>
            <p>Дата создания: ${new Date().toLocaleDateString('ru-RU')}</p>
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
    initVoiceRecognition();
    const savedUser = localStorage.getItem('receptor_user');
    console.log('Checking for saved user:', savedUser);
    if (savedUser) {
      const parsedUser = JSON.parse(savedUser);
      console.log('Setting currentUser from localStorage:', parsedUser);
      setCurrentUser(parsedUser);
    }
  }, []);

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black flex items-center justify-center p-4">
        <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-8 w-full max-w-md border border-gray-700">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-purple-300 mb-2">RECEPTOR PRO</h1>
            <p className="text-gray-400">AI для создания техкарт</p>
          </div>

          {!showRegistration && !showLogin ? (
            <div className="space-y-6">
              <button
                onClick={() => setShowRegistration(true)}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all"
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
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all"
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
      {/* Header */}
      <header className="border-b border-purple-400/30 p-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <h1 className="text-3xl font-bold text-purple-300">RECEPTOR PRO</h1>
          <div className="flex items-center space-x-6">
            <span className="text-purple-300 font-bold">{currentUser.name}</span>
            <button
              onClick={handleLogout}
              className="text-purple-300 hover:text-purple-200 font-semibold"
            >
              ВЫЙТИ
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
          {/* Left Panel */}
          <div className="lg:col-span-1">
            <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-8 border border-gray-700 space-y-8">
              <div>
                <h2 className="text-2xl font-bold text-purple-300 mb-6">СОЗДАТЬ ТЕХКАРТУ</h2>
                <form onSubmit={handleGenerateTechCard} className="space-y-6">
                  <div>
                    <label className="block text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
                      НАЗВАНИЕ БЛЮДА
                    </label>
                    <div className="relative">
                      <textarea
                        value={dishName}
                        onChange={(e) => setDishName(e.target.value)}
                        placeholder="Опишите блюдо подробно. Например: Стейк из говядины с картофельным пюре и грибным соусом"
                        className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none min-h-[120px] resize-none"
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
                        } text-white`}
                        title="Голосовой ввод"
                      >
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={isGenerating}
                    className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all disabled:opacity-50"
                  >
                    {isGenerating ? 'ГЕНЕРИРУЕТСЯ...' : 'СОЗДАТЬ ТЕХКАРТУ'}
                  </button>
                </form>
              </div>

              {/* AI Editing */}
              {techCard && (
                <div className="border-t border-purple-400/30 pt-8">
                  <h3 className="text-xl font-bold text-purple-300 mb-6">
                    РЕДАКТИРОВАТЬ ЧЕРЕЗ AI
                  </h3>
                  <div className="space-y-4">
                    <textarea
                      value={editInstruction}
                      onChange={(e) => setEditInstruction(e.target.value)}
                      placeholder="Детально опишите что изменить. Например: увеличить порцию в 2 раза, заменить картофель на рис"
                      className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none min-h-[100px] resize-none"
                      rows={4}
                    />
                    <button
                      onClick={() => alert('AI редактирование временно недоступно')}
                      disabled={!editInstruction.trim()}
                      className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                    >
                      ИЗМЕНИТЬ ЧЕРЕЗ AI
                    </button>
                  </div>
                  
                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    className="w-full mt-4 bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                  >
                    {isEditing ? 'ЗАКРЫТЬ РЕДАКТОР' : 'РУЧНОЕ РЕДАКТИРОВАНИЕ'}
                  </button>
                </div>
              )}

              {/* Manual Editing */}
              {isEditing && techCard && (
                <div className="border-t border-purple-400/30 pt-8">
                  <h3 className="text-xl font-bold text-purple-300 mb-6">
                    РУЧНОЕ РЕДАКТИРОВАНИЕ
                  </h3>
                  <div className="space-y-4">
                    <button
                      onClick={() => alert('Интерактивный редактор ингредиентов скоро')}
                      className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                    >
                      РЕДАКТИРОВАТЬ ИНГРЕДИЕНТЫ
                    </button>
                    <button
                      onClick={() => alert('Редактор этапов скоро')}
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
              <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-8 border border-gray-700">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
                  <h2 className="text-2xl font-bold text-purple-300">ТЕХНОЛОГИЧЕСКАЯ КАРТА</h2>
                  <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
                    <button 
                      onClick={() => navigator.clipboard.writeText(techCard)}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-bold transition-colors"
                    >
                      КОПИРОВАТЬ
                    </button>
                    <button 
                      onClick={handlePrintTechCard}
                      className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-bold transition-colors"
                    >
                      ЭКСПОРТ В PDF
                    </button>
                  </div>
                </div>
                <div className="prose prose-invert max-w-none">
                  {formatTechCard(techCard)}
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
    </div>
  );
}

export default App;