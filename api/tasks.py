from celery import shared_task
from .export.export import ExportAll
from .deployment.largetier import LargeTier
from .reports.census import Census
from .custom_fields.update import UpdateCustomFields
from celery.exceptions import SoftTimeLimitExceeded


@shared_task(bind=True)
def export_all(*arg, **kwargs):
    """Used to call the ExportAll Class"""
    data = arg[1]
    ExportAll(data['domain'], data['account'], data['file_name']).run()


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
    """Used to call the ExportAll Class"""
    data = arg[1]
    Census(data['queue_id'], data['domain'], data['token'],).run()


@shared_task(bind=True)
def custom_fields(*arg, **kwargs):
    """Used to call the ExportAll Class"""
    data = arg[1]
    UpdateCustomFields(data['domain'], data['account']).run()
