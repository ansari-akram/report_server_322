from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import re
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from spacy_langdetect import LanguageDetector
import spacy
from spacy.tokens import Doc, Span
from googletrans import Translator
from spacy.language import Language
from .models import Log, EventType
from difflib import SequenceMatcher
import xml.etree.ElementTree as ET
import requests
from django.shortcuts import render
from .filters import LogFilter

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from .utils import render_to_pdf
from django.http import HttpResponse
from django.views.generic import View

import xlwt
import random

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

tree = ET.parse('zayed_university_app\ZU_xml_v2.xml')


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


workspace_id = 'lMpsX8-ivT4J5jaAZRo4cNUnotfqOO-_Vp2zia532An5'
workspace_url = 'https://api.eu-gb.assistant.watson.cloud.ibm.com/instances/dbb25da5-56bd-4b0c-ac66-62db88b266a6'
assistant_id_eng = '20a3ca09-8ae6-4c62-ae83-b9f9d1f7e394'
assistant_url = 'https://api.eu-gb.assistant.watson.cloud.ibm.com/instances/dbb25da5-56bd-4b0c-ac66-62db88b266a6'
assistant_id_ar = '67525f3e-6b3d-4474-a957-dfe0ee55730f'
assistant_crawl_id = '4c8f53fc-7293-43dd-970c-fba16887b8b2'

cont = {}
translator = ''
# assistant = ''
session_id_ = ''


def custom_detection_function(spacy_object):
    assert isinstance(spacy_object, Doc) or isinstance(

        spacy_object, Span), "spacy_object must be a spacy Doc or Span object but it is a {}".format(type(spacy_object))

    detection = Translator().detect(spacy_object.text)

    return {'language': detection.lang, 'score': detection.confidence}


def create_lang_detector(nlp, name):
    return LanguageDetector()


Language.factory("language_detector", func=create_lang_detector)
nlp = spacy.load("en_core_web_sm")
nlp.add_pipe('language_detector', last=True)


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


global assistant
authenticator = IAMAuthenticator(workspace_id)
assistant = AssistantV2(version='2021-06-14', authenticator=authenticator)
assistant.set_service_url(assistant_url)


def get_data(_dict):
    return _dict['event_type'], _dict['event_question'], _dict['user_email']


