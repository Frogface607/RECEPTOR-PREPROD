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

  useEffect(() => {
    fetchCities();
    fetchSubscriptionPlans();
    fetchKitchenEquipment();
    initVoiceRecognition();
    const savedUser = localStorage.getItem('receptor_user');
    if (savedUser) {
      setCurrentUser(JSON.parse(savedUser));
    }
  }, []);

  useEffect(() => {
    if (currentUser) {
      fetchUserTechCards();
      fetchUserSubscription();
    }
  }, [currentUser]);

  const initVoiceRecognition = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = false;
      recognitionInstance.lang = 'ru-RU';
      
      recognitionInstance.onstart = () => {
        setIsListening(true);
        setVoiceStatus('Говорите название блюда...');
        setShowVoiceModal(true);
      };
      
      recognitionInstance.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setDishName(transcript);
        setVoiceStatus(`Распознано: "${transcript}"`);
        setTimeout(() => {
          setShowVoiceModal(false);
          setIsListening(false);
        }, 1500);
      };
      
      recognitionInstance.onerror = (event) => {
        setVoiceStatus('Ошибка распознавания. Попробуйте еще раз.');
        setTimeout(() => {
          setShowVoiceModal(false);
          setIsListening(false);
        }, 2000);
      };
      
      recognitionInstance.onend = () => {
        setIsListening(false);
      };
      
      setRecognition(recognitionInstance);
    }
  };

  const startVoiceRecognition = () => {
    if (recognition) {
      recognition.start();
    } else {
      alert('Голосовое распознавание не поддерживается в вашем браузере');
    }
  };

  const stopVoiceRecognition = () => {
    if (recognition && isListening) {
      recognition.stop();
      setShowVoiceModal(false);
      setIsListening(false);
    }
  };

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
    try {
      const response = await axios.get(`${API}/user-subscription/${currentUser.id}`);
      setUserSubscription(response.data);
      setUserEquipment(response.data.kitchen_equipment || []);
    } catch (error) {
      console.error('Error fetching user subscription:', error);
    }
  };

  const handleUpgradeSubscription = async (planType) => {
    setIsUpgrading(true);
    try {
      const response = await axios.post(`${API}/upgrade-subscription/${currentUser.id}`, {
        subscription_plan: planType
      });
      
      if (response.data.success) {
        await fetchUserSubscription();
        setShowPricingModal(false);
        alert(`Подписка успешно обновлена до ${subscriptionPlans[planType]?.name}!`);
      }
    } catch (error) {
      console.error('Error upgrading subscription:', error);
      alert('Ошибка при обновлении подписки. Попробуйте еще раз.');
    } finally {
      setIsUpgrading(false);
    }
  };

  const handleUpdateKitchenEquipment = async () => {
    try {
      const response = await axios.post(`${API}/update-kitchen-equipment/${currentUser.id}`, {
        equipment_ids: userEquipment
      });
      
      if (response.data.success) {
        setShowEquipmentModal(false);
        alert('Оборудование успешно обновлено!');
      }
    } catch (error) {
      console.error('Error updating kitchen equipment:', error);
      if (error.response?.status === 403) {
        alert('Управление кухонным оборудованием доступно только в PRO подписке');
      } else {
        alert('Ошибка при обновлении оборудования. Попробуйте еще раз.');
      }
    }
  };

  const toggleEquipment = (equipmentId) => {
    setUserEquipment(prev => {
      if (prev.includes(equipmentId)) {
        return prev.filter(id => id !== equipmentId);
      } else {
        return [...prev, equipmentId];
      }
    });
  };

  const canUseFeature = (feature) => {
    if (!userSubscription) return false;
    return userSubscription.plan_info[feature] || false;
  };

  const getRemainingTechCards = () => {
    if (!userSubscription) return 0;
    const limit = userSubscription.plan_info.monthly_tech_cards;
    if (limit === -1) return Infinity;
    return Math.max(0, limit - userSubscription.monthly_tech_cards_used);
  };

  const fetchUserTechCards = async () => {
    try {
      const response = await axios.get(`${API}/tech-cards/${currentUser.id}`);
      setUserTechCards(response.data);
    } catch (error) {
      console.error('Error fetching tech cards:', error);
    }
  };

  const handleRegistration = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/register`, registrationData);
      const user = response.data;
      setCurrentUser(user);
      localStorage.setItem('receptor_user', JSON.stringify(user));
      setShowRegistration(false);
    } catch (error) {
      if (error.response?.status === 400) {
        try {
          const userResponse = await axios.get(`${API}/user/${registrationData.email}`);
          const user = userResponse.data;
          setCurrentUser(user);
          localStorage.setItem('receptor_user', JSON.stringify(user));
          setShowRegistration(false);
        } catch (fetchError) {
          console.error('Error fetching existing user:', fetchError);
        }
      } else {
        console.error('Registration error:', error);
      }
    }
  };

  const handleGenerateTechCard = async (e) => {
    e.preventDefault();
    if (!dishName.trim()) return;

    // Check usage limits
    const remaining = getRemainingTechCards();
    if (remaining <= 0) {
      setShowPricingModal(true);
      return;
    }

    setIsGenerating(true);
    try {
      const response = await axios.post(`${API}/generate-tech-card`, {
        dish_name: dishName,
        user_id: currentUser.id
      });
      
      setTechCard(response.data.tech_card);
      setCurrentTechCardId(response.data.id);
      setDishName('');
      setIsEditing(false);
      parseIngredients(response.data.tech_card);
      fetchUserTechCards();
      
      // Update user subscription data
      if (userSubscription) {
        setUserSubscription(prev => ({
          ...prev,
          monthly_tech_cards_used: response.data.monthly_used
        }));
      }
    } catch (error) {
      console.error('Error generating tech card:', error);
      if (error.response?.status === 403) {
        alert('Достигнут лимит техкарт. Обновите подписку для продолжения.');
        setShowPricingModal(true);
      } else {
        alert('Ошибка при генерации техкарты. Попробуйте еще раз.');
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const handleEditWithAI = async (e) => {
    e.preventDefault();
    if (!editInstruction.trim() || !currentTechCardId) return;

    setIsEditingAI(true);
    try {
      const response = await axios.post(`${API}/edit-tech-card`, {
        tech_card_id: currentTechCardId,
        edit_instruction: editInstruction
      });
      
      setTechCard(response.data.tech_card);
      setEditInstruction('');
      parseIngredients(response.data.tech_card);
      fetchUserTechCards();
    } catch (error) {
      console.error('Error editing tech card:', error);
      alert('Ошибка при редактировании техкарты. Попробуйте еще раз.');
    } finally {
      setIsEditingAI(false);
    }
  };

  const parseIngredients = (techCardContent) => {
    // Parse ingredients directly from tech card content
    const lines = techCardContent.split('\n');
    const ingredients = [];
    const editableIngredients = [];
    let inIngredientsSection = false;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      if (line.includes('Ингредиенты')) {
        inIngredientsSection = true;
        continue;
      }
      
      if (inIngredientsSection && (line.startsWith('**') || line.includes('Пошаговый рецепт'))) {
        break;
      }
      
      if (inIngredientsSection && line.startsWith('- ') && (line.includes(' — ') || line.includes(' - '))) {
        let parts = line.replace('- ', '').split(' — ');
        if (parts.length < 3) {
          parts = line.replace('- ', '').split(' - ');
        }
        
        if (parts.length >= 3) {
          const ingredient = {
            name: parts[0].trim(),
            quantity: parts[1].trim(),
            price: parseFloat(parts[2].replace(/[^\d.,]/g, '').replace(',', '.')) || 0
          };
          
          ingredients.push(ingredient);
          editableIngredients.push({
            id: `ing-${editableIngredients.length}`,
            ...ingredient,
            unit: parts[1].replace(/[0-9\s]/g, '') || 'г'
          });
        }
      }
    }
    
    setIngredients(ingredients);
    setEditableIngredients(editableIngredients);
    
    // Parse steps for interactive editor
    const steps = [];
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line.match(/^\d+\./)) {
        steps.push({
          id: `step-${steps.length}`,
          number: steps.length + 1,
          text: line.replace(/^\d+\.\s*/, '')
        });
      }
    }
    setEditableSteps(steps);

  const addIngredient = () => {
    const newIngredient = {
      id: `ing-${Date.now()}`,
      name: '',
      quantity: '',
      price: 0,
      unit: 'г'
    };
    setEditableIngredients([...editableIngredients, newIngredient]);
  };

  const removeIngredient = (id) => {
    setEditableIngredients(editableIngredients.filter(ing => ing.id !== id));
  };

  const updateIngredient = (id, field, value) => {
    setEditableIngredients(editableIngredients.map(ing => 
      ing.id === id ? { ...ing, [field]: value } : ing
    ));
  };

  const saveIngredientsToTechCard = () => {
    // Calculate total cost
    const totalCost = editableIngredients.reduce((sum, ing) => sum + (parseFloat(ing.price) || 0), 0);
    const recommendedPrice = Math.round(totalCost * 3);
    
    // Update tech card content with new ingredients
    let updatedContent = techCard;
    
    // Create new ingredients section
    const ingredientsSection = editableIngredients.map(ing => 
      `- ${ing.name} — ${ing.quantity} — ~${ing.price} ₽`
    ).join('\n');
    
    // Replace ingredients section
    updatedContent = updatedContent.replace(
      /(Ингредиенты[:\s]*\n)([\s\S]*?)(\n\n.*?(Пошаговый рецепт|Время:|Выход:))/,
      `$1\n${ingredientsSection}$3`
    );
    
    // Update costs
    updatedContent = updatedContent.replace(
      /- По ингредиентам: \d+ ₽/,
      `- По ингредиентам: ${Math.round(totalCost)} ₽`
    );
    updatedContent = updatedContent.replace(
      /- Рекомендуемая цена \(×3\): \d+ ₽/,
      `- Рекомендуемая цена (×3): ${recommendedPrice} ₽`
    );
    
    setTechCard(updatedContent);
    setIsEditingIngredients(false);
    
    // Update ingredients array for manual editor too
    setIngredients(editableIngredients.map(ing => ({
      name: ing.name,
      quantity: ing.quantity,
      price: ing.price
    })));
  };

  const addStep = () => {
    const newStep = {
      id: `step-${Date.now()}`,
      number: editableSteps.length + 1,
      text: ''
    };
    setEditableSteps([...editableSteps, newStep]);
  };

  const removeStep = (id) => {
    const filtered = editableSteps.filter(step => step.id !== id);
    // Renumber steps
    const renumbered = filtered.map((step, index) => ({
      ...step,
      number: index + 1
    }));
    setEditableSteps(renumbered);
  };

  const updateStep = (id, text) => {
    setEditableSteps(editableSteps.map(step => 
      step.id === id ? { ...step, text } : step
    ));
  };

  const moveStep = (id, direction) => {
    const currentIndex = editableSteps.findIndex(step => step.id === id);
    if (
      (direction === 'up' && currentIndex === 0) ||
      (direction === 'down' && currentIndex === editableSteps.length - 1)
    ) {
      return;
    }
    
    const newSteps = [...editableSteps];
    const newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
    
    [newSteps[currentIndex], newSteps[newIndex]] = [newSteps[newIndex], newSteps[currentIndex]];
    
    // Renumber steps
    const renumbered = newSteps.map((step, index) => ({
      ...step,
      number: index + 1
    }));
    
    setEditableSteps(renumbered);
  };

  const saveStepsToTechCard = () => {
    let updatedContent = techCard;
    
    // Create new steps section
    const stepsSection = editableSteps.map(step => 
      `${step.number}. ${step.text}`
    ).join('\n\n');
    
    // Replace steps section
    updatedContent = updatedContent.replace(
      /(Пошаговый рецепт[:\s]*\n)([\s\S]*?)(\n\n.*?(Время:|Выход:|Себестоимость:|КБЖУ:))/,
      `$1\n${stepsSection}\n$3`
    );
    
    setTechCard(updatedContent);
    setIsEditingSteps(false);
  };

  const handleIngredientChange = (index, field, value) => {
    const newIngredients = [...ingredients];
    newIngredients[index][field] = value;
    setIngredients(newIngredients);
    updateTechCardWithIngredients(newIngredients);
  };

  const updateTechCardWithIngredients = (newIngredients) => {
    const totalCost = newIngredients.reduce((sum, ing) => sum + (ing.price || 0), 0);
    const recommendedPrice = Math.round(totalCost * 3);
    
    let updatedContent = techCard;
    
    const ingredientsSection = newIngredients.map(ing => 
      `- ${ing.name} — ${ing.quantity} — ~${ing.price} ₽`
    ).join('\n');
    
    updatedContent = updatedContent.replace(
      /(\*\*Ингредиенты:\*\*\n\n)([\s\S]*?)(\n\n\*\*Пошаговый рецепт:\*\*)/,
      `$1${ingredientsSection}$3`
    );
    
    updatedContent = updatedContent.replace(
      /- По ингредиентам: \d+ ₽/,
      `- По ингредиентам: ${Math.round(totalCost)} ₽`
    );
    updatedContent = updatedContent.replace(
      /- Рекомендуемая цена \(×3\): \d+ ₽/,
      `- Рекомендуемая цена (×3): ${recommendedPrice} ₽`
    );
    
    setTechCard(updatedContent);
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('receptor_user');
    setTechCard(null);
    setUserTechCards([]);
    setIsEditing(false);
    setCurrentTechCardId(null);
    setIngredients([]);
  };

  const handleSelectTechCard = (card) => {
    setTechCard(card.content);
    setCurrentTechCardId(card.id);
    setIsEditing(false);
    parseIngredients(card.content);
  };

  const handlePrintTechCard = () => {
    const dishName = techCard.split('\n')[0].replace(/\*\*/g, '').replace('Название:', '').trim();
    const printWindow = window.open('', '_blank');
    
    // Process content to create ingredients table
    const lines = techCard.split('\n');
    let processedContent = '';
    let inIngredientsSection = false;
    let ingredientRows = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      if (line.includes('Ингредиенты')) {
        inIngredientsSection = true;
        processedContent += `<h2 style="color: #1A1B23; font-size: 18px; font-weight: 800; margin-top: 25px; margin-bottom: 15px; border-bottom: 2px solid #C084FC; padding-bottom: 8px;">ИНГРЕДИЕНТЫ</h2>`;
        
        // Collect ingredient lines
        for (let j = i + 1; j < lines.length; j++) {
          const nextLine = lines[j];
          if (nextLine.startsWith('**') || nextLine.includes('Пошаговый рецепт') || nextLine.includes('Время:')) break;
          if (nextLine.startsWith('- ') && nextLine.includes(' — ')) {
            const parts = nextLine.replace('- ', '').split(' — ');
            if (parts.length >= 3) {
              ingredientRows.push({
                name: parts[0].trim(),
                quantity: parts[1].trim(),
                price: parts[2].trim()
              });
            }
          }
        }
        
        // Create ingredients table
        if (ingredientRows.length > 0) {
          processedContent += `
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0; border: 2px solid #8B5CF6; border-radius: 8px;">
              <thead>
                <tr style="background: linear-gradient(135deg, #8B5CF6, #C084FC);">
                  <th style="color: white; font-weight: 800; font-size: 12px; text-transform: uppercase; padding: 12px; text-align: left;">ИНГРЕДИЕНТ</th>
                  <th style="color: white; font-weight: 800; font-size: 12px; text-transform: uppercase; padding: 12px; text-align: center;">КОЛИЧЕСТВО</th>
                  <th style="color: white; font-weight: 800; font-size: 12px; text-transform: uppercase; padding: 12px; text-align: right;">ЦЕНА</th>
                </tr>
              </thead>
              <tbody>
                ${ingredientRows.map(ing => `
                  <tr>
                    <td style="padding: 10px 12px; border-bottom: 1px solid #C084FC; font-weight: 500;">${ing.name}</td>
                    <td style="padding: 10px 12px; border-bottom: 1px solid #C084FC; text-align: center;">${ing.quantity}</td>
                    <td style="padding: 10px 12px; border-bottom: 1px solid #C084FC; text-align: right; font-weight: bold;">${ing.price}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          `;
        }
        
        continue;
      }
      
      // Skip ingredient lines as they're already processed
      if (inIngredientsSection && line.startsWith('- ') && line.includes(' — ')) {
        continue;
      }
      
      if (line.startsWith('**') && !line.includes('Ингредиенты')) {
        inIngredientsSection = false;
      }
      
      // Process other content
      processedContent += formatTechCardForPrint([line]).join('');
    }
    
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
            h1 { 
              color: #8B5CF6; 
              font-size: 28px; 
              font-weight: 900;
              text-transform: uppercase;
              letter-spacing: 1.5px;
              text-align: center; 
              margin-bottom: 30px; 
              border-bottom: 3px solid #8B5CF6;
              padding-bottom: 15px;
            }
            h2 { 
              color: #1A1B23; 
              font-size: 18px; 
              font-weight: 800;
              text-transform: uppercase;
              letter-spacing: 0.8px;
              margin-top: 25px; 
              margin-bottom: 15px; 
              border-bottom: 2px solid #C084FC; 
              padding-bottom: 8px; 
            }
            @media print {
              body { margin: 20px; }
            }
          </style>
        </head>
        <body>
          <h1>ТЕХНОЛОГИЧЕСКАЯ КАРТА</h1>
          <div>${processedContent}</div>
          <div style="margin-top: 30px; text-align: center; font-size: 12px; color: #64748B;">
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

  const formatTechCardForPrint = (content) => {
    return content.split('\n').map(line => {
      // Remove all ** formatting
      let cleanLine = line.replace(/\*\*/g, '');
      
      // Format section headers
      if (line.startsWith('**') && line.endsWith('**')) {
        const title = cleanLine.replace(':', '').trim();
        if (title.includes('Название')) {
          const dishName = title.replace('Название', '').trim();
          return `<h1 style="color: #8B5CF6; font-size: 28px; font-weight: 900; margin-bottom: 20px;">${dishName}</h1>`;
        }
        return `<h2 style="color: #1A1B23; font-size: 18px; font-weight: 800; margin-top: 25px; margin-bottom: 15px; border-bottom: 2px solid #C084FC; padding-bottom: 8px;">${title}</h2>`;
      }
      
      // Format ingredients section
      if (cleanLine.trim() === 'Ингредиенты') {
        return `<h2 style="color: #1A1B23; font-size: 18px; font-weight: 800; margin-top: 25px; margin-bottom: 15px; border-bottom: 2px solid #C084FC; padding-bottom: 8px;">ИНГРЕДИЕНТЫ</h2>`;
      }
      
      // Format ingredient items as table rows
      if (line.startsWith('- ') && line.includes(' — ')) {
        const parts = line.replace('- ', '').split(' — ');
        if (parts.length >= 3) {
          return `<tr><td style="padding: 8px; border-bottom: 1px solid #C084FC; font-weight: 500;">${parts[0].trim()}</td><td style="padding: 8px; border-bottom: 1px solid #C084FC; text-align: center;">${parts[1].trim()}</td><td style="padding: 8px; border-bottom: 1px solid #C084FC; text-align: right; font-weight: bold;">${parts[2].trim()}</td></tr>`;
        }
      }
      
      // Format cost information
      if (line.includes('Себестоимость:') || line.includes('Рекомендуемая цена') || line.includes('По ингредиентам:')) {
        return `<div style="background: #F0FDF4; border: 2px solid #10B981; border-radius: 8px; padding: 15px; margin: 15px 0; font-weight: 700;">${cleanLine}</div>`;
      }
      
      // Format КБЖУ information
      if (line.includes('КБЖУ') || line.includes('Калории')) {
        return `<div style="background: #EFF6FF; border: 2px solid #3B82F6; border-radius: 8px; padding: 15px; margin: 15px 0; font-weight: 700;">${cleanLine}</div>`;
      }
      
      // Format numbered steps
      if (line.match(/^\d+\./)) {
        return `<div style="background: #F8FAFC; border-left: 4px solid #8B5CF6; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">${cleanLine}</div>`;
      }
      
      // Format tips and advice
      if (line.includes('Совет от RECEPTOR') || line.includes('Фишка для продвинутых') || line.includes('Вариации')) {
        const tipLine = cleanLine.replace(/💡|🔥|🌀/g, '').trim();
        return `<div style="background: #F3E8FF; border: 2px solid #C084FC; border-radius: 8px; padding: 12px; margin: 10px 0; font-style: italic;">${tipLine}</div>`;
      }
      
      // Format regular list items
      if (line.startsWith('- ') && !line.includes(' — ')) {
        return `<p style="margin-left: 20px; margin-bottom: 8px;">• ${cleanLine.replace('- ', '')}</p>`;
      }
      
      // Format regular paragraphs
      if (cleanLine.trim() && !cleanLine.startsWith('─')) {
        return `<p style="margin-bottom: 12px; line-height: 1.6;">${cleanLine}</p>`;
      }
      
      return '';
    }).join('');
  };

  const formatTechCard = (content) => { // FIXED version
    const lines = content.split('\n');
    const result = [];
    
    for (let index = 0; index < lines.length; index++) {
      const line = lines[index].trim();
      
      // Main title - FIXED to show dish name
      if (line.startsWith('**') && line.endsWith('**') && line.includes('Название')) {
        const title = line.replace(/\*\*/g, '').replace('Название:', '').trim();
        if (title) {
          result.push(
            <div key={index} className="fade-in-scale mb-8">
              <div className="tech-card-title text-center">
                {title}
              </div>
            </div>
          );
        }
        continue;
      }
      
      // Section headers - clean format without stars
      if (line.startsWith('**') && line.endsWith('**')) {
        const title = line.replace(/\*\*/g, '').replace(':', '').trim();
        result.push(
          <div key={index} className="tech-card-section slide-in-bottom">
            {title}
          </div>
        );
        continue;
      }
      
      // Ingredients section - CRITICAL FIX
      if (line === 'Ингредиенты' || line.includes('Ингредиенты')) {
        // Find all ingredient lines after this header
        const ingredientLines = [];
        let nextIndex = index + 1;
        
        while (nextIndex < lines.length) {
          const nextLine = lines[nextIndex].trim();
          
          // Stop at next section header
          if (nextLine.startsWith('**') || 
              nextLine.includes('Пошаговый рецепт') || 
              nextLine.includes('Время:') ||
              nextLine.includes('Выход:')) {
            break;
          }
          
          // Collect ingredient lines
          if (nextLine.startsWith('- ') && nextLine.includes(' — ')) {
            ingredientLines.push(nextLine);
          }
          
          nextIndex++;
        }
        
        console.log('Found ingredients:', ingredientLines); // Debug
        
        if (ingredientLines.length > 0) {
          const tableRows = ingredientLines.map((ingLine, ingIndex) => {
            const parts = ingLine.replace('- ', '').split(' — ');
            if (parts.length >= 3) {
              return (
                <tr key={`ing-${ingIndex}`} className="slide-in-bottom" style={{animationDelay: `${ingIndex * 0.1}s`}}>
                  <td className="font-semibold text-purple-200 py-3 px-4 border-b border-purple-400/30">{parts[0].trim()}</td>
                  <td className="text-center text-gray-300 py-3 px-4 border-b border-purple-400/30">{parts[1].trim()}</td>
                  <td className="text-right font-bold text-green-300 py-3 px-4 border-b border-purple-400/30">{parts[2].trim()}</td>
                </tr>
              );
            }
            return null;
          }).filter(Boolean);
          
          result.push(
            <div key={index} className="my-8 slide-in-right">
              <div className="tech-card-section mb-4">ИНГРЕДИЕНТЫ</div>
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
                    {tableRows}
                  </tbody>
                </table>
              </div>
            </div>
          );
        } else {
          // Fallback if no ingredients found in table format
          result.push(
            <div key={index} className="tech-card-section slide-in-bottom">
              ИНГРЕДИЕНТЫ
            </div>
          );
        }
        continue;
      }
      
      // Skip ingredient lines that are already rendered in table
      if (line.startsWith('- ') && line.includes(' — ')) {
        // Check if we're in ingredients section
        const previousLines = lines.slice(0, index);
        const hasIngredientHeader = previousLines.some(l => 
          l.includes('Ингредиенты') && !l.includes('Пошаговый рецепт')
        );
        const hasNextSection = lines.slice(index).some(l => 
          l.startsWith('**') || l.includes('Пошаговый рецепт') || l.includes('Время:')
        );
        
        if (hasIngredientHeader && !hasNextSection) {
          continue; // Skip as it's already rendered in table
        }
      }
      
      // Cost information with better formatting
      if (line.includes('Себестоимость') || line.includes('Рекомендуемая цена') || line.includes('По ингредиентам')) {
        result.push(
          <div key={index} className="cost-highlight slide-in-left my-4">
            <div className="font-bold text-lg text-green-100 bg-green-900/20 p-4 rounded-lg border border-green-500/30">
              {line}
            </div>
          </div>
        );
        continue;
      }
      
      // КБЖУ information
      if (line.includes('КБЖУ') || line.includes('Калории')) {
        result.push(
          <div key={index} className="mb-6">
            <div className="font-bold text-blue-200 bg-blue-900/20 p-3 rounded-lg border border-blue-500/30">{line}</div>
          </div>
        );
        continue;
      }
      
      // Tips and advice - clean format
      if (line.includes('Совет от RECEPTOR') || line.includes('Фишка для продвинутых') || line.includes('Вариации')) {
        const cleanLine = line.replace(/💡|🔥|🌀|\*/g, '').trim();
        result.push(
          <div key={index} className="tip-box slide-in-bottom my-4">
            <div className="font-semibold text-purple-100 bg-purple-900/20 p-3 rounded-lg border border-purple-500/30">{cleanLine}</div>
          </div>
        );
        continue;
      }
      
      // Regular list items
      if (line.startsWith('- ') && !line.includes(' — ')) {
        result.push(
          <div key={index} className="ml-6 mb-2 text-gray-300 font-medium flex items-start">
            <span className="text-purple-400 mr-2 mt-1">•</span>
            <span>{line.replace('- ', '')}</span>
          </div>
        );
        continue;
      }
      
      // Numbered steps with better styling
      if (line.match(/^\d+\./)) {
        result.push(
          <div key={index} className="step-card slide-in-bottom mb-4" style={{animationDelay: `${index * 0.05}s`}}>
            <div className="font-medium text-gray-200 leading-relaxed bg-gray-800/50 p-4 rounded-lg border-l-4 border-purple-500">
              {line}
            </div>
          </div>
        );
        continue;
      }
      
      // Regular paragraphs
      if (line && !line.startsWith('**') && !line.startsWith('─') && line !== '') {
        result.push(
          <div key={index} className="mb-3 text-gray-300 font-medium leading-relaxed">
            {line}
          </div>
        );
        continue;
      }
    }
    
    return result.filter(Boolean);
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-20 w-72 h-72 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full filter blur-3xl"></div>
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full filter blur-3xl"></div>
        </div>
        
        <div className="relative z-10 flex items-center justify-center min-h-screen p-4">
          <div className="max-w-md w-full">
            <div className="text-center mb-12 slide-in-bottom">
              <div className="mb-8">
                <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl flex items-center justify-center pulse-glow">
                  <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center">
                    <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg"></div>
                  </div>
                </div>
              </div>
              <h1 className="heading-main slide-in-left">
                RECEPTOR
              </h1>
              <p className="text-selling mb-4 slide-in-right">
                AI-ПОМОЩНИК ДЛЯ ШЕФ-ПОВАРОВ
              </p>
              <p className="text-subtitle slide-in-bottom">
                Создавайте профессиональные технологические карты за секунды
              </p>
              
              {/* Selling Points */}
              <div className="mt-8 space-y-3">
                <div className="selling-point slide-in-left" style={{animationDelay: '0.2s'}}>
                  ЭКОНОМЬТЕ 2 ЧАСА НА КАЖДОЙ ТЕХКАРТЕ
                </div>
                <div className="selling-point slide-in-left" style={{animationDelay: '0.4s'}}>
                  ТОЧНЫЕ РАСЧЕТЫ ДО КОПЕЙКИ
                </div>
                <div className="selling-point slide-in-left" style={{animationDelay: '0.6s'}}>
                  ОТ ИДЕИ ДО ТЕХКАРТЫ ЗА 30 СЕКУНД
                </div>
              </div>
            </div>

            {!showRegistration ? (
              <div className="card-glass p-8 slide-in-bottom">
                <h2 className="heading-section text-center mb-8">
                  ДОБРО ПОЖАЛОВАТЬ!
                </h2>
                <button
                  onClick={() => setShowRegistration(true)}
                  className="w-full btn-primary"
                >
                  НАЧАТЬ РАБОТУ
                </button>
              </div>
            ) : (
              <div className="card-glass p-8 slide-in-scale">
                <h2 className="heading-section text-center mb-8">
                  РЕГИСТРАЦИЯ
                </h2>
                <form onSubmit={handleRegistration} className="space-y-6">
                  <div>
                    <label className="block text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
                      EMAIL
                    </label>
                    <input
                      type="email"
                      value={registrationData.email}
                      onChange={(e) => setRegistrationData({...registrationData, email: e.target.value})}
                      className="w-full input-modern"
                      placeholder="ваш@email.com"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
                      ИМЯ
                    </label>
                    <input
                      type="text"
                      value={registrationData.name}
                      onChange={(e) => setRegistrationData({...registrationData, name: e.target.value})}
                      className="w-full input-modern"
                      placeholder="Имя Фамилия"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
                      ГОРОД
                    </label>
                    <select
                      value={registrationData.city}
                      onChange={(e) => setRegistrationData({...registrationData, city: e.target.value})}
                      className="w-full input-modern"
                      required
                    >
                      <option value="">Выберите город</option>
                      {cities.map(city => (
                        <option key={city.code} value={city.code}>
                          {city.name} {city.coefficient !== 1.0 && `(${city.coefficient}x)`}
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    type="submit"
                    className="w-full btn-primary"
                  >
                    ЗАРЕГИСТРИРОВАТЬСЯ
                  </button>
                </form>
                <button
                  onClick={() => setShowRegistration(false)}
                  className="w-full mt-4 text-purple-300 hover:text-purple-200 text-sm font-semibold uppercase tracking-wide"
                >
                  НАЗАД
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute top-10 left-10 w-96 h-96 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full filter blur-3xl"></div>
        <div className="absolute bottom-10 right-10 w-96 h-96 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full filter blur-3xl"></div>
      </div>

      {/* Voice Recognition Modal */}
      {showVoiceModal && (
        <div className="voice-status fade-in-scale">
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-purple-300 mb-4">ГОЛОСОВОЙ ВВОД</h3>
            <p className="text-gray-300 mb-4">{voiceStatus}</p>
            <div className="voice-waves">
              <div className="voice-wave"></div>
              <div className="voice-wave"></div>
              <div className="voice-wave"></div>
              <div className="voice-wave"></div>
              <div className="voice-wave"></div>
            </div>
            <button
              onClick={stopVoiceRecognition}
              className="btn-secondary mt-4"
            >
              ОСТАНОВИТЬ
            </button>
          </div>
        </div>
      )}

      <header className="relative z-10 card-glass border-0 border-b border-purple-400/30 rounded-none">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center slide-in-left">
              <h1 className="heading-card text-3xl">RECEPTOR</h1>
              <span className="ml-4 text-purple-300 font-semibold uppercase tracking-wide">AI для шеф-поваров</span>
            </div>
            <div className="flex items-center space-x-6 slide-in-right">
              <div className="text-right">
                <div className="text-gray-300 font-medium">
                  <span className="text-purple-300 font-bold">{currentUser.name}</span>
                  <span className="text-gray-400 ml-2">
                    ({cities.find(c => c.code === currentUser.city)?.name})
                  </span>
                </div>
                {userSubscription && (
                  <div className="text-sm">
                    <span className={`font-bold ${
                      userSubscription.subscription_plan === 'free' ? 'text-gray-400' :
                      userSubscription.subscription_plan === 'starter' ? 'text-blue-400' :
                      userSubscription.subscription_plan === 'pro' ? 'text-purple-400' :
                      'text-yellow-400'
                    }`}>
                      {userSubscription.plan_info.name}
                    </span>
                    {userSubscription.plan_info.monthly_tech_cards !== -1 && (
                      <span className="text-gray-400 ml-2">
                        ({userSubscription.monthly_tech_cards_used}/{userSubscription.plan_info.monthly_tech_cards})
                      </span>
                    )}
                  </div>
                )}
              </div>
              <button
                onClick={() => setShowPricingModal(true)}
                className="text-purple-300 hover:text-purple-200 font-semibold uppercase tracking-wide transition-all duration-300"
              >
                ПОДПИСКА
              </button>
              <button
                onClick={handleLogout}
                className="text-purple-300 hover:text-purple-200 font-semibold uppercase tracking-wide transition-all duration-300"
              >
                ВЫЙТИ
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 xl:grid-cols-4 lg:grid-cols-3 gap-6 lg:gap-10">
          {/* Left Panel - Controls */}
          <div className="xl:col-span-1 lg:col-span-1 slide-in-left space-y-8">
            <div className="card-glass p-6 lg:p-8">
              <h2 className="heading-card mb-6">
                СОЗДАТЬ ТЕХКАРТУ
              </h2>
              <form onSubmit={handleGenerateTechCard} className="space-y-6">
                <div>
                  <label className="block text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
                    НАЗВАНИЕ БЛЮДА
                  </label>
                  <div className="voice-input-container">
                    <textarea
                      value={dishName}
                      onChange={(e) => setDishName(e.target.value)}
                      placeholder="Опишите блюдо подробно. Например: Стейк из говядины с картофельным пюре и соусом из белых грибов"
                      className="input-modern min-h-[120px] resize-none"
                      rows={5}
                      required
                    />
                    <button
                      type="button"
                      onClick={startVoiceRecognition}
                      className={`btn-voice ${isListening ? 'recording' : ''}`}
                      title="Голосовой ввод"
                    >
                      <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={isGenerating}
                  className={`w-full btn-primary ${isGenerating ? 'loading-pulse' : ''}`}
                >
                  {isGenerating ? 'ГЕНЕРИРУЕТСЯ...' : 'СОЗДАТЬ ТЕХКАРТУ'}
                </button>
                
                {/* Usage Limits Display */}
                {userSubscription && userSubscription.plan_info.monthly_tech_cards !== -1 && (
                  <div className="mt-4 p-3 bg-gray-800/50 rounded-lg">
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-400">Использовано в этом месяце:</span>
                      <span className={`font-bold ${
                        getRemainingTechCards() <= 3 ? 'text-red-400' : 'text-green-400'
                      }`}>
                        {userSubscription.monthly_tech_cards_used}/{userSubscription.plan_info.monthly_tech_cards}
                      </span>
                    </div>
                    {getRemainingTechCards() <= 3 && getRemainingTechCards() > 0 && (
                      <div className="mt-2 text-yellow-400 text-xs">
                        Осталось {getRemainingTechCards()} техкарт
                      </div>
                    )}
                    {getRemainingTechCards() <= 0 && (
                      <button
                        onClick={() => setShowPricingModal(true)}
                        className="w-full mt-2 btn-primary"
                      >
                        ОБНОВИТЬ ПОДПИСКУ
                      </button>
                    )}
                  </div>
                )}
              </form>

              {/* AI Editing */}
              {techCard && (
                <div className="mt-8 border-t border-purple-400/30 pt-8 slide-in-bottom">
                  <h3 className="heading-card text-lg mb-6">
                    РЕДАКТИРОВАТЬ ЧЕРЕЗ AI
                  </h3>
                  <form onSubmit={handleEditWithAI} className="space-y-4">
                    <textarea
                      value={editInstruction}
                      onChange={(e) => setEditInstruction(e.target.value)}
                      placeholder="Детально опишите что изменить. Например: увеличить порцию в 2 раза, заменить картофель на рис, добавить 100г сливочного масла"
                      className="w-full input-modern min-h-[100px] resize-none"
                      rows={4}
                    />
                    <button
                      type="submit"
                      disabled={isEditingAI || !editInstruction.trim()}
                      className={`w-full btn-secondary ${isEditingAI ? 'loading-pulse' : ''}`}
                    >
                      {isEditingAI ? 'РЕДАКТИРУЕТСЯ...' : 'ИЗМЕНИТЬ ЧЕРЕЗ AI'}
                    </button>
                  </form>
                  
                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    className="w-full mt-4 btn-secondary"
                  >
                    {isEditing ? 'ЗАКРЫТЬ РЕДАКТОР' : 'РУЧНОЕ РЕДАКТИРОВАНИЕ'}
                  </button>
                </div>
              )}

              {/* Kitchen Equipment - PRO Feature */}
              {userSubscription && canUseFeature('kitchen_equipment') && (
                <div className="mt-8 border-t border-purple-400/30 pt-8 slide-in-bottom">
                  <h3 className="heading-card text-lg mb-6">
                    КУХОННОЕ ОБОРУДОВАНИЕ
                    <span className="text-xs ml-2 px-2 py-1 bg-purple-600 text-white rounded-full">PRO</span>
                  </h3>
                  <p className="text-gray-400 text-sm mb-4">
                    Адаптация рецептов под ваше оборудование
                  </p>
                  <button
                    onClick={() => setShowEquipmentModal(true)}
                    className="w-full btn-secondary"
                  >
                    НАСТРОИТЬ ОБОРУДОВАНИЕ ({userEquipment.length})
                  </button>
                </div>
              )}

              {/* Manual Editing */}
              {isEditing && ingredients.length > 0 && (
                <div className="mt-8 border-t border-purple-400/30 pt-8 slide-in-bottom">
                  <h3 className="heading-card text-lg mb-6">
                    РЕДАКТИРОВАТЬ ИНГРЕДИЕНТЫ
                  </h3>
                  <div className="space-y-4 max-h-80 overflow-y-auto">
                    {ingredients.map((ingredient, index) => (
                      <div key={index} className="card-glass p-4">
                        <div className="text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
                          {ingredient.name}
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <input
                            type="text"
                            value={ingredient.quantity}
                            onChange={(e) => handleIngredientChange(index, 'quantity', e.target.value)}
                            className="input-modern text-sm"
                            placeholder="Количество"
                          />
                          <input
                            type="number"
                            value={ingredient.price}
                            onChange={(e) => handleIngredientChange(index, 'price', parseFloat(e.target.value) || 0)}
                            className="input-modern text-sm"
                            placeholder="Цена ₽"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Center Panel - Main Content */}
          <div className="xl:col-span-3 lg:col-span-2 slide-in-right">
            {techCard ? (
              <div className="tech-card-container">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
                  <h2 className="heading-section text-xl sm:text-2xl">
                    ТЕХНОЛОГИЧЕСКАЯ КАРТА
                  </h2>
                  <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4 w-full sm:w-auto">
                    <button 
                      onClick={() => navigator.clipboard.writeText(techCard)}
                      className="btn-secondary text-sm px-4 py-2"
                    >
                      КОПИРОВАТЬ
                    </button>
                    <button 
                      onClick={handlePrintTechCard}
                      className="btn-success text-sm px-4 py-2"
                    >
                      ЭКСПОРТ В PDF
                    </button>
                  </div>
                </div>
                <div className="tech-card-content">
                  {formatTechCard(techCard)}
                  
                  {/* Interactive Ingredients Editor */}
                  {editableIngredients.length > 0 && (
                    <div className="mt-8 bg-gray-800/50 rounded-lg p-6">
                      <div className="flex justify-between items-center mb-6">
                        <h3 className="heading-card text-xl">
                          ИНТЕРАКТИВНЫЙ РЕДАКТОР ИНГРЕДИЕНТОВ
                        </h3>
                        <button
                          onClick={() => setIsEditingIngredients(!isEditingIngredients)}
                          className={`px-4 py-2 rounded-lg font-bold transition-all ${
                            isEditingIngredients 
                              ? 'bg-green-600 hover:bg-green-700 text-white'
                              : 'bg-purple-600 hover:bg-purple-700 text-white'
                          }`}
                        >
                          {isEditingIngredients ? 'СОХРАНИТЬ ИЗМЕНЕНИЯ' : 'РЕДАКТИРОВАТЬ'}
                        </button>
                      </div>
                      
                      {isEditingIngredients ? (
                        <div className="space-y-4">
                          <div className="overflow-x-auto">
                            <table className="w-full border-collapse bg-gray-900/50 rounded-lg overflow-hidden">
                              <thead>
                                <tr className="bg-gradient-to-r from-purple-600 to-purple-700">
                                  <th className="text-left py-3 px-4 text-white font-bold text-sm">ИНГРЕДИЕНТ</th>
                                  <th className="text-center py-3 px-4 text-white font-bold text-sm">КОЛИЧЕСТВО</th>
                                  <th className="text-center py-3 px-4 text-white font-bold text-sm">ЦЕНА (₽)</th>
                                  <th className="text-center py-3 px-4 text-white font-bold text-sm">ДЕЙСТВИЯ</th>
                                </tr>
                              </thead>
                              <tbody>
                                {editableIngredients.map((ingredient, index) => (
                                  <tr key={ingredient.id} className="border-b border-gray-700 hover:bg-gray-800/50">
                                    <td className="py-3 px-4">
                                      <input
                                        type="text"
                                        value={ingredient.name}
                                        onChange={(e) => updateIngredient(ingredient.id, 'name', e.target.value)}
                                        className="w-full bg-gray-700 text-white px-3 py-2 rounded border-0 focus:ring-2 focus:ring-purple-500"
                                        placeholder="Название ингредиента"
                                      />
                                    </td>
                                    <td className="py-3 px-4">
                                      <input
                                        type="text"
                                        value={ingredient.quantity}
                                        onChange={(e) => updateIngredient(ingredient.id, 'quantity', e.target.value)}
                                        className="w-full bg-gray-700 text-white px-3 py-2 rounded border-0 focus:ring-2 focus:ring-purple-500 text-center"
                                        placeholder="100 г"
                                      />
                                    </td>
                                    <td className="py-3 px-4">
                                      <input
                                        type="number"
                                        value={ingredient.price}
                                        onChange={(e) => updateIngredient(ingredient.id, 'price', parseFloat(e.target.value) || 0)}
                                        className="w-full bg-gray-700 text-white px-3 py-2 rounded border-0 focus:ring-2 focus:ring-purple-500 text-center"
                                        placeholder="0"
                                        step="0.01"
                                      />
                                    </td>
                                    <td className="py-3 px-4 text-center">
                                      <button
                                        onClick={() => removeIngredient(ingredient.id)}
                                        className="text-red-400 hover:text-red-300 font-bold text-lg px-2"
                                        title="Удалить ингредиент"
                                      >
                                        ×
                                      </button>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                          
                          <div className="flex justify-between items-center">
                            <button
                              onClick={addIngredient}
                              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-bold"
                            >
                              + ДОБАВИТЬ ИНГРЕДИЕНТ
                            </button>
                            
                            <div className="text-right">
                              <div className="text-sm text-gray-400">Общая стоимость:</div>
                              <div className="text-xl font-bold text-green-400">
                                {editableIngredients.reduce((sum, ing) => sum + (parseFloat(ing.price) || 0), 0).toFixed(2)} ₽
                              </div>
                              <div className="text-sm text-purple-400">
                                Рекомендуемая цена: {(editableIngredients.reduce((sum, ing) => sum + (parseFloat(ing.price) || 0), 0) * 3).toFixed(2)} ₽
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex space-x-4">
                            <button
                              onClick={saveIngredientsToTechCard}
                              className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-bold"
                            >
                              ПРИМЕНИТЬ ИЗМЕНЕНИЯ
                            </button>
                            <button
                              onClick={() => setIsEditingIngredients(false)}
                              className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-bold"
                            >
                              ОТМЕНА
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="text-gray-400 text-center py-8">
                          Нажмите "РЕДАКТИРОВАТЬ" чтобы изменить ингредиенты
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* Interactive Steps Editor */}
                  {editableSteps.length > 0 && (
                    <div className="mt-8 bg-gray-800/50 rounded-lg p-6">
                      <div className="flex justify-between items-center mb-6">
                        <h3 className="heading-card text-xl">
                          РЕДАКТОР ЭТАПОВ ПРИГОТОВЛЕНИЯ
                        </h3>
                        <button
                          onClick={() => setIsEditingSteps(!isEditingSteps)}
                          className={`px-4 py-2 rounded-lg font-bold transition-all ${
                            isEditingSteps 
                              ? 'bg-green-600 hover:bg-green-700 text-white'
                              : 'bg-purple-600 hover:bg-purple-700 text-white'
                          }`}
                        >
                          {isEditingSteps ? 'СОХРАНИТЬ ЭТАПЫ' : 'РЕДАКТИРОВАТЬ ЭТАПЫ'}
                        </button>
                      </div>
                      
                      {isEditingSteps ? (
                        <div className="space-y-4">
                          {editableSteps.map((step, index) => (
                            <div key={step.id} className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                              <div className="flex items-start space-x-4">
                                <div className="bg-purple-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold text-sm flex-shrink-0 mt-1">
                                  {step.number}
                                </div>
                                
                                <textarea
                                  value={step.text}
                                  onChange={(e) => updateStep(step.id, e.target.value)}
                                  className="flex-1 bg-gray-700 text-white px-3 py-2 rounded border-0 focus:ring-2 focus:ring-purple-500 min-h-[80px] resize-none"
                                  placeholder="Описание этапа приготовления..."
                                />
                                
                                <div className="flex flex-col space-y-2 flex-shrink-0">
                                  <button
                                    onClick={() => moveStep(step.id, 'up')}
                                    disabled={index === 0}
                                    className={`p-1 rounded ${
                                      index === 0 
                                        ? 'text-gray-600 cursor-not-allowed' 
                                        : 'text-blue-400 hover:text-blue-300'
                                    }`}
                                    title="Переместить вверх"
                                  >
                                    ↑
                                  </button>
                                  <button
                                    onClick={() => moveStep(step.id, 'down')}
                                    disabled={index === editableSteps.length - 1}
                                    className={`p-1 rounded ${
                                      index === editableSteps.length - 1 
                                        ? 'text-gray-600 cursor-not-allowed' 
                                        : 'text-blue-400 hover:text-blue-300'
                                    }`}
                                    title="Переместить вниз"
                                  >
                                    ↓
                                  </button>
                                  <button
                                    onClick={() => removeStep(step.id)}
                                    className="text-red-400 hover:text-red-300 p-1"
                                    title="Удалить этап"
                                  >
                                    ×
                                  </button>
                                </div>
                              </div>
                            </div>
                          ))}
                          
                          <div className="flex justify-between items-center pt-4">
                            <button
                              onClick={addStep}
                              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-bold"
                            >
                              + ДОБАВИТЬ ЭТАП
                            </button>
                            
                            <div className="flex space-x-4">
                              <button
                                onClick={saveStepsToTechCard}
                                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-bold"
                              >
                                ПРИМЕНИТЬ ИЗМЕНЕНИЯ
                              </button>
                              <button
                                onClick={() => setIsEditingSteps(false)}
                                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-bold"
                              >
                                ОТМЕНА
                              </button>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="text-gray-400 text-center py-8">
                          Нажмите "РЕДАКТИРОВАТЬ ЭТАПЫ" чтобы изменить последовательность приготовления
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="card-glass p-12 text-center slide-in-scale">
                <div className="mb-8">
                  <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-purple-400/30 to-pink-500/30 rounded-2xl flex items-center justify-center border-2 border-purple-400/30">
                    <svg className="w-12 h-12 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                </div>
                <h3 className="heading-card text-2xl mb-4">
                  ТЕХКАРТА ПОЯВИТСЯ ЗДЕСЬ
                </h3>
                <p className="text-subtitle">
                  Введите название блюда слева и нажмите <span className="text-purple-300 font-bold">"СОЗДАТЬ ТЕХКАРТУ"</span>
                </p>
                <div className="mt-8">
                  <div className="selling-point">
                    ПОПРОБУЙТЕ ГОЛОСОВОЙ ВВОД!
                  </div>
                </div>
              </div>
            )}

            {/* Collapsible History */}
            <div className="mt-10 slide-in-bottom">
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="w-full flex justify-between items-center p-4 bg-gray-800/50 rounded-lg hover:bg-gray-800/70 transition-all"
              >
                <h3 className="heading-card text-lg">
                  ИСТОРИЯ ({userTechCards.length})
                </h3>
                <svg 
                  className={`w-5 h-5 transition-transform ${showHistory ? 'rotate-180' : ''}`} 
                  fill="currentColor" 
                  viewBox="0 0 20 20"
                >
                  <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
              
              {showHistory && (
                <div className="mt-4 space-y-3 max-h-96 overflow-y-auto">
                  {userTechCards
                    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                    .slice(0, 20)
                    .map((card, index) => (
                    <div
                      key={card.id}
                      onClick={() => handleSelectTechCard(card)}
                      className={`history-item ${currentTechCardId === card.id ? 'active' : ''}`}
                      style={{animationDelay: `${index * 0.1}s`}}
                    >
                      <div className="font-bold text-purple-300 text-sm uppercase tracking-wide">
                        {card.dish_name}
                      </div>
                      <div className="text-gray-400 text-xs font-medium">
                        {new Date(card.created_at).toLocaleDateString('ru-RU')}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Pricing Modal */}
      {showPricingModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-8">
              <h2 className="heading-section text-2xl">ВЫБЕРИТЕ ТАРИФ</h2>
              <button
                onClick={() => setShowPricingModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {Object.entries(subscriptionPlans).map(([planKey, plan]) => (
                <div
                  key={planKey}
                  className={`card-glass p-6 text-center ${
                    userSubscription?.subscription_plan === planKey 
                      ? 'border-2 border-purple-500' 
                      : 'hover:border-purple-400/50'
                  }`}
                >
                  <h3 className="heading-card text-xl mb-4">
                    {plan.name}
                    {planKey === 'pro' && <span className="text-xs ml-2 px-2 py-1 bg-purple-600 text-white rounded-full">ПОПУЛЯРНЫЙ</span>}
                  </h3>
                  
                  <div className="text-3xl font-bold text-purple-300 mb-4">
                    {plan.price === 0 ? 'БЕСПЛАТНО' : `${plan.price}₽`}
                    {plan.price > 0 && <span className="text-sm text-gray-400">/месяц</span>}
                  </div>
                  
                  <ul className="text-sm text-gray-300 space-y-2 mb-6">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-center">
                        <span className="text-green-400 mr-2">✓</span>
                        {feature}
                      </li>
                    ))}
                  </ul>
                  
                  {userSubscription?.subscription_plan === planKey ? (
                    <button className="w-full btn-primary opacity-50 cursor-not-allowed">
                      ТЕКУЩИЙ ТАРИФ
                    </button>
                  ) : (
                    <button
                      onClick={() => handleUpgradeSubscription(planKey)}
                      disabled={isUpgrading}
                      className={`w-full ${
                        planKey === 'pro' ? 'btn-primary' : 'btn-secondary'
                      } ${isUpgrading ? 'loading-pulse' : ''}`}
                    >
                      {isUpgrading ? 'ОБНОВЛЕНИЕ...' : 'ВЫБРАТЬ'}
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Kitchen Equipment Modal */}
      {showEquipmentModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-8">
              <h2 className="heading-section text-2xl">КУХОННОЕ ОБОРУДОВАНИЕ</h2>
              <button
                onClick={() => setShowEquipmentModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-6">
              {Object.entries(kitchenEquipment).map(([categoryKey, equipment]) => (
                <div key={categoryKey}>
                  <h3 className="heading-card text-lg mb-4">
                    {categoryKey === 'cooking_methods' ? 'СПОСОБЫ ПРИГОТОВЛЕНИЯ' :
                     categoryKey === 'prep_equipment' ? 'ОБОРУДОВАНИЕ ДЛЯ ПОДГОТОВКИ' :
                     'ХРАНЕНИЕ'}
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    {equipment.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => toggleEquipment(item.id)}
                        className={`p-3 rounded-lg border text-sm font-medium transition-all ${
                          userEquipment.includes(item.id)
                            ? 'bg-purple-600 border-purple-500 text-white'
                            : 'bg-gray-800 border-gray-600 text-gray-300 hover:border-purple-400'
                        }`}
                      >
                        {item.name}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            
            <div className="flex justify-end space-x-4 mt-8">
              <button
                onClick={() => setShowEquipmentModal(false)}
                className="btn-secondary"
              >
                ОТМЕНА
              </button>
              <button
                onClick={handleUpdateKitchenEquipment}
                className="btn-primary"
              >
                СОХРАНИТЬ ({userEquipment.length})
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;