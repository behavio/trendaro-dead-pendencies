from django.contrib import admin

from mailer.models import Message


class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'recipients', 'created', 'updated', 'priority', 'status')

admin.site.register(Message, MessageAdmin)