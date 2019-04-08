from django.contrib import admin

# Register your models here.
from .models import (
    BilbyCWJob,
    DataSource,
    DataParameter,
    SearchParameter,
    EngineParameter,
    ViterbiParameter,
    OutputParameter,
)


@admin.register(BilbyCWJob)
class BilbyCWJob(admin.ModelAdmin):
    list_display = ('name', 'description', 'status_display', 'user',)
    search_fields = ['name', 'description', 'user__username', 'user__first_name', 'user__last_name', ]


@admin.register(DataSource)
class DataSource(admin.ModelAdmin):
    list_display = ('job', 'data_source')
    search_fields = ['job__name', 'job__user__username', 'data_source', ]


@admin.register(DataParameter)
class DataParameter(admin.ModelAdmin):
    list_display = ('get_job', 'data_source', 'name', 'value')
    search_fields = ['name', 'value']

    def get_job(self, obj):
        return obj.data_source.job.name

    get_job.admin_order_field = 'data_source__job'  # Allows column order sorting
    get_job.short_description = 'BilbyCWJob'  # Renames column head

    def get_data(self, obj):
        return obj.data_source.data_choice

    get_data.admin_order_field = 'data_source'  # Allows column order sorting
    get_data.short_description = 'data_source'  # Renames column head


@admin.register(SearchParameter)
class SearchParameter(admin.ModelAdmin):
    list_display = ('job', 'name', 'value')
    search_fields = ['job__name', 'job__user__username', 'name', 'value', ]


@admin.register(EngineParameter)
class EngineParameter(admin.ModelAdmin):
    list_display = ('job', 'name', 'value')
    search_fields = ['job__name', 'job__user__username', 'name', 'value', ]


@admin.register(ViterbiParameter)
class ViterbiParameter(admin.ModelAdmin):
    list_display = ('job', 'name', 'value')
    search_fields = ['job__name', 'job__user__username', 'name', 'value', ]


@admin.register(OutputParameter)
class OutputParameter(admin.ModelAdmin):
    list_display = ('job', 'name', 'value')
    search_fields = ['job__name', 'job__user__username', 'name', 'value', ]
