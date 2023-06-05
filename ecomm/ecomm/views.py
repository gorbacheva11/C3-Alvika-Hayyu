from django_ratelimit.decorators import ratelimit
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render


@ratelimit(key='user', rate='5/m')
@csrf_exempt
def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():  # log in user
            user = form.get_user()
            login(request, user)
        if 'next' in request.POST:
            return redirect(request.POST.get('next'))
        else:
            return redirect('home-produk-list')
    else:
        form = AuthenticationForm()
        next_url = request.GET.get('next')
    return render(request, '/accounts/login', {'form': form, 'next': next_url})


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            # log the user in
            return redirect('toko:home-produk-list')
    else:
        form = UserCreationForm()

    form = UserCreationForm()
    return render(request, '/accounts/signup', {'form': form})
