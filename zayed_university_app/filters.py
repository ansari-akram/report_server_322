import django_filters
from zayed_university_app.models import *


class LogFilter(django_filters.FilterSet):
    user_email = django_filters.CharFilter(lookup_expr='icontains')
    event_question = django_filters.CharFilter(lookup_expr='icontains')
    event_answer = django_filters.CharFilter(lookup_expr='icontains')
    # intent = django_filters.CharFilter(lookup_expr='icontains')


    class Meta:
        model = Log
        fields = ['event_type_id', 'user_email', 'event_question', 'event_answer', 'user_datetime']
