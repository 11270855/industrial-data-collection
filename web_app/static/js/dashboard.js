/**
 * 仪表盘实时数据更新脚本
 * 负责从API获取数据并更新页面显示
 */

// 全局变量
let energyChart = null;
let oeeChart = null;
let updateInterval = null;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initCharts();
    loadInitialData();
    startAutoUpdate();
    requestNotificationPermission();
});

/**
 * 初始化图表
 */
function initCharts() {
    // 初始化能耗趋势图
    const energyCtx = document.getElementById('energyChart');
    if (energyCtx) {
        energyChart = new Chart(energyCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '传送带',
                        data: [],
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: '工位1',
                        data: [],
                        borderColor: 'rgb(249, 115, 22)',
                        backgroundColor: 'rgba(249, 115, 22, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: '工位2',
                        data: [],
                        borderColor: 'rgb(239, 68, 68)',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    title: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '功率 (kW)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: '时间'
                        }
                    }
                }
            }
        });
    }
    
    // 初始化OEE图表
    const oeeCtx = document.getElementById('oeeChart');
    if (oeeCtx) {
        oeeChart = new Chart(oeeCtx, {
            type: 'bar',
            data: {
                labels: ['可用率', '性能率', '质量率', 'OEE'],
                datasets: [{
                    label: '百分比',
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        'rgba(34, 197, 94, 0.7)',
                        'rgba(59, 130, 246, 0.7)',
                        'rgba(168, 85, 247, 0.7)',
                        'rgba(249, 115, 22, 0.7)'
                    ],
                    borderColor: [
                        'rgb(34, 197, 94)',
                        'rgb(59, 130, 246)',
                        'rgb(168, 85, 247)',
                        'rgb(249, 115, 22)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: '百分比 (%)'
                        }
                    }
                }
            }
        });
    }
}

/**
 * 加载初始数据
 */
async function loadInitialData() {
    await updateDeviceData();
    await updateAlarms();
    await updateProductionStats();
}

/**
 * 启动自动更新
 */
function startAutoUpdate() {
    // 每2秒更新一次数据
    updateInterval = setInterval(async () => {
        await updateDeviceData();
        await updateAlarms();
        await updateProductionStats();
    }, 2000);
}

/**
 * 更新设备数据
 */
async function updateDeviceData() {
    try {
        // 获取传送带数据
        const conveyorResponse = await fetch('/api/devices/conveyor/current');
        if (conveyorResponse.ok) {
            const conveyorData = await conveyorResponse.json();
            updateDeviceCard('conveyor', conveyorData);
        }
        
        // 获取工位1数据
        const station1Response = await fetch('/api/devices/station1/current');
        if (station1Response.ok) {
            const station1Data = await station1Response.json();
            updateDeviceCard('station1', station1Data);
        }
        
        // 获取工位2数据
        const station2Response = await fetch('/api/devices/station2/current');
        if (station2Response.ok) {
            const station2Data = await station2Response.json();
            updateDeviceCard('station2', station2Data);
        }
        
        // 更新能耗趋势图
        updateEnergyChart();
        
    } catch (error) {
        console.error('更新设备数据失败:', error);
    }
}

/**
 * 更新设备卡片显示
 */
