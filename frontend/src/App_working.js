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

  // Registration form state
  const [registrationData, setRegistrationData] = useState({
    email: '',
    name: '',
    city: ''
  });

  // Simple tech card formatter without complex parsing
  const formatTechCard = (content) => {
    const lines = content.split('\n');
    const result = [];
    
    for (let index = 0; index < lines.length; index++) {
      const line = lines[index].trim();
      
      // Main title
      if (line.startsWith('**') && line.endsWith('**') && line.includes('Название')) {
        const title = line.replace(/\*\*/g, '').replace('Название:', '').trim();
        if (title) {
          result.push(
            <div key={index} className="text-center mb-8">
              <h1 className="text-4xl font-bold text-purple-300 mb-4">{title}</h1>
            </div>
          );
        }
        continue;
      }
      
      // Section headers
      if (line.startsWith('**') && line.endsWith('**')) {
        const title = line.replace(/\*\*/g, '').replace(':', '').trim();
        if (title && !title.includes('Название')) {
          result.push(
            <h2 key={index} className="text-2xl font-bold text-purple-400 mt-8 mb-4 border-b border-purple-400 pb-2">
              {title}
            </h2>
          );
        }
        continue;
      }
      
      // List items
      if (line.startsWith('- ')) {
        result.push(
          <div key={index} className="ml-6 mb-2 text-gray-300">
            <span className="text-purple-400 mr-2">•</span>
            {line.replace('- ', '')}
          </div>
        );
        continue;
      }
      
      // Numbered steps
      if (line.match(/^\d+\./)) {
        result.push(
          <div key={index} className="bg-gray-800/50 p-4 rounded-lg mb-4 border-l-4 border-purple-500">
            <div className="text-gray-200">{line}</div>
          </div>
        );
        continue;
      }
      
      // Regular text
      if (line && !line.startsWith('─')) {
        result.push(
          <p key={index} className="mb-3 text-gray-300">
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

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/register`, registrationData);
      setCurrentUser(response.data);
      localStorage.setItem('receptor_user', JSON.stringify(response.data));
      setShowRegistration(false);
      setRegistrationData({ email: '', name: '', city: '' });
    } catch (error) {
      alert('Ошибка регистрации. Попробуйте еще раз.');
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

  useEffect(() => {
    fetchCities();
    const savedUser = localStorage.getItem('receptor_user');
    if (savedUser) {
      setCurrentUser(JSON.parse(savedUser));
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

          {!showRegistration ? (
            <div className="space-y-6">
              <button
                onClick={() => setShowRegistration(true)}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all"
              >
                НАЧАТЬ РАБОТУ
              </button>
            </div>
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
            <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-8 border border-gray-700">
              <h2 className="text-2xl font-bold text-purple-300 mb-6">СОЗДАТЬ ТЕХКАРТУ</h2>
              <form onSubmit={handleGenerateTechCard} className="space-y-6">
                <textarea
                  value={dishName}
                  onChange={(e) => setDishName(e.target.value)}
                  placeholder="Опишите блюдо подробно. Например: Стейк из говядины с картофельным пюре и грибным соусом"
                  className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none min-h-[120px] resize-none"
                  rows={5}
                  required
                />
                <button
                  type="submit"
                  disabled={isGenerating}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all disabled:opacity-50"
                >
                  {isGenerating ? 'ГЕНЕРИРУЕТСЯ...' : 'СОЗДАТЬ ТЕХКАРТУ'}
                </button>
              </form>
            </div>
          </div>

          {/* Right Panel */}
          <div className="lg:col-span-2">
            {techCard ? (
              <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-8 border border-gray-700">
                <div className="flex justify-between items-center mb-8">
                  <h2 className="text-2xl font-bold text-purple-300">ТЕХНОЛОГИЧЕСКАЯ КАРТА</h2>
                  <button 
                    onClick={() => navigator.clipboard.writeText(techCard)}
                    className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-bold"
                  >
                    КОПИРОВАТЬ
                  </button>
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
    </div>
  );
}

export default App;