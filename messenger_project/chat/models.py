from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return self.user.username


class Chat(models.Model):
    name = models.CharField(max_length=255, blank=True)
    participants = models.ManyToManyField(User, related_name="chats")
    is_group = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if not self.is_group and self.participants.count() == 2:
            participant_names = ", ".join([user.username for user in self.participants.all()])
            return f"Приватный чат между {participant_names}"
        return self.name or f'Чат {self.id}'

    def get_other_user(self, current_user):
        if not self.is_group:
            other_users = self.participants.exclude(id=current_user.id)
            return other_users.first() if other_users.exists() else None
        return None
    
    @classmethod
    def get_or_create_private_chat(cls, user1, user2):
        # Ищем существующий чат между двумя пользователями
        chat = cls.objects.filter(
            participants=user1
        ).filter(participants=user2)

        if chat.exists():
            return chat.first()  
        
        # Если не существует, создаем новый чат
        new_chat = cls.objects.create(is_group=False)
        new_chat.participants.add(user1, user2)
        return new_chat
    

class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def formatted_timestamp(self):
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    def __str__(self):
        return f'Message from {self.sender.username} at {self.timestamp}'