function updateDeviceCard(deviceId, data) {
    if (!data) return;
    
    const prefix = deviceId === 'conveyor' ? 'conveyor' : deviceId;
    
    // 更新状态
    const statusElement = document.getElementById(`${prefix}Status`);
    if (statusElement && data.status) {
        const statusMap = {
            'running': { text: '运行中', class: 'bg-green-500 text-white' },
            'standby': { text: '待机', class: 'bg-gray-400 text-white' },
            'fault': { text: '故障', class: 'bg-red-500 text-white' }
        };
        const status = statusMap[data.status] || statusMap['standby'];
        statusElement.innerHTML = `<i class="fas fa-circle mr-1"></i>${status.text}`;
        statusElement.className = `px-3 py-1 rounded-full text-sm font-semibold ${status.class}`;
    }
    
    // 更新功率
    if (data.power !== undefined) {
        const powerElement = document.getElementById(`${prefix}Power`);
        if (powerElement) {
            powerElement.textContent = `${data.power.toFixed(1)} kW`;
        }
        
        // 更新功率条
        const powerBar = document.getElementById(`${prefix}PowerBar`);
        if (powerBar) {
            const maxPower = deviceId === 'conveyor' ? 5 : 10;
            const percentage = Math.min((data.power / maxPower) * 100, 100);
            powerBar.style.width = `${percentage}%`;
        }
    }
    
    // 更新能耗
    if (data.energy !== undefined) {
        const energyElement = document.getElementById(`${prefix}Energy`);
        if (energyElement) {
            energyElement.textContent = `${data.energy.toFixed(1)} kWh`;
        }
    }
    
    // 更新速度（仅传送带）
    if (deviceId === 'conveyor' && data.speed !== undefined) {
        const speedElement = document.getElementById('conveyorSpeed');
        if (speedElement) {
            speedElement.textContent = `${data.speed.toFixed(1)} m/s`;
        }
    }
    
    // 更新激活状态（仅工位）
    if (deviceId !== 'conveyor' && data.active !== undefined) {
        const activeElement = document.getElementById(`${prefix}Active`);
        if (activeElement) {
            activeElement.textContent = data.active ? '激活' : '未激活';
            activeElement.className = data.active ? 'font-bold text-lg text-green-600' : 'font-bold text-lg text-gray-600';
        }
    }
}

/**
 * 更新能耗趋势图
 */
async function updateEnergyChart() {
    if (!energyChart) return;
    
    try {
        const now = new Date();
        const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
        
        const response = await fetch(`/api/energy/summary?start_time=${oneHourAgo.toISOString()}&end_time=${now.toISOString()}`);
        if (response.ok) {
            const data = await response.json();
            
            if (data.trend && data.trend.length > 0) {
                const labels = data.trend.map(item => {
                    const time = new Date(item.timestamp);
                    return time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
                });
                
                energyChart.data.labels = labels;
                energyChart.data.datasets[0].data = data.trend.map(item => item.conveyor || 0);
                energyChart.data.datasets[1].data = data.trend.map(item => item.station1 || 0);
                energyChart.data.datasets[2].data = data.trend.map(item => item.station2 || 0);
                energyChart.update('none');
            }
        }
    } catch (error) {
        console.error('更新能耗趋势图失败:', error);
    }
}

/**
 * 更新报警列表
 */
let lastAlarmIds = new Set();

