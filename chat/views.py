
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from .models import Message, Profile

# ─────────────────────────────────────────────
# Auth Views
# ─────────────────────────────────────────────

@require_http_methods(["GET", "POST"])     # ✅ Reject unexpected HTTP methods
def register_view(request):
    # ✅ Redirect already-logged-in users away from register page
    if request.user.is_authenticated:
        return redirect('home')

    error = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # ✅ Basic input validation
        if not username or not password:
            error = 'Username and password are required.'
        elif len(username) > 150:
            error = 'Username too long.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif User.objects.filter(username=username).exists():
            error = 'Username already taken.'
        else:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            return redirect('home')

    return render(request, 'register.html', {'error': error})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    error = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # ✅ Don't hit the DB at all if inputs are empty
        if not username or not password:
            error = 'Please enter both username and password.'
        else:
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                profile, _ = Profile.objects.get_or_create(user=user)
                profile.is_online = True
                profile.save(update_fields=['is_online'])
                next_url = request.GET.get('next', '')
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                return redirect('home')
            else:
                error = 'Wrong username or password.'

    return render(request, 'login.html', {'error': error})


@require_http_methods(["POST", "GET"])     # ✅ Ideally POST-only; GET kept for convenience
def logout_view(request):
    # ✅ Set offline on logout
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.is_online = False
        profile.last_seen = timezone.now()
        profile.save(update_fields=['is_online', 'last_seen'])
    logout(request)
    return redirect('login')


# ─────────────────────────────────────────────
# Main Views
# ─────────────────────────────────────────────

@login_required(login_url='/login/')
def home(request):
    search_query = request.GET.get('search', '').strip()
    search_results = []
    recent_chats   = []

    if search_query:
        # ✅ select_related('profile') avoids N+1 for profile lookups
        users = (
            User.objects
            .filter(username__icontains=search_query)
            .exclude(id=request.user.id)
            .select_related('profile')
                )

        for user in users:
            # ✅ Use hasattr guard; only call get_or_create if profile truly missing
            profile = getattr(user, 'profile', None)
            if profile is None:
                profile, _ = Profile.objects.get_or_create(user=user)
            search_results.append({
                'user':      user,
                'is_online': profile.is_online,
            })

    else:
        # ✅ Fetch only the latest message per conversation (avoids loading entire history)
        messages = (
            Message.objects
            .filter(Q(sender=request.user) | Q(receiver=request.user))
            .order_by('-timestamp')
            .select_related('sender', 'receiver')
        )

        seen_ids    = set()          # ✅ set() is O(1) lookup vs list O(n)
        other_users = []

        for msg in messages:
            other = msg.receiver if msg.sender == request.user else msg.sender
            if other.id not in seen_ids:
                seen_ids.add(other.id)
                other_users.append(other)

        # ✅ Single query for all profiles (no per-user DB hit)
        profiles    = Profile.objects.filter(user__in=other_users).select_related('user')
        profile_map = {p.user_id: p for p in profiles}

        for other in other_users:
            profile = profile_map.get(other.id)
            if not profile:
                profile, _ = Profile.objects.get_or_create(user=other)
            recent_chats.append({
                'user':      other,
                'is_online': profile.is_online,
            })

    return render(request, 'home.html', {
        'search_results': search_results,
        'recent_chats':   recent_chats,
        'search_query':   search_query,
    })

# ✅ Replace your chat_view with this updated version
# It now passes recent_chats to the template so the sidebar works

@login_required(login_url='/login/')
def chat_view(request, username):
    other_user = get_object_or_404(User, username=username)

    if other_user == request.user:
        return redirect('home')

    messages = (
        Message.objects
        .filter(
            Q(sender=request.user, receiver=other_user) |
            Q(sender=other_user,   receiver=request.user)
        )
        .order_by('timestamp')
        .select_related('sender', 'receiver')
    )

    profile, _ = Profile.objects.get_or_create(user=other_user)
    last_seen  = profile.get_last_seen_display()

    # ✅ Sidebar data — same logic as home view
    search_query   = request.GET.get('search', '').strip()
    search_results = []
    recent_chats   = []

    if search_query:
        users = (
            User.objects
            .filter(username__icontains=search_query)
            .exclude(id=request.user.id)
            .select_related('profile')
        )
        for user in users:
            p = getattr(user, 'profile', None)
            if not p:
                p, _ = Profile.objects.get_or_create(user=user)
            search_results.append({'user': user, 'is_online': p.is_online})
    else:
        msgs = (
            Message.objects
            .filter(Q(sender=request.user) | Q(receiver=request.user))
            .order_by('-timestamp')
            .select_related('sender', 'receiver')
        )
        seen_ids    = set()
        other_users = []
        for msg in msgs:
            other = msg.receiver if msg.sender == request.user else msg.sender
            if other.id not in seen_ids:
                seen_ids.add(other.id)
                other_users.append(other)

        profiles    = Profile.objects.filter(user__in=other_users).select_related('user')
        profile_map = {p.user_id: p for p in profiles}
        for o in other_users:
            p = profile_map.get(o.id)
            if not p:
                p, _ = Profile.objects.get_or_create(user=o)
            recent_chats.append({'user': o, 'is_online': p.is_online})

    return render(request, 'chat.html', {
        'other_user':     other_user,
        'messages':       messages,
        'last_seen':      last_seen,
        'recent_chats':   recent_chats,
        'search_results': search_results,
        'search_query':   search_query,
    })
    
    
def error_404(request, exception=None):
    return render(request, '404.html', status=404)

def error_500(request):
    return render(request, '500.html', status=500)

def error_403(request, exception=None):
    return render(request, '403.html', status=403)