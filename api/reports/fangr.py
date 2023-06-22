from datetime import datetime
from time import time
from api.functions import *
from openpyxl import load_workbook
from io import BytesIO
import requests
import urllib.parse
import subprocess
import os
import json


class Fangr:
    def __init__(self, queue_id, domain, account, year, breed, email, token):
        self.queue_id = queue_id
        self.domain = domain
        self.account = account
        self.year = year
        self.breed = breed
        self.email = email
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
        self.file_name = f"FAnGR-UKGLE-Inventory-{self.epoch}-report.xlsx"
        self.offset_bre = 0
        self.offset_ped = 0
        self.domain = domain

        self.url = "https://s3.eu-west-1.amazonaws.com/media.cloud-lines.com/reports/UKGLE_Inventory_form_v0.2.xlsx"

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
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        data = json.loads(result.stdout)
        response = requests.get(self.url)

        # get breed data
        breed_data = requests.get(url=urllib.parse.urljoin(self.domain, f"/api/breeds/{self.breed}/"), headers=headers)

        # get account data
        account_data = requests.get(url=urllib.parse.urljoin(self.domain, f"/api/attached-service/{self.account}/"), headers=headers)

        # Load the Excel file into memory
        excel_file = BytesIO(response.content)
        workbook = load_workbook(excel_file)

        # Edit the Excel file (example: change a cell value)
        sheet = workbook['Inventory']
        sheet['C5'] = breed_data.json()['breed_name']
        sheet['C10'] = self.year
        sheet['C11'] = data['females_this_year']
        sheet['C12'] = data['males_this_year']
        sheet['C13'] = data['total_females']
        sheet['C14'] = data['total_males']
        sheet['C15'] = data['total_breeders']
        sheet['C20'] = account_data.json()['organisation_or_society_name']
        sheet['C21'] = self.email
        sheet['C23'] = self.date.date().strftime('%d/%m/%Y')

        # Save the edited file locally
        with open(f"data/{self.file_name}", "wb") as output_file:
            workbook.save(output_file)

        # upload
        multi_part_upload_with_s3(f"data/{self.file_name}", f"reports/{self.file_name}", content_type="application/vnd.ms-excel")

        # update report object
        data='{"account": %d, "file_name": "%s", "download_url": "%s"}' % (queue['account'], self.file_name, f"https://media.cloud-lines.com/reports/{self.file_name}")
        res = requests.put(url=urllib.parse.urljoin(self.domain, f"/api/report-queue/{queue['id']}/"), data=data, headers=headers)
        # # clean up
        # os.remove(f"data/{self.file_name}.{queue['file_type']}")
