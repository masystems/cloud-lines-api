from celery import shared_task
from .export.export import ExportAll
from .deployment.largetier import LargeTier


@shared_task(bind=True)
def export_all(*arg, **kwargs):
    """Used to call the ExportAll Class"""
    data = arg[1]
    ExportAll(data['domain'], data['account'], data['file_name']).run()


@shared_task(bind=True)
def new_large_tier(*arg, **kwargs):
    """Used to call the LargeTier Class"""
    data = arg[1]
    LargeTier(data['queue_id']).deploy()


