from celery import shared_task
from api.models import ExportQueue
from time import sleep

@shared_task(bind=True)
def test_func(self):
    sleep(10)
    for i in range(10):
        print(i)
    return "Done"


@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)


@shared_task
def count_widgets():
    return ExportQueue.objects.count()


@shared_task
def rename_widget(widget_id, domain):
    w = ExportQueue.objects.get(id=widget_id)
    w.domain = domain
    w.save()