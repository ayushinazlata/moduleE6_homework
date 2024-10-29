from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from rest_framework.routers import DefaultRouter

from . import views
from .views import ChatViewSet, MessageViewSet



router = DefaultRouter()
router.register(r'chats', ChatViewSet)
router.register(r'messages', MessageViewSet)

urlpatterns = [
    path('', include(router.urls)),  # Включение маршрутов для API
    path('home/', views.default_view, name='default'),  # Главная страница (список чатов)
    path('login/', views.CustomLoginView.as_view(), name='login'),  # Страница входа
    path('signup/', views.signup_view, name='signup'),  # Страница регистрации
    path('logout/', views.logout_view, name='logout'),  # Страница выхода
    path('create_chat/', views.create_chat_view, name='create_chat'),  # Страница создания группового чата
    path('create_private_chat/<int:user_id>/', views.create_private_chat, name='create_private_chat'),  # Страница создания приватного чата
    path('edit_chat/<int:chat_id>/', views.edit_chat_view, name='edit_chat'),   # Страница редактирования группового чата по ID
    path('delete/<int:chat_id>/', views.delete_chat_view, name='delete_chat'),  # Страница удаления группового чата
    path('chat/group/<int:chat_id>/', views.chat_room_view, name='chat_room'),  # Страница группового чата по ID
    path('chat/privat/<int:user_id>/', views.private_chat_view, name='private_chat'),  # Личный чат с пользователем по ID
    path('my_profile/',views.profile_view, name='profile'), # Редактирование профиля
    path('users/', views.all_users_view, name='all_users'),  # URL для страницы всех пользователей
    path('api/get_previous_messages', views.get_previous_messages, name='get_previous_messages'),   # Загрузка предыдущих сообщений
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
