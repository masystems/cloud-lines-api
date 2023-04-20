from datetime import datetime
from time import time
from api.functions import *
import urllib.parse
import xlwt
import subprocess
import os


class All:
    def __init__(self, queue_id, domain, account, token):
        self.queue_id = queue_id
        self.domain = domain
        self.account = account
        self.token = token

        self.date = datetime.now()
        self.epoch = int(time())
        self.file_name = f"FAnGR-UKGLE-Inventory-{self.epoch}-report"
        self.offset_bre = 0
        self.offset_ped = 0
        self.domain = domain

    def run(self):
        headers = get_headers(self.domain, self.token)
        # check if user has permission
        queue_item = requests.get(url=urllib.parse.urljoin(self.domain, f"/api/report-queue/{self.queue_id}/"))
        queue = queue_item.json()

        command = ["ls"]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(result.stdout)




            
            # # upload
            # multi_part_upload_with_s3(f"data/{self.file_name}.{queue['file_type']}", f"reports/{self.file_name}.{queue['file_type']}", content_type="application/vnd.ms-excel")

            # # update report object
            # data='{"account": %d, "file_name": "%s", "download_url": "%s"}' % (queue['account'], f"{self.file_name}.{queue['file_type']}", f"https://media.cloud-lines.com/reports/{self.file_name}.{queue['file_type']}")
            # res = requests.put(url=urllib.parse.urljoin(self.domain, f"/api/report-queue/{queue['id']}/"), data=data, headers=headers)
            # # clean up
            # os.remove(f"data/{self.file_name}.{queue['file_type']}")
