from json import loads, JSONDecodeError
from django.conf import settings
from boto3.s3.transfer import TransferConfig
from boto3 import resource
from pathlib import Path
import arrow
import os
import csv
import requests


class ExportAll:
    def __init__(self, domain, account, file_name):
        self.domain = domain
        self.account = account
        self.offset = 0
        self.header = False
        self.local_output_dir = 'data/'
        self.critical_delete_time = arrow.now().shift(days=-5)
        self.local_csv = os.path.join(self.local_output_dir, f'{file_name}.csv')
        self.remote_csv_path = f'exports/{file_name}.csv'

    def multi_part_upload_with_s3(self, file_path, remote_output):
        s3 = resource('s3')
        # Multipart upload
        config = TransferConfig(multipart_threshold=1024 * 10, max_concurrency=10,
                                multipart_chunksize=1024 * 10, use_threads=True)
        s3.meta.client.upload_file(file_path, settings.AWS_S3_CUSTOM_DOMAIN, remote_output,
                                   ExtraArgs={'ACL': 'public-read', 'ContentType': 'text/json'},
                                   Config=config,
                                   )

    def run(self):
        token_res = requests.post(url=f'{self.domain}/api/api-token-auth',
                                  data={'username': settings.CL_USER, 'password': settings.CL_PASS})
        headers = {'Content-Type': 'application/json', 'Authorization': f"token {token_res.json()['token']}"}

        with open(self.local_csv, mode='w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            while True:
                pedigrees = requests.get(url=f"{self.domain}/api/pedigrees/?account={self.account}&limit=100&offset={self.offset}",
                                         headers=headers)

                for pedigree in pedigrees.json()['results']:
                    head = []
                    row = []
                    for key, val in pedigree.items():
                        if key in ('id', 'state', 'creator', 'account'):
                            continue
                        # load custom fields
                        if key == 'custom_fields':
                            try:
                                custom_fields = loads(pedigree['custom_fields']).values()
                            except JSONDecodeError:
                                custom_fields = {}

                        if not self.header:
                            if key == 'custom_fields':
                                # add a columns for each custom field
                                for field, value in loads(pedigree['custom_fields']).items():
                                    head.append(field)
                            else:
                                # use verbose names of the pedigree fields as field names
                                head.append(key)

                        if key == 'custom_fields':
                            # populate each custom field column with the value
                            for field in custom_fields:
                                if 'field_value' in field:
                                    row.append(field['field_value'])
                                else:
                                    row.append('')
                        else:
                            row.append('{}'.format(val))
                    if not self.header:
                        writer.writerow(head)
                        self.header = True
                        break
                    writer.writerow(row)

                if len(pedigrees.json()['results']) == 0:
                    break
                else:
                    self.offset += 100

        self.multi_part_upload_with_s3(self.local_csv, self.remote_csv_path)
        self.cleanup()
        return True

    def cleanup(self):
        for item in Path(self.local_output_dir).glob('*'):
            if item.is_file():
                itemtime = arrow.get(item.stat().st_mtime)
                if itemtime < self.critical_delete_time:
                    os.remove(item)
                    pass