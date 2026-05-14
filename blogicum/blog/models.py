from django.db import models
from django.contrib.auth import get_user_model
from core.models import PublishModel


User = get_user_model()


class Category(PublishModel):
    """Модель категории публикаций."""

    title = models.CharField(max_length=256, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    slug = models.SlugField(unique=True, verbose_name='Идентификатор',
                            help_text='Идентификатор страницы для URL;'
                            ' разрешены символы латиницы, цифры, '
                            'дефис и подчёркивание.')

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'


class Location(PublishModel):
    """Модель местоположения публикации."""

    name = models.CharField(max_length=256, blank=False,
                            verbose_name='Название места')

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'


class Post(PublishModel):
    """Модель публикации поста."""

    title = models.CharField(max_length=256, blank=False,
                             verbose_name='Заголовок')
    text = models.TextField(blank=False, verbose_name='Текст')
    pub_date = models.DateTimeField(blank=False,
                                    verbose_name='Дата и время публикации',
                                    help_text='Если установить дату и время в '
                                    'будущем — можно делать отложенные '
                                    'публикации.')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               blank=False,
                               verbose_name='Автор публикации')
    location = models.ForeignKey(Location,
                                 on_delete=models.SET_NULL,
                                 null=True,
                                 blank=False,
                                 verbose_name='Местоположение')
    category = models.ForeignKey(Category,
                                 on_delete=models.SET_NULL,
                                 null=True,
                                 blank=False,
                                 verbose_name='Категория')
    image = models.ImageField(
        upload_to='post_images/',
        blank=True,
        verbose_name='Фото',
    )

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ['-pub_date']


class Comment(models.Model):
    """Модель комментария."""

    text = models.TextField(verbose_name='Текст комментария')
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comments',
                             verbose_name='Публикация')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments',
        verbose_name='Автор',)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Добавлено',)

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_at']

    def __str__(self):
        return f'Комментарий от {self.author} к "{self.post}"'
