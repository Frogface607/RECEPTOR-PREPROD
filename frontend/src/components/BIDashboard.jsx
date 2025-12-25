import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
    BarChart3, TrendingUp, DollarSign, Package, 
    Loader2, RefreshCw, Calendar, Filter,
    AlertCircle, CheckCircle2, XCircle
} from 'lucide-react';

const API_URL = process.env.REACT_APP_API_URL || 'https://receptor-preprod-production.up.railway.app/api';

function BIDashboard({ userId, apiUrl = API_URL }) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    // Данные для дашбордов
    const [dishStatistics, setDishStatistics] = useState(null);
    const [revenue, setRevenue] = useState(null);
    const [salesReport, setSalesReport] = useState(null);
    
    // Фильтры
    const [periodType, setPeriodType] = useState('LAST_MONTH');
    const [topN, setTopN] = useState(10);
    
    // Статус подключения
    const [rmsStatus, setRmsStatus] = useState(null);
    
    useEffect(() => {
        checkConnection();
        loadAllData();
    }, [periodType]);
    
    const checkConnection = async () => {
        try {
            const response = await axios.get(`${apiUrl}/iiko/rms/status/${userId}`);
            setRmsStatus(response.data);
        } catch (error) {
            console.error('Error checking RMS connection:', error);
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
                loadSalesReport()
            ]);
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Ошибка загрузки данных');
            console.error('Error loading BI data:', err);
        } finally {
            setLoading(false);
        }
    };
    
    const loadDishStatistics = async () => {
        try {
            const response = await axios.get(
                `${apiUrl}/iiko/rms/bi/dish-statistics/${userId}`,
                { params: { period_type: periodType, top_n: topN } }
            );
            setDishStatistics(response.data);
        } catch (error) {
            console.error('Error loading dish statistics:', error);
            throw error;
        }
    };
    
    const loadRevenue = async () => {
        try {
            const response = await axios.get(
                `${apiUrl}/iiko/rms/bi/revenue/${userId}`,
                { params: { period_type: periodType } }
            );
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
    
    if (!rmsStatus || rmsStatus.status !== 'connected') {
        return (
            <div className="flex-1 flex items-center justify-center p-8">
                <div className="text-center max-w-md">
                    <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-white mb-2">IIKO RMS не подключен</h2>
                    <p className="text-gray-400 mb-6">
                        Для работы с аналитикой необходимо подключить IIKO RMS сервер
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
                
                <div className="flex items-center gap-4">
                    {/* Фильтр периода */}
                    <div className="flex items-center gap-2">
                        <Calendar className="w-5 h-5 text-gray-400" />
                        <select
                            value={periodType}
                            onChange={(e) => setPeriodType(e.target.value)}
                            className="bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="TODAY">Сегодня</option>
                            <option value="YESTERDAY">Вчера</option>
                            <option value="CURRENT_WEEK">Текущая неделя</option>
                            <option value="LAST_WEEK">Прошлая неделя</option>
                            <option value="CURRENT_MONTH">Текущий месяц</option>
                            <option value="LAST_MONTH">Прошлый месяц</option>
                        </select>
                    </div>
                    
                    {/* Кнопка обновления */}
                    <button
                        onClick={loadAllData}
                        disabled={loading}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors disabled:opacity-50"
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
            
            {/* Loading state */}
            {loading && !dishStatistics && (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
                    <span className="ml-3 text-gray-400">Загрузка данных...</span>
                </div>
            )}
            
            {/* Stats Cards */}
            {revenue && revenue.revenue && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-400 text-sm mb-1">Общая выручка</p>
                                <p className="text-2xl font-bold text-white">
                                    {formatCurrency(
                                        revenue.revenue.summary?.reduce((sum, item) => 
                                            sum + (parseFloat(item.DishSumInt || 0)), 0
                                        ) || 0
                                    )}
                                </p>
                            </div>
                            <DollarSign className="w-8 h-8 text-green-500" />
                        </div>
                    </div>
                    
                    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-400 text-sm mb-1">Топ блюд</p>
                                <p className="text-2xl font-bold text-white">
                                    {dishStatistics?.statistics?.data?.length || 0}
                                </p>
                            </div>
                            <Package className="w-8 h-8 text-blue-500" />
                        </div>
                    </div>
                    
                    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-400 text-sm mb-1">Период</p>
                                <p className="text-lg font-semibold text-white capitalize">
                                    {periodType.toLowerCase().replace('_', ' ')}
                                </p>
                            </div>
                            <TrendingUp className="w-8 h-8 text-purple-500" />
                        </div>
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
            
            {/* Revenue Chart Placeholder */}
            {revenue && revenue.revenue && revenue.revenue.data && revenue.revenue.data.length > 0 && (
                <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-4">
                        <TrendingUp className="w-6 h-6" />
                        Динамика выручки
                    </h2>
                    
                    <div className="space-y-3">
                        {revenue.revenue.data.slice(0, 10).map((item, index) => {
                            const date = item['OpenDate.Typed'] || item.date || 'Неизвестно';
                            const sum = parseFloat(item.DishSumInt || item.dishSumInt || 0);
                            
                            return (
                                <div key={index} className="flex items-center justify-between p-3 bg-gray-900 rounded border border-gray-700">
                                    <span className="text-gray-300">{date}</span>
                                    <span className="text-green-400 font-semibold">{formatCurrency(sum)}</span>
                                </div>
                            );
                        })}
                    </div>
                </div>
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

