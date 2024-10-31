import json

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import UserProfile, Chat, Message
from .serializers import ChatSerializer, MessageSerializer
from .forms import ProfileForm, UserRegistrationForm, ChatForm


# Класс для обработки входа в систему
class CustomLoginView(LoginView):
    template_name = 'login.html'

    def get_success_url(self):
        return reverse('default')
    

# Страница регистрации
def signup_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save()
            print(f"User saved successfully: {user.username}")
            
            # Проверяем, был ли аватар сохранен в профиле
            if hasattr(user, 'userprofile') and user.userprofile.avatar:
                print(f"Avatar saved successfully for user {user.username}")
            else:
                print(f"No avatar saved for user {user.username}")

            return redirect('login')
        else:
            print("Form is not valid:", form.errors)
    else:
        form = UserRegistrationForm()
        
    return render(request, 'signup.html', {'form': form})



# Страница выхода из системы
def logout_view(request):
    logout(request)
    return redirect('default')


# Cраница редактирования профиля
@login_required
def profile_view(request):
    try:
        profile, create = UserProfile.objects.get_or_create(user=request.user)

        if request.method == 'POST':
            form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
            if form.is_valid():
                form.save()
                request.user.username = form.cleaned_data['username']
                request.user.save()
                return redirect('profile') 
        else:
            form = ProfileForm(instance=profile, user=request.user)

        return render(request, 'simple_profile.html', {'form': form, 'profile': profile})

    except Exception as e:
        return render(request, 'simple_profile.html', {'form': None, 'error': str(e)})

    
# Страница создания группового чата
def create_chat_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        participants = request.POST.getlist('participants')

        if not participants or len(participants) < 1:
            messages.error(request, 'Для создания чата выберите хотя бы одного участника.')
            return redirect('create_chat') 

        participants.append(request.user.id)  # Добавляем создателя чата

        if len(participants) == 2:
            chat = Chat.objects.create(name=name, is_group=False)
            chat.participants.add(*participants)
            return redirect('private_chat', user_id=participants[1])
        elif len(participants) >= 3:
            chat = Chat.objects.create(name=name, is_group=True)
            chat.participants.add(*participants)
            return redirect('chat_room', chat_id=chat.id)

    # Получаем всех пользователей, кроме текущего
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'create_chat.html', {'users': users})


# Страница редактирования группового чата
def edit_chat_view(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)  
    if request.method == 'POST':
        form = ChatForm(request.POST, instance=chat)  # Заполняем форму текущими данными чата
        if form.is_valid():
            chat = form.save(commit=False)  # Сохраняем без немедленной записи в БД
            form.save_m2m()  # Сохраняем отношения между чатом и участниками
            return redirect('chat_room', chat_id=chat.id)
    else:
        form = ChatForm(instance=chat)  # Создаем форму с текущими данными

    return render(request, 'edit_chat.html', {
        'chat': chat,
        'form': form,
        'participants': chat.participants.all()  # Получаем только участников данного чата
    })  


# Страница удаления группового чата
def delete_chat_view(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    
    # Проверка, что пользователь участвует в чате
    if request.user in chat.participants.all():
        chat.delete()
        return redirect('default') 
    else:
        return render(request, 'error.html', {'message': 'Вы не можете удалить этот чат.'})


# Главная страница (список чатов)
def default_view(request):
    if request.user.is_authenticated:
        user_chats = Chat.objects.filter(participants=request.user)

        chat_filter = request.GET.get('filter')

        if chat_filter == 'private':
            user_chats = user_chats.filter(is_group=False)
        elif chat_filter == 'group':
            user_chats = user_chats.filter(is_group=True)

        # Логика для замены имени чата на "чат с {пользователь}"
        for chat in user_chats:
            if not chat.is_group and chat.participants.count() == 2:
                other_user = chat.participants.exclude(id=request.user.id).first()
                chat.display_name = f"Chat with {other_user.username}" if other_user else chat.name
                chat.other_user_id = other_user.id if other_user else None
            else:
                chat.display_name = chat.name  

        # Пагинация
        paginator = Paginator(user_chats, 10)  
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'default.html', {'page_obj': page_obj})
    else:
        return render(request, 'default.html', {'message': 'Please log in to see your chats.'})
    

# Страница групповго чата
def chat_room_view(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    if request.user not in chat.participants.all():
        return redirect('default_view')

    messages = chat.messages.order_by('timestamp')
    user_avatars = {
        user.id: user.userprofile.avatar.url if user.userprofile.avatar else '/static/default_avatar.png'
        for user in chat.participants.all()
    }
    user_avatars_json = json.dumps(user_avatars)  # Преобразуем словарь в JSON для передачи в шаблон

    return render(request, 'chat_room.html', {
        'chat': chat,
        'messages': messages,
        'room_name': chat.name,
        'participants_count': chat.participants.count(),
        'chat_id': chat.id,
        'username': request.user.username,
        'user_avatars_json': user_avatars_json,  
    })


# Функция для создания приватного чата
def create_private_chat(request, user_id):
    if request.user.is_authenticated:
        recipient = get_object_or_404(User, id=user_id)

        # Проверяем, существует ли уже приватный чат между текущим пользователем и получателем
        private_chat = Chat.objects.filter(
            is_group=False, 
            participants=request.user
        ).filter(participants=recipient).first()

        if private_chat:
            return redirect('private_chat', user_id=recipient.id)

        # Если чата нет, создаем новый приватный чат
        new_chat = Chat.objects.create(is_group=False)
        new_chat.participants.add(request.user, recipient)

        return redirect('private_chat', user_id=recipient.id)
    else:
        return redirect('login')
    

# Страница приватного чата с пользователем по ID
@login_required
def private_chat_view(request, user_id):
    # Получаем текущего пользователя
    current_user = request.user

    # Находим другого пользователя
    other_user = get_object_or_404(User, id=user_id)

    # Пытаемся получить чат между текущим пользователем и другим пользователем
    chat = Chat.objects.filter(participants=current_user).filter(participants=other_user)

    # Если чата не существует, можно создать его (если нужно)
    if chat.exists():
        chat = chat.first()  # Получаем первый чат
    else:
        # Если чата не существует, создаем его
        chat = Chat.objects.create(name=f"Chat with {other_user.username}", is_group=False)
        chat.participants.add(current_user, other_user)
    
    # Извлекаем все сообщения, связанные с этим чатом
    messages = chat.messages.order_by('timestamp')

    # Здесь вы можете добавить логику для отображения чата
    return render(request, 'privat_chat.html', {'chat': chat, 'other_user': other_user, 'messages': messages})


# Функция для отображения всех пользователей
def all_users_view(request):
    users_list = User.objects.exclude(id=request.user.id) 
    paginator = Paginator(users_list, 10) 
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)

    return render(request, 'all_users.html', {'users': users})


# ViewSet для API чатов
class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer


# ViewSet для API сообщений
class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_queryset(self):
        chat_id = self.request.query_params.get('chat', None)
        if chat_id is not None:
            return self.queryset.filter(chat_id=chat_id)
        return self.queryset


# Загрузка предыдущих сообщений
@api_view(['GET'])
def get_previous_messages(request):
    chat_id = request.query_params.get('chat_id')  
    if chat_id:
        chat = get_object_or_404(Chat, id=chat_id)
        messages = chat.messages.order_by('timestamp')  

        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    else:
        return Response({'error': 'Chat ID is required'}, status=400)