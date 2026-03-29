import React, { useState } from 'react';
import { toast } from './Toast';
import {
  Download,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  Star,
  MapPin,
  Calendar,
  Target,
  ShoppingBag,
  Zap,
  Shield
} from 'lucide-react';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

function ResearchResults({ research, venueName, onClose }) {
  const [exporting, setExporting] = useState(false);

  if (!research || research.status !== 'completed') {
    return null;
  }

  const data = research.data || research;

  const exportToPDF = async () => {
    setExporting(true);
    try {
      const element = document.getElementById('research-results-content');
      const canvas = await html2canvas(element, {
        scale: 2,
        logging: false,
        useCORS: true,
        backgroundColor: '#111827'
      });
      
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4'
      });
      
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = canvas.width;
      const imgHeight = canvas.height;
      const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight) * 25.4;
      const imgX = (pdfWidth - imgWidth * ratio) / 2;
      const imgY = 10;
      
      pdf.addImage(imgData, 'PNG', imgX, imgY, imgWidth * ratio, imgHeight * ratio);
      pdf.save(`${venueName || 'venue'}_research_${new Date().toISOString().split('T')[0]}.pdf`);
    } catch (error) {
      console.error('Error exporting PDF:', error);
      toast('Ошибка при экспорте PDF', 'error');
    } finally {
      setExporting(false);
    }
  };

  // Данные для отображения
  const {
    summary = '',
    positioning = '',
    price_segment = 'unknown',
    avg_check_estimate = 'unknown',
    rating_estimate = 'unknown',
    strengths = [],
    weaknesses = [],
    popular_items = [],
    opportunities = [],
    threats = [],
    competitors = [],
    research_date = new Date().toISOString()
  } = data;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 overflow-auto">
      <div className="min-h-screen py-8 px-4">
        <div className="max-w-6xl mx-auto">
          {/* Header with close and export buttons */}
          <div className="flex justify-between items-center mb-6">
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              ← Закрыть
            </button>
            
            <button
              onClick={exportToPDF}
              disabled={exporting}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-500 disabled:opacity-50 transition-colors"
            >
              {exporting ? (
                <>Экспортируем...</>
              ) : (
                <>
                  <Download size={18} />
                  Скачать PDF
                </>
              )}
            </button>
          </div>

          {/* Main content for PDF export */}
          <div id="research-results-content" className="bg-gray-900 rounded-2xl p-8 space-y-8">
            {/* Hero Section */}
            <div className="text-center space-y-4 pb-8 border-b border-gray-800">
              <h1 className="text-4xl font-bold text-white">
                🔬 Исследование заведения
              </h1>
              <h2 className="text-2xl text-emerald-400">
                {data.venue_name || venueName}
              </h2>
              <div className="flex items-center justify-center gap-6 text-gray-400">
                <span className="flex items-center gap-2">
                  <MapPin size={16} />
                  {data.city || 'Город не указан'}
                </span>
                <span className="flex items-center gap-2">
                  <Calendar size={16} />
                  {new Date(research_date).toLocaleDateString('ru-RU')}
                </span>
              </div>
              {summary && (
                <p className="text-lg text-gray-300 max-w-3xl mx-auto mt-4">
                  {summary}
                </p>
              )}
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <MetricCard
                icon={<DollarSign className="text-emerald-400" />}
                label="Ценовой сегмент"
                value={price_segment}
                subtext={avg_check_estimate !== 'unknown' ? `Средний чек: ${avg_check_estimate}` : ''}
              />
              <MetricCard
                icon={<Star className="text-yellow-400" />}
                label="Рейтинг"
                value={rating_estimate !== 'unknown' ? rating_estimate : 'Нет данных'}
              />
              <MetricCard
                icon={<Target className="text-blue-400" />}
                label="Позиционирование"
                value={positioning || 'Не определено'}
              />
            </div>

            {/* SWOT Analysis Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Strengths */}
              <SwotSection
                title="Сильные стороны"
                items={strengths}
                icon={<TrendingUp className="text-emerald-400" />}
                bgColor="bg-emerald-900/20"
                borderColor="border-emerald-700"
                textColor="text-emerald-300"
              />
              
              {/* Weaknesses */}
              <SwotSection
                title="Слабые места"
                items={weaknesses}
                icon={<TrendingDown className="text-orange-400" />}
                bgColor="bg-orange-900/20"
                borderColor="border-orange-700"
                textColor="text-orange-300"
              />
              
              {/* Opportunities */}
              <SwotSection
                title="Возможности"
                items={opportunities}
                icon={<Zap className="text-blue-400" />}
                bgColor="bg-blue-900/20"
                borderColor="border-blue-700"
                textColor="text-blue-300"
              />
              
              {/* Threats */}
              <SwotSection
                title="Угрозы"
                items={threats}
                icon={<Shield className="text-red-400" />}
                bgColor="bg-red-900/20"
                borderColor="border-red-700"
                textColor="text-red-300"
              />
            </div>

            {/* Popular Items */}
            {popular_items.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                  <ShoppingBag className="text-purple-400" />
                  Популярные позиции
                </h3>
                <div className="bg-purple-900/20 border border-purple-700 rounded-xl p-6">
                  <div className="flex flex-wrap gap-3">
                    {popular_items.map((item, index) => (
                      <span
                        key={index}
                        className="px-4 py-2 bg-purple-800/50 text-purple-200 rounded-full text-sm"
                      >
                        🔥 {item}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Competitors */}
            {competitors.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                  <Users className="text-indigo-400" />
                  Основные конкуренты
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {competitors.map((competitor, index) => (
                    <CompetitorCard key={index} competitor={competitor} />
                  ))}
                </div>
              </div>
            )}

            {/* Footer */}
            <div className="pt-8 border-t border-gray-800 text-center">
              <p className="text-gray-500 text-sm">
                Исследование проведено AI-системой RECEPTOR
              </p>
              <p className="text-gray-600 text-xs mt-1">
                Данные получены из открытых источников и могут требовать уточнения
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Компонент для метрики
function MetricCard({ icon, label, value, subtext }) {
  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6 space-y-2">
      <div className="flex items-center gap-3">
        {icon}
        <span className="text-gray-400 text-sm">{label}</span>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      {subtext && <p className="text-sm text-gray-500">{subtext}</p>}
    </div>
  );
}

// Компонент для секции SWOT
function SwotSection({ title, items, icon, bgColor, borderColor, textColor }) {
  return (
    <div className={`${bgColor} border ${borderColor} rounded-xl p-6 space-y-3`}>
      <h4 className="text-lg font-semibold text-white flex items-center gap-2">
        {icon}
        {title}
      </h4>
      {items.length > 0 ? (
        <ul className="space-y-2">
          {items.slice(0, 5).map((item, index) => (
            <li key={index} className={`${textColor} text-sm flex items-start gap-2`}>
              <span className="mt-1">•</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-gray-500 text-sm italic">Нет данных</p>
      )}
    </div>
  );
}

// Компонент для карточки конкурента
function CompetitorCard({ competitor }) {
  const name = typeof competitor === 'string' ? competitor : competitor.name || 'Неизвестно';
  const positioning = typeof competitor === 'object' ? competitor.positioning : '';
  const price = typeof competitor === 'object' ? competitor.price : '';
  
  return (
    <div className="bg-indigo-900/20 border border-indigo-700 rounded-xl p-4 space-y-2">
      <h5 className="font-semibold text-indigo-200">{name}</h5>
      {positioning && (
        <p className="text-sm text-gray-400">{positioning}</p>
      )}
      {price && (
        <p className="text-sm text-indigo-300">💰 {price}</p>
      )}
    </div>
  );
}

export default ResearchResults;
