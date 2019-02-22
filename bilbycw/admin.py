from django.contrib import admin

# Register your models here.
from bilbycw.models import BilbyCWJob


@admin.register(BilbyCWJob)
class BilbyCWJob(admin.ModelAdmin):
    list_display = ('name', 'description', 'status_display', 'user',)
    search_fields = ['name', 'description', 'user__username', 'user__first_name', 'user__last_name', ]