async function updateAlarms() {
    try {
        const response = await fetch('/api/alarms?page_size=5&acknowledged=false');
        if (response.ok) {
            const data = await response.json();
            const alarmsList = document.getElementById('alarmsList');
            
            if (data.alarms && data.alarms.length > 0) {
                // 检查新报警并显示通知
                checkNewAlarms(data.alarms);
                
                alarmsList.innerHTML = data.alarms.map(alarm => {
                    const levelConfig = getAlarmLevelConfig(alarm.alarm_level);
                    const time = new Date(alarm.timestamp).toLocaleTimeString('zh-CN');
                    
                    return `
                        <div class="border-l-4 ${levelConfig.borderColor} ${levelConfig.bgColor} p-3 rounded hover:shadow-md transition cursor-pointer" onclick="acknowledgeAlarmFromDashboard(${alarm.id})">
                            <div class="flex items-start justify-between">
                                <div class="flex items-start flex-1">
                                    <i class="fas ${levelConfig.icon} ${levelConfig.textColor} mt-1 mr-2"></i>
                                    <div class="flex-1">
                                        <p class="font-semibold text-sm text-gray-800">${alarm.message}</p>
                                        <p class="text-xs text-gray-600 mt-1">
                                            <i class="fas fa-microchip mr-1"></i>${alarm.device_id} | 
                                            <i class="fas fa-clock mr-1"></i>${time}
                                        </p>
                                    </div>
                                </div>
                                <button onclick="event.stopPropagation(); acknowledgeAlarmFromDashboard(${alarm.id})" 
                                        class="ml-2 px-2 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition"
                                        title="确认报警">
                                    <i class="fas fa-check"></i>
                                </button>
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                alarmsList.innerHTML = `
                    <div class="text-center text-gray-500 py-8">
                        <i class="fas fa-check-circle text-4xl mb-2"></i>
                        <p>暂无报警</p>
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('更新报警列表失败:', error);
    }
}

/**
 * 获取报警级别配置
 */
function getAlarmLevelConfig(level) {
    const configs = {
        'warning': {
            icon: 'fa-exclamation-triangle',
            textColor: 'text-yellow-600',
            bgColor: 'bg-yellow-50',
            borderColor: 'border-yellow-500'
        },
        'critical': {
            icon: 'fa-exclamation-circle',
            textColor: 'text-orange-600',
            bgColor: 'bg-orange-50',
            borderColor: 'border-orange-500'
        },
        'emergency': {
            icon: 'fa-times-circle',
            textColor: 'text-red-600',
            bgColor: 'bg-red-50',
            borderColor: 'border-red-500'
        }
    };
    return configs[level] || configs['warning'];
}

/**
 * 检查新报警并显示通知
 */
function checkNewAlarms(alarms) {
    const currentAlarmIds = new Set(alarms.map(a => a.id));
    
    // 找出新报警
    alarms.forEach(alarm => {
        if (!lastAlarmIds.has(alarm.id) && !alarm.acknowledged) {
            // 显示浏览器通知
            showBrowserNotification(alarm);
            
            // 显示页面内弹窗通知
            showAlarmPopup(alarm);
        }
    });
    
    lastAlarmIds = currentAlarmIds;
}

/**
 * 请求浏览器通知权限
 */
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                console.log('浏览器通知权限已授予');
            }
        });
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
        
        const title = `${levelMap[alarm.alarm_level] || '报警'} - 能源管理系统`;
        const options = {
            body: `${alarm.device_id}: ${alarm.message}`,
            icon: '/static/favicon.ico',
            badge: '/static/favicon.ico',
            tag: `alarm-${alarm.id}`,
            requireInteraction: alarm.alarm_level === 'emergency',
            vibrate: [200, 100, 200]
        };
        
        const notification = new Notification(title, options);
        
        notification.onclick = function() {
            window.focus();
            // 可选：跳转到报警详情页
            // window.location.href = '/alarms';
            notification.close();
        };
        
        // 自动关闭（除非是紧急报警）
        if (alarm.alarm_level !== 'emergency') {
            setTimeout(() => notification.close(), 10000);
        }
    }
}

/**
 * 显示页面内报警弹窗
 */
