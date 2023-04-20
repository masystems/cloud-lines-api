from celery import shared_task
from .export.export import ExportAll
from .deployment.largetier import LargeTier
from .reports.census import Census
from .reports.all import All
from .reports.fangr import Fanger
from .custom_fields.update import UpdateCustomFields
from celery.exceptions import SoftTimeLimitExceeded


@shared_task(bind=True)
def export_all(*arg, **kwargs):
    """Used to call the ExportAll Class"""
    data = arg[1]
    ExportAll(data['domain'], data['token'], data['account'], data['file_name']).run()


@shared_task(bind=True)
def new_large_tier(*arg, **kwargs):
    """Used to call the LargeTier Class"""
    data = arg[1]
    try:
        LargeTier(data['queue_id']).deploy()
    except SoftTimeLimitExceeded:
        print("Timelimit exceeded")


@shared_task(bind=True)
def report_census(*arg, **kwargs):
    """Used to call the cencus report"""
    data = arg[1]
    Census(data['queue_id'], data['domain'], data['token'],).run()


@shared_task(bind=True)
def report_all(*arg, **kwargs):
    """Used to call the ExportAll Class"""
    data = arg[1]
    All(data['queue_id'], data['domain'], data['token'],).run()


@shared_task(bind=True)
def fangr(*arg, **kwargs):
    """Used to call the Fanger Class"""
    data = arg[1]
    Fangr(data['queue_id'], data['domain'], data['account'], data['token']).run()


@shared_task(bind=True)
def custom_fields(*arg, **kwargs):
    """Used to call the updatecustomfields Class"""
    data = arg[1]
    UpdateCustomFields(data['domain'], data['account'], data['token']).run()

