from django.urls import path, re_path
from .views import *

urlpatterns = [
    path('', index, name='home'),
    path('index_admin', index_admin, name='index_admin'),
    path('user', users, name='user'),
    path('home/', index, name='report'),
    path('update_report', update_report, name='update_report'),
    # re_path(r'^.*\.*', pages, name='pages'),
    path('dashboard/<department_name>', get_dept_data, name="department_data"),
    path('login_/', dept_login, name='login_'),
    path('register_/', dept_register, name='register_'),
    path('logout_/', dept_logout, name='logout_'),
    path('page_not_found/', page_not_found, name='page_not_found'),

    # path('ViewDailyPDF/', ViewDailyPDF, name='ViewDailyPDF'),
    path('show/<report_name>/', report, name='show'),
    path('export_pdf/<report_name>/', report, name='export_pdf'),
    path('export_excel/<report_name>/', report, name='export_excel'),

]
