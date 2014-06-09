from django.conf.urls import include, patterns, url

urlpatterns = patterns('record.views',
    (r'^add/(.+)/$', 'add'),
    (r'^add/$', 'add'),
    (r'^import/$', 'add_many'),
    url(r'^(\d+)/$', 'update', name='record-detail'),
    (r'^(\d+)/update/$', 'update'),
    (r'^(\d+)/update/category/$', 'update_category'),
    (r'^(\d+)/update/title/$', 'update_title'),
    (r'^(\d+)/delete/$', 'delete'),
    (r'^category/$', 'category'),
    (r'^category/reorder/$', 'reorder_category'),
    (r'^category/add/$', 'add_category'),
    (r'^category/(\d+)/delete/$', 'delete_category'),
    (r'^category/(\d+)/rename/$', 'rename_category'),
)
