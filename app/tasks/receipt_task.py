from celery import shared_task

@shared_task
def process(hello):
  print(f"process {hello}")