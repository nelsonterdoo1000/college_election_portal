from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/public/elections/(?P<election_id>\d+)/live-results/$', consumers.ElectionResultsConsumer.as_asgi()),
] 