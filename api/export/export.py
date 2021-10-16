from json import loads, JSONDecodeError
from pathlib import Path
from api.functions import *
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
        self.file_name_csv = f'{file_name}.csv'
        self.local_csv = os.path.join(self.local_output_dir, self.file_name_csv)
        self.remote_csv_path = f'exports/{self.file_name_csv}'
        self.s3 = resource('s3')

    def run(self):
        headers = get_headers(self.domain)

        with open(self.local_csv, mode='w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            while True:
                pedigrees = requests.get(url=f"{self.domain}/api/pedigrees/?account={self.account}&limit=100&offset={self.offset}",
                                         headers=headers)
                if len(pedigrees.json()['results']) == 0:
                    break

                for pedigree in pedigrees.json()['results']:
                    head = []
                    row = []
                    for key, val in pedigree.items():
                        if key in ('id', 'state', 'creator', 'account'):
                            continue
                        # load custom fields
                        if key == 'custom_fields':
                            try:
                                #print(pedigree['custom_fields'])
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
                    writer.writerow(row)

                self.offset += 100

        multi_part_upload_with_s3(self.local_csv, self.remote_csv_path, content_type="text/csv")
        self.cleanup()
        return True

    def cleanup(self):
        for item in Path(self.local_output_dir).glob('*'):
            if item.is_file():
                itemtime = arrow.get(item.stat().st_mtime)
                if itemtime < self.critical_delete_time:
                    os.remove(item)
                    pass
