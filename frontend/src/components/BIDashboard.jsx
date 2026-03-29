import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import {
    BarChart3, TrendingUp, DollarSign, Package,
    Loader2, RefreshCw, Calendar, Filter,
    AlertCircle, CheckCircle2, XCircle, Download
} from 'lucide-react';
import {
    LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { API_URL } from '../config';

function BIDashboard({ userId, apiUrl = API_URL }) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    // Данные для дашбордов
    const [dishStatistics, setDishStatistics] = useState(null);
    const [revenue, setRevenue] = useState(null);
    const [salesReport, setSalesReport] = useState(null);
    const [shiftsReport, setShiftsReport] = useState(null);
    
    // Фильтры
    const [periodType, setPeriodType] = useState('LAST_MONTH');
    const [topN, setTopN] = useState(10);
    const [activeTab, setActiveTab] = useState('overview'); // 'overview' или 'shifts'
    const [customDateFrom, setCustomDateFrom] = useState(null);
    const [customDateTo, setCustomDateTo] = useState(null);
    
    // Статус подключения
    const [rmsStatus, setRmsStatus] = useState(null);
    
    useEffect(() => {
        checkConnection();
        if (periodType !== 'CUSTOM') {
            loadAllData();
        }
    }, [periodType]);
    
    const checkConnection = async () => {
        try {
            // Проверяем Cloud API подключение (приоритет)
            const cloudResponse = await axios.get(`${apiUrl}/iiko/cloud/status/${userId}`);
            if (cloudResponse.data?.status === 'connected') {
                setRmsStatus({ 
                    status: 'connected', 
                    type: 'cloud',
                    organization_name: cloudResponse.data.organization_name 
                });
                return;
            }
        } catch (error) {
            console.log('Cloud API not connected, checking RMS...');
        }
        
        // Fallback на RMS
        try {
            const response = await axios.get(`${apiUrl}/iiko/rms/status/${userId}`);
            setRmsStatus({ ...response.data, type: 'rms' });
        } catch (error) {
            console.error('Error checking connection:', error);
            setRmsStatus({ status: 'error', message: 'Не удалось проверить подключение' });
        }
    };
    
    const loadAllData = async () => {
        setLoading(true);
        setError(null);
        
        try {
            await Promise.all([
                loadDishStatistics(),
                loadRevenue(),
                loadSalesReport(),
                loadShiftsReport()
            ]);
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Ошибка загрузки данных');
            console.error('Error loading BI data:', err);
        } finally {
            setLoading(false);
        }
    };
    
    const loadShiftsReport = async (dateFrom = null, dateTo = null) => {
        try {
            const params = {};
            if (periodType === 'CUSTOM' && dateFrom && dateTo) {
                params.date_from = dateFrom;
                params.date_to = dateTo;
            } else {
                params.period_type = periodType;
            }
            
            // Отчеты по сменам пока только через RMS (Cloud API не поддерживает смены напрямую)
            const response = await axios.get(
                `${apiUrl}/iiko/rms/bi/shifts/${userId}`,
                { params }
            );
            setShiftsReport(response.data);
        } catch (error) {
            console.error('Error loading shifts report:', error);
            // Не критичная ошибка - просто не показываем отчет по сменам
        }
    };
    
    const loadAllDataWithDates = async (dateFrom, dateTo) => {
        setLoading(true);
        setError(null);
        
        try {
            await Promise.all([
                loadDishStatisticsWithDates(dateFrom, dateTo),
                loadRevenueWithDates(dateFrom, dateTo),
                loadShiftsReport(dateFrom, dateTo)
            ]);
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Ошибка загрузки данных');
            console.error('Error loading BI data:', err);
        } finally {
            setLoading(false);
        }
    };
    
    const loadDishStatisticsWithDates = async (dateFrom, dateTo) => {
        try {
            const params = {};
            if (dateFrom && dateTo) {
                params.date_from = dateFrom;
                params.date_to = dateTo;
            } else {
                params.period_type = periodType;
            }
            params.top_n = topN;
            
            // Пробуем сначала Cloud API
            let response;
            try {
                response = await axios.get(
                    `${apiUrl}/iiko/cloud/bi/dish-statistics/${userId}`,
                    { params }
                );
            } catch (cloudError) {
                // Fallback на RMS
                response = await axios.get(
                    `${apiUrl}/iiko/rms/bi/dish-statistics/${userId}`,
                    { params }
                );
            }
            setDishStatistics(response.data);
        } catch (error) {
            console.error('Error loading dish statistics:', error);
            throw error;
        }
    };
    
    const loadRevenueWithDates = async (dateFrom, dateTo) => {
        try {
            const params = {};
            if (dateFrom && dateTo) {
                params.date_from = dateFrom;
                params.date_to = dateTo;
            } else {
                params.period_type = periodType;
            }
            
            // Пробуем сначала Cloud API
            let response;
            try {
                response = await axios.get(
                    `${apiUrl}/iiko/cloud/bi/revenue/${userId}`,
                    { params }
                );
            } catch (cloudError) {
                // Fallback на RMS
                response = await axios.get(
                    `${apiUrl}/iiko/rms/bi/revenue/${userId}`,
                    { params }
                );
            }
            setRevenue(response.data);
        } catch (error) {
            console.error('Error loading revenue:', error);
            throw error;
        }
    };
    
    const loadDishStatistics = async () => {
        try {
            // Пробуем сначала Cloud API
            let response;
            try {
                response = await axios.get(
                    `${apiUrl}/iiko/cloud/bi/dish-statistics/${userId}`,
                    { params: { period_type: periodType, top_n: topN } }
                );
            } catch (cloudError) {
                // Fallback на RMS
                response = await axios.get(
                    `${apiUrl}/iiko/rms/bi/dish-statistics/${userId}`,
                    { params: { period_type: periodType, top_n: topN } }
                );
            }
            setDishStatistics(response.data);
        } catch (error) {
            console.error('Error loading dish statistics:', error);
            throw error;
        }
    };
    
    const loadRevenue = async () => {
        try {
            // Пробуем сначала Cloud API
            let response;
            try {
                response = await axios.get(
                    `${apiUrl}/iiko/cloud/bi/revenue/${userId}`,
                    { params: { period_type: periodType } }
                );
            } catch (cloudError) {
                // Fallback на RMS
                response = await axios.get(
                    `${apiUrl}/iiko/rms/bi/revenue/${userId}`,
                    { params: { period_type: periodType } }
                );
            }
            setRevenue(response.data);
        } catch (error) {
            console.error('Error loading revenue:', error);
            throw error;
        }
    };
    
    const loadSalesReport = async () => {
        try {
            const response = await axios.post(`${apiUrl}/iiko/rms/bi/olap-report`, {
                user_id: userId,
                period_type: periodType,
                group_by: 'dish'
            });
            setSalesReport(response.data);
        } catch (error) {
            console.error('Error loading sales report:', error);
            throw error;
        }
    };
    
    const exportToCSV = () => {
        if (!dishStatistics?.statistics?.data) return;

        const data = dishStatistics.statistics.data;
        const headers = ['Блюдо', 'Группа', 'Количество', 'Сумма (₽)'];
        const rows = data.map(item => [
            item.DishName || item.dishName || '',
            item.DishGroup || item.dishGroup || '',
            item.DishAmountInt || item.dishAmountInt || 0,
            item.DishSumInt || item.dishSumInt || 0,
        ]);

        // BOM for Excel UTF-8 support
        const BOM = '\uFEFF';
        const csvContent = BOM + [
            headers.join(';'),
            ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(';'))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `receptor_bi_${periodType.toLowerCase()}_${new Date().toISOString().slice(0, 10)}.csv`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    };

    const formatCurrency = (value) => {
        if (!value) return '0 ₽';
        const num = typeof value === 'string' ? parseFloat(value) : value;
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(num);
    };
    
    const formatNumber = (value) => {
        if (!value) return '0';
        const num = typeof value === 'string' ? parseFloat(value) : value;
        return new Intl.NumberFormat('ru-RU').format(num);
    };
    
    // Цвета для категорий (pie chart)
    const COLORS = [
        '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
        '#06b6d4', '#ec4899', '#14b8a6', '#f97316', '#6366f1'
    ];
    
    // Подготовка данных для графиков
    const revenueChartData = useMemo(() => {
        if (!revenue?.revenue?.data) return [];
        
        return revenue.revenue.data
            .map(item => {
                const date = item['OpenDate.Typed'] || item.date || '';
                const sum = parseFloat(item.DishSumInt || item.dishSumInt || 0);
                // Форматируем дату для отображения
                const dateFormatted = date ? new Date(date).toLocaleDateString('ru-RU', { 
                    day: '2-digit', 
                    month: '2-digit' 
                }) : '';
                
                return {
                    date: dateFormatted,
                    dateFull: date,
                    revenue: sum
                };
            })
            .filter(item => item.revenue > 0)
            .slice(0, 30); // Ограничиваем до 30 дней для читаемости
    }, [revenue]);
    
    // Данные для графика по категориям
    const categoriesChartData = useMemo(() => {
        if (!dishStatistics?.statistics?.data) return [];
        
        const categoryMap = {};
        dishStatistics.statistics.data.forEach(item => {
            const category = item.DishGroup || item.dishGroup || 'Без категории';
            const revenue = parseFloat(item.DishSumInt || item.dishSumInt || 0);
            
            if (!categoryMap[category]) {
                categoryMap[category] = 0;
            }
            categoryMap[category] += revenue;
        });
        
        return Object.entries(categoryMap)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 10); // Топ 10 категорий
    }, [dishStatistics]);
    
    // Данные для горизонтального графика топ блюд
    const topDishesChartData = useMemo(() => {
        if (!dishStatistics?.statistics?.data) return [];
        
        return dishStatistics.statistics.data
            .slice(0, 10) // Топ 10
            .map(item => {
                const name = item.DishName || item.dishName || 'Без названия';
                const revenue = parseFloat(item.DishSumInt || item.dishSumInt || 0);
                // Сокращаем длинные названия
                const shortName = name.length > 30 ? name.substring(0, 30) + '...' : name;
                
                return {
                    name: shortName,
                    fullName: name,
                    revenue: revenue
                };
            });
    }, [dishStatistics]);

    // ABC-анализ блюд (Парето: A=80% выручки, B=15%, C=5%)
    const abcAnalysis = useMemo(() => {
        if (!dishStatistics?.statistics?.data) return null;

        const dishes = dishStatistics.statistics.data
            .map(item => ({
                name: item.DishName || item.dishName || 'Без названия',
                group: item.DishGroup || item.dishGroup || '',
                revenue: parseFloat(item.DishSumInt || item.dishSumInt || 0),
                quantity: parseFloat(item.DishAmountInt || item.dishAmountInt || 0),
            }))
            .filter(d => d.revenue > 0)
            .sort((a, b) => b.revenue - a.revenue);

        const totalRevenue = dishes.reduce((s, d) => s + d.revenue, 0);
        if (totalRevenue === 0) return null;

        let cumulative = 0;
        const classified = dishes.map(dish => {
            cumulative += dish.revenue;
            const percent = cumulative / totalRevenue;
            const category = percent <= 0.8 ? 'A' : percent <= 0.95 ? 'B' : 'C';
            return { ...dish, category, sharePercent: (dish.revenue / totalRevenue * 100).toFixed(1) };
        });

        return {
            dishes: classified,
            summary: {
                A: classified.filter(d => d.category === 'A').length,
                B: classified.filter(d => d.category === 'B').length,
                C: classified.filter(d => d.category === 'C').length,
            },
            totalRevenue,
            totalDishes: classified.length,
        };
    }, [dishStatistics]);

    // Расширенные KPI
    const kpiMetrics = useMemo(() => {
        if (!dishStatistics?.statistics?.data) return null;

        const data = dishStatistics.statistics.data;
        const totalRevenue = data.reduce((s, item) =>
            s + parseFloat(item.DishSumInt || item.dishSumInt || 0), 0);
        const totalQuantity = data.reduce((s, item) =>
            s + parseFloat(item.DishAmountInt || item.dishAmountInt || 0), 0);

        const daysCount = revenueChartData.length || 1;

        return {
            totalRevenue,
            totalQuantity,
            avgCheck: totalQuantity > 0 ? totalRevenue / totalQuantity : 0,
            revenuePerDay: totalRevenue / daysCount,
            dishesPerDay: totalQuantity / daysCount,
            uniqueDishes: data.length,
        };
    }, [dishStatistics, revenueChartData]);

    if (!rmsStatus || rmsStatus.status !== 'connected') {
        return (
            <div className="flex-1 flex items-center justify-center p-8">
                <div className="text-center max-w-md">
                    <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-white mb-2">IIKO не подключен</h2>
                    <p className="text-gray-400 mb-6">
                        Для работы с аналитикой необходимо подключить IIKO Cloud API или RMS сервер
                    </p>
                    <button
                        onClick={() => window.location.hash = '#integrations'}
                        className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                    >
                        Перейти к настройкам
                    </button>
                </div>
            </div>
        );
    }
    
    return (
        <div className="flex-1 flex flex-col p-6 space-y-6 overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <BarChart3 className="w-8 h-8" />
                        BI Dashboard
                    </h1>
                    <p className="text-gray-400 mt-1">Аналитика и отчеты по продажам</p>
                </div>
                
                {/* Табы для переключения между обзором и сменами */}
                <div className="flex gap-2 bg-gray-800/50 backdrop-blur-sm rounded-xl p-1.5 border border-gray-700/50">
                    <button
                        onClick={() => setActiveTab('overview')}
                        className={`px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 ${
                            activeTab === 'overview'
                                ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg shadow-blue-500/30'
                                : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                        }`}
                    >
                        Обзор
                    </button>
                    <button
                        onClick={() => {
                            setActiveTab('shifts');
                            if (!shiftsReport) {
                                if (periodType === 'CUSTOM' && customDateFrom && customDateTo) {
                                    loadShiftsReport(customDateFrom, customDateTo);
                                } else {
                                    loadShiftsReport();
                                }
                            }
                        }}
                        className={`px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 ${
                            activeTab === 'shifts'
                                ? 'bg-gradient-to-r from-purple-600 to-purple-700 text-white shadow-lg shadow-purple-500/30'
                                : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                        }`}
                    >
                        По сменам
                    </button>
                </div>
                
                <div className="flex items-center gap-4">
                    {/* Фильтр периода */}
                    <div className="flex items-center gap-2">
                        <Calendar className="w-5 h-5 text-gray-400" />
                        <select
                            value={periodType}
                            onChange={(e) => setPeriodType(e.target.value)}
                            className="bg-gray-800/80 backdrop-blur-sm border border-gray-700/50 text-white rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 hover:border-gray-600 transition-all duration-200 font-medium shadow-sm"
                        >
                            <option value="TODAY">Сегодня</option>
                            <option value="YESTERDAY">Вчера</option>
                            <option value="CURRENT_WEEK">Текущая неделя</option>
                            <option value="LAST_WEEK">Прошлая неделя</option>
                            <option value="CURRENT_MONTH">Текущий месяц</option>
                            <option value="LAST_MONTH">Прошлый месяц</option>
                        </select>
                    </div>
                    
                    {/* Кнопка экспорта */}
                    {dishStatistics?.statistics?.data && (
                        <button
                            onClick={exportToCSV}
                            className="flex items-center gap-2 px-4 py-2.5 bg-gray-800/80 border border-gray-700/50 hover:bg-gray-700 text-gray-300 hover:text-white rounded-lg transition-all duration-200 font-medium"
                            title="Экспорт данных в CSV"
                        >
                            <Download className="w-4 h-4" />
                            CSV
                        </button>
                    )}

                    {/* Кнопка обновления */}
                    <button
                        onClick={loadAllData}
                        disabled={loading}
                        className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/20 hover:shadow-xl hover:shadow-blue-500/30 font-medium"
                    >
                        <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                        Обновить
                    </button>
                </div>
            </div>
            
            {/* Error message */}
            {error && (
                <div className="bg-red-900/20 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg flex items-center gap-2">
                    <AlertCircle className="w-5 h-5" />
                    <span>{error}</span>
                </div>
            )}
            
            {/* Loading state with skeleton */}
            {loading && !dishStatistics && (
                <div className="space-y-6">
                    {/* Skeleton cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="bg-gray-800/50 rounded-xl p-6 border border-gray-700/50 animate-pulse">
                                <div className="h-4 bg-gray-700/50 rounded w-24 mb-4"></div>
                                <div className="h-8 bg-gray-700/50 rounded w-32 mb-2"></div>
                                <div className="h-3 bg-gray-700/30 rounded w-20"></div>
                            </div>
                        ))}
                    </div>
                    {/* Skeleton chart */}
                    <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700/50 animate-pulse">
                        <div className="h-6 bg-gray-700/50 rounded w-48 mb-6"></div>
                        <div className="h-64 bg-gray-700/30 rounded"></div>
                    </div>
                </div>
            )}
            
            {/* KPI Cards */}
            {kpiMetrics && (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                    <div className="bg-gradient-to-br from-emerald-900/40 to-gray-900 rounded-xl p-4 border border-emerald-700/30">
                        <p className="text-gray-400 text-xs mb-1">Выручка</p>
                        <p className="text-xl font-bold text-emerald-400">{formatCurrency(kpiMetrics.totalRevenue)}</p>
                    </div>
                    <div className="bg-gradient-to-br from-blue-900/40 to-gray-900 rounded-xl p-4 border border-blue-700/30">
                        <p className="text-gray-400 text-xs mb-1">Выручка / день</p>
                        <p className="text-xl font-bold text-blue-400">{formatCurrency(kpiMetrics.revenuePerDay)}</p>
                    </div>
                    <div className="bg-gradient-to-br from-purple-900/40 to-gray-900 rounded-xl p-4 border border-purple-700/30">
                        <p className="text-gray-400 text-xs mb-1">Средний чек</p>
                        <p className="text-xl font-bold text-purple-400">{formatCurrency(kpiMetrics.avgCheck)}</p>
                    </div>
                    <div className="bg-gray-800 rounded-xl p-4 border border-gray-700/50">
                        <p className="text-gray-400 text-xs mb-1">Продано позиций</p>
                        <p className="text-xl font-bold text-white">{formatNumber(kpiMetrics.totalQuantity)}</p>
                    </div>
                    <div className="bg-gray-800 rounded-xl p-4 border border-gray-700/50">
                        <p className="text-gray-400 text-xs mb-1">Позиций / день</p>
                        <p className="text-xl font-bold text-white">{formatNumber(Math.round(kpiMetrics.dishesPerDay))}</p>
                    </div>
                    <div className="bg-gray-800 rounded-xl p-4 border border-gray-700/50">
                        <p className="text-gray-400 text-xs mb-1">Уникальных блюд</p>
                        <p className="text-xl font-bold text-white">{kpiMetrics.uniqueDishes}</p>
                    </div>
                </div>
            )}
            
            {/* Top Dishes */}
            {dishStatistics && dishStatistics.statistics && (
                <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-bold text-white flex items-center gap-2">
                            <Package className="w-6 h-6" />
                            Топ {topN} блюд по продажам
                        </h2>
                        <select
                            value={topN}
                            onChange={(e) => {
                                setTopN(parseInt(e.target.value));
                                loadDishStatistics();
                            }}
                            className="bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-1 text-sm"
                        >
                            <option value="5">Топ 5</option>
                            <option value="10">Топ 10</option>
                            <option value="20">Топ 20</option>
                        </select>
                    </div>
                    
                    {dishStatistics.statistics.data && dishStatistics.statistics.data.length > 0 ? (
                        <div className="space-y-3">
                            {dishStatistics.statistics.data.map((dish, index) => {
                                const dishName = dish.DishName || dish.dishName || 'Без названия';
                                const amount = parseFloat(dish.DishAmountInt || dish.dishAmountInt || 0);
                                const sum = parseFloat(dish.DishSumInt || dish.dishSumInt || 0);
                                
                                return (
                                    <div
                                        key={index}
                                        className="flex items-center justify-between p-4 bg-gray-900 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors"
                                    >
                                        <div className="flex items-center gap-4 flex-1">
                                            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                                                {index + 1}
                                            </div>
                                            <div className="flex-1">
                                                <p className="text-white font-semibold">{dishName}</p>
                                                <p className="text-gray-400 text-sm">
                                                    Продано: {formatNumber(amount)} шт.
                                                </p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-green-400 font-bold text-lg">
                                                {formatCurrency(sum)}
                                            </p>
                                            <p className="text-gray-400 text-xs">
                                                {formatCurrency(sum / (amount || 1))} / шт.
                                            </p>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-400">
                            Нет данных за выбранный период
                        </div>
                    )}
                </div>
            )}
            
            {/* ABC Analysis */}
            {abcAnalysis && activeTab === 'overview' && (
                <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-bold text-white flex items-center gap-2">
                            <TrendingUp className="w-6 h-6" />
                            ABC-анализ меню
                        </h2>
                        <div className="flex gap-3 text-sm">
                            <span className="flex items-center gap-1.5">
                                <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                                A — хиты ({abcAnalysis.summary.A})
                            </span>
                            <span className="flex items-center gap-1.5">
                                <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                                B — стандарт ({abcAnalysis.summary.B})
                            </span>
                            <span className="flex items-center gap-1.5">
                                <span className="w-3 h-3 rounded-full bg-gray-500"></span>
                                C — аутсайдеры ({abcAnalysis.summary.C})
                            </span>
                        </div>
                    </div>
                    <p className="text-gray-400 text-sm mb-4">
                        Категория A — 80% выручки (хиты, которые кормят бизнес). B — 15%. C — 5% (кандидаты на вывод или переработку).
                    </p>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                        {abcAnalysis.dishes.slice(0, 30).map((dish, index) => {
                            const colors = {
                                A: { bg: 'bg-emerald-900/30', border: 'border-emerald-700/50', badge: 'bg-emerald-600', text: 'text-emerald-400' },
                                B: { bg: 'bg-blue-900/20', border: 'border-blue-700/30', badge: 'bg-blue-600', text: 'text-blue-400' },
                                C: { bg: 'bg-gray-900/50', border: 'border-gray-700/30', badge: 'bg-gray-600', text: 'text-gray-400' },
                            };
                            const c = colors[dish.category];
                            return (
                                <div key={index} className={`flex items-center justify-between p-3 ${c.bg} rounded-lg border ${c.border}`}>
                                    <div className="flex items-center gap-3 flex-1">
                                        <span className={`w-7 h-7 ${c.badge} rounded-full flex items-center justify-center text-white text-xs font-bold`}>
                                            {dish.category}
                                        </span>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-white text-sm truncate">{dish.name}</p>
                                            <p className="text-gray-500 text-xs">{dish.group}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-6 text-sm">
                                        <span className="text-gray-400">{formatNumber(dish.quantity)} шт.</span>
                                        <span className={`font-semibold ${c.text}`}>{formatCurrency(dish.revenue)}</span>
                                        <span className="text-gray-500 w-14 text-right">{dish.sharePercent}%</span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Shifts Report Tab */}
            {activeTab === 'shifts' && shiftsReport?.shifts && (
                <div className="space-y-6">
                    <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
                        <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-4">
                            <BarChart3 className="w-6 h-6" />
                            Продажи по кассовым сменам
                        </h2>
                        
                        {shiftsReport.shifts.data && shiftsReport.shifts.data.length > 0 ? (
                            <div className="space-y-4">
                                {shiftsReport.shifts.data.map((shift, index) => {
                                    // Пробуем разные варианты полей для даты
                                    let shiftDate = null;
                                    const dateFields = [
                                        'SessionOpenDate.Typed',
                                        'OpenDate.Typed', 
                                        'SessionDate.Typed',
                                        'SessionOpenDate',
                                        'OpenDate',
                                        'date',
                                        'Date'
                                    ];
                                    
                                    for (const field of dateFields) {
                                        if (shift[field]) {
                                            shiftDate = shift[field];
                                            break;
                                        }
                                    }
                                    
                                    // Если не нашли, пробуем найти любое поле с датой
                                    if (!shiftDate) {
                                        for (const key in shift) {
                                            if (key.toLowerCase().includes('date') || key.toLowerCase().includes('time')) {
                                                shiftDate = shift[key];
                                                break;
                                            }
                                        }
                                    }
                                    
                                    // Форматируем дату
                                    let formattedDate = 'Дата не указана';
                                    if (shiftDate) {
                                        try {
                                            const date = new Date(shiftDate);
                                            if (!isNaN(date.getTime())) {
                                                formattedDate = date.toLocaleDateString('ru-RU', {
                                                    day: '2-digit',
                                                    month: '2-digit',
                                                    year: 'numeric',
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                });
                                            } else {
                                                // Если это строка, пробуем распарсить
                                                formattedDate = typeof shiftDate === 'string' 
                                                    ? shiftDate.split('T')[0] 
                                                    : String(shiftDate);
                                            }
                                        } catch (e) {
                                            formattedDate = typeof shiftDate === 'string' 
                                                ? shiftDate.split('T')[0] 
                                                : String(shiftDate);
                                        }
                                    }
                                    
                                    const revenue = parseFloat(shift.DishSumInt || shift.dishSumInt || 0);
                                    const amount = parseFloat(shift.DishAmountInt || shift.dishAmountInt || 0);
                                    
                                    return (
                                        <div
                                            key={index}
                                            className="group flex items-center justify-between p-5 bg-gray-900/50 hover:bg-gray-900 rounded-xl border border-gray-700/50 hover:border-purple-500/50 transition-all duration-200 hover:shadow-lg hover:shadow-purple-500/5"
                                        >
                                            <div className="flex items-center gap-4 flex-1 min-w-0">
                                                <div className="w-14 h-14 bg-gradient-to-br from-purple-600 to-purple-700 rounded-xl flex items-center justify-center text-white font-bold text-sm flex-shrink-0 shadow-lg shadow-purple-500/20 group-hover:from-purple-500 group-hover:to-purple-600 transition-all">
                                                    {index + 1}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-white font-semibold truncate group-hover:text-purple-400 transition-colors mb-1">
                                                        Смена {index + 1}
                                                    </p>
                                                    <p className="text-gray-400 text-sm mb-1">
                                                        {formattedDate}
                                                    </p>
                                                    <p className="text-gray-500 text-sm">
                                                        Позиций продано: <span className="text-gray-300 font-medium">{formatNumber(amount)}</span>
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="text-right flex-shrink-0 ml-4">
                                                <p className="text-emerald-400 font-bold text-xl group-hover:text-emerald-300 transition-colors">
                                                    {formatCurrency(revenue)}
                                                </p>
                                            </div>
                                        </div>
                                    );
                                })}
                                
                                {/* Итого по всем сменам */}
                                {shiftsReport.shifts.summary && shiftsReport.shifts.summary.length > 0 && (
                                    <div className="mt-6 pt-6 border-t border-gray-700/50">
                                        <div className="flex items-center justify-between p-5 bg-gradient-to-r from-blue-900/30 to-purple-900/30 rounded-xl border border-blue-700/30 shadow-lg">
                                            <span className="text-white font-bold text-lg flex items-center gap-2">
                                                <TrendingUp className="w-5 h-5 text-blue-400" />
                                                Итого за период:
                                            </span>
                                            <span className="text-blue-400 font-bold text-2xl">
                                                {formatCurrency(
                                                    shiftsReport.shifts.summary.reduce((sum, item) => 
                                                        sum + (parseFloat(item.DishSumInt || 0)), 0
                                                    )
                                                )}
                                            </span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="text-center py-8 text-gray-400">
                                Нет данных по сменам за выбранный период
                            </div>
                        )}
                    </div>
                </div>
            )}
            
            {/* Overview Tab - Charts */}
            {activeTab === 'overview' && (
            <>
            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* График выручки по дням */}
                {revenueChartData.length > 0 && (
                    <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
                        <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-4">
                            <TrendingUp className="w-6 h-6" />
                            Динамика выручки по дням
                        </h2>
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={revenueChartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                <XAxis 
                                    dataKey="date" 
                                    stroke="#9ca3af"
                                    style={{ fontSize: '12px' }}
                                />
                                <YAxis 
                                    stroke="#9ca3af"
                                    style={{ fontSize: '12px' }}
                                    tickFormatter={(value) => `${(value / 1000).toFixed(0)}к`}
                                />
                                <Tooltip 
                                    contentStyle={{ 
                                        backgroundColor: '#1f2937', 
                                        border: '1px solid #374151',
                                        borderRadius: '8px',
                                        color: '#fff'
                                    }}
                                    formatter={(value) => formatCurrency(value)}
                                />
                                <Legend wrapperStyle={{ color: '#9ca3af' }} />
                                <Line 
                                    type="monotone" 
                                    dataKey="revenue" 
                                    stroke="#10b981" 
                                    strokeWidth={2}
                                    dot={{ fill: '#10b981', r: 4 }}
                                    activeDot={{ r: 6 }}
                                    name="Выручка"
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                )}
                
                {/* График по категориям */}
                {categoriesChartData.length > 0 && (
                    <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
                        <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-4">
                            <Package className="w-6 h-6" />
                            Продажи по категориям
                        </h2>
                        <ResponsiveContainer width="100%" height={300}>
                            <PieChart>
                                <Pie
                                    data={categoriesChartData}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                    outerRadius={100}
                                    fill="#8884d8"
                                    dataKey="value"
                                >
                                    {categoriesChartData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip 
                                    contentStyle={{ 
                                        backgroundColor: '#1f2937', 
                                        border: '1px solid #374151',
                                        borderRadius: '8px',
                                        color: '#fff'
                                    }}
                                    formatter={(value) => formatCurrency(value)}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                )}
            </div>
            
            {/* График топ блюд (горизонтальный) */}
            {topDishesChartData.length > 0 && (
                <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-4">
                        <BarChart3 className="w-6 h-6" />
                        Топ-10 блюд по выручке
                    </h2>
                    <ResponsiveContainer width="100%" height={400}>
                        <BarChart 
                            data={topDishesChartData}
                            layout="vertical"
                            margin={{ top: 5, right: 30, left: 150, bottom: 5 }}
                        >
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis 
                                type="number" 
                                stroke="#9ca3af"
                                style={{ fontSize: '12px' }}
                                tickFormatter={(value) => `${(value / 1000).toFixed(0)}к ₽`}
                            />
                            <YAxis 
                                type="category" 
                                dataKey="name" 
                                stroke="#9ca3af"
                                style={{ fontSize: '12px' }}
                                width={140}
                            />
                            <Tooltip 
                                contentStyle={{ 
                                    backgroundColor: '#1f2937', 
                                    border: '1px solid #374151',
                                    borderRadius: '8px',
                                    color: '#fff'
                                }}
                                formatter={(value) => formatCurrency(value)}
                            />
                            <Legend wrapperStyle={{ color: '#9ca3af' }} />
                            <Bar 
                                dataKey="revenue" 
                                fill="#3b82f6"
                                name="Выручка"
                                radius={[0, 8, 8, 0]}
                            />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}
            </>
            )}
            
            {/* Connection Status */}
            {rmsStatus && (
                <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            {rmsStatus.status === 'connected' ? (
                                <CheckCircle2 className="w-5 h-5 text-green-500" />
                            ) : (
                                <XCircle className="w-5 h-5 text-red-500" />
                            )}
                            <span className="text-gray-300">
                                IIKO RMS: {rmsStatus.status === 'connected' ? 'Подключен' : 'Не подключен'}
                            </span>
                        </div>
                        {rmsStatus.organization_name && (
                            <span className="text-gray-400 text-sm">
                                {rmsStatus.organization_name}
                            </span>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export default BIDashboard;

