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
  const [userHistory, setUserHistory] = useState([]);
  const [showTwistModal, setShowTwistModal] = useState(false);
  const [showPriceModal, setShowPriceModal] = useState(false);
  const [userPrices, setUserPrices] = useState([]);
  const [uploadingPrices, setUploadingPrices] = useState(false);
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
      if (line.includes('**Название:**') || (line.startsWith('**') && line.includes('Название'))) {
        let title = line.replace(/\*\*/g, '').replace('Название:', '').replace('Название:', '').trim();
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
      
      // Description section
      if (line.includes('**Описание:**')) {
        const descriptionLine = line.replace(/\*\*/g, '').replace('Описание:', '').trim();
        if (descriptionLine) {
          result.push(
            <div key={index} className="my-6">
              <h3 className="text-lg font-bold text-purple-400 mb-3 uppercase tracking-wide">
                ОПИСАНИЕ
              </h3>
              <p className="text-gray-300 leading-relaxed bg-gray-800/30 p-4 rounded-lg">
                {descriptionLine}
              </p>
            </div>
          );
        }
        continue;
      }
      
      // Category section
      if (line.includes('**Категория:**')) {
        const categoryLine = line.replace(/\*\*/g, '').replace('Категория:', '').trim();
        if (categoryLine) {
          result.push(
            <div key={index} className="my-4">
              <span className="inline-block bg-purple-600 text-white px-3 py-1 rounded-full text-sm font-bold uppercase">
                {categoryLine}
              </span>
            </div>
          );
        }
        continue;
      }
      
      // INGREDIENTS TABLE - в правильном месте
      if (line.includes('Ингредиенты') || line.includes('**Ингредиенты:**')) {
        console.log('CREATING INGREDIENTS TABLE');
        
        // Найти все строки ингредиентов из всей техкарты - РАСШИРЕННЫЙ ПОИСК
        const allIngredientLines = lines.filter(l => 
          l.startsWith('- ') && (l.includes('₽') || l.includes('руб') || l.includes('—') || l.includes('~'))
        );
        
        console.log('Found ingredient lines:', allIngredientLines);
        
        if (allIngredientLines.length > 0) {
          result.push(
            <div key={`ingredients-${index}`} className="my-8">
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
                    {allIngredientLines.map((ingLine, ingIndex) => {
                      const cleanLine = ingLine.replace('- ', '');
                      let parts = [];
                      
                      if (cleanLine.includes(' — ')) {
                        parts = cleanLine.split(' — ');
                      } else if (cleanLine.includes(' - ')) {
                        parts = cleanLine.split(' - ');
                      } else {
                        parts = [cleanLine, '', ''];
                      }
                      
                      return (
                        <tr key={ingIndex} className={ingIndex % 2 === 0 ? 'bg-gray-700/30' : 'bg-gray-600/30'}>
                          <td className="py-3 px-4 text-gray-200 border-r border-gray-600">
                            {parts[0] ? parts[0].trim() : 'Ингредиент'}
                          </td>
                          <td className="py-3 px-4 text-gray-200 text-center border-r border-gray-600">
                            {parts[1] ? parts[1].trim() : ''}
                          </td>
                          <td className="py-3 px-4 text-gray-200 text-right">
                            {parts[2] ? parts[2].trim() : parts[parts.length - 1].trim()}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              
              <div className="mt-4">
                <button
                  onClick={() => {
                    const editIngredients = allIngredientLines.map(line => {
                      const cleanLine = line.replace('- ', '');
                      let parts = [];
                      
                      if (cleanLine.includes(' — ')) {
                        parts = cleanLine.split(' — ');
                      } else if (cleanLine.includes(' - ')) {
                        parts = cleanLine.split(' - ');
                      } else {
                        parts = [cleanLine, '', ''];
                      }
                      
                      return {
                        name: parts[0] ? parts[0].trim() : '',
                        quantity: parts[1] ? parts[1].trim() : '',
                        price: parts[2] ? parts[2].trim() : parts[parts.length - 1].trim()
                      };
                    });
                    
                    setEditableIngredients(editIngredients);
                    setIsEditingIngredients(true);
                  }}
                  className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-bold transition-colors"
                >
                  РЕДАКТИРОВАТЬ
                </button>
              </div>
            </div>
          );
        }
        continue;
      }
      
      // Skip ingredient lines that are already rendered
      if (line.startsWith('- ') && 
          (line.includes('₽') || line.includes('руб') || 
           line.includes(' г ') || line.includes(' мл '))) {
        continue;
      }
      
      // Portion section - показываем размер порции четко
      if (line.includes('**Порция:**')) {
        const portionLine = line.replace(/\*\*/g, '').replace('Порция:', '').trim();
        if (portionLine) {
          result.push(
            <div key={index} className="my-6">
              <div className="bg-gradient-to-r from-green-600/20 to-emerald-600/20 border border-green-400/30 rounded-lg p-4">
                <h3 className="text-lg font-bold text-green-300 mb-2 uppercase tracking-wide">
                  РАЗМЕР ПОРЦИИ
                </h3>
                <p className="text-green-200 text-xl font-bold">
                  {portionLine}
                </p>
              </div>
            </div>
          );
        }
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
      console.log('No dish name provided');
      return;
    }

    setIsGenerating(true);
    try {
      console.log('Sending request to:', `${API}/generate-tech-card`);
      const response = await axios.post(`${API}/generate-tech-card`, {
        dish_name: dishName,
        user_id: currentUser.id
      });
      
      console.log('Response received:', response.data);
      setTechCard(response.data.tech_card);
      setCurrentTechCardId(response.data.id);
      setDishName('');
      
      // Parse ingredients and steps for editing
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
      console.error('Error generating tech card:', error);
      alert('Ошибка при генерации техкарты');
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePriceFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    setUploadingPrices(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', currentUser.id);
      
      const response = await axios.post(`${API}/upload-prices`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setUserPrices(response.data.prices);
      
      // Show success message with statistics
      const stats = response.data;
      alert(`Успешно загружено ${stats.count} позиций!\nНайдено категорий: ${stats.categories_found}\nДанные очищены и категоризированы.`);
      
    } catch (error) {
      console.error('Error uploading prices:', error);
      alert('Ошибка загрузки файла. Проверьте формат.');
    } finally {
      setUploadingPrices(false);
      // Reset file input
      event.target.value = '';
    }
  };

  const fetchUserHistory = async () => {
    try {
      const response = await axios.get(`${API}/user-history/${currentUser.id}`);
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
      
      // Load user prices for PRO users
      if (parsedUser.subscription_plan === 'pro' || parsedUser.subscription_plan === 'business') {
        loadUserPrices(parsedUser.id);
      }
    }
  }, []);

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
          
          {/* Subscription Info */}
          <div className="flex items-center space-x-4">
            <div className="text-center">
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
            
            <div className="flex items-center space-x-6">
              <button
                onClick={() => {
                  setShowHistory(!showHistory);
                  if (!showHistory) {
                    fetchUserHistory();
                  }
                }}
                className="text-purple-300 hover:text-purple-200 font-semibold"
              >
                ИСТОРИЯ
              </button>
              <span className="text-purple-300 font-bold">{currentUser.name}</span>
              <button
                onClick={handleLogout}
                className="text-purple-300 hover:text-purple-200 font-semibold"
              >
                ВЫЙТИ
              </button>
            </div>
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
                    disabled={!dishName.trim() || isGenerating}
                    className="w-full bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-bold py-3 px-6 rounded-lg transition-colors flex items-center justify-center"
                  >
                    {isGenerating ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
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
                  <div className="border-t border-purple-400/30 pt-6">
                    <h3 className="text-lg font-bold text-purple-300 mb-4">PRO ФУНКЦИИ</h3>
                    <button
                      onClick={() => setShowPriceModal(true)}
                      className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-bold py-3 px-6 rounded-lg transition-colors mb-4"
                    >
                      💰 УПРАВЛЕНИЕ ПРАЙСАМИ
                    </button>
                    {userPrices.length > 0 && (
                      <div className="text-sm text-green-400 text-center">
                        Загружено {userPrices.length} позиций
                      </div>
                    )}
                  </div>
                )}
                
                {/* Upgrade prompt for Free users */}
                {currentUser.subscription_plan === 'free' && currentUser.monthly_tech_cards_used >= 3 && (
                  <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 border border-purple-400/30 rounded-lg p-4 mt-4">
                    <h3 className="text-lg font-bold text-purple-300 mb-2">ЛИМИТ ИСЧЕРПАН</h3>
                    <p className="text-gray-300 text-sm mb-3">
                      Вы использовали все 3 техкарты в месяце. Обновите подписку для неограниченного доступа!
                    </p>
                    <button
                      onClick={() => alert('Функция обновления подписки скоро будет доступна')}
                      className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-2 px-4 rounded-lg transition-all hover:from-purple-700 hover:to-pink-700"
                    >
                      ОБНОВИТЬ ПОДПИСКУ
                    </button>
                  </div>
                )}
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
                      onClick={handleEditTechCard}
                      disabled={!editInstruction.trim() || isEditingAI}
                      className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold py-3 px-6 rounded-lg transition-colors flex items-center justify-center"
                    >
                      {isEditingAI ? (
                        <>
                          <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
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
                    <button 
                      onClick={() => setShowTwistModal(true)}
                      className="bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 text-white px-4 py-2 rounded-lg font-bold transition-colors"
                    >
                      🎲 ТВИСТ
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
                      const priceNum = parseFloat(ing.price.replace(/[^\d.]/g, '')) || 0;
                      return sum + priceNum;
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
              <h3 className="text-2xl font-bold text-green-300">💰 УПРАВЛЕНИЕ ПРАЙСАМИ</h3>
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
              <h4 className="text-blue-300 font-bold mb-2">💡 УМНАЯ ОБРАБОТКА:</h4>
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

      {/* Twist Modal */}
      {showTwistModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-md w-full mx-4 border border-orange-500/30">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-orange-600 to-red-600 rounded-full flex items-center justify-center">
                <span className="text-2xl">🎲</span>
              </div>
              <h3 className="text-xl font-bold text-orange-300 mb-4">ТВИСТ НА БЛЮДО</h3>
              <p className="text-gray-300 mb-6 text-sm">
                Выберите стиль для интересной вариации вашего блюда
              </p>
              
              <div className="grid grid-cols-2 gap-3 mb-6">
                {[
                  { emoji: '🍜', text: 'Азиатский стиль', action: 'адаптируй под азиатскую кухню' },
                  { emoji: '🥗', text: 'Здоровое питание', action: 'сделай более здоровым и диетическим' },
                  { emoji: '🌱', text: 'Веганская версия', action: 'адаптируй для веганов, замени животные продукты' },
                  { emoji: '💎', text: 'Премиум вариант', action: 'сделай премиум версию с дорогими ингредиентами' },
                  { emoji: '⚡', text: 'Быстрое приготовление', action: 'упрости рецепт для быстрого приготовления' },
                  { emoji: '🔬', text: 'Молекулярная кухня', action: 'адаптируй под молекулярную кухню' },
                  { emoji: '🍂', text: 'Сезонные ингредиенты', action: 'используй сезонные ингредиенты' },
                  { emoji: '🚫', text: 'Безглютеновый', action: 'сделай безглютеновую версию' }
                ].map((twist, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setEditInstruction(`${twist.action}, сохрани структуру и стиль техкарты`);
                      setShowTwistModal(false);
                      // Auto-apply the twist
                      setTimeout(() => {
                        handleEditTechCard();
                      }, 100);
                    }}
                    className="bg-gray-700 hover:bg-orange-600 text-white p-3 rounded-lg transition-colors text-sm flex flex-col items-center"
                  >
                    <span className="text-lg mb-1">{twist.emoji}</span>
                    <span className="text-xs">{twist.text}</span>
                  </button>
                ))}
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    const twists = [
                      'адаптируй под азиатскую кухню',
                      'сделай более здоровым и диетическим', 
                      'адаптируй для веганов, замени животные продукты',
                      'сделай премиум версию с дорогими ингредиентами',
                      'упрости рецепт для быстрого приготовления',
                      'адаптируй под молекулярную кухню',
                      'используй сезонные ингредиенты',
                      'сделай безглютеновую версию'
                    ];
                    const randomTwist = twists[Math.floor(Math.random() * twists.length)];
                    setEditInstruction(`${randomTwist}, сохрани структуру и стиль техкарты`);
                    setShowTwistModal(false);
                    // Auto-apply the random twist
                    setTimeout(() => {
                      handleEditTechCard();
                    }, 100);
                  }}
                  className="flex-1 bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 text-white px-4 py-2 rounded-lg transition-colors text-sm"
                >
                  🎲 СЛУЧАЙНЫЙ
                </button>
                <button
                  onClick={() => setShowTwistModal(false)}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors text-sm"
                >
                  ОТМЕНА
                </button>
              </div>
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
    </div>
  );
}

export default App;