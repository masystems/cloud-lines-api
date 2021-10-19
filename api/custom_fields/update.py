from json import loads, JSONDecodeError
from pathlib import Path
from api.functions import *
import json
import requests


class UpdateCustomFields:
    def __init__(self, domain, account):
        self.domain = domain
        self.account = account
        self.offset = 0

    def run(self):
        headers = get_headers(self.domain)

        attached_service = requests.get(
            url=f"{self.domain}/api/attached-service/{self.account}",
            headers=headers).json()

        while True:
            pedigrees = requests.get(
                url=f"{self.domain}/api/pedigrees/?account={self.account}&limit=100&offset={self.offset}",
                headers=headers)

            if len(pedigrees.json()['results']) == 0:
                break
            for pedigree in pedigrees.json()['results']:
                # check custom fields are correct
                try:
                    ped_custom_fields = loads(pedigree['custom_fields'])
                except json.decoder.JSONDecodeError:
                    ped_custom_fields = {}
                try:
                    acc_custom_fields = json.loads(attached_service['custom_fields'])
                except json.decoder.JSONDecodeError:
                    acc_custom_fields = {}

                # variable to keep track of whether the field has been updated
                changed = False
                # go through account custom fields
                for key, val in acc_custom_fields.items():
                    # add the field to pedigree custom fields if not already there
                    if key not in ped_custom_fields.keys():
                        ped_custom_fields[key] = {'id': val['id'],
                                                  'location': val['location'],
                                                  'fieldName': val['fieldName'],
                                                  'fieldType': val['fieldType']}
                        changed = True
                    # update custom fields if they have been edited
                    else:
                        if ped_custom_fields[key]['id'] != val['id']:
                            ped_custom_fields[key]['id'] = val['id']
                            changed = True
                        if ped_custom_fields[key]['location'] != val['location']:
                            ped_custom_fields[key]['location'] = val['location']
                            changed = True
                        if ped_custom_fields[key]['fieldName'] != val['fieldName']:
                            ped_custom_fields[key]['fieldName'] = val['fieldName']
                            changed = True
                        if ped_custom_fields[key]['fieldType'] != val['fieldType']:
                            ped_custom_fields[key]['fieldType'] = val['fieldType']
                            changed = True

                # go through pedigree custom fields
                to_delete = []
                for key, val in ped_custom_fields.items():
                    # remove custom field if it has been deleted from account
                    if key not in acc_custom_fields.keys():
                        to_delete.append(key)
                        changed = True
                for key in to_delete:
                    ped_custom_fields.pop(key, None)

                # update pedigree custom fields if we need to
                if changed:
                    pedigree['custom_fields'] = json.dumps(ped_custom_fields)
                    data = """{"custom_fields": "%s"}""" % json.dumps(ped_custom_fields).replace('"', '\\"')
                    print(data)
                    post_res = requests.put(url=f'{self.domain}/api/pedigrees/{pedigree["id"]}/',
                            data=data,
                            headers=headers)
                    print(post_res.text)
            self.offset += 100
        return True

