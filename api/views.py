from django.shortcuts import HttpResponse
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework.decorators import action
from .tasks import *


class Tasks(viewsets.ViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=['post'])
    def export_all(self, request):
        export_all.delay(request.data)
        return HttpResponse(True)

    @action(detail=False, methods=['post'])
    def new_large_tier(self, request):
        new_large_tier.delay(request.data)
        return HttpResponse(True)


class Reports(viewsets.ViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=['post'])
    def census(self, request):
        report_census.delay(request.data)
        return HttpResponse(True)

    @action(detail=False, methods=['post'])
    def all(self, request):
        report_all.delay(request.data)
        return HttpResponse(True)

    @action(detail=False, methods=['post'])
    def all_boo(self, request):
        # all breeder or owner
        report_all_boo.delay(request.data)
        return HttpResponse(True)

    @action(detail=False, methods=['post'])
    def fangr(self, request):
        fangr.delay(request.data)
        return HttpResponse(True)


class CustomFields(viewsets.ViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=['post'])
    def update_fields(self, request):
        custom_fields.delay(request.data)
        return HttpResponse(True)

