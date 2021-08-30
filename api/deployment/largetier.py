from django.conf import settings
from clapi.mail import send_mail
from requests.adapters import HTTPAdapter
from jinja2 import Environment, FileSystemLoader
from botocore.config import Config
from git import Repo
from time import sleep
import urllib.parse
import json
import os
import shutil
import random
import string
import subprocess
import requests
import boto3


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
        token_res = requests.post(url=urllib.parse.urljoin(self.domain, "/api/api-token-auth"),
                                  data={'username': settings.CL_USER, 'password': settings.CL_PASS})
        headers = {'Content-Type': 'application/json', 'Authorization': f"token {token_res.json()['token']}"}
        queue_item = requests.put(url=urllib.parse.urljoin(self.domain, f"/api/large-tier-queue/{self.build_id}/"))
        deployment = queue_item.json()

        # update settings
        requests.put(url=urllib.parse.urljoin(self.domain, f"/api/large-tier-queue/{self.build_id}/"),
                     data={"build_state": "building"})

        self.site_name = deployment['subdomain']
        self.target_dir = '/opt/instances/{}/{}'.format(self.site_name, self.site_name)

        # set template dir root
        self.env = Environment(loader=FileSystemLoader(self.target_dir))

        # update settings
        self.update_build_status("Captured your settings", 10)
        sleep(10)

        # create database
        client = boto3.client(
            'rds', region_name='eu-west-2', config=self.boto_config
        )
        db_vars = {
            "DBName": self.site_name,
            "DBInstanceIdentifier": self.site_name,
            "AllocatedStorage": 20,
            "DBInstanceClass": "db.t2.micro",
            "Engine": "postgres",
            "MasterUsername": self.db_username,
            "MasterUserPassword": self.db_password,
            "VpcSecurityGroupIds": [
                "sg-0a2432a6a0c703f5e",
            ],
            "DBSubnetGroupName": "default-vpc-016908fc41dd3e6f8",
            "DBParameterGroupName": "default.postgres10",
            "BackupRetentionPeriod": 0,
            "MultiAZ": False,
            "EngineVersion": "10.6",
            "PubliclyAccessible": True,
            "StorageType": "gp2",
        }
        new_db = client.create_db_instance(**db_vars)

        # update settings
        self.update_build_status("Initiating database creation", 20)
        sleep(10)

        # clone repo
        Repo.clone_from(f'https://masystems:{settings.GIT_AUTH}@github.com/masystems/cloud-lines.git',
                        self.target_dir)

        # update settings
        self.update_build_status("Created clone of Cloud-Lines", 30)
        sleep(10)

        # copy in dependencies
        for dep in self.dependency_packages:
            fullpath = os.path.join('dependcies/', dep)
            if os.path.isfile(fullpath):
                shutil.copy(fullpath, self.target_dir)

        # update settings
        self.update_build_status("Added in some dependencies", 40)
        sleep(10)

        # update zappa settings
        template = self.env.get_template('zappa_settings.j2')
        with open(os.path.join(self.target_dir, 'zappa_settings.json'), 'w') as fh:
            fh.write(template.render(site_name=self.site_name))

        # update settings
        self.update_build_status("Created site configuration file", 50)
        sleep(10)

        # create virtualenv
        subprocess.Popen(['/usr/local/bin/virtualenv', '-p', 'python3', '/opt/instances/{}/venv'.format(self.site_name)])

        # update settings
        self.update_build_status("Created virtual environment", 60)
        sleep(10)

        # wait for db to be created
        waiter = client.get_waiter("db_instance_available")
        waiter.wait(DBInstanceIdentifier=self.site_name, WaiterConfig={"Delay": 10, "MaxAttempts": 60}, )

        # update settings
        self.update_build_status("Database has been created", 70)
        sleep(10)

        # get db endpoint
        details = client.describe_db_instances(DBInstanceIdentifier=self.site_name)
        db_host = details['DBInstances'][0]['Endpoint']['Address']

        # update settings
        self.update_build_status("Captured new database settings", 80)
        sleep(10)

        # update local settings
        template = self.env.get_template('cloudlines/local_settings.j2')
        with open(os.path.join(self.target_dir, 'cloudlines/local_settings.py'), 'w') as fh:
            fh.write(template.render(site_name=self.site_name,
                                     site_mode='hierarchy',
                                     django_password=self.django_password,
                                     db_name=self.site_name,
                                     db_username=self.db_username,
                                     db_password=self.db_password,
                                     db_host=db_host))

        # update settings
        self.update_build_status("Connected site to database", 90)
        sleep(10)

        # generate user data
        process = subprocess.Popen(['/usr/bin/python3', '/opt/cloudlines/cloud-lines/manage.py', 'dumpdata', 'auth.user'], stdout=subprocess.PIPE)
        stdout = process.communicate()[0]
        users = json.loads(stdout)
        for user in users:
            if user['pk'] == deployment.user.pk:
                with open(os.path.join(self.target_dir, 'user.json'), 'w') as outfile:
                    json.dump(user, outfile)

        # wrap user.json in square brackets because django said so!
        with open(os.path.join(self.target_dir, 'user.json'), "r+") as original:
            data = original.read()

        with open(os.path.join(self.target_dir, 'user.json'), "w") as original:
            original.write('[{}]'.format(data))

        # update settings
        self.update_build_status("Captured users settings", 95)
        sleep(10)

        # run commands inside the venv
        subprocess.Popen(['/opt/venv.sh',
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
                          deployment['animal_type']])

        # update settings
        self.update_build_status("New Cloud-Lines site build complete!", 100)
        sleep(10)

        # update settings
        requests.put(url=urllib.parse.urljoin(self.domain, f"/api/large-tier-queue/{self.build_id}/"),
                     data={"build_state": "complete"})

        # wait for domain to come up
        domain = 'https://{}.cloud-lines.com'.format(deployment.subdomain)
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
                    send_mail('Your new Cloud-Lines instance is live!', deployment.user.username, msg, send_to=deployment.user.email)
                    # send to admin
                    send_mail('Your new Cloud-Lines instance is live!', deployment.user.username, msg)
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

    def update_build_status(self, status, percentage):
        requests.put(url=urllib.parse.urljoin(self.domain, f"/api/large-tier-queue/{self.build_id}/"),
                     data={"build_status": f"{status}",
                           "percentage_complete": percentage})