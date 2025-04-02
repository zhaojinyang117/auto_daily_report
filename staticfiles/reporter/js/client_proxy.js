/**
 * 客户端代理模式 - Gemini API处理工具
 * 
 * 这个脚本用于在客户端代理模式下调用Google Gemini API
 * 当服务器端配置为使用客户端代理时，将使用浏览器的网络环境访问API
 */

// 处理客户端代理请求的主函数
async function processWithClientProxy(apiData) {
    try {
        // 显示加载状态
        showLoadingState();

        // 从API数据中提取必要信息
        const { api_key, prompt, original_content, model } = apiData;

        console.log("使用客户端代理模式调用Gemini API");

        // 构建API请求
        const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${api_key}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                contents: [{
                    parts: [{
                        text: prompt
                    }]
                }]
            })
        });

        // 检查响应状态
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`API调用失败: ${errorData.error?.message || '未知错误'}`);
        }

        // 处理响应
        const data = await response.json();
        let processedContent = data.candidates[0]?.content?.parts[0]?.text || '';

        // 应用相同的格式处理
        processedContent = formatText(processedContent);

        // 更新UI显示处理后的内容
        updateContentDisplay(processedContent);

        // 返回处理结果
        return {
            success: true,
            processedContent
        };
    } catch (error) {
        console.error("客户端代理处理失败:", error);
        // 显示错误，回退到原始内容
        showError(`客户端代理处理失败: ${error.message}`);
        updateContentDisplay(apiData.original_content);
        return {
            success: false,
            error: error.message
        };
    } finally {
        // 隐藏加载状态
        hideLoadingState();
    }
}

// 格式化文本，应用与后端相同的格式规则
function formatText(text) {
    // 确保文本已清理
    let formatted = text.trim();

    // 移除可能的结果前缀，如"以下是学习总结："
    formatted = formatted.replace(/^(?:以下是|以下是对|这是|这是对|根据|这里是|以下是我|下面是|根据您提供的内容，|嗨，以下是|为您总结).*?(要点|总结|学习|内容|笔记)(?:：|:)?\s*/i, '');

    // 移除可能的结尾
    formatted = formatted.replace(/(?:这些是|这些是今天的|以上是|以上是今天的|希望|祝您|如有|如果|需要|如需).{0,50}$/i, '');

    // 移除常见的问候语和结束语
    formatted = formatted.replace(/尊敬的领导|尊敬的同事|各位领导|各位同事|尊敬的[\w\s]+:|亲爱的[\w\s]+:/gi, '');
    formatted = formatted.replace(/此致[，,]?\s*敬礼|祝(?:您|你)[\w\s]+|感谢您的[\w\s]+|此致|敬礼|顺祝[\w\s]+/gi, '');

    // 移除可能已存在的<br>标签，确保数字和要点在同一行
    for (let i = 1; i <= 10; i++) {
        formatted = formatted.replace(new RegExp(`${i}\\. <br><br>`, 'g'), `${i}. `);
        formatted = formatted.replace(new RegExp(`${i}\\.<br><br>`, 'g'), `${i}. `);
        // 确保每个要点开始都是"数字. "的格式
        formatted = formatted.replace(new RegExp(`${i}\\)\\s+`, 'g'), `${i}. `);
        formatted = formatted.replace(new RegExp(`${i}、\\s*`, 'g'), `${i}. `);
    }

    // 在每个数字序号前添加空行（从第2个开始），确保要点之间有空行
    for (let i = 2; i <= 10; i++) {
        formatted = formatted.replace(new RegExp(`${i}\\. `, 'g'), `<br><br>${i}. `);
    }

    // 再次清理多余的空格和换行
    formatted = formatted.replace(/^\s+|\s+$/g, '');
    formatted = formatted.replace(/<br><br><br>+/g, '<br><br>');

    // 检查是否开头就是数字列表，如果不是，尝试寻找第一个要点
    if (!/^1\.\s/.test(formatted)) {
        const firstPoint = formatted.match(/1\.\s/);
        if (firstPoint && firstPoint.index > 0) {
            // 移除第一个要点前的所有内容
            formatted = formatted.substring(firstPoint.index);
        }
    }

    return formatted;
}

