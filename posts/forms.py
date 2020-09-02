from django.forms import ModelForm, Textarea
from django.contrib.auth import get_user_model
from .models import Post, Comment


User = get_user_model()


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {
          'group': 'Группа:', 'text': 'Текст поста:', 'image': 'Изображение:'
        }
        help_texts = {
            'group': 'Отправить пост в группу?',
            'text': 'html не поддерживается'
            }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {'text': Textarea()}
        labels = {'text': 'Текст комментария'}
        help_texts = {'text': 'Будьте вежливы'}
