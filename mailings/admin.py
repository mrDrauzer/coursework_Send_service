from django.contrib import admin

from .models import Recipient, Message, Mailing, Attempt


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "full_name", "owner")
    search_fields = ("email", "full_name")
    list_filter = ("owner",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "owner")
    search_fields = ("subject",)
    list_filter = ("owner",)


class AttemptInline(admin.TabularInline):
    model = Attempt
    extra = 0
    readonly_fields = ("when", "status", "server_response")


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "start_at", "end_at", "owner")
    list_filter = ("status", "owner")
    filter_horizontal = ("recipients",)
    inlines = [AttemptInline]


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "mailing", "status", "when")
    list_filter = ("status",)
