from django.conf import settings
from clapi.mail import send_mail
from requests.adapters import HTTPAdapter
from jinja2 import Environment, FileSystemLoader
from subprocess import PIPE
from botocore.config import Config
from git import Repo
from time import sleep
from api.functions import *
import urllib.parse
import json
import os
import random
import string
import subprocess
import requests
import boto3
import re


class LargeTier:
    def __init__(self, build_id):
        """
        id: ID of the large tier queue item, used to get the data from the cloud-lines small tier APA
        """
        self.build_id = build_id
        self.domain = "https://cloud-lines.com"

        # Generate passwords
        self.django_password = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(50)])
        self.db_password = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(16)])
        self.db_username = 'pedigreedbuser'

        self.boto_config = Config(retries=dict(max_attempts=20))

        self.dependency_packages = os.listdir('api/deployment/dependencies/')

    def deploy(self):
        headers = get_headers(self.domain)
        queue_item = requests.put(url=urllib.parse.urljoin(self.domain, f"/api/large-tier-queue/{self.build_id}/"))
        deployment = queue_item.json()

        ## update settings
        requests.put(url=urllib.parse.urljoin(self.domain, f"/api/large-tier-queue/{self.build_id}/"),
                     data={"build_state": "building"})

        self.site_name = deployment['subdomain']
        self.site_name_safe = re.sub(r'[^a-zA-Z0-9]', '', self.site_name)
        
        self.target_dir = '/opt/instances/{}/{}'.format(self.site_name_safe, self.site_name_safe)

        ## set template dir root
        self.env = Environment(loader=FileSystemLoader(self.target_dir))

        ## update settings
        self.update_build_status("Captured your settings", 10)
        sleep(10)

        ## create database
        print("Creating DB")
        # set db name
        self.db_name = re.sub(r'[^a-zA-Z0-9]', '', self.site_name)
        client = boto3.client(
            'rds', region_name='eu-west-2', config=self.boto_config
        )
        db_vars = {
            "DBName": self.db_name,
            "DBInstanceIdentifier": self.db_name,
            "AllocatedStorage": 20,
            "DBInstanceClass": "db.t3.micro",
            "Engine": "postgres",
            "MasterUsername": self.db_username,
            "MasterUserPassword": self.db_password,
            "VpcSecurityGroupIds": [
                "sg-0a2432a6a0c703f5e",
            ],
            "DBSubnetGroupName": "default-vpc-016908fc41dd3e6f8",
            "DBParameterGroupName": "default.postgres14",
            "BackupRetentionPeriod": 0,
            "MultiAZ": False,
            "EngineVersion": "16.1",
            "PubliclyAccessible": True,
            "StorageType": "gp2",
        }
        new_db = client.create_db_instance(**db_vars)

        ## update settings
        self.update_build_status("Initiating database creation", 20)
        sleep(10)

        ## clone repo
        print("Cloning repo")
        Repo.clone_from(f'https://masystems:{settings.GIT_AUTH}@github.com/masystems/cloud-lines.git',
                        self.target_dir)

        ## update settings
        self.update_build_status("Created clone of Cloud-Lines", 30)
        sleep(10)

        ## copy in dependencies
        #print("Copying dependencies")
        #for dep in self.dependency_packages:
        #    fullpath = os.path.join('api/deployment/dependencies/', dep)
        #    if os.path.isfile(fullpath):
        #        shutil.copy(fullpath, self.target_dir)

        #        shutil.copy(fullpath, self.target_dir)

        ## update settings
        self.update_build_status("Added in some dependencies", 40)
        sleep(10)

        ## update zappa settings
        print("Creating zappa settings")
        template = self.env.get_template('zappa_settings.j2')
        with open(os.path.join(self.target_dir, 'zappa_settings.json'), 'w') as fh:
            fh.write(template.render(site_name=self.site_name))

        ## update settings
        self.update_build_status("Created site configuration file", 50)
        sleep(10)

        ## create virtualenv
        print("Creating venv")
        # /usr/bin/python3 -m venv venv
        subprocess.Popen(['/usr/bin/python3', '-m', 'venv', '/opt/instances/{}/venv'.format(self.site_name_safe)])

        ## update settings
        self.update_build_status("Created virtual environment", 60)
        sleep(10)

        ## wait for db to be created
        print("Waiting for DB to be created")
        waiter = client.get_waiter("db_instance_available")
        waiter.wait(DBInstanceIdentifier=self.db_name, WaiterConfig={"Delay": 10, "MaxAttempts": 60}, )

        ## update settings
        self.update_build_status("Database has been created", 70)
        sleep(10)

        ## get db endpoint
        print("Getting DB endpoint")
        details = client.describe_db_instances(DBInstanceIdentifier=self.db_name)
        db_host = details['DBInstances'][0]['Endpoint']['Address']

        ## update settings
        self.update_build_status("Captured new database settings", 80)
        sleep(10)

        ## update local settings
        print("Creating local settings")
        template = self.env.get_template('cloudlines/local_settings.j2')
        with open(os.path.join(self.target_dir, 'cloudlines/local_settings.py'), 'w') as fh:
            fh.write(template.render(site_name=self.site_name,
                                     site_mode='hierarchy',
                                     django_password=self.django_password,
                                     db_name=self.db_name,
                                     db_username=self.db_username,
                                     db_password=self.db_password,
                                     db_host=db_host))

        ## update settings
        self.update_build_status("Connected site to database", 90)
        sleep(10)

        ## generate user data
        print("Getting user data")
        with open(os.path.join(self.target_dir, 'user.json'), 'w') as outfile:
            json.dump(deployment['user_data'], outfile)

        # get services
        print("Getting services")
        #service_get = requests.get(url=urllib.parse.urljoin(self.domain, f"/api/services/"))
        with open(os.path.join(self.target_dir, 'services.json'), 'w') as outfile:
            json.dump(deployment['services_data'], outfile)
        
        self.update_build_status("Captured users settings", 95)

        # Initiate site
        print("Running initiation with the following args:")
        print(f"{self.site_name_safe}")
        # run commands inside the venv
        venv = subprocess.Popen(['/opt/site_initiate.sh', self.site_name_safe], stdout=PIPE, stderr=PIPE)
        print(venv.stdout.read())
        print(venv.stderr.read())

        # update settings
        self.update_build_status("New Cloud-Lines site build complete!", 100)
        sleep(10)

        # update settings
        requests.put(url=urllib.parse.urljoin(self.domain, f"/api/large-tier-queue/{self.build_id}/"),
                     data={"build_state": "complete"})

        # wait for domain to come up
        print("Waiting for domain to come up")
        domain = f'https://{self.site_name}.cloud-lines.com'
        status = ''
        for x in range(0, 500):
            try:
                session = requests.Session()
                session.mount(domain, HTTPAdapter(max_retries=1))
                request = session.get(domain, timeout=5)

                if request.status_code == 200:
                    print('Web site exists')
                    # send mail
                    msg = """Your site is now live at <a href="{}">{}</a>
                    Enjoy your new Cloud-Lines instance!""".format(domain, domain)
                    # send to user
                    send_mail('Your new Cloud-Lines instance is live!', deployment['user_data'][0]['fields']['username'], msg, send_to=deployment['user_data'][0]['fields']['email'])
                    # send to admin
                    send_mail('Your new Cloud-Lines instance is live!', deployment['user_data'][0]['fields']['username'], msg)
                    break
                else:
                    print('Web site does not exist')
            except requests.exceptions.ConnectionError:
                status = "DOWN"
            except requests.exceptions.HTTPError:
                status = "HttpError"
            except requests.exceptions.ProxyError:
                status = "ProxyError"
            except requests.exceptions.Timeout:
                status = "TimeoutError"
            except requests.exceptions.ConnectTimeout:
                status = "connectTimeout"
            except requests.exceptions.ReadTimeout:
                status = "ReadTimeout"
            except requests.exceptions.TooManyRedirects:
                status = "TooManyRedirects"
            except requests.exceptions.MissingSchema:
                status = "MissingSchema"
            except requests.exceptions.InvalidURL:
                status = "InvalidURL"
            except requests.exceptions.InvalidHeader:
                status = "InvalidHeader"
            except requests.exceptions.URLRequired:
                status = "URLmissing"
            except requests.exceptions.InvalidProxyURL:
                status = "InvalidProxy"
            except requests.exceptions.RetryError:
                status = "RetryError"
            except requests.exceptions.InvalidSchema:
                status = "InvalidSchema"
            print(status)
            sleep(5)

        # Initiate site
        print("Running configuration with the following args:")
        print(f"{self.site_name_safe} {str(deployment['username'])} {str(deployment['service_id'])} {deployment['stripe_id']} {deployment['site_mode']} {deployment['animal_type']}")
        # run commands inside the venv
        venv = subprocess.Popen(['/opt/site_configure.sh',
                          # $SITE_NAME
                          self.site_name,
                          # $USERNAME
                          str(deployment['username']),
                          # $SERVICE_PK
                          str(deployment['service_id']),
                          # $STRIPE_ID
                          deployment['stripe_id'],
                          # $SITE_MODE
                          deployment['site_mode'],
                          # $ANIMAL_TYPE
                          deployment['animal_type'],
                          # $SITE_NAME_SAFE
                          self.site_name_safe], stdout=PIPE, stderr=PIPE)
        #print(venv.stdout.read())
        #print(venv.stderr.read())


    def update_build_status(self, status, percentage):
        requests.put(url=urllib.parse.urljoin(self.domain, f"/api/large-tier-queue/{self.build_id}/"),
                data={"build_status": f"{status}",
                "percentage_complete": percentage})