@csrf_exempt
def get_response_from_watson(request):
    _data = JSONParser().parse(request)
    ip = request.META.get('REMOTE_ADDR')
    try:
        event_type, text, user_email = get_data(_data)
        session_id_ = _data['session_value']
    except:
        text = ''
        session_id_ = ''

    doc = nlp(text.upper())
    # if session_id_ == '' and doc._.language['language'] == 'en':
    #     session_id_ = assistant.create_session(assistant_id_eng).get_result()['session_id']
    #     response = assistant.message(assistant_id=assistant_id_eng, session_id=session_id_, input={'text': text},context=cont)

    if session_id_ == '' and doc._.language['language'] == 'ar':
        session_id_ = assistant.create_session(assistant_id_ar).get_result()['session_id']
        response = assistant.message(assistant_id=assistant_id_ar, session_id=session_id_, input={'text': text},
                                     context=cont)
    else:
        session_id_ = assistant.create_session(assistant_id_eng).get_result()['session_id']
        response = assistant.message(assistant_id=assistant_id_eng, session_id=session_id_, input={'text': text},
                                     context=cont)
        print("assistant_id_eng")

        # eid = EventType.objects.get(id=int(5))

        # Log.objects.create(event_type_id=eid, user_email=user_email, user_ip=ip, event_question=text,

        #                    event_answer='')

        # return JsonResponse({'session_id': session_id_, 'answer': "Sorry, I am not able to detect the language you are asking."})

    res = response.get_result()

    if len(res['output']['intents']) > 0:
        intents = res['output']['intents'][0]['intent']
        print("intents", intents)
    else:
        intents = ""
        print("Emty Intent")
        session_id_ = assistant.create_session(assistant_crawl_id).get_result()['session_id']
        response = assistant.message(assistant_id=assistant_crawl_id, session_id=session_id_, input={'text': text},
                                     context=cont)
        res = response.get_result()
        print("In 1st try")
        output = ''
        link = 'https://www.zu.ac.ae/main'
        root = tree.getroot()
        for country in root.findall('system-folder'):
            name = country.find('name').text
            path = country.find('path').text
            if similar(name, text) >= 0.8:
                output = link + path
                payload = {}
                headers = {}

                response = requests.request("GET", output, headers=headers, data=payload)
                if response.status_code == 200:
                    eid = EventType.objects.get(id=int(4))
                    Log.objects.create(event_type_id=eid, user_email=user_email, user_ip=ip, event_question=text,
                                       event_answer=output, intent='General')
                    return JsonResponse(
                        {'session_id': '', 'answer': '', 'intent': 'general', 'url': output})

                else:
                    eid = EventType.objects.get(id=int(4))
                    Log.objects.create(event_type_id=eid, user_email=user_email, user_ip=ip, event_question=text,
                                       event_answer=str(response.status_code), intent='General')
                    return JsonResponse(
                        {'session_id': '', 'answer': str(response.status_code) + ' Link is not up', 'intent': 'general',
                         'url': output})

        try:
            print("In 2nd Try")
            output_desc = res['output']['generic'][0]['primary_results'][0]['highlight']['Description'][0]
            output_url = res['output']['generic'][0]['primary_results'][0]['highlight']['GeneratedLink'][0]
            output_code = res['output']['generic'][0]['primary_results'][0]['highlight']['ServiceCode'][0]
            eid = EventType.objects.get(id=int(4))
            Log.objects.create(event_type_id=eid, user_email=user_email, user_ip=ip, event_question=text,
                               event_answer='', intent='General')
            return JsonResponse(
                {'session_id': session_id_, 'answer': f'{output_desc}', 'intent': 'general', 'url': output_url})

        except:
            eid = EventType.objects.get(id=int(5))
            Log.objects.create(event_type_id=eid, user_email=user_email, user_ip=ip, event_question=text,
                               event_answer='', intent='General')
            return JsonResponse(
                {'session_id': session_id_,
                 'answer': "Sorry, I am not able to detect the language you are asking."})

    try:
        output = res['output']['generic'][0]['primary_results'][0]['highlight']['answer']
    except:
        try:
            output = res['output']['generic'][0]['additional_results'][0]['highlight']['answer']
        except:
            try:
                output = res['output']['generic'][0]['text']
            except:
                print("In 3rd Except")
                eid = EventType.objects.get(id=int(5))
                Log.objects.create(event_type_id=eid, user_email=user_email, user_ip=ip, event_question=text,
                                   event_answer='', intent=intents)
                return JsonResponse(
                    {'session_id': session_id_,
                     'answer': "Sorry, I am not able to detect the language you are asking."})

    if len(output) > 1:
        temp = ''
        for o in output:
            temp += o + ' '
        message = cleanhtml(temp)

    else:
        message = cleanhtml(output[0])
    if message == '':
        message = cleanhtml(res['output']['generic'][0]['primary_results'][0]['answers'][0]['text'])
    message = cleanhtml(message)
    eid = EventType.objects.get(id=int(event_type))
    Log.objects.create(event_type_id=eid, user_email=user_email, user_ip=ip, event_question=text,
                       event_answer=message, intent=intents)
    return JsonResponse({'session_id': session_id_, 'answer': message, 'intent': intents})


@csrf_exempt
def login(request):
    _data = JSONParser().parse(request)
    event_type, event_question, user_email = get_data(_data)
    ip = request.META.get('REMOTE_ADDR')
    eid = EventType.objects.get(id=int(event_type))
    Log.objects.create(event_type_id=eid, user_email=user_email, user_ip=ip, event_question=event_question,
                       event_answer='')
    return JsonResponse({'status': 'success'})


@csrf_exempt
def wrong_answer(request):
    _data = JSONParser().parse(request)

    event_type, event_question, user_email = get_data(_data)

    ip = request.META.get('REMOTE_ADDR')

    event_answer = _data['event_answer']

    intents = _data['intent']

    eid = EventType.objects.get(id=int(3))
    print('[INFO]', event_type, event_question, user_email, ip, event_answer, intents, eid.description)
    Log.objects.create(event_type_id=eid, user_email=user_email, user_ip=ip, event_question=event_question,
                       event_answer=event_answer, intent=intents)

    return JsonResponse({'status': 'success'})


@csrf_exempt
def reset_count(request):
    _data = JSONParser().parse(request)
    event_type, event_question, user_email = get_data(_data)
    ip = request.META.get('REMOTE_ADDR')

    intents = _data['intent']

    eid = EventType.objects.get(id=int(_data['event_type']))
    Log.objects.create(event_type_id=eid, user_email=user_email, user_ip=ip, event_question=event_question,
                       event_answer='', intent=intents)

    return JsonResponse({'status': 'success'})



def is_valid_queryparam(param):
    return param != '' and param is not None


# Common Global variable
log_exp = None


def advance_filter(request):
    global log_exp

    log_ = Log.objects.all()

    # for pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(log_, 10)
    try:
        pages = paginator.page(page)
    except PageNotAnInteger:
        pages = paginator.page(1)
    except EmptyPage:
        pages = paginator.page(paginator.num_pages)

    event_type_id_exact_query = request.GET.get('etype')
    user_email = request.GET.get('email')
    event_question = request.GET.get('quest')
    event_answer = request.GET.get('ans')
    date_min = request.GET.get('date_min')
    date_max = request.GET.get('date_max')
    intent_exact_query = request.GET.get('dtype')

    if is_valid_queryparam(event_type_id_exact_query):
        log_ = log_.filter(event_type_id=event_type_id_exact_query)

    if is_valid_queryparam(user_email):
        log_ = log_.filter(user_email__icontains=user_email)

    if is_valid_queryparam(event_question):
        log_ = log_.filter(event_question__icontains=event_question)

    if is_valid_queryparam(event_question):
        log_ = log_.filter(event_question__icontains=event_question)
    if is_valid_queryparam(event_answer):
        log_ = log_.filter(event_answer__icontains=event_answer)

    if is_valid_queryparam(date_min):
        log_ = log_.filter(user_datetime__gte=date_min)

    if is_valid_queryparam(date_max):
        log_ = log_.filter(user_datetime__lte=date_max)

    if is_valid_queryparam(intent_exact_query):
        log_ = log_.filter(intent=intent_exact_query)

    dept = Log.objects.all().values_list('intent', flat=True).distinct()
    dept_list = [i for i in dept if i != '']

    event_ = EventType.objects.all()
    # event_list = [i for i in event_ if i != '']
    # print("event_type_id>>> ", event_.description)

    log_exp = log_

    context = {
        'log_': log_,
        'dept_list': dept_list,
        'event_': event_,
        'pages': pages
    }

    return render(request, 'home/advance_filter.html', context)


# Opens up page as PDF
class ViewPDF(LoginRequiredMixin, UserPassesTestMixin, View):

    def get(self, request, *args, **kwargs):
        context = {
            'log_': Log.objects.all()
        }

        pdf = render_to_pdf('home/filter_template.html', context)
        if pdf:
            return HttpResponse(pdf, content_type='application/pdf')
        return HttpResponse("PDF Not Found.")

    def test_func(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
        return False


def admin_check(user):
    if user.is_staff or user.is_superuser:
        return True
    return False


@login_required
@user_passes_test(admin_check)
def export_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Report.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Report')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Event ID', 'User Email', 'Question', 'Answer',
               'Date Time', 'Department']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    font_style = xlwt.XFStyle()

    rows = Log.objects.all().values_list(
        'event_type_id__description', 'user_email', 'event_question',
        'event_answer', 'user_datetime', 'intent')

    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)
    wb.save(response)

    if wb:
        return response
    return HttpResponse("No Data Found.")


# Automatically downloads Filtered PDF file
class FilterPDF(LoginRequiredMixin, UserPassesTestMixin, View):

    def get(self, request, *args, **kwargs):
        global log_exp

        context = {
            'log_': log_exp,
        }
        pdf = render_to_pdf('home/filter_template.html', context)
        if pdf:
            return HttpResponse(pdf, content_type='application/pdf')
        return HttpResponse("PDF Not Found.")

    def test_func(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
        return False


# Automatically downloads Filtered Excel file
@login_required
@user_passes_test(admin_check)
def filter_excel(request):
    global log_exp
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Report.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Report')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Event ID', 'User Email', 'Question', 'Answer',
               'Date Time', 'Department']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    font_style = xlwt.XFStyle()

    rows = log_exp.values_list(
        'event_type_id__description', 'user_email', 'event_question',
        'event_answer', 'user_datetime', 'intent')

    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)
    wb.save(response)

    if wb:
        return response
    return HttpResponse("No Data Found.")
