from datetime import datetime
from time import time
from api.functions import *
import urllib.parse
import xlwt
import subprocess
import os


class Fangr:
    def __init__(self, queue_id, domain, account, year, breed, token):
        self.queue_id = queue_id
        self.domain = domain
        self.account = account
        self.year = year
        self.breed = breed
        self.token = token

        # get subdomain
        try:
            netloc = urllib.parse.urlsplit(self.domain).netloc
            if netloc.startswith("www."):
                netloc = netloc[4:]
            self.subdomain = netloc.split(".")[0]
        except IndexError:
            self.subdomain = None

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

        command = ["/opt/cloud-lines-api/run_in_venv.sh",
                f"/opt/instances/{self.subdomain}/venv",
                f"/opt/instances/{self.subdomain}/venv/bin/python",
                f"/opt/instances/{self.subdomain}/{self.subdomain}/manage.py",
                "fangr",
                "--attached_service",
                f" {self.account}",
                "--breed",
                f"{self.breed}",
                "--year",
                f"{self.year}"]
        print(command)
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        print(result.stdout)
        print(result.stderr)

        

            
            # # upload
            # multi_part_upload_with_s3(f"data/{self.file_name}.{queue['file_type']}", f"reports/{self.file_name}.{queue['file_type']}", content_type="application/vnd.ms-excel")

            # # update report object
            # data='{"account": %d, "file_name": "%s", "download_url": "%s"}' % (queue['account'], f"{self.file_name}.{queue['file_type']}", f"https://media.cloud-lines.com/reports/{self.file_name}.{queue['file_type']}")
            # res = requests.put(url=urllib.parse.urljoin(self.domain, f"/api/report-queue/{queue['id']}/"), data=data, headers=headers)
            # # clean up
            # os.remove(f"data/{self.file_name}.{queue['file_type']}")
