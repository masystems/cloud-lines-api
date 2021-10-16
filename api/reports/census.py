from datetime import datetime
from api.functions import *
import urllib.parse
import xlwt


class Census:
    def __init__(self, queue_id, from_date=False, to_date=False):
        self.queue_id = queue_id
        self.from_date = from_date
        self.to_date = to_date
        self.date = datetime.now()
        self.offset = 0

    def run(self):
        headers = get_headers(self.domain)
        # check if user has permission
        queue_item = requests.put(url=urllib.parse.urljoin(self.domain, f"/api/report-queue/{self.queue_id}/"))
        queue = queue_item.json()

        form = False
        if self.from_date and self.to_date:
            form = True
            # convert dates
            start_date_object = datetime.strptime(self.from_date, '%d/%m/%Y')
            start_date = start_date_object.strftime('%Y-%m-%d')
            end_date_object = datetime.strptime(self.to_date, '%d/%m/%Y')
            end_date = end_date_object.strftime('%Y-%m-%d')

        if queue['file_type'] == 'xls':
            # creating workbook
            workbook = xlwt.Workbook(encoding='utf-8')

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
                    url=f"{self.domain}/api/breeders/?account={self.account}&active=true&limit=100&offset={self.offset}",
                    headers=headers)

                for breeder in breeders.json()['results']:
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
                    pedigrees = requests.get(
                    url=f"{self.domain}/api/pedigrees/?account={self.account}&current_owner={breeder['id']}&status=alive&limit=100&offset={self.offset}",
                    headers=headers)
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

                        if len(pedigrees.json()['results']) == 0:
                            break
                        else:
                            self.offset += 100
                workbook.save(f"data/self.file_name.{self.file_type}")
        elif type == 'pdf':
            context = {}
            context['breeders'] = []
            while True:
                breeders = requests.get(
                    url=f"{self.domain}/api/breeders/?account={self.account}&active=true&limit=100&offset={self.offset}",
                    headers=headers)
                context['breeders'].append(breeders.json()['results'])
                if len(breeders.json()['results']) == 0:
                    break
                else:
                    self.offset += 100
            # if form:
            #     context['pedigrees'] = Pedigree.objects.filter(account=attached_service,
            #                                                    status='alive',
            #                                                    date_of_registration__range=[start_date, end_date], )
            # else:
            context['pedigrees'] = []
            while True:
                pedigrees = requests.get(
                    url=f"{self.domain}/api/pedigrees/?account={self.account}&&status=alive&limit=100&offset={self.offset}",
                    headers=headers)
                context['pedigrees'].append(pedigrees.json()['results'])
                if len(pedigrees.json()['results']) == 0:
                    break
                else:
                    self.offset += 100

            render_to_pdf('census.html', context, self.file_name)

            # upload
            multi_part_upload_with_s3(f"data/{self.file_type}.pdf", f"exports/self.file_name.{self.file_type}")