function showAlarmPopup(alarm) {
    const levelConfig = getAlarmLevelConfig(alarm.alarm_level);
    const levelText = {
        'warning': '警告',
        'critical': '严重',
        'emergency': '紧急'
    };
    
    const popup = document.createElement('div');
    popup.className = `fixed top-20 right-4 max-w-md bg-white rounded-lg shadow-2xl p-4 border-l-4 ${levelConfig.borderColor} z-50 animate-slide-in`;
    popup.style.animation = 'slideIn 0.3s ease-out';
    popup.innerHTML = `
        <div class="flex items-start">
            <i class="fas ${levelConfig.icon} ${levelConfig.textColor} text-2xl mr-3 mt-1"></i>
            <div class="flex-1">
                <div class="flex items-center justify-between mb-2">
                    <h4 class="font-bold ${levelConfig.textColor}">${levelText[alarm.alarm_level] || '报警'}</h4>
                    <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-gray-600">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <p class="text-sm text-gray-800 font-semibold mb-1">${alarm.message}</p>
                <p class="text-xs text-gray-600 mb-3">
                    <i class="fas fa-microchip mr-1"></i>${alarm.device_id} | 
                    <i class="fas fa-clock mr-1"></i>${new Date(alarm.timestamp).toLocaleTimeString('zh-CN')}
                </p>
                ${alarm.threshold_value ? `<p class="text-xs text-gray-600 mb-1"><i class="fas fa-chart-line mr-1"></i>阈值: ${alarm.threshold_value}</p>` : ''}
                ${alarm.actual_value ? `<p class="text-xs text-gray-600 mb-3"><i class="fas fa-tachometer-alt mr-1"></i>实际值: ${alarm.actual_value}</p>` : ''}
                <div class="flex space-x-2">
                    <button onclick="acknowledgeAlarmFromPopup(${alarm.id}, this.closest('.fixed'))" 
                            class="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition">
                        <i class="fas fa-check mr-1"></i>确认
                    </button>
                    <button onclick="this.closest('.fixed').remove()" 
                            class="px-3 py-2 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300 transition">
                        关闭
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(popup);
    
    // 播放提示音（可选）
    playAlarmSound(alarm.alarm_level);
    
    // 自动移除（紧急报警不自动移除）
    if (alarm.alarm_level !== 'emergency') {
        setTimeout(() => {
            if (popup.parentElement) {
                popup.style.animation = 'slideOut 0.3s ease-in';
                setTimeout(() => popup.remove(), 300);
            }
        }, 10000);
    }
}

/**
 * 播放报警提示音
 */
function playAlarmSound(level) {
    // 使用Web Audio API播放简单的提示音
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // 根据报警级别设置不同的频率
        const frequencies = {
            'warning': 440,    // A4
            'critical': 554,   // C#5
            'emergency': 659   // E5
        };
        
        oscillator.frequency.value = frequencies[level] || 440;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
        console.log('无法播放提示音:', error);
    }
}

/**
 * 从仪表盘确认报警
 */
async function acknowledgeAlarmFromDashboard(alarmId) {
    try {
        const response = await fetch(`/api/alarms/${alarmId}/acknowledge`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showSuccessToast('报警已确认');
            // 立即刷新报警列表
            await updateAlarms();
        } else {
            const data = await response.json();
            showErrorToast(data.error || '确认失败');
        }
    } catch (error) {
        console.error('确认报警失败:', error);
        showErrorToast('网络错误，请稍后重试');
    }
}

/**
 * 从弹窗确认报警
 */
async function acknowledgeAlarmFromPopup(alarmId, popupElement) {
    try {
        const response = await fetch(`/api/alarms/${alarmId}/acknowledge`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showSuccessToast('报警已确认');
            popupElement.remove();
            // 立即刷新报警列表
            await updateAlarms();
        } else {
            const data = await response.json();
            showErrorToast(data.error || '确认失败');
        }
    } catch (error) {
        console.error('确认报警失败:', error);
        showErrorToast('网络错误，请稍后重试');
    }
}

/**
 * 显示成功提示
 */
function showSuccessToast(message) {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    toast.innerHTML = `<i class="fas fa-check-circle mr-2"></i>${message}`;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * 显示错误提示
 */
function showErrorToast(message) {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    toast.innerHTML = `<i class="fas fa-exclamation-circle mr-2"></i>${message}`;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * 更新生产统计
 */
async function updateProductionStats() {
    try {
        const response = await fetch('/api/oee');
        if (response.ok) {
            const data = await response.json();
            
            // 更新产品计数
            if (data.product_count !== undefined) {
                document.getElementById('productCount').textContent = data.product_count;
            }
            
            // 更新不良品计数
            if (data.reject_count !== undefined) {
                document.getElementById('rejectCount').textContent = data.reject_count;
            }
            
            // 更新运行时间
            if (data.runtime_seconds !== undefined) {
                const hours = Math.floor(data.runtime_seconds / 3600);
                const minutes = Math.floor((data.runtime_seconds % 3600) / 60);
                document.getElementById('runTime').textContent = `${hours}h ${minutes}m`;
            }
            
            // 更新停机时间
            if (data.downtime_seconds !== undefined) {
                const hours = Math.floor(data.downtime_seconds / 3600);
                const minutes = Math.floor((data.downtime_seconds % 3600) / 60);
                document.getElementById('downTime').textContent = `${hours}h ${minutes}m`;
            }
            
            // 更新合格率
            if (data.quality_rate !== undefined) {
                document.getElementById('qualityRate').textContent = `${data.quality_rate.toFixed(1)}%`;
            }
            
            // 更新OEE图表
            if (oeeChart && data.availability !== undefined) {
                oeeChart.data.datasets[0].data = [
                    data.availability || 0,
                    data.performance || 0,
                    data.quality_rate || 0,
                    data.oee_percentage || 0
                ];
                oeeChart.update('none');
                
                // 更新OEE值显示
                document.getElementById('oeeValue').textContent = `${(data.oee_percentage || 0).toFixed(1)}%`;
            }
        }
    } catch (error) {
        console.error('更新生产统计失败:', error);
    }
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
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .animate-slide-in {
        animation: slideIn 0.3s ease-out;
    }
`;
document.head.appendChild(style);
