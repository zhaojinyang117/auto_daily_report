# 自动日报系统常见问题及解决方案

## 模板错误："Invalid filter: 'add_class'"

### 问题描述
访问用户设置页面时，出现错误："Invalid filter: 'add_class'"。

### 原因
虽然`django-widget-tweaks`包已经安装并添加到`INSTALLED_APPS`中，但在使用过滤器的模板中忘记了添加`{% load widget_tweaks %}`语句。

### 解决方案
在使用`widget_tweaks`过滤器的模板顶部添加`{% load widget_tweaks %}`语句。例如：

```html
{% extends 'reporter/base.html' %}
{% load widget_tweaks %}

{% block title %}用户设置 | 自动日报系统{% endblock %}
```

## 依赖安装说明

本项目使用`uv`作为包管理器，比传统的pip更快速、可靠。安装新依赖时应使用：

```bash
uv add [package-name]
```

而不是传统的`pip install [package-name]`。

## 静态文件配置

如果需要部署到生产环境，确保在`settings.py`中配置了`STATIC_ROOT`：

```python
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

并且执行`python manage.py collectstatic`来收集静态文件。
