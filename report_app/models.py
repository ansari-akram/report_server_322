from django.db import models
from django.contrib.auth.models import User
from multiselectfield import MultiSelectField


class Report(models.Model):
    report_name = models.CharField("REPORT NAME", max_length=50)
    assigned_to = models.ManyToManyField(User)

    def __str__(self):
        return self.report_name


class UserType(models.Model):
    usertype = models.CharField(max_length=50)

    def __str__(self):
        return self.usertype


class Department(models.Model):
    # departments = models.CharField(max_length=50)
    # assigned_dept = models.ManyToManyField(DepartmentAdminUser)
    department = models.CharField(max_length=50)

    def __str__(self):
        return self.department


class DepartmentAdminUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    usertype = models.ForeignKey(UserType, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username
