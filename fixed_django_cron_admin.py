from datetime import timedelta

from django.contrib import admin
from django.db.models import F
from django.utils.translation import gettext_lazy as _

from django_cron.models import CronJobLog, CronJobLock


def humanize_duration(duration):
    """
    Returns a humanized string representing time difference.
    For example: 2 days 1 hour 25 minutes 10 seconds
    """
    days, remainder = divmod(duration.total_seconds(), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    result = ""
    if days:
        result += f"{int(days)} days "
    if hours:
        result += f"{int(hours)} hours "
    if minutes:
        result += f"{int(minutes)} minutes "
    if seconds or not result:
        result += f"{int(seconds)} seconds"

    return result.strip()


class DurationFilter(admin.SimpleListFilter):
    title = _("duration")
    parameter_name = "duration"

    def lookups(self, request, model_admin):
        return (
            ("lte_minute", _("<= 1 minute")),
            ("gt_minute", _("> 1 minute")),
            ("gt_hour", _("> 1 hour")),
            ("gt_day", _("> 1 day")),
        )

    def queryset(self, request, queryset):
        if self.value() == "lte_minute":
            return queryset.filter(end_time__lte=F("start_time") + timedelta(minutes=1))
        if self.value() == "gt_minute":
            return queryset.filter(end_time__gt=F("start_time") + timedelta(minutes=1))
        if self.value() == "gt_hour":
            return queryset.filter(end_time__gt=F("start_time") + timedelta(hours=1))
        if self.value() == "gt_day":
            return queryset.filter(end_time__gt=F("start_time") + timedelta(days=1))


class CronJobLogAdmin(admin.ModelAdmin):
    class Meta:
        model = CronJobLog

    search_fields = ("code", "message")
    ordering = ("-start_time",)
    list_display = ("code", "start_time", "end_time", "humanize_duration", "is_success")
    list_filter = ("code", "start_time", "is_success", DurationFilter)

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser and obj is not None:
            names = [f.name for f in CronJobLog._meta.fields if f.name != "id"]
            return self.readonly_fields + tuple(names)
        return self.readonly_fields

    def humanize_duration(self, obj):
        return humanize_duration(obj.end_time - obj.start_time)

    humanize_duration.short_description = _("Duration")
    humanize_duration.admin_order_field = "duration"


admin.site.register(CronJobLog, CronJobLogAdmin)
admin.site.register(CronJobLock)
