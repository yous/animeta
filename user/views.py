# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView, TemplateView
from django.contrib.auth import login as _login
from django.contrib.auth.models import User
from django.contrib.auth.views import login as login_view
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from chart.models import weekly, PopularWorksChart
from connect import get_connected_services
from record.models import Uncategorized, StatusTypes, include_records
from record.templatetags.indexing import group_records
from api import views_v2 as api_v2
import datetime
import json

@csrf_protect
def login(request):
    if request.POST.has_key('remember'):
        request.session.set_expiry(3600 * 24 * 14)
    else:
        request.session.set_expiry(0)
    return login_view(request)

@csrf_protect
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            _login(request, user)
            request.session.set_expiry(0)
            return redirect(user)
    else:
        form = UserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})

class SettingsView(TemplateView):
    template_name = 'user/settings.html'

    def get(self, request, *args, **kwargs):
        self.password_change_form = PasswordChangeForm(user=request.user)
        return super(SettingsView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.password_change_form = PasswordChangeForm(user=request.user, data=request.POST)
        if self.password_change_form.is_valid():
            self.password_change_form.save()
            messages.success(request, u'암호를 바꿨습니다.')
            return redirect('/settings/')
        return super(SettingsView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return {
            'password_change_form': self.password_change_form,
            'services': get_connected_services(self.request.user),
        }

def shortcut(request, username):
    try:
        user = User.objects.get(username=username)
        return redirect(user)
    except User.DoesNotExist:
        return redirect('/%s/' % username)

def _date_header(date):
    # 오늘/어제/그저께/그끄저께/이번 주/지난 주/이번 달/지난 달/YYYY-MM
    today = datetime.date.today()
    dt = lambda **kwargs: today - datetime.timedelta(**kwargs)
    if date == today: return u'오늘'
    elif date == dt(days=1): return u'어제'
    elif date == dt(days=2): return u'그저께'
    elif date == dt(days=3): return u'그끄저께'
    elif date.isocalendar()[:2] == today.isocalendar()[:2]:
        return u'이번 주'
    elif date.isocalendar()[:2] == dt(weeks=1).isocalendar()[:2]:
        return u'지난 주'
    elif date.year == today.year and date.month == today.month:
        return u'이번 달'
    else:
        last_month = (today.year, today.month - 1)
        if last_month[1] == 0:
            last_month = (last_month[0] - 1, 12)
        if date.year == last_month[0] and date.month == last_month[1]:
            return u'지난 달'
        else:
            return date.strftime('%Y/%m')

def library(request, username=None):
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user

    return render(request, 'user/library.html', {
        'owner': user,
        'preload_data': json.dumps({
            'owner': api_v2.serialize_user(user),
            'categories': map(api_v2.serialize_category, [Uncategorized(user)] + list(user.category_set.all())),
            'current_user': api_v2.serialize_user(request.user) if request.user.is_authenticated() else None,
            'records': map(api_v2.serialize_record, user.record_set.all()),
        })
    })

def include_delete_flag(user):
    def _callback(qs):
        for history in qs:
            history.can_delete = history.deletable_by(user)
    return _callback

class HistoryListView(ListView):
    template_name = 'user/history.html'
    paginate_by = 8

    def get_queryset(self):
        self.user = get_object_or_404(User, username=self.kwargs['username'])
        return self.user.history_set.select_related('work', 'user') \
                .transform(include_records) \
                .transform(include_delete_flag(self.request.user))

    def get_context_data(self, **kwargs):
        context = super(HistoryListView, self).get_context_data(**kwargs)
        context['owner'] = self.user
        return context

class HistoryFeedView(ListView):
    template_name = 'user/history.atom'
    paginate_by = 20

    def get_queryset(self):
        self.user = get_object_or_404(User, username=self.kwargs['username'])
        return self.user.history_set.select_related('work', 'user')

    def get_context_data(self, **kwargs):
        context = super(HistoryFeedView, self).get_context_data(**kwargs)
        context['owner'] = self.user
        return context

    def render_to_response(self, context, **response_kwargs):
        response_kwargs['mimetype'] = 'application/atom+xml'
        return super(HistoryFeedView, self).render_to_response(context, **response_kwargs)
