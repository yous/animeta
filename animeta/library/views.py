# -*- coding: utf-8 -*-

from django.shortcuts import *
from django.contrib.auth.models import User

from record.models import StatusTypes
from record.forms import RecordUpdateForm
from connect import get_connected_services

from django import forms
from record.models import Category
class FilterForm(forms.Form):
    category = forms.ModelChoiceField(
        label=u'분류',
        queryset=Category.objects.none(),
        empty_label=u'전체',
        required=False
    )
    sort_by = forms.ChoiceField(
        label=u'정렬 기준',
        choices=(
            ('date', u'날짜'),
            ('title', u'제목')
        ),
        initial='date',
        widget=forms.RadioSelect
    )
    status = forms.MultipleChoiceField(
        label=u'감상 상태',
        choices=(
            ('watching', u'보는 중'),
            ('finished', u'완료'),
            ('suspended', u'중단'),
            ('interested', u'관심 작품'),
        ),
        initial=('watching', 'interested'),
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, owner, *args, **kwargs):
        super(FilterForm, self).__init__(*args, **kwargs)
        self.owner = owner
        self.fields['category'].queryset = Category.objects.filter(user=self.owner)

    def get_items(self):
        if not self.is_bound or not self.is_valid():
        	category = None
        	sort_by = self.fields['sort_by'].initial
        	status = self.fields['status'].initial
        else:
        	category = self.cleaned_data['category']
        	sort_by = self.cleaned_data['sort_by']
        	status = self.cleaned_data['status']

        items = self.owner.record_set.filter(
            status_type__in=(StatusTypes.from_name(s) for s in status),
        )
        if category:
        	items = items.filter(category=category)
        if sort_by == 'date':
        	items = items.order_by('-updated_at')
        elif sort_by == 'title':
            items = items.order_by('title')
        return items

def library(request, username):
    owner = get_object_or_404(User, username=username)
    filter_form = FilterForm(owner, request.GET or None)
    items = filter_form.get_items()
    records = owner.history_set.all()[:10]
    return render(request, 'library/library.html', {
    	'owner': owner,
    	'filter_form': filter_form,
    	'items': items,
    	'records': records,
    })

def item_detail(request, username, id):
    owner = get_object_or_404(User, username=username)
    item = owner.record_set.get(id=id)
    if request.user == owner:
    	form = RecordUpdateForm(item)
    else:
    	form = None
    return render(request, 'library/item_detail.html', {
    	'owner': owner,
    	'item': item,
    	'records': item.history_set,
    	'update_form': form,
    	'connected_services': get_connected_services(owner),
    })
