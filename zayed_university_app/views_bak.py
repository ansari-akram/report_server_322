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

tree = ET.parse('zayed_university_app/ZU_xml_v2.xml')


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


# except:

#     return {

#         'message': 'Please bind your assistant service',

#         'context': '{}',

#         'output': '{}',

#         'intents': '{}',

#         'language': ''

#     }


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

                return JsonResponse(
                    {'session_id': '', 'answer': output, 'intent': 'general', 'url': output})

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
    # print('[INFO]', event_type, event_question, user_email, ip, event_answer, intents, eid.description)
    Log.objects.create(event_type_id=eid, user_email=user_email, user_ip=ip, event_question=event_question,
                       event_answer='', intent=intents)

    return JsonResponse({'status': 'success'})

