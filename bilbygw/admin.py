from django.contrib import admin

# Register your models here.
from bilbygw.models import BilbyGJob


@admin.register(BilbyGJob)
class BilbyGJob(admin.ModelAdmin):
    list_display = ('name', 'description', 'status_display', 'user',)
    search_fields = ['name', 'description', 'user__username', 'user__first_name', 'user__last_name', ]
