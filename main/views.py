import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

from main.forms import LoginForm, AddSnippetForm
from main.models import Snippet


def get_base_context(request, pagename):
    return {
        'pagename': pagename,
        'user': request.user,
        'loginform': LoginForm(),
    }


def index_page(request):
    snippet_id = request.GET.get('snippet_id')
    if snippet_id:
        try:
            id = int(snippet_id)
            return redirect('view_snippet', id=id)
        except:
            raise Http404
    context = get_base_context(request, 'PythonBin')
    return render(request, 'pages/index.html', context)


def add_snippet_page(request):
    context = get_base_context(request, 'Добавление нового сниппета')
    if request.method == 'POST':
        addform = AddSnippetForm(request.POST)
        if addform.is_valid():
            record = Snippet(
                name=addform.data['name'],
                code=addform.data['code'],
                creation_date=datetime.datetime.now(),
                user=None,
            )
            if request.user.is_authenticated:
                record.user = request.user
            record.save()
            id = record.id
            messages.add_message(request, messages.SUCCESS, "Сниппет успешно добавлен")
            return redirect('view_snippet', id=id)
        else:
            messages.add_message(request, messages.ERROR, "Некорректные данные в форме")
            return redirect('add_snippet')
    else:
        if request.user.is_authenticated:
            user = request.user.username
        else:
            user = 'AnonymousUser'
            
        context['addform'] = AddSnippetForm(
            initial={
                'user': user,
            }
        )
    return render(request, 'pages/add_snippet.html', context)


def view_snippet_page(request, id):
    context = get_base_context(request, 'Просмотр сниппета')
    try:
        record = Snippet.objects.get(id=id)
        initial_data = {
            'name': record.name,
            'code': record.code,
        }
        if record.user:
            initial_data['user'] = record.user.username
        else:
            initial_data['user'] = 'AnonymousUser'
        formatter = HtmlFormatter(cssclass='codehilite')
        context['code_html'] = highlight(record.code, PythonLexer(), formatter)
        context['code_css'] = formatter.get_style_defs('.codehilite')
        context['addform'] = AddSnippetForm(initial=initial_data)

    except Snippet.DoesNotExist:
        raise Http404
    return render(request, 'pages/view_snippet.html', context)


def login_page(request):
    if request.method == 'POST':
        loginform = LoginForm(request.POST)
        if loginform.is_valid():
            username = loginform.data['username']
            password = loginform.data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.add_message(request, messages.SUCCESS, "Авторизация успешна")
            else:
                messages.add_message(request, messages.ERROR, "Неправильный логин или пароль")
        else:
            messages.add_message(request, messages.ERROR, "Некорректные данные в форме авторизации")
    return redirect('index')


def logout_page(request):
    logout(request)
    messages.add_message(request, messages.INFO, "Вы успешно вышли из аккаунта")
    return redirect('index')


def my_snippets_page(request):
    context = get_base_context(request, 'Мои сниппеты')
    context['snippets'] = Snippet.objects.filter(user=request.user).order_by('-creation_date')
    return render(request, 'pages/my_snippets.html', context)
