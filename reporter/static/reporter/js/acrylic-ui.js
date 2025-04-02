/**
 * 亚克力UI效果控制
 * 负责管理背景图片设置和透明度调节
 */
document.addEventListener('DOMContentLoaded', function () {
    // 初始化亚克力UI
    initAcrylicUI();

    // 添加事件监听器
    setupEventListeners();
});

/**
 * 初始化亚克力UI效果
 */
function initAcrylicUI() {
    // 获取保存的设置
    const opacity = localStorage.getItem('acrylic-opacity') || 0.8;
    const blur = localStorage.getItem('acrylic-blur') || 12;
    const bgImage = localStorage.getItem('custom-bg-image');

    // 设置透明度和模糊值
    document.documentElement.style.setProperty('--acrylic-bg-opacity', opacity);
    document.documentElement.style.setProperty('--acrylic-blur', `${blur}px`);

    // 应用背景图片
    if (bgImage) {
        applyBackgroundImage(bgImage);
    }

    // 更新控制器值
    const opacitySlider = document.getElementById('opacity-slider');
    if (opacitySlider) {
        opacitySlider.value = opacity * 100;
        document.getElementById('opacity-value').textContent = Math.round(opacity * 100) + '%';
    }

    const blurSlider = document.getElementById('blur-slider');
    if (blurSlider) {
        blurSlider.value = blur;
        document.getElementById('blur-value').textContent = blur + 'px';
    }
}

/**
 * 应用背景图片
 * @param {string} imageUrl - 背景图片URL，为空则使用默认
 */
function applyBackgroundImage(imageUrl) {
    const body = document.body;
    body.classList.add('custom-bg');

    if (imageUrl) {
        // 创建一个Image对象来验证图片是否可用
        const img = new Image();
        img.onload = function () {
            // 图片加载成功后应用
            document.documentElement.style.setProperty('--custom-bg-image', `url('${imageUrl}')`);
            localStorage.setItem('custom-bg-image', imageUrl);
        };
        img.onerror = function () {
            // 图片加载失败时移除存储的图片URL
            console.error('背景图片加载失败');
            localStorage.removeItem('custom-bg-image');
            document.documentElement.style.removeProperty('--custom-bg-image');
        };
        img.src = imageUrl;
    } else {
        // 移除自定义背景,使用默认渐变
        document.documentElement.style.removeProperty('--custom-bg-image');
    }
}

/**
 * 设置事件监听器
 */
function setupEventListeners() {
    // 监听透明度滑块变化
    const opacitySlider = document.getElementById('opacity-slider');
    if (opacitySlider) {
        opacitySlider.addEventListener('input', function () {
            const value = this.value / 100;
            document.documentElement.style.setProperty('--acrylic-bg-opacity', value);
            document.getElementById('opacity-value').textContent = this.value + '%';
            localStorage.setItem('acrylic-opacity', value);
        });
    }

    // 监听模糊度滑块变化
    const blurSlider = document.getElementById('blur-slider');
    if (blurSlider) {
        blurSlider.addEventListener('input', function () {
            const value = this.value;
            document.documentElement.style.setProperty('--acrylic-blur', `${value}px`);
            document.getElementById('blur-value').textContent = value + 'px';
            localStorage.setItem('acrylic-blur', value);
        });
    }

    // 监听背景图片上传
    const bgImageInput = document.getElementById('bg-image-input');
    if (bgImageInput) {
        bgImageInput.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                if (file.size > 5 * 1024 * 1024) { // 5MB限制
                    alert('图片大小不能超过5MB');
                    this.value = '';
                    return;
                }

                const reader = new FileReader();
                reader.onload = function (e) {
                    const imageUrl = e.target.result;
                    applyBackgroundImage(imageUrl);
                };
                reader.onerror = function () {
                    console.error('图片读取失败');
                    alert('图片读取失败,请重试');
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // 重置按钮
    const resetButton = document.getElementById('reset-bg');
    if (resetButton) {
        resetButton.addEventListener('click', function () {
            localStorage.removeItem('custom-bg-image');
            localStorage.setItem('acrylic-opacity', 0.8);
            localStorage.setItem('acrylic-blur', 12);
            initAcrylicUI();
        });
    }
} 