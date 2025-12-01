/**
 * 历史数据查询脚本
 * 负责历史数据的查询、展示和导出功能
 */

// 全局变量
let historyChart = null;
let currentChartType = 'line';
let historyData = [];
let currentPage = 1;
let totalPages = 1;
const pageSize = 50;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
    initializeChart();
    setupEventListeners();
});

/**
 * 初始化页面
 */
function initializePage() {
    // 设置默认时间范围为最近24小时
    const now = new Date();
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    
    document.getElementById('endTime').value = formatDateTimeLocal(now);
    document.getElementById('startTime').value = formatDateTimeLocal(yesterday);
}

/**
 * 格式化日期时间为datetime-local输入格式
 */
function formatDateTimeLocal(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

/**
 * 初始化图表
 */
function initializeChart() {
    const ctx = document.getElementById('historyChart');
    if (!ctx) return;
    
    historyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '功率 (kW)',
                data: [],
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 3,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y.toFixed(2) + ' kW';
                            }
                            return label;
                        }
                    }
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
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

/**
 * 设置事件监听器
 */
function setupEventListeners() {
    // 快捷时间选择
    document.getElementById('quickSelect').addEventListener('change', function(e) {
        const value = e.target.value;
        if (!value) return;
        
        const now = new Date();
        let startTime = new Date();
        
        switch(value) {
            case '1h':
                startTime = new Date(now.getTime() - 60 * 60 * 1000);
                break;
            case '6h':
                startTime = new Date(now.getTime() - 6 * 60 * 60 * 1000);
                break;
            case '24h':
                startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                break;
            case '7d':
                startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                break;
            case '30d':
                startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                break;
        }
        
        document.getElementById('startTime').value = formatDateTimeLocal(startTime);
        document.getElementById('endTime').value = formatDateTimeLocal(now);
    });
    
    // 回车键触发查询
    document.getElementById('startTime').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') queryHistory();
    });
    
    document.getElementById('endTime').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') queryHistory();
    });
}

/**
 * 查询历史数据
 */
async function queryHistory() {
    const deviceId = document.getElementById('deviceSelect').value;
    const startTime = document.getElementById('startTime').value;
    const endTime = document.getElementById('endTime').value;
    
    // 验证输入
    if (!startTime || !endTime) {
        showErrorToast('请选择开始时间和结束时间');
        return;
    }
    
    const startDate = new Date(startTime);
    const endDate = new Date(endTime);
    
    if (startDate >= endDate) {
        showErrorToast('开始时间必须早于结束时间');
        return;
    }
    
    // 显示加载状态
    showLoading(true);
    
    try {
        // 构建查询URL
        const params = new URLSearchParams({
            start_time: startDate.toISOString(),
            end_time: endDate.toISOString()
        });
        
        const response = await fetch(`/api/devices/${deviceId}/history?${params}`);
        
        if (!response.ok) {
            throw new Error('查询失败');
        }
        
        const data = await response.json();
        
        // 保存数据
        historyData = data.data || [];
        
        // 更新统计信息
        updateStatistics(historyData);
        
        // 更新图表
        updateChart(historyData);
        
        // 更新表格
        currentPage = 1;
        updateTable();
        
        showSuccessToast(`成功加载 ${historyData.length} 条数据`);
        
    } catch (error) {
        console.error('查询历史数据失败:', error);
        showErrorToast('查询失败，请稍后重试');
    } finally {
        showLoading(false);
    }
}

/**
 * 更新统计信息
 */