// 发送处理后的内容给服务器
async function sendProcessedContent(processedContent, dateStr) {
    try {
        // 显示发送中状态
        const loadingElement = document.createElement('div');
        loadingElement.id = 'email-sending';
        loadingElement.className = 'alert alert-info mt-3';
        loadingElement.innerHTML = '<strong>处理中...</strong> 正在发送邮件，请稍候...';

        // 添加到内容区域后面
        const cardBody = document.querySelector('.card-body');
        if (cardBody) {
            cardBody.appendChild(loadingElement);
        }

        // 禁用发送按钮
        const sendEmailButton = document.getElementById('send-email');
        if (sendEmailButton) {
            sendEmailButton.disabled = true;
        }

        // 将处理后的内容转换为JSON对象
        const postData = JSON.stringify({
            processed_content: processedContent
        });

        // 发送到服务器
        const response = await fetch(`/reporter/send-report/?date=${dateStr}`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: postData
        });

        // 获取响应
        const data = await response.json();

        // 移除加载状态
        const loadingElem = document.getElementById('email-sending');
        if (loadingElem) {
            loadingElem.remove();
        }

        // 显示结果消息
        const alertClass = data.success ? 'alert-success' : 'alert-danger';
        const alertMessage = data.success ? '<strong>成功!</strong> ' : '<strong>错误!</strong> ';

        const messageElement = document.createElement('div');
        messageElement.className = `alert ${alertClass} mt-3`;
        messageElement.innerHTML = alertMessage + data.message;

        // 添加到内容区域后面
        if (cardBody) {
            cardBody.appendChild(messageElement);
        }

        // 重新启用按钮
        if (sendEmailButton) {
            sendEmailButton.disabled = false;
        }

        return data;
    } catch (error) {
        console.error('发送处理后内容时出错:', error);

        // 移除加载状态
        const loadingElement = document.getElementById('email-sending');
        if (loadingElement) {
            loadingElement.remove();
        }

        // 显示错误消息
        const errorElement = document.createElement('div');
        errorElement.className = 'alert alert-danger mt-3';
        errorElement.innerHTML = '<strong>错误!</strong> 发送邮件时出错，服务器无响应。';

        // 添加到内容区域后面
        const cardBody = document.querySelector('.card-body');
        if (cardBody) {
            cardBody.appendChild(errorElement);
        }

        // 重新启用按钮
        const sendEmailButton = document.getElementById('send-email');
        if (sendEmailButton) {
            sendEmailButton.disabled = false;
        }

        return {
            success: false,
            message: '发送处理后内容失败: ' + error.message
        };
    }
}

// 获取CSRF令牌
function getCsrfToken() {
    // 从cookie中获取CSRF令牌
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// UI交互相关函数
function showLoadingState() {
    // 创建加载指示器元素
    const loadingElement = document.createElement('div');
    loadingElement.id = 'gemini-loading';
    loadingElement.className = 'alert alert-info';
    loadingElement.innerHTML = '<strong>处理中...</strong> 正在通过客户端代理调用Gemini API';

    // 添加到内容前
    const contentDisplay = document.querySelector('.content-display');
    if (contentDisplay) {
        contentDisplay.parentNode.insertBefore(loadingElement, contentDisplay);
    }
}

function hideLoadingState() {
    // 移除加载指示器
    const loadingElement = document.getElementById('gemini-loading');
    if (loadingElement) {
        loadingElement.remove();
    }
}

function updateContentDisplay(content) {
    // 更新内容显示区域
    const contentDisplay = document.querySelector('.content-display');
    if (contentDisplay) {
        contentDisplay.innerHTML = content;
    }
}

function showError(message) {
    // 显示错误消息
    const errorElement = document.createElement('div');
    errorElement.className = 'alert alert-danger';
    errorElement.innerHTML = message;

    // 添加到内容前
    const contentDisplay = document.querySelector('.content-display');
    if (contentDisplay) {
        contentDisplay.parentNode.insertBefore(errorElement, contentDisplay);
    }
}

// 初始化客户端代理功能
document.addEventListener('DOMContentLoaded', function () {
    // 检查页面上是否有需要处理的客户端代理数据
    const clientProxyDataElement = document.getElementById('client-proxy-data');
    if (clientProxyDataElement) {
        try {
            // 解析数据但不自动执行处理
            const clientProxyData = JSON.parse(clientProxyDataElement.textContent);
            console.log("客户端代理数据已加载，等待手动触发");
        } catch (error) {
            console.error("解析客户端代理数据失败:", error);
        }
    }

    // 为手动触发按钮添加事件监听器
    const processButton = document.getElementById('process-with-gemini');
    if (processButton) {
        processButton.addEventListener('click', function () {
            const clientProxyDataElement = document.getElementById('client-proxy-data');
            if (clientProxyDataElement) {
                try {
                    const clientProxyData = JSON.parse(clientProxyDataElement.textContent);
                    if (clientProxyData && clientProxyData.use_client_proxy) {
                        processWithClientProxy(clientProxyData);
                    } else {
                        console.error("客户端代理数据无效");
                        showError("客户端代理数据无效");
                    }
                } catch (error) {
                    console.error("解析客户端代理数据失败:", error);
                    showError("解析客户端代理数据失败");
                }
            }
        });
    }
}); 