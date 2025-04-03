from django import template

register = template.Library()


@register.filter
def split(value, arg):
    """
    将字符串按指定分隔符分割

    用法: {{ value|split:',' }}
    """
    return value.split(arg)
