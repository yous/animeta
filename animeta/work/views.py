# -*- coding: utf-8 -*-
import urllib
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.db import models, transaction
from django.views.generic import list_detail
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from work.models import Work, MergeRequest, normalize_title
from record.models import Record, History

def old_url(request, remainder):
    return HttpResponseRedirect('/works/' + urllib.quote(remainder.encode('UTF-8')))

def _get_record(request, work):
    if request.user.is_authenticated():
        try:
            record = request.user.record_set.get(work=work)
        except:
            record = None
    else:
        record = None
    return record

def detail(request, title):
    work = get_object_or_404(Work, title=title)

    N = 6
    history = work.history_set.all().select_related('user')
    comments = list(history.exclude(comment='')[:N])
    if len(comments) < N:
        comments += list(history.filter(comment='')[:N-len(comments)])

    similar_works = work.similar_objects[:7]
    normal_title = normalize_title(work.title)
    for w in similar_works:
        w.can_merge = normalize_title(w.title) != normal_title and not w.has_merge_request(work)
    return render(request, "work/work_detail.html", {
        'work': work,
        'record': _get_record(request, work),
        'records': work.record_set,
        'similar_works': similar_works,
        'comments': comments,
        'daum_api_key': settings.DAUM_API_KEY
    })

def list_users(request, title):
    work = get_object_or_404(Work, title=title)
    return render(request, "work/users.html", {
        'work': work,
        'record': _get_record(request, work),
        'records': work.record_set.order_by('status_type', 'user__username')
    })

def video(request, title, provider, id):
    work = get_object_or_404(Work, title=title)

    return render(request, "work/video.html", {
        'work': work,
        'record': _get_record(request, work),
        'records': work.record_set,
        'video_id': id
    })

def search(request):
    keyword = request.GET.get('keyword', '')
    return list_detail.object_list(request,
        queryset = Work.objects.filter(title__icontains=keyword),
        extra_context = {'keyword': keyword},
    )

def merge_dashboard(request):
    error = None

    if request.method == 'POST':
        if 'apply' in request.POST:
            success = 0
            fail = 0
            for id in request.POST.getlist('apply'):
                with transaction.commit_on_success():
                    try:
                        req = MergeRequest.objects.get(id=id)
                        req.target.merge(req.source)
                        success += 1
                    except:
                        fail += 1
            error = 'Success: %d, failure: %d' % (success, fail)
        else:
            work = Work.objects.get(title=request.POST['target'])
            source = Work.objects.get(title=request.POST['source'])
            if work.has_merge_request(source):
                error = u'이미 요청이 있습니다.'
            else:
                MergeRequest.objects.create(user=request.user, source=source, target=work)

    return list_detail.object_list(request,
        queryset = MergeRequest.objects.order_by('-id'),
        paginate_by = 50,
        template_object_name = 'merge',
        template_name = 'work/merge_dashboard.html',
        extra_context = {
            'contributors': User.objects.annotate(count=models.Count('mergerequest')).order_by('-count').exclude(count=0),
            'error': error,
        }
    )

@login_required
@require_http_methods(['POST'])
def request_merge(request, title, id):
    work = get_object_or_404(Work, title=title)

    if request.method == 'POST':
        source = get_object_or_404(Work, id=id)
        try:
            req, created = MergeRequest.objects.get_or_create(user=request.user, source=source, target=work)
            if created:
                return HttpResponse("merged")
            else:
                req.delete()
                return HttpResponse("cancelled")
        except:
            return HttpResponse("fail")
