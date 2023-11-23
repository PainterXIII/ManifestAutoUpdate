from django.contrib import admin
from .models import *
# Register your models here.
admin.site.site_header = "数据管理系统"
admin.site.site_title = "数据管理系统"
admin.site.index_title = "数据管理系统"
class DataAdmin(admin.ModelAdmin):
    """The admin model of AuthorInfoAdmin"""
    list_display = ('keystr','flag','posttime')
    ordering = ('keystr',)
    search_fields=('keystr',)
admin.site.register(Task, DataAdmin)