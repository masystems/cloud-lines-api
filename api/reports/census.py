from datetime import datetime
from time import time
from api.functions import *
import urllib.parse
import xlwt
import os


class Census:
    def __init__(self, queue_id, domain, token):
        self.queue_id = queue_id
        self.domain = domain
        self.token = token

        self.date = datetime.now()
        self.epoch = int(time())
        self.file_name = f"census-{self.epoch}-report"
        self.offset_bre = 0
        self.offset_ped = 0
        self.domain = domain

    def run(self):
        headers = get_headers(self.domain, self.token)
        # check if user has permission
        queue_item = requests.get(url=urllib.parse.urljoin(self.domain, f"/api/report-queue/{self.queue_id}/"))
        queue = queue_item.json()
        #print(queue)

        if queue['file_type'] == 'xls':
            # creating workbook
            workbook = xlwt.Workbook(encoding='UTF-8')

            # adding sheet
            worksheet = workbook.add_sheet("flockbook")

            # Sheet header, first row
            row_num = 0

            font_style_header = xlwt.XFStyle()
            # headers are bold
            font_style_header.font.bold = True

            date_format = xlwt.XFStyle()
            date_format.num_format_str = 'dd/mm/yyyy'

            # column header names, you can use your own headers here
            columns = ['Sex', 'Reg No', 'Date Of Birth', 'Name', 'Tag No', 'Litter Size', 'Sire', 'Sire Name', 'Dam',
                       'Dam Name', 'DOR']

            # write column headers in sheet
            for col_num in range(len(columns)):
                worksheet.write(row_num, col_num, columns[col_num], font_style_header)

            while True:
                breeders = requests.get(
                    url=f"{self.domain}/api/breeders/?account={queue['account']}&active=true&limit=100&offset={self.offset_bre}",
                    headers=headers)
               #print(f"breeders: {len(breeders.json()['results'])}")

                if len(breeders.json()['results']) == 0:
                    break
                else:
                    self.offset_bre += 100

                for breeder in breeders.json()['results']:
                    self.offset_ped = 0
                    # write breeder column headers in sheet
                    row_num = row_num + 1
                    worksheet.write(row_num, 0, breeder['contact_name'], font_style_header)
                    worksheet.write(row_num, 1, f"Prefix: {breeder['breeding_prefix']}", font_style_header)

                    # Sheet body, remaining rows
                    font_style = xlwt.XFStyle()

                    # if self.from_date and self.to_date:
                    #     pedigrees = Pedigree.objects.filter(account=attached_service,
                    #                                         current_owner=breeder,
                    #                                         date_of_registration__range=[start_date, end_date],
                    #                                         status='alive')
                    # else:
                    while True:
                        if queue["from_date"] and queue["to_date"]:
                            pedigrees = requests.get(
                                    url=f"{self.domain}/api/pedigrees/?from_date={queue['from_date']}&to_date={queue['to_date']}&account={queue['account']}&current_owner={breeder['id']}&status=alive&limit=100&offset={self.offset_ped}",
                                    headers=headers)
                            #print(f"{self.domain}/api/pedigrees/?from_date={queue['from_date']}&to_date={queue['to_date']}&current_owner={breeder['id']}&account={queue['account']}&status=alive&limit=100&offset={self.offset_ped}")
                            #print(f"peds: {len(pedigrees.json()['results'])}")
                        else:
                            pedigrees = requests.get(
                                    url=f"{self.domain}/api/pedigrees/?account={queue['account']}&current_owner={breeder['id']}&status=alive&limit=100&offset={self.offset_ped}",
                                    headers=headers)
                            #print(f"{self.domain}/api/pedigrees/?account={queue['account']}&current_owner={breeder['id']}&status=alive&limit=100&offset={self.offset_ped}")
                            #print(f"peds: {len(pedigrees.json()['results'])}")
                        
                        if len(pedigrees.json()['results']) > 0:
                            self.offset_ped += 100
                        else:
                            #print("no more results found")
                            break

                        for pedigree in pedigrees.json()['results']:
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
                            worksheet.write(row_num, 0, pedigree['sex'], font_style)
                            worksheet.write(row_num, 1, pedigree['reg_no'], font_style)
                            worksheet.write(row_num, 2, pedigree['dob'], font_style)
                            worksheet.write(row_num, 3, pedigree['name'], font_style)
                            worksheet.write(row_num, 4, pedigree['tag_no'], font_style)
                            worksheet.write(row_num, 5, pedigree['litter_size'], font_style)
                            worksheet.write(row_num, 6, father, font_style)
                            worksheet.write(row_num, 7, father_name, font_style)
                            worksheet.write(row_num, 8, mother, font_style)
                            worksheet.write(row_num, 9, mother_name, font_style)
                            worksheet.write(row_num, 10, pedigree['date_of_registration'], date_format)


            workbook.save(f"data/{self.file_name}.{queue['file_type']}")

                # upload
            multi_part_upload_with_s3(f"data/{self.file_name}.{queue['file_type']}", f"reports/{self.file_name}.{queue['file_type']}", content_type="application/vnd.ms-excel")

        elif queue['file_type'] == 'pdf':
            context = {}
            context['breeders'] = []
            context['pedigrees'] = []
            while True:
                breeders = requests.get(
                    url=f"{self.domain}/api/breeders/?account={queue['account']}&active=true&limit=100&offset={self.offset_bre}",
                    headers=headers)
                #print(f"{self.domain}/api/breeders/?account={queue['account']}&active=true&limit=100&offset={self.offset_bre}")
                #print(f"breeders: {len(breeders.json()['results'])}")
                context['breeders'].append(breeders.json()['results'])
                
                for breeder in breeders.json()['results']:
                    self.offset_ped = 0
                    while True:
                        if queue["from_date"] and queue["to_date"]:
                            pedigrees = requests.get(
                                    url=f"{self.domain}/api/pedigrees/?from_date={queue['from_date']}&to_date={queue['to_date']}&account={queue['account']}&current_owner={breeder['id']}&active=true&limit=100&offset={self.offset_ped}",
                                    headers=headers)
                        else:
                            pedigrees = requests.get(
                                url=f"{self.domain}/api/pedigrees/?account={queue['account']}&current_owner={breeder['id']}&status=alive&limit=100&offset={self.offset_ped}",
                                headers=headers)
                            #print(f"{self.domain}/api/pedigrees/?account={queue['account']}&current_owner={breeder['id']}&status=alive&limit=100&offset={self.offset_ped}")
                            #print(f"peds: {len(pedigrees.json()['results'])}")

                        if len(pedigrees.json()['results']) > 0:
                            for ped in pedigrees.json()['results']:
                                context['pedigrees'].append(ped)
                        else:
                            #print("no more results found")
                            break
                        self.offset_ped += 100
                else:
                    break
                self.offset_bre += 100

            render_to_pdf('census.html', context, f"{self.file_name}")

            # upload
            multi_part_upload_with_s3(f"data/{self.file_name}.{queue['file_type']}", f"reports/{self.file_name}.{queue['file_type']}", content_type="application/pdf")
        
        # update report object
        data='{"account": %d, "file_name": "%s", "download_url": "%s"}' % (queue['account'], f"{self.file_name}.{queue['file_type']}", f"https://media.cloud-lines.com/reports/{self.file_name}.{queue['file_type']}")
        res = requests.put(url=urllib.parse.urljoin(self.domain, f"/api/report-queue/{queue['id']}/"), data=data, headers=headers)
        # clean up
        os.remove(f"data/{self.file_name}.{queue['file_type']}")
