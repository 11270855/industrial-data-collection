/**
 * 报警管理页面脚本
 * 负责报警列表显示、过滤、确认和通知功能
 */

// 全局变量
let alarmsData = [];
let currentFilter = 'all'; // all, warning, critical, emergency
let currentPage = 1;
let totalPages = 1;
const pageSize = 20;
let updateInterval = null;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    loadAlarms();
    startAutoUpdate();
    setupEventListeners();
    requestNotificationPermission();
});

/**
 * 请求浏览器通知权限
 */
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

/**
 * 显示浏览器通知
 */
function showBrowserNotification(alarm) {
    if ('Notification' in window && Notification.permission === 'granted') {
        const levelMap = {
            'warning': '⚠️ 警告',
            'critical': '🔶 严重',
            'emergency': '🚨 紧急'
        };
        
        const title = levelMap[alarm.alarm_level] || '报警';
        const options = {
            body: alarm.message,
            icon: '/static/favicon.ico',
            badge: '/static/favicon.ico',
            tag: `alarm-${alarm.id}`,
            requireInteraction: alarm.alarm_level === 'emergency'
        };
        
        const notification = new Notification(title, options);
        
        notification.onclick = function() {
            window.focus();
            notification.close();
        };
    }
}

/**
 * 设置事件监听器
 */
function setupEventListeners() {
    // 过滤按钮
    document.querySelectorAll('[data-filter]').forEach(button => {
        button.addEventListener('click', function() {
            currentFilter = this.dataset.filter;
            currentPage = 1;
            
            // 更新按钮样式
            document.querySelectorAll('[data-filter]').forEach(btn => {
                btn.classList.remove('bg-blue-600', 'text-white');
                btn.classList.add('bg-gray-200', 'text-gray-700');
            });
            this.classList.remove('bg-gray-200', 'text-gray-700');
            this.classList.add('bg-blue-600', 'text-white');
            
            loadAlarms();
        });
    });
    
    // 刷新按钮
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadAlarms();
        });
    }
}

/**
 * 加载报警数据
 */
async function loadAlarms() {
    try {
        showLoading();
        
        // 构建查询参数
        const params = new URLSearchParams({
            page: currentPage,
            page_size: pageSize
        });
        
        if (currentFilter !== 'all') {
            params.append('alarm_level', currentFilter);
        }
        
        const response = await fetch(`/api/alarms?${params}`);
        if (response.ok) {
            const data = await response.json();
            alarmsData = data.alarms || [];
            const pagination = data.pagination || {};
            totalPages = pagination.total_pages || Math.ceil((pagination.total || 0) / pageSize);
            
            renderAlarms();
            renderPagination();
            updateStatistics(data);
            
            // 检查新报警并显示通知
            checkNewAlarms(alarmsData);
        } else {
            showError('加载报警数据失败');
        }
    } catch (error) {
        console.error('加载报警失败:', error);
        showError('网络错误，请稍后重试');
    }
}

/**
 * 渲染报警列表
 */
