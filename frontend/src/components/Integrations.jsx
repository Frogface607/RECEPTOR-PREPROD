import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
    Cloud, Server, CheckCircle2, XCircle, Loader2, 
    RefreshCw, Eye, EyeOff, Unlink, Database, 
    Building2, Wifi, WifiOff, AlertCircle, ChevronDown
} from 'lucide-react';

function Integrations({ userId, apiUrl }) {
    // ============ STATE ============
    const [activeTab, setActiveTab] = useState('cloud'); // 'cloud' or 'rms'
    
    // Cloud API state
    const [cloudApiKey, setCloudApiKey] = useState('');
    const [cloudStatus, setCloudStatus] = useState(null);
    const [cloudLoading, setCloudLoading] = useState(false);
    const [cloudError, setCloudError] = useState(null);
    const [showCloudKey, setShowCloudKey] = useState(false);
    
    // RMS state
    const [rmsHost, setRmsHost] = useState('');
    const [rmsLogin, setRmsLogin] = useState('');
    const [rmsPassword, setRmsPassword] = useState('');
    const [rmsStatus, setRmsStatus] = useState(null);
    const [rmsLoading, setRmsLoading] = useState(false);
    const [rmsError, setRmsError] = useState(null);
    const [showRmsPassword, setShowRmsPassword] = useState(false);
    
    // Organizations state
    const [organizations, setOrganizations] = useState([]);
    const [selectedOrg, setSelectedOrg] = useState(null);
    const [syncStatus, setSyncStatus] = useState(null);
    const [syncing, setSyncing] = useState(false);
    
    // Cloud organizations state
    const [cloudOrganizations, setCloudOrganizations] = useState([]);
    const [selectedCloudOrg, setSelectedCloudOrg] = useState(null);

    // ============ EFFECTS ============
    useEffect(() => {
        fetchAllStatuses();
    }, []);

    const fetchAllStatuses = async () => {
        await Promise.all([
            fetchCloudStatus(),
            fetchRmsStatus()
        ]);
    };

    // ============ CLOUD API FUNCTIONS ============
    const fetchCloudStatus = async () => {
        try {
            const response = await axios.get(`${apiUrl}/iiko/cloud/status/${userId}`);
            setCloudStatus(response.data);
            
            // Загружаем организации и выбранную
            if (response.data.organizations) {
                setCloudOrganizations(response.data.organizations);
            }
            if (response.data.selected_organization_id) {
                setSelectedCloudOrg({
                    id: response.data.selected_organization_id,
                    name: response.data.selected_organization_name
                });
            }
        } catch (error) {
            console.error('Error fetching Cloud status:', error);
            setCloudStatus({ status: 'not_connected' });
        }
    };

    const connectCloud = async (e) => {
        e.preventDefault();
        if (!cloudApiKey.trim()) return;
        
        setCloudLoading(true);
        setCloudError(null);
        
        try {
            const response = await axios.post(`${apiUrl}/iiko/cloud/connect`, {
                api_key: cloudApiKey,
                user_id: userId
            });
            
            setCloudStatus({ status: 'connected', ...response.data });
            setCloudOrganizations(response.data.organizations || []);
            
            // Если одна организация - автоматически выбираем
            if (response.data.organizations && response.data.organizations.length === 1) {
                const org = response.data.organizations[0];
                setSelectedCloudOrg(org);
                // Автоматически выбираем организацию на бэкенде
                await selectCloudOrganization(org);
            } else if (response.data.organizations && response.data.organizations.length > 0) {
                // Если несколько - выбираем первую по умолчанию (или можно оставить выбор пользователю)
                const org = response.data.organizations[0];
                setSelectedCloudOrg(org);
                await selectCloudOrganization(org);
            }
            
            setCloudApiKey(''); // Clear for security
            
        } catch (error) {
            console.error('Cloud connection error:', error);
            setCloudError(error.response?.data?.detail || 'Ошибка подключения');
        } finally {
            setCloudLoading(false);
        }
    };

    const selectCloudOrganization = async (org) => {
        try {
            await axios.post(`${apiUrl}/iiko/cloud/select-organization`, {
                organization_id: org.id,
                user_id: userId
            });
            setSelectedCloudOrg(org);
            // Обновляем статус чтобы получить актуальную информацию
            await fetchCloudStatus();
        } catch (error) {
            console.error('Error selecting Cloud organization:', error);
        }
    };

    const syncCloudNomenclature = async () => {
        if (!selectedCloudOrg) return;
        
        setSyncing(true);
        try {
            const response = await axios.post(`${apiUrl}/iiko/cloud/sync`, {
                organization_id: selectedCloudOrg.id,
                user_id: userId
            });
            setSyncStatus(response.data);
        } catch (error) {
            console.error('Cloud sync error:', error);
            setSyncStatus({ status: 'error', error: error.response?.data?.detail });
        } finally {
            setSyncing(false);
        }
    };

    const disconnectCloud = async () => {
        if (!window.confirm('Отключить iikoCloud API?')) return;
        
        setCloudLoading(true);
        try {
            await axios.delete(`${apiUrl}/iiko/cloud/disconnect/${userId}`);
            setCloudStatus({ status: 'not_connected' });
            setCloudOrganizations([]);
            setSelectedCloudOrg(null);
        } catch (error) {
            console.error('Error disconnecting Cloud:', error);
        } finally {
            setCloudLoading(false);
        }
    };

    // ============ RMS FUNCTIONS ============
    const fetchRmsStatus = async () => {
        try {
            const response = await axios.get(`${apiUrl}/iiko/rms/status/${userId}`);
            setRmsStatus(response.data);
            
            if (response.data.status === 'connected' || response.data.status === 'restored') {
                setSelectedOrg({
                    id: response.data.organization_id,
                    name: response.data.organization_name
                });
            }
        } catch (error) {
            console.error('Error fetching RMS status:', error);
            setRmsStatus({ status: 'not_connected' });
        }
    };

    const connectRms = async (e) => {
        e.preventDefault();
        if (!rmsHost.trim() || !rmsLogin.trim() || !rmsPassword.trim()) return;
        
        setRmsLoading(true);
        setRmsError(null);
        
        try {
            const response = await axios.post(`${apiUrl}/iiko/rms/connect`, {
                host: rmsHost,
                login: rmsLogin,
                password: rmsPassword,
                user_id: userId
            });
            
            setRmsStatus({ status: 'connected', ...response.data });
            setOrganizations(response.data.organizations || []);
            setRmsPassword(''); // Clear for security
            
        } catch (error) {
            console.error('RMS connection error:', error);
            setRmsError(error.response?.data?.detail || 'Ошибка подключения');
        } finally {
            setRmsLoading(false);
        }
    };

    const disconnectRms = async () => {
        if (!window.confirm('Отключить iiko RMS Server?')) return;
        
        setRmsLoading(true);
        try {
            await axios.delete(`${apiUrl}/iiko/rms/disconnect/${userId}`);
            setRmsStatus({ status: 'not_connected' });
            setSelectedOrg(null);
        } catch (error) {
            console.error('Error disconnecting RMS:', error);
        } finally {
            setRmsLoading(false);
        }
    };

    const selectOrganization = async (org) => {
        try {
            await axios.post(`${apiUrl}/iiko/rms/select-organization`, {
                organization_id: org.id,
                user_id: userId
            });
            setSelectedOrg(org);
        } catch (error) {
            console.error('Error selecting organization:', error);
        }
    };

    const syncNomenclature = async () => {
        setSyncing(true);
        try {
            const response = await axios.post(`${apiUrl}/iiko/rms/sync`, {
                organization_id: selectedOrg?.id || 'default',
                force: false
            });
            setSyncStatus(response.data);
        } catch (error) {
            console.error('Sync error:', error);
            setSyncStatus({ status: 'error', error: error.response?.data?.detail });
        } finally {
            setSyncing(false);
        }
    };

    // ============ RENDER HELPERS ============
    const renderStatusBadge = (status) => {
        const isConnected = status === 'connected' || status === 'restored';
        return (
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${
                isConnected 
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                    : 'bg-gray-700/50 text-gray-400 border border-gray-600'
            }`}>
                {isConnected ? <Wifi size={14} /> : <WifiOff size={14} />}
                {isConnected ? 'Подключено' : 'Не подключено'}
            </div>
        );
    };

    // ============ RENDER ============
    return (
        <div className="flex-1 overflow-y-auto p-4 md:p-6 bg-gray-900">
            <div className="max-w-4xl mx-auto space-y-6">
                
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">Интеграции</h1>
                        <p className="text-gray-400">Подключите iiko для синхронизации данных вашего ресторана</p>
                    </div>
                    <button 
                        onClick={fetchAllStatuses}
                        className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
                        title="Обновить статус"
                    >
                        <RefreshCw size={20} />
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 p-1 bg-gray-800/50 rounded-lg border border-gray-700">
                    <button
                        onClick={() => setActiveTab('cloud')}
                        className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all ${
                            activeTab === 'cloud'
                                ? 'bg-emerald-600 text-white shadow-lg'
                                : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                        }`}
                    >
                        <Cloud size={18} />
                        iikoCloud API
                    </button>
                    <button
                        onClick={() => setActiveTab('rms')}
                        className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all ${
                            activeTab === 'rms'
                                ? 'bg-emerald-600 text-white shadow-lg'
                                : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                        }`}
                    >
                        <Server size={18} />
                        iiko RMS Server
                    </button>
                </div>

                {/* Cloud API Panel */}
                {activeTab === 'cloud' && (
                    <div className="bg-gray-950 rounded-xl border border-gray-800 overflow-hidden">
                        {/* Header */}
                        <div className="p-6 border-b border-gray-800 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 bg-blue-600/20 rounded-xl flex items-center justify-center">
                                    <Cloud className="text-blue-400" size={24} />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-white">iikoCloud API</h2>
                                    <p className="text-gray-400 text-sm">Облачный API для доступа к данным</p>
                                </div>
                            </div>
                            {renderStatusBadge(cloudStatus?.status)}
                        </div>

                        {/* Content */}
                        <div className="p-6">
                            {cloudStatus?.status === 'connected' ? (
                                <div className="space-y-6">
                                    {/* Connection Info */}
                                    <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                                        <div className="flex items-center justify-between mb-4">
                                            <div>
                                                <p className="text-sm text-gray-400">API Ключ</p>
                                                <p className="text-white font-mono text-sm">{cloudStatus.api_key_masked || '********'}</p>
                                            </div>
                                            <div>
                                                <p className="text-sm text-gray-400">Организаций</p>
                                                <p className="text-white font-bold text-lg">{cloudStatus.organizations_count || 0}</p>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Organization Selection */}
                                    {cloudOrganizations.length > 0 && (
                                        <div>
                                            <label className="block text-gray-300 text-sm font-medium mb-2">
                                                Выберите организацию
                                            </label>
                                            <div className="space-y-2">
                                                {cloudOrganizations.map((org) => (
                                                    <button
                                                        key={org.id}
                                                        onClick={() => selectCloudOrganization(org)}
                                                        className={`w-full flex items-center gap-3 p-3 rounded-lg border transition-all ${
                                                            selectedCloudOrg?.id === org.id
                                                                ? 'bg-emerald-600/20 border-emerald-500/50 text-white'
                                                                : 'bg-gray-800/50 border-gray-700 text-gray-300 hover:bg-gray-800 hover:border-gray-600'
                                                        }`}
                                                    >
                                                        <Building2 size={18} />
                                                        <span className="flex-1 text-left">{org.name}</span>
                                                        {selectedCloudOrg?.id === org.id && (
                                                            <CheckCircle2 size={18} className="text-emerald-400" />
                                                        )}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Selected Organization Info */}
                                    {selectedCloudOrg && (
                                        <div className="bg-emerald-600/10 rounded-lg p-4 border border-emerald-500/30">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <Building2 className="text-emerald-400" size={20} />
                                                    <div>
                                                        <p className="text-white font-medium">{selectedCloudOrg.name}</p>
                                                        <p className="text-emerald-400/80 text-sm">Активная организация</p>
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={syncCloudNomenclature}
                                                    disabled={syncing}
                                                    className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-500 disabled:opacity-50 transition-colors"
                                                >
                                                    {syncing ? (
                                                        <Loader2 size={16} className="animate-spin" />
                                                    ) : (
                                                        <Database size={16} />
                                                    )}
                                                    {syncing ? 'Синхронизация...' : 'Синхронизировать'}
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    {/* Sync Status */}
                                    {syncStatus && (
                                        <div className={`rounded-lg p-4 border ${
                                            syncStatus.status === 'completed' 
                                                ? 'bg-emerald-600/10 border-emerald-500/30' 
                                                : syncStatus.status === 'error'
                                                    ? 'bg-red-600/10 border-red-500/30'
                                                    : 'bg-gray-800/50 border-gray-700'
                                        }`}>
                                            <p className="font-medium text-white mb-2">
                                                {syncStatus.status === 'completed' ? '✅ Синхронизация завершена' : 
                                                 syncStatus.status === 'error' ? '❌ Ошибка синхронизации' :
                                                 '⏳ Синхронизация...'}
                                            </p>
                                            {syncStatus.stats && (
                                                <div className="grid grid-cols-3 gap-4 text-sm">
                                                    <div>
                                                        <p className="text-gray-400">Обработано</p>
                                                        <p className="text-white font-bold">{syncStatus.stats.products_processed || 0}</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-gray-400">Создано</p>
                                                        <p className="text-emerald-400 font-bold">{syncStatus.stats.products_created || 0}</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-gray-400">Групп</p>
                                                        <p className="text-blue-400 font-bold">{syncStatus.stats.groups_count || 0}</p>
                                                    </div>
                                                </div>
                                            )}
                                            {syncStatus.error && (
                                                <p className="text-red-400 text-sm mt-2">{syncStatus.error}</p>
                                            )}
                                        </div>
                                    )}
                                    
                                    <button
                                        onClick={disconnectCloud}
                                        disabled={cloudLoading}
                                        className="flex items-center gap-2 px-4 py-2 bg-red-600/20 text-red-400 rounded-lg hover:bg-red-600/30 transition-colors border border-red-600/30"
                                    >
                                        <Unlink size={16} />
                                        Отключить
                                    </button>
                                </div>
                            ) : (
                                <form onSubmit={connectCloud} className="space-y-4">
                                    <div>
                                        <label className="block text-gray-300 text-sm font-medium mb-2">
                                            API Ключ iikoCloud
                                        </label>
                                        <div className="relative">
                                            <input
                                                type={showCloudKey ? 'text' : 'password'}
                                                value={cloudApiKey}
                                                onChange={(e) => setCloudApiKey(e.target.value)}
                                                placeholder="Введите ваш API ключ"
                                                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setShowCloudKey(!showCloudKey)}
                                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                                            >
                                                {showCloudKey ? <EyeOff size={18} /> : <Eye size={18} />}
                                            </button>
                                        </div>
                                        <p className="mt-2 text-xs text-gray-500">
                                            Получите ключ в личном кабинете iikoCloud → API → Ключи
                                        </p>
                                    </div>

                                    {cloudError && (
                                        <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                                            <AlertCircle size={16} />
                                            {cloudError}
                                        </div>
                                    )}

                                    <button
                                        type="submit"
                                        disabled={cloudLoading || !cloudApiKey.trim()}
                                        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                                    >
                                        {cloudLoading ? (
                                            <>
                                                <Loader2 size={18} className="animate-spin" />
                                                Подключение...
                                            </>
                                        ) : (
                                            <>
                                                <Wifi size={18} />
                                                Подключить
                                            </>
                                        )}
                                    </button>
                                </form>
                            )}
                        </div>
                    </div>
                )}

                {/* RMS Server Panel */}
                {activeTab === 'rms' && (
                    <div className="bg-gray-950 rounded-xl border border-gray-800 overflow-hidden">
                        {/* Header */}
                        <div className="p-6 border-b border-gray-800 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 bg-purple-600/20 rounded-xl flex items-center justify-center">
                                    <Server className="text-purple-400" size={24} />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-white">iiko RMS Server</h2>
                                    <p className="text-gray-400 text-sm">Прямое подключение к серверу iiko</p>
                                </div>
                            </div>
                            {renderStatusBadge(rmsStatus?.status)}
                        </div>

                        {/* Content */}
                        <div className="p-6">
                            {rmsStatus?.status === 'connected' || rmsStatus?.status === 'restored' ? (
                                <div className="space-y-6">
                                    {/* Connection Info */}
                                    <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <p className="text-sm text-gray-400">Сервер</p>
                                                <p className="text-white font-mono text-sm">{rmsStatus.host}</p>
                                            </div>
                                            <div>
                                                <p className="text-sm text-gray-400">Логин</p>
                                                <p className="text-white">{rmsStatus.login}</p>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Organization Selection */}
                                    {organizations.length > 0 && (
                                        <div>
                                            <label className="block text-gray-300 text-sm font-medium mb-2">
                                                Выберите организацию
                                            </label>
                                            <div className="space-y-2">
                                                {organizations.map((org) => (
                                                    <button
                                                        key={org.id}
                                                        onClick={() => selectOrganization(org)}
                                                        className={`w-full flex items-center gap-3 p-3 rounded-lg border transition-all ${
                                                            selectedOrg?.id === org.id
                                                                ? 'bg-emerald-600/20 border-emerald-500/50 text-white'
                                                                : 'bg-gray-800/50 border-gray-700 text-gray-300 hover:bg-gray-800 hover:border-gray-600'
                                                        }`}
                                                    >
                                                        <Building2 size={18} />
                                                        <span className="flex-1 text-left">{org.name}</span>
                                                        {selectedOrg?.id === org.id && (
                                                            <CheckCircle2 size={18} className="text-emerald-400" />
                                                        )}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Selected Organization Info */}
                                    {selectedOrg && (
                                        <div className="bg-emerald-600/10 rounded-lg p-4 border border-emerald-500/30">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <Building2 className="text-emerald-400" size={20} />
                                                    <div>
                                                        <p className="text-white font-medium">{selectedOrg.name || rmsStatus.organization_name}</p>
                                                        <p className="text-emerald-400/80 text-sm">Активная организация</p>
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={syncNomenclature}
                                                    disabled={syncing}
                                                    className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-500 disabled:opacity-50 transition-colors"
                                                >
                                                    {syncing ? (
                                                        <Loader2 size={16} className="animate-spin" />
                                                    ) : (
                                                        <Database size={16} />
                                                    )}
                                                    {syncing ? 'Синхронизация...' : 'Синхронизировать'}
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    {/* Sync Status */}
                                    {syncStatus && (
                                        <div className={`rounded-lg p-4 border ${
                                            syncStatus.status === 'completed' 
                                                ? 'bg-emerald-600/10 border-emerald-500/30' 
                                                : syncStatus.status === 'error'
                                                    ? 'bg-red-600/10 border-red-500/30'
                                                    : 'bg-gray-800/50 border-gray-700'
                                        }`}>
                                            <p className="font-medium text-white mb-2">
                                                {syncStatus.status === 'completed' ? '✅ Синхронизация завершена' : 
                                                 syncStatus.status === 'error' ? '❌ Ошибка синхронизации' :
                                                 '⏳ Синхронизация...'}
                                            </p>
                                            {syncStatus.stats && (
                                                <div className="grid grid-cols-3 gap-4 text-sm">
                                                    <div>
                                                        <p className="text-gray-400">Обработано</p>
                                                        <p className="text-white font-bold">{syncStatus.stats.products_processed}</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-gray-400">Создано</p>
                                                        <p className="text-emerald-400 font-bold">{syncStatus.stats.products_created}</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-gray-400">Обновлено</p>
                                                        <p className="text-blue-400 font-bold">{syncStatus.stats.products_updated}</p>
                                                    </div>
                                                </div>
                                            )}
                                            {syncStatus.error && (
                                                <p className="text-red-400 text-sm mt-2">{syncStatus.error}</p>
                                            )}
                                        </div>
                                    )}

                                    <button
                                        onClick={disconnectRms}
                                        disabled={rmsLoading}
                                        className="flex items-center gap-2 px-4 py-2 bg-red-600/20 text-red-400 rounded-lg hover:bg-red-600/30 transition-colors border border-red-600/30"
                                    >
                                        <Unlink size={16} />
                                        Отключить
                                    </button>
                                </div>
                            ) : (
                                <form onSubmit={connectRms} className="space-y-4">
                                    <div>
                                        <label className="block text-gray-300 text-sm font-medium mb-2">
                                            Адрес сервера
                                        </label>
                                        <input
                                            type="text"
                                            value={rmsHost}
                                            onChange={(e) => setRmsHost(e.target.value)}
                                            placeholder="https://your-server.iiko.it"
                                            className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                                        />
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-gray-300 text-sm font-medium mb-2">
                                                Логин
                                            </label>
                                            <input
                                                type="text"
                                                value={rmsLogin}
                                                onChange={(e) => setRmsLogin(e.target.value)}
                                                placeholder="admin"
                                                className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-gray-300 text-sm font-medium mb-2">
                                                Пароль
                                            </label>
                                            <div className="relative">
                                                <input
                                                    type={showRmsPassword ? 'text' : 'password'}
                                                    value={rmsPassword}
                                                    onChange={(e) => setRmsPassword(e.target.value)}
                                                    placeholder="••••••••"
                                                    className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                                                />
                                                <button
                                                    type="button"
                                                    onClick={() => setShowRmsPassword(!showRmsPassword)}
                                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                                                >
                                                    {showRmsPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                                </button>
                                            </div>
                                        </div>
                                    </div>

                                    {rmsError && (
                                        <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                                            <AlertCircle size={16} />
                                            {rmsError}
                                        </div>
                                    )}

                                    <button
                                        type="submit"
                                        disabled={rmsLoading || !rmsHost.trim() || !rmsLogin.trim() || !rmsPassword.trim()}
                                        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                                    >
                                        {rmsLoading ? (
                                            <>
                                                <Loader2 size={18} className="animate-spin" />
                                                Подключение...
                                            </>
                                        ) : (
                                            <>
                                                <Wifi size={18} />
                                                Подключить
                                            </>
                                        )}
                                    </button>

                                    <p className="text-xs text-gray-500 text-center">
                                        Данные для подключения можно найти в настройках iiko BackOffice
                                    </p>
                                </form>
                            )}
                        </div>
                    </div>
                )}

                {/* Help Section */}
                <div className="bg-gray-800/30 rounded-xl border border-gray-700/50 p-6">
                    <h3 className="text-lg font-medium text-white mb-3">💡 Какой тип подключения выбрать?</h3>
                    <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-400">
                        <div>
                            <p className="font-medium text-blue-400 mb-1">iikoCloud API</p>
                            <p>Облачное решение. Рекомендуется для современных установок iiko. Нужен API-ключ из личного кабинета.</p>
                        </div>
                        <div>
                            <p className="font-medium text-purple-400 mb-1">iiko RMS Server</p>
                            <p>Прямое подключение к серверу. Для локальных серверов iiko. Нужен адрес сервера и учетные данные.</p>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}

export default Integrations;

