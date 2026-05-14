from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,)

from .forms import CommentForm, PostForm, UserProfileForm
from .models import Category, Comment, Post

User = get_user_model()

POSTS_PER_PAGE = 10


def get_published_posts():
    """Возвращает QuerySet опубликованных постов с количеством комментариев."""
    return Post.objects.select_related(
        'author', 'category', 'location'
    ).filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True,
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')


class IndexView(ListView):
    """Главная страница."""

    template_name = 'blog/index.html'
    paginate_by = POSTS_PER_PAGE
    context_object_name = 'post_list'

    def get_queryset(self):
        return get_published_posts()


class PostDetailView(DetailView):
    """Страница отдельного поста с формой для комментариев."""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if post.author != self.request.user:
            post = get_object_or_404(
                get_published_posts(),
                pk=self.kwargs['post_id'],
            )
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class CategoryPostsView(ListView):
    """Страница постов выбранной категории."""

    template_name = 'blog/category.html'
    paginate_by = POSTS_PER_PAGE
    context_object_name = 'post_list'

    def get_category(self):
        return get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
        )

    def get_queryset(self):
        return get_published_posts().filter(
            category=self.get_category()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.get_category()
        return context


class UserProfileView(ListView):
    """Страница профиля пользователя со списком его постов."""

    template_name = 'blog/profile.html'
    paginate_by = POSTS_PER_PAGE
    context_object_name = 'post_list'

    def get_author(self):
        return get_object_or_404(
            User, username=self.kwargs['username']
        )

    def get_queryset(self):
        author = self.get_author()
        if author == self.request.user:
            return Post.objects.filter(
                author=author
            ).annotate(
                comment_count=Count('comments')
            ).order_by('-pub_date')
        return get_published_posts().filter(author=author)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_author()
        return context


class UserProfileEditView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля пользователя."""

    model = User
    form_class = UserProfileForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username},
        )


class PostCreateView(LoginRequiredMixin, CreateView):
    """Создание нового поста."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username},
        )


class PostEditView(LoginRequiredMixin, UpdateView):
    """Редактирование существующего поста (только для автора)."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=kwargs['post_id'])
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.pk},
        )


class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление поста (только для автора)."""

    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=kwargs['post_id'])
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username},
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Создание комментария к посту."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post, pk=self.kwargs['post_id']
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']},
        )


class CommentEditView(LoginRequiredMixin, UpdateView):
    """Редактирование комментария (только для автора)."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=kwargs['comment_id'])
        if comment.author != request.user:
            return redirect(
                'blog:post_detail', post_id=kwargs['post_id']
            )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']},
        )


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление комментария (только для автора)."""

    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=kwargs['comment_id'])
        if comment.author != request.user:
            return redirect(
                'blog:post_detail', post_id=kwargs['post_id']
            )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username},
        )
