from django.urls import path
from .views import *
from django.conf.urls import url

urlpatterns = [
    path('watson-assistant/', get_response_from_watson, name="watson-assistant"),
    path('login/', login),
    path('reset/', reset_count),
    path('wrong_answer/', wrong_answer, name="wrong_answer"),
    # path('advance_filter/', advance_filter, name='advance_filter')
    path('advance_filter/', advance_filter, name='advance_filter'),

    path('pdf_view/', ViewPDF.as_view(), name="pdf_view"),
    path('filter_pdf/', FilterPDF.as_view(), name="filter_pdf"),

    path('export_excel/', export_excel, name="export_excel"),
    path('filter_excel/', filter_excel, name="filter_excel"),
]
