from django.db import models
import uuid


class EventType(models.Model):
    description = models.CharField(max_length=20)

    def __str__(self):
        return self.description


class MasterTable(models.Model):
    question = models.CharField(max_length=1000)
    answer = models.TextField(max_length=8000)

    def __str__(self):
        return self.question


class Log(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type_id = models.ForeignKey(EventType, on_delete=models.CASCADE)
    user_email = models.EmailField()
    user_ip = models.GenericIPAddressField()
    event_question = models.CharField(max_length=1000)
    event_answer = models.CharField(max_length=2000)
    user_datetime = models.DateTimeField(auto_now_add=True)
    intent = models.CharField(default='', max_length=100)


    def __str__(self):
        return self.user_email

    # added
    class Meta:
        db_table = "zayed_university_app_log"
