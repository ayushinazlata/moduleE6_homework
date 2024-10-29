from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import UserProfile, Chat, Message


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'avatar')  # Поля, которые будут отображаться в списке
    search_fields = ('user__username',)  # Возможность поиска по имени пользователя


admin.site.unregister(User)  # Сначала отменяем регистрацию стандартной модели User
admin.site.register(User, UserAdmin)  # Затем регистрируем её заново с админским интерфейсом
admin.site.register(Chat)
admin.site.register(Message)