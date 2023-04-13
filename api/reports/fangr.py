from datetime import datetime
from time import time
from api.functions import *
import urllib.parse
import xlwt
import os


class All:
    def __init__(self, queue_id, domain, token):
        self.queue_id = queue_id
        self.domain = domain
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

        if queue['file_type'] == 'xls':
            # creating workbook
            workbook = xlwt.Workbook(encoding='UTF-8')

            # adding sheet
            worksheet = workbook.add_sheet("all living animals")

            # Sheet header, first row
            row_num = 0

            font_style_header = xlwt.XFStyle()
            # headers are bold
            font_style_header.font.bold = True

            date_format = xlwt.XFStyle()
            date_format.num_format_str = 'dd/mm/yyyy'

            # column header names, you can use your own headers here
            columns = ['Breeder',
                   'Current Owner',
                   'Reg No',
                   'Tag No',
                   'Name',
                   'Description',
                   'Date Of Registration',
                   'Date Of Birth',
                   'Sex',
                   'Litter Size',
                   'Father',
                   'Father Notes',
                   'Mother',
                   'Mother Notes',
                   'Breed',
                   'COI',
                   'Mean Kinship']

            # write column headers in sheet
            for col_num in range(len(columns)):
                worksheet.write(row_num, col_num, columns[col_num], font_style_header)

            font_style = xlwt.XFStyle()
            while True:
                pedigrees = requests.get(
                        url=f"{self.domain}/api/pedigrees/?account={queue['account']}&status=alive&limit=100&offset={self.offset_ped}", headers=headers)
                #print(len(pedigrees.json()))

                if len(pedigrees.json()['results']) > 0:
                    self.offset_ped += 100
                else:
                    #print("no more results found")
                    break

                for pedigree in pedigrees.json()['results']:
                    #print(pedigree)
                    row_num = row_num + 1
            
                    try:
                        father = pedigree['parent_father_reg_no']
                        father_name = pedigree['parent_father_name']
                    except AttributeError:
                        father = ""
                        father_name = ""
                    try:
                        mother = pedigree['parent_mother_reg_no']
                        mother_name = pedigree['parent_mother_name']
                    except AttributeError:
                        mother = ""
                        mother_name = ""
                    try:
                        breeder_prefix = pedigree['breeder_breeding_prefix']
                    except AttributeError:
                        breeder_prefix = ""
                    try:
                        current_owner = pedigree['current_owner']
                    except AttributeError:
                        current_owner = ""
                
                    worksheet.write(row_num, 0, breeder_prefix, font_style)
                    worksheet.write(row_num, 1, current_owner, font_style)
                    worksheet.write(row_num, 2, pedigree['reg_no'], font_style)
                    worksheet.write(row_num, 3, pedigree['tag_no'], font_style)
                    worksheet.write(row_num, 4, pedigree['name'], font_style)
                    worksheet.write(row_num, 5, pedigree['description'], font_style)
                    worksheet.write(row_num, 6, pedigree['date_of_registration'], date_format)
                    worksheet.write(row_num, 7, pedigree['dob'], date_format)
                    worksheet.write(row_num, 8, pedigree['sex'], font_style)
                    worksheet.write(row_num, 9, pedigree['litter_size'], font_style)
                    worksheet.write(row_num, 10, father, font_style)
                    worksheet.write(row_num, 11, pedigree['parent_father_notes'], font_style)
                    worksheet.write(row_num, 12, mother, font_style)
                    worksheet.write(row_num, 13, pedigree['parent_mother_notes'], font_style)
                    worksheet.write(row_num, 14, pedigree['breed_breed_name'], font_style)
                    worksheet.write(row_num, 15, pedigree['coi'], font_style)
                    worksheet.write(row_num, 16, pedigree['mean_kinship'], font_style)

            workbook.save(f"data/{self.file_name}.{queue['file_type']}")

                # upload
            multi_part_upload_with_s3(f"data/{self.file_name}.{queue['file_type']}", f"reports/{self.file_name}.{queue['file_type']}", content_type="application/vnd.ms-excel")

            # update report object
            data='{"account": %d, "file_name": "%s", "download_url": "%s"}' % (queue['account'], f"{self.file_name}.{queue['file_type']}", f"https://media.cloud-lines.com/reports/{self.file_name}.{queue['file_type']}")
            res = requests.put(url=urllib.parse.urljoin(self.domain, f"/api/report-queue/{queue['id']}/"), data=data, headers=headers)
            # clean up
            os.remove(f"data/{self.file_name}.{queue['file_type']}")
