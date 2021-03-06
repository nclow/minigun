import json
import yaml

from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render
from cerberus import Validator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions

from minigunapp.models import Email
from minigunapp.serializers import EmailSerializer
from minigunapp.tasks import send_email


v = Validator()
schema = yaml.load(open('minigunapp/schemas/email.yaml'))
page_size = 10


class EmailList(APIView):

    def get(self, request, format=None):
        """ Returns a single page of emails in Json format """

        page = int(request.GET.get('page', 1))
        page = page if page > 0 else 1
        start = page_size * page
        end = page_size * (page + 1)

        emails = Email.objects[start:end]
        emails = [EmailSerializer(email).data for email in emails]
        return JsonResponse(emails, safe=False)

    def post(self, request, format=None):
        """ Creates and saves new email, then dispatches send task to celery.
        Returns the new email object.
        """

        body = json.loads(request.body.decode("utf-8"))
        valid = v.validate(body, schema)
        if(not valid):
            return JsonResponse(v.errors, status=400)

        email = Email(**body)
        email.from_ = 'nclow@localhost.localdomain'
        email.status = 'pending'
        email.save()

        send_email.delay(str(email.id))

        email = EmailSerializer(email)
        return JsonResponse(email.data, safe=False)


class EmailDetail(APIView):
    def get(self, request, id, format=None):
        """ Returns a single email by id, in Json format """

        email = Email.objects.get(id=id)
        email = EmailSerializer(email)
        return JsonResponse(email.data, safe=False)
