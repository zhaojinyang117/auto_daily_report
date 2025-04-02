/**
 * 统计数据和图表处理
 * 负责首页统计卡片和图表的数据加载和渲染
 */
document.addEventListener('DOMContentLoaded', function () {
    // 初始化统计图表
    if (document.getElementById('emailMonthlyChart')) {
        initEmailStats();
    }

    // 初始化注册天数计算
    if (document.getElementById('days-since-registration')) {
        updateDaysSinceRegistration();
    }
});

/**
 * 初始化邮件统计
 */
function initEmailStats() {
    // 获取统计数据元素
    const monthlyEmailsElement = document.getElementById('monthly-emails-count');
    const totalEmailsElement = document.getElementById('total-emails-count');

    // 如果元素存在且有数据属性，使用它们的值；否则使用默认值
    const monthlyEmails = monthlyEmailsElement ? parseInt(monthlyEmailsElement.dataset.count) : 0;
    const totalEmails = totalEmailsElement ? parseInt(totalEmailsElement.dataset.count) : 0;

    // 更新显示
    if (monthlyEmailsElement) monthlyEmailsElement.textContent = monthlyEmails;
    if (totalEmailsElement) totalEmailsElement.textContent = totalEmails;

    // 渲染月度邮件图表
    renderMonthlyEmailChart();
}

/**
 * 渲染月度邮件图表
 */
function renderMonthlyEmailChart() {
    const ctx = document.getElementById('emailMonthlyChart');
    if (!ctx) return;

    // 获取图表数据
    const chartData = JSON.parse(ctx.dataset.chartData || '[]');
    const labels = chartData.map(item => item.day);
    const data = chartData.map(item => item.count);

    // 使用Chart.js创建图表
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '发送邮件数',
                data: data,
                backgroundColor: 'rgba(0, 120, 215, 0.2)',
                borderColor: 'rgba(0, 120, 215, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(0, 120, 215, 1)',
                pointRadius: 4,
                tension: 0.2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

/**
 * 更新注册天数
 */
function updateDaysSinceRegistration() {
    const daysElement = document.getElementById('days-since-registration');
    if (!daysElement) return;

    // 从数据属性获取注册日期
    const registerDateStr = daysElement.dataset.registerDate;
    if (!registerDateStr) return;

    // 计算从注册到现在的天数
    const registerDate = new Date(registerDateStr);
    const today = new Date();
    const diffTime = Math.abs(today - registerDate);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    // 更新显示
    daysElement.textContent = diffDays;
} 