# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from work.models import Work
from django.db.models import Count
import datetime

class Chart(object):
	item_class = lambda self, o, c: o

	def __init__(self, range = None, limit=None):
		self.range = range
		self.limit = limit
		self.queryset = None

	@property
	def start(self):
		return self.range[0]

	@property
	def end(self):
		return self.range[1]

	def __iter__(self):
		return self

	def next(self):
		if not self.queryset:
			self.queryset = self.get_query_set()[:self.limit]
			self.iter = iter(self.queryset)

		return self.item_class(self.iter.next(), self)

	def get_query_set(self):
		raise NotImplementedError

class WorkItem(object):
	def __init__(self, row, chart):
		self.title = row['title']
		self.factor = row['factor']
		self.chart = chart

	def __unicode__(self):
		return self.title

	@models.permalink
	def get_absolute_url(self):
		return ('work.views.detail', (), {'title': unicode(self)})

class PopularWorksChart(Chart):
	item_class = WorkItem
	def get_query_set(self):
		qs = Work.objects
		if self.range:
			qs = qs.filter(record__updated_at__range=self.range)
		return qs.exclude(title='').values('title').annotate(factor=Count('record')).filter(factor__gt=1).order_by('-factor')

class EnthusiastsChart(Chart):
	title = u'열혈 사용자'
	def get_query_set(self):
		qs = User.objects
		if self.range:
			qs = qs.filter(history__updated_at__range=self.range)
		return qs.annotate(factor=Count('history')).exclude(factor=0).order_by('-factor')

def during(**kwargs):
	now = datetime.datetime.now()
	start = now - datetime.timedelta(**kwargs)
	return (start, now)
