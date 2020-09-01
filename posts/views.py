from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
        )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {'group': group, 'page': page, 'paginator': paginator}
        )


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
        return render(request, 'posts/new_post.html', {'form': form})
    form = PostForm()
    return render(request, 'posts/new_post.html', {'form': form})


def profile(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    post = author.posts.first()
    posts_count = author.posts.count()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = Follow.objects.filter(
        user__username=user, author__username=author
        ).exists()
    count_followers = Follow.objects.filter(author__username=author).count
    count_following = Follow.objects.filter(user__username=author).count
    context = {
        'author': author,
        'user': user,
        'posts_count': posts_count,
        'page': page,
        'paginator': paginator,
        'post': post,
        'following': following,
        'count_followers': count_followers,
        'count_following': count_following,
    }
    return render(request, 'posts/profile.html', context)


def post_view(request, username, post_id):
    user = request.user
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    comments = post.comments.all()
    form = CommentForm()

    author = post.author
    posts_count = author.posts.count()
    return render(
        request,
        'posts/post.html',
        {
            'post': post,
            'author': author,
            'posts_count': posts_count,
            'user': user,
            'comments': comments,
            'form': form
            }
        )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)

    if request.user != post.author:
        return redirect('post', username=username, post_id=post_id)

    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
        )

    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)

    return render(
        request,
        'posts/new_post.html',
        {'form': form, 'post': post}
        )


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('post', username=username, post_id=post_id)
    form = CommentForm()
    return render(request, 'posts/comments.html', {'form': form, 'post': post})


@login_required
def follow_index(request):
    user = request.user
    followed_users = User.objects.filter(following__user=request.user)
    posts = []
    for user in followed_users:
        posts.extend(Post.objects.filter(author=user))
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        "posts/follow.html",
        {'page': page, 'paginator': paginator}
    )


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    follow_exist = Follow.objects.filter(
        user__username=user, author__username=author
        ).exists()
    same_user = (user.pk == author.pk)
    if follow_exist or same_user:
        return redirect('profile', username=author.username)
    Follow.objects.create(user=user, author=author)
    return redirect('profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user__username=user, author__username=author
        ).delete()
    return redirect('profile', username=author.username)