function updateStatistics(data) {
    if (!data || data.length === 0) {
        document.getElementById('dataPointCount').textContent = '0';
        document.getElementById('avgPower').textContent = '0.0 kW';
        document.getElementById('totalEnergy').textContent = '0.0 kWh';
        document.getElementById('maxPower').textContent = '0.0 kW';
        return;
    }
    
    // 数据点数
    document.getElementById('dataPointCount').textContent = data.length;
    
    // 计算平均功率
    const avgPower = data.reduce((sum, item) => sum + (item.power_kw || 0), 0) / data.length;
    document.getElementById('avgPower').textContent = avgPower.toFixed(1) + ' kW';
    
    // 计算总能耗（使用最后一条记录的累计能耗）
    const totalEnergy = data.length > 0 ? (data[data.length - 1].energy_kwh || 0) : 0;
    document.getElementById('totalEnergy').textContent = totalEnergy.toFixed(1) + ' kWh';
    
    // 计算峰值功率
    const maxPower = Math.max(...data.map(item => item.power_kw || 0));
    document.getElementById('maxPower').textContent = maxPower.toFixed(1) + ' kW';
}

/**
 * 更新图表
 */
function updateChart(data) {
    if (!historyChart || !data || data.length === 0) {
        if (historyChart) {
            historyChart.data.labels = [];
            historyChart.data.datasets[0].data = [];
            historyChart.update();
        }
        return;
    }
    
    // 如果数据点太多，进行采样
    let sampledData = data;
    if (data.length > 200) {
        const step = Math.ceil(data.length / 200);
        sampledData = data.filter((_, index) => index % step === 0);
    }
    
    // 准备图表数据
    const labels = sampledData.map(item => {
        const date = new Date(item.timestamp);
        return date.toLocaleString('zh-CN', { 
            month: '2-digit', 
            day: '2-digit', 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    });
    
    const powerData = sampledData.map(item => item.power_kw || 0);
    
    // 更新图表
    historyChart.data.labels = labels;
    historyChart.data.datasets[0].data = powerData;
    historyChart.update();
}

/**
 * 更新数据表格
 */
function updateTable() {
    const tbody = document.getElementById('dataTableBody');
    
    if (!historyData || historyData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-8 text-center text-gray-500">
                    <i class="fas fa-inbox text-4xl mb-2"></i>
                    <p>暂无数据</p>
                </td>
            </tr>
        `;
        document.getElementById('paginationContainer').classList.add('hidden');
        document.getElementById('tableInfo').textContent = '显示 0 条记录';
        return;
    }
    
    // 计算分页
    totalPages = Math.ceil(historyData.length / pageSize);
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = Math.min(startIndex + pageSize, historyData.length);
    const pageData = historyData.slice(startIndex, endIndex);
    
    // 生成表格行
    tbody.innerHTML = pageData.map(item => {
        const time = new Date(item.timestamp).toLocaleString('zh-CN');
        const deviceName = getDeviceName(item.device_id);
        const power = (item.power_kw || 0).toFixed(2);
        const energy = (item.energy_kwh || 0).toFixed(2);
        const status = getStatusBadge(item.status);
        
        return `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${time}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${deviceName}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${power}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${energy}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${status}
                </td>
            </tr>
        `;
    }).join('');
    
    // 更新分页信息
    document.getElementById('tableInfo').textContent = `显示 ${startIndex + 1}-${endIndex} 条，共 ${historyData.length} 条记录`;
    document.getElementById('paginationInfo').textContent = `第 ${currentPage} 页，共 ${totalPages} 页`;
    document.getElementById('paginationContainer').classList.remove('hidden');
    
    // 更新分页按钮状态
    updatePaginationButtons();
}

/**
 * 获取设备名称
 */
function getDeviceName(deviceId) {
    const names = {
        'conveyor': '传送带',
        'station1': '加工工位1',
        'station2': '加工工位2'
    };
    return names[deviceId] || deviceId;
}

/**
 * 获取状态徽章HTML
 */
function getStatusBadge(status) {
    const badges = {
        'running': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">运行中</span>',
        'standby': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">待机</span>',
        'fault': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">故障</span>'
    };
    return badges[status] || badges['standby'];
}

/**
 * 更新分页按钮状态
 */
function updatePaginationButtons() {
    document.getElementById('firstPageBtn').disabled = currentPage === 1;
    document.getElementById('prevPageBtn').disabled = currentPage === 1;
    document.getElementById('nextPageBtn').disabled = currentPage === totalPages;
    document.getElementById('lastPageBtn').disabled = currentPage === totalPages;
}

/**
 * 切换页面
 */
function changePage(action) {
    switch(action) {
        case 'first':
            currentPage = 1;
            break;
        case 'prev':
            if (currentPage > 1) currentPage--;
            break;
        case 'next':
            if (currentPage < totalPages) currentPage++;
            break;
        case 'last':
            currentPage = totalPages;
            break;
    }
    
    updateTable();
    
    // 滚动到表格顶部
    document.querySelector('table').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * 切换图表类型
 */
function toggleChartType(type) {
    if (!historyChart) return;
    
    currentChartType = type;
    historyChart.config.type = type;
    historyChart.update();
    
    // 更新按钮样式
    document.getElementById('lineChartBtn').className = type === 'line' 
        ? 'px-3 py-1 text-sm bg-blue-100 text-blue-600 rounded hover:bg-blue-200 transition'
        : 'px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded hover:bg-gray-200 transition';
    
    document.getElementById('barChartBtn').className = type === 'bar'
        ? 'px-3 py-1 text-sm bg-blue-100 text-blue-600 rounded hover:bg-blue-200 transition'
        : 'px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded hover:bg-gray-200 transition';
}

/**
 * 导出为CSV
 */
function exportToCSV() {
    if (!historyData || historyData.length === 0) {
        showErrorToast('没有可导出的数据');
        return;
    }
    
    try {
        // 构建CSV内容
        const headers = ['时间', '设备ID', '设备名称', '功率(kW)', '能耗(kWh)', '状态'];
        const rows = historyData.map(item => [
            new Date(item.timestamp).toLocaleString('zh-CN'),
            item.device_id,
            getDeviceName(item.device_id),
            (item.power_kw || 0).toFixed(2),
            (item.energy_kwh || 0).toFixed(2),
            item.status || 'standby'
        ]);
        
        // 添加BOM以支持Excel正确显示中文
        let csvContent = '\uFEFF';
        csvContent += headers.join(',') + '\n';
        csvContent += rows.map(row => row.join(',')).join('\n');
        
        // 创建Blob并下载
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        const deviceId = document.getElementById('deviceSelect').value;
        const deviceName = getDeviceName(deviceId);
        const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
        const filename = `历史数据_${deviceName}_${timestamp}.csv`;
        
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showSuccessToast(`成功导出 ${historyData.length} 条数据`);
        
    } catch (error) {
        console.error('导出CSV失败:', error);
        showErrorToast('导出失败，请稍后重试');
    }
}

/**
 * 重置过滤条件
 */
function resetFilters() {
    // 重置为默认值（最近24小时）
    const now = new Date();
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    
    document.getElementById('deviceSelect').value = 'conveyor';
    document.getElementById('startTime').value = formatDateTimeLocal(yesterday);
    document.getElementById('endTime').value = formatDateTimeLocal(now);
    document.getElementById('quickSelect').value = '';
    
    // 清空数据
    historyData = [];
    updateStatistics([]);
    updateChart([]);
    updateTable();
    
    showSuccessToast('已重置查询条件');
}

/**
 * 显示/隐藏加载状态
 */
function showLoading(show) {
    const indicator = document.getElementById('loadingIndicator');
    if (indicator) {
        if (show) {
            indicator.classList.remove('hidden');
        } else {
            indicator.classList.add('hidden');
        }
    }
}

/**
 * 显示成功提示
 */
function showSuccessToast(message) {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-slide-in';
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
    toast.className = 'fixed bottom-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-slide-in';
    toast.innerHTML = `<i class="fas fa-exclamation-circle mr-2"></i>${message}`;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

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
