from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Post, Follow


def index(request):
    if request.method == "POST" and request.user.is_authenticated:
        content = request.POST.get("content")
        if content:
            Post.objects.create(user=request.user, content=content)
            return HttpResponseRedirect(reverse("index"))

    posts = Post.objects.all().order_by('-timestamp')  # Get all posts, newest first
    return render(request, "network/index.html", {
        "posts": posts
    })


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


# Add this function to network/views.py
def profile(request, username):
    try:
        profile_user = User.objects.get(username=username)
    except User.DoesNotExist:
        # Handle user not found
        return render(request, "network/profile.html", {"error": "User not found"})
    
    posts = Post.objects.filter(user=profile_user).order_by('-timestamp')
    followers_count = profile_user.followers.count()
    following_count = profile_user.following.count()
    
    # Check if current user follows this profile user
    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()
    
    return render(request, "network/profile.html", {
        "profile_user": profile_user,
        "posts": posts,
        "followers_count": followers_count,
        "following_count": following_count,
        "is_following": is_following
    })


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