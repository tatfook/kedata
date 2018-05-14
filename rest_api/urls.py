from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = [
    url(r'^users/(?P<username>[^/]+)/snippets/$', views.SnippetList.as_view()), 
    url(r'^users/(?P<username>[^/]+)/snippets/(?P<pk>[0-9]+)/$', views.SnippetDetail.as_view()),
    url(r'^gitlab_hook$', views.gitlab_hook),
]

# urlpatterns = format_suffix_patterns(urlpatterns)