function renderAlarms() {
    const container = document.getElementById('alarmsContainer');
    if (!container) return;
    
    if (alarmsData.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12">
                <i class="fas fa-check-circle text-6xl text-green-500 mb-4"></i>
                <p class="text-xl text-gray-600">暂无报警</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = alarmsData.map(alarm => {
        const levelConfig = getLevelConfig(alarm.alarm_level);
        const time = new Date(alarm.timestamp).toLocaleString('zh-CN');
        const acknowledged = alarm.acknowledged;
        
        return `
            <div class="bg-white rounded-lg shadow-md p-4 border-l-4 ${levelConfig.borderColor} hover:shadow-lg transition">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center mb-2">
                            <i class="fas ${levelConfig.icon} ${levelConfig.textColor} text-xl mr-3"></i>
                            <span class="px-3 py-1 rounded-full text-xs font-semibold ${levelConfig.bgColor} ${levelConfig.textColor}">
                                ${levelConfig.label}
                            </span>
                            ${acknowledged ? '<span class="ml-2 px-2 py-1 bg-gray-200 text-gray-600 rounded text-xs"><i class="fas fa-check mr-1"></i>已确认</span>' : ''}
                        </div>
                        <h4 class="text-lg font-semibold text-gray-800 mb-2">${alarm.message}</h4>
                        <div class="grid grid-cols-2 gap-2 text-sm text-gray-600 mb-2">
                            <div><i class="fas fa-microchip mr-2"></i>设备: ${alarm.device_id}</div>
                            <div><i class="fas fa-clock mr-2"></i>${time}</div>
                            ${alarm.threshold_value ? `<div><i class="fas fa-chart-line mr-2"></i>阈值: ${alarm.threshold_value}</div>` : ''}
                            ${alarm.actual_value ? `<div><i class="fas fa-tachometer-alt mr-2"></i>实际值: ${alarm.actual_value}</div>` : ''}
                        </div>
                        ${acknowledged ? `
                            <div class="text-xs text-gray-500 mt-2">
                                <i class="fas fa-user mr-1"></i>确认人: ${alarm.acknowledged_by || 'N/A'} | 
                                <i class="fas fa-calendar mr-1"></i>${new Date(alarm.acknowledged_at).toLocaleString('zh-CN')}
                            </div>
                        ` : ''}
                    </div>
                    <div class="ml-4">
                        ${!acknowledged ? `
                            <button onclick="acknowledgeAlarm(${alarm.id})" 
                                    class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition">
                                <i class="fas fa-check mr-2"></i>确认
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * 获取报警级别配置
 */
function getLevelConfig(level) {
    const configs = {
        'warning': {
            label: '警告',
            icon: 'fa-exclamation-triangle',
            textColor: 'text-yellow-600',
            bgColor: 'bg-yellow-100',
            borderColor: 'border-yellow-500'
        },
        'critical': {
            label: '严重',
            icon: 'fa-exclamation-circle',
            textColor: 'text-orange-600',
            bgColor: 'bg-orange-100',
            borderColor: 'border-orange-500'
        },
        'emergency': {
            label: '紧急',
            icon: 'fa-times-circle',
            textColor: 'text-red-600',
            bgColor: 'bg-red-100',
            borderColor: 'border-red-500'
        }
    };
    return configs[level] || configs['warning'];
}

/**
 * 确认报警
 */
async function acknowledgeAlarm(alarmId) {
    try {
        const response = await fetch(`/api/alarms/${alarmId}/acknowledge`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showSuccess('报警已确认');
            loadAlarms();
        } else {
            const data = await response.json();
            showError(data.error || '确认失败');
        }
    } catch (error) {
        console.error('确认报警失败:', error);
        showError('网络错误，请稍后重试');
    }
}

/**
 * 渲染分页
 */
function renderPagination() {
    const container = document.getElementById('paginationContainer');
    if (!container) return;
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '<div class="flex justify-center items-center space-x-2">';
    
    // 上一页按钮
    html += `
        <button onclick="changePage(${currentPage - 1})" 
                ${currentPage === 1 ? 'disabled' : ''}
                class="px-3 py-2 rounded ${currentPage === 1 ? 'bg-gray-200 text-gray-400 cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700'}">
            <i class="fas fa-chevron-left"></i>
        </button>
    `;
    
    // 页码按钮
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            html += `
                <button onclick="changePage(${i})" 
                        class="px-4 py-2 rounded ${i === currentPage ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}">
                    ${i}
                </button>
            `;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            html += '<span class="px-2">...</span>';
        }
    }
    
    // 下一页按钮
    html += `
        <button onclick="changePage(${currentPage + 1})" 
                ${currentPage === totalPages ? 'disabled' : ''}
                class="px-3 py-2 rounded ${currentPage === totalPages ? 'bg-gray-200 text-gray-400 cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700'}">
            <i class="fas fa-chevron-right"></i>
        </button>
    `;
    
    html += '</div>';
    container.innerHTML = html;
}

/**
 * 切换页码
 */
function changePage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    loadAlarms();
}

/**
 * 更新统计信息
 */
function updateStatistics(data) {
    const stats = data.statistics || {};
    const byLevel = stats.by_level || {};
    
    const totalElement = document.getElementById('totalAlarms');
    if (totalElement) {
        const pagination = data.pagination || {};
        totalElement.textContent = pagination.total || 0;
    }
    
    const warningElement = document.getElementById('warningCount');
    if (warningElement) {
        warningElement.textContent = byLevel.warning || 0;
    }
    
    const criticalElement = document.getElementById('criticalCount');
    if (criticalElement) {
        criticalElement.textContent = byLevel.critical || 0;
    }
    
    const emergencyElement = document.getElementById('emergencyCount');
    if (emergencyElement) {
        emergencyElement.textContent = byLevel.emergency || 0;
    }
}

/**
 * 检查新报警并显示通知
 */
let lastAlarmIds = new Set();

function checkNewAlarms(alarms) {
    const currentAlarmIds = new Set(alarms.map(a => a.id));
    
    // 找出新报警
    alarms.forEach(alarm => {
        if (!lastAlarmIds.has(alarm.id) && !alarm.acknowledged) {
            // 显示浏览器通知
            showBrowserNotification(alarm);
            
            // 显示页面内通知
            showAlarmToast(alarm);
        }
    });
    
    lastAlarmIds = currentAlarmIds;
}

/**
 * 显示页面内报警提示
 */
function showAlarmToast(alarm) {
    const levelConfig = getLevelConfig(alarm.alarm_level);
    
    const toast = document.createElement('div');
    toast.className = `fixed top-20 right-4 max-w-md bg-white rounded-lg shadow-2xl p-4 border-l-4 ${levelConfig.borderColor} z-50 animate-slide-in`;
    toast.innerHTML = `
        <div class="flex items-start">
            <i class="fas ${levelConfig.icon} ${levelConfig.textColor} text-2xl mr-3 mt-1"></i>
            <div class="flex-1">
                <h4 class="font-bold ${levelConfig.textColor} mb-1">${levelConfig.label}报警</h4>
                <p class="text-sm text-gray-700">${alarm.message}</p>
                <p class="text-xs text-gray-500 mt-1">${alarm.device_id}</p>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-gray-400 hover:text-gray-600">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // 5秒后自动移除
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 5000);
}

/**
 * 启动自动更新
 */
function startAutoUpdate() {
    // 每5秒更新一次
    updateInterval = setInterval(() => {
        loadAlarms();
    }, 5000);
}

/**
 * 显示加载状态
 */
function showLoading() {
    const container = document.getElementById('alarmsContainer');
    if (container) {
        container.innerHTML = `
            <div class="text-center py-12">
                <i class="fas fa-spinner fa-spin text-4xl text-blue-600 mb-4"></i>
                <p class="text-gray-600">加载中...</p>
            </div>
        `;
    }
}

/**
 * 显示错误信息
 */
function showError(message) {
    const container = document.getElementById('alarmsContainer');
    if (container) {
        container.innerHTML = `
            <div class="text-center py-12">
                <i class="fas fa-exclamation-triangle text-4xl text-red-600 mb-4"></i>
                <p class="text-gray-600">${message}</p>
            </div>
        `;
    }
}

/**
 * 显示成功消息
 */
function showSuccess(message) {
    const toast = document.createElement('div');
    toast.className = 'fixed top-20 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    toast.innerHTML = `<i class="fas fa-check-circle mr-2"></i>${message}`;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// 页面卸载时清理定时器
window.addEventListener('beforeunload', function() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slide-in {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    .animate-slide-in {
        animation: slide-in 0.3s ease-out;
    }
`;
document.head.appendChild(style);
