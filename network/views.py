import json
from django.contrib.auth import authenticate, login, logout
from django.core import paginator
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.http.response import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from network.forms import PostForm

from .models import Follower, User, Post, UserFollowing


def index(request):
    posts = Post.objects.all().order_by('-date_created')
    post_list = pagination(request, posts)

    if request.method == "POST":
        if request.POST.get('content'):
            post_form = PostForm(request.POST)
            print(post_form)
            if post_form.is_valid():
                new_post = post_form.save(commit=False)
                new_post.author = request.user
                new_post.save()
                print(f'Saved {new_post, new_post.author}')

    return render(request, "network/index.html", {
        "posts": Post.objects.all().order_by('-date_created'),
        "paginatior":paginator,
        "post_list":post_list,
        # "likes":Like.objects.all()
    })



@csrf_exempt
@login_required
def edit_post(request, pk):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    post = Post.objects.get(id=pk)
    data = json.loads(request.body)

    if (request.user != post.author):
        return JsonResponse({
            "error": "You have to be post creator to be able to edit it"
        }, status=400)

    edited_post = data["body"]
    if edited_post == [""]:
        return JsonResponse({
            "error": "At least one character is required"
        }, status=400)

    try:
        post.content = edited_post
        print(post)
        post.save()
    except:
        return JsonResponse({
            "error": "Something bad happened"
        }, status=400)

    return JsonResponse({"message": "Post edited successfully."}, status=201)


@csrf_exempt
@login_required
def like_post(request, pk):
    print('got it')
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    post = Post.objects.get(id=pk)
    user = request.user

    try:
        if Post.objects.filter(id=pk, liked_by=user).exists():
            post.liked_by.remove(user)
            post.save()
            return JsonResponse({"message": "Like has been removed.",
            "total_likes": f"{post.liked_by.count()}"}, status=201)
        else:
            post.liked_by.add(user)
            post.save()
    except:
        return JsonResponse({
            "error": "Something bad happened"
        }, status=400)

    return JsonResponse({"message": "Liked post successfully.", "total_likes": f"{post.liked_by.count()}"}, status=201)




def pagination(request, posts):
    page = request.GET.get('page', 1)
    paginator = Paginator(posts, 10)
    try:
        post_list = paginator.page(page)
    except PageNotAnInteger:
        post_list = paginator.page(1)
    except EmptyPage:
        post_list = paginator.page(paginator.num_pages)

    return post_list

def user_profile(request, username):

    current_user = request.user
    user = User.objects.get(username=username)
    posts = Post.objects.filter(author=user).order_by('-date_created')
    post_list = pagination(request, posts)
    is_it_same_user = user == current_user
    print(is_it_same_user)
    try:
        UserFollowing.objects.filter(user_id=current_user, following_user_id=user)
        following_is_true = True
        print('following')
    except:
        following_is_true = False
        print('here')
    user_following = len(user.following.all())
    user_followers = len(user.followers.all())
    print(user_followers)
    context = {
       "user": user,
       "following_is_true":following_is_true,
       'user_followers':user_followers,
       'user_following':user_following,
       'post_list':post_list,
       "paginatior":paginator,
       "is_it_same_user":is_it_same_user
    }

    return render(request, 'user_profile.html', context)

def followers_count(request):
    if request.method == "POST":
        print('POST')
        value = request.POST['value']
        user = request.POST['user']
        follower = request.POST['follower']
        print('user = ', user)
        main_user = User.objects.get(username=request.POST['user'])
        follower_user = User.objects.get(username=request.POST['follower'])
        if value == 'follow':
            UserFollowing.objects.create(user_id=main_user,
                             following_user_id=follower_user)
        else: 
            UserFollowing.objects.filter(user_id=main_user,
                             following_user_id=follower_user).delete()
        return redirect('/profile/'+follower)

def following_page(request):
    user_id_array = []
    all_posts = None
    message = ""
    following_users = UserFollowing.objects.filter(user_id=request.user).values('following_user_id')
    if len(following_users) == 0:
        post_list = ""
        message = "You are not following anyone"
    for user in following_users:
        user_id = user.get('following_user_id')
        user_id_array.append(user_id)
        all_posts = Post.objects.filter(author__in=user_id_array).order_by('-date_created')
        post_list = pagination(request, all_posts)


    return render(request, "network/following_page.html", {
        "post_list":post_list,
        "message":message
    })

# def edit(request, entity):
#         if request.method == "POST":
#         if request.POST.get("title") and request.POST.get("content"):
#             print(request.POST.get("title"))

def login_view(request):
    if request.method == "POST":
        if request.POST.get('amount'):
            print('jaja')

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
