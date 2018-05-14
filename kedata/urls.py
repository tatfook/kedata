from django.conf.urls import url, include

urlpatterns = [
    
    url(r'^', include('rest_api.urls')),
]