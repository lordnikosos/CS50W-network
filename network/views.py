from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json

from .models import User, Post, Follow, Like


def index(request):
    if request.method == "POST" and request.user.is_authenticated:
        content = request.POST.get("content")
        if content:
            Post.objects.create(user=request.user, content=content)
            return HttpResponseRedirect(reverse("index"))
    
    posts = Post.objects.all().order_by('-timestamp')  # Get all posts, newest first

    # Add like information for each post
    for post in posts:
        post.is_liked_by_user = post.is_liked_by(request.user) if request.user.is_authenticated else False

    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)

    return render(request, "network/index.html", {
        "posts": posts,
        "posts_of_the_page": posts_of_the_page
    })


def following(request):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    # Get users that current user follows (more efficient way)
    following_users = Follow.objects.filter(follower=request.user).values_list('following', flat=True)
    
    # Get posts from those users directly (much more efficient)
    following_posts = Post.objects.filter(user__in=following_users).order_by('-timestamp')
    
    # Add like information for each post
    for post in following_posts:
        post.is_liked_by_user = post.is_liked_by(request.user)
    
    # Pagination
    paginator = Paginator(following_posts, 10)
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)

    return render(request, "network/following.html", {
        "posts_of_the_page": posts_of_the_page
    })


def edit_post(request, post_id):
    if request.method == 'POST':
        try:
            post = Post.objects.get(id=post_id)
            # Security check
            if post.user != request.user:
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            data = json.loads(request.body)
            post.content = data['content']
            post.save()
            
            return JsonResponse({'success': True})
        except Post.DoesNotExist:
            return JsonResponse({'error': 'Post not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


def profile(request, username):
    try:
        profile_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return render(request, "network/profile.html", {"error": "User not found"})
    
    #Handle follow/unfollow
    if request.method == "POST" and request.user.is_authenticated:
        action = request.POST.get("action")
        if action == "follow":
            Follow.objects.get_or_create(follower=request.user, following=profile_user)
        elif action == "unfollow":
            Follow.objects.filter(follower=request.user, following=profile_user).delete()
        return HttpResponseRedirect(reverse("profile", args=[username]))

    posts = Post.objects.filter(user=profile_user).order_by('-timestamp')
    followers_count = profile_user.followers.count()
    following_count = profile_user.following.count()

    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()
    
    return render(request, "network/profile.html", {
        "profile_user": profile_user,
        "posts": posts,
        "followers_count": followers_count,
        "following_count": following_count,
        "is_following": is_following,
    })


def toggle_like(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        like, created = Like.objects.get_or_create(
            user=request.user,
            post=post
        )

        if not created:
            like.delete()
            liked = False
        else:
            liked = True

        return JsonResponse({
            'success': True,
            'liked': liked,
            'liked_count': post.like_count()
        })
    
    except Post.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Post not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


