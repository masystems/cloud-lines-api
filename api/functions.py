from boto3.s3.transfer import TransferConfig
from boto3 import resource
from django.conf import settings
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import StringIO, BytesIO
import requests


def multi_part_upload_with_s3(file_path, remote_output, content_type="text/json"):
    # Multipart upload
    s3 = resource('s3')
    config = TransferConfig(multipart_threshold=1024 * 10, max_concurrency=10,
                            multipart_chunksize=1024 * 10, use_threads=True)
    s3.meta.client.upload_file(file_path, settings.AWS_S3_CUSTOM_DOMAIN, remote_output,
                                    ExtraArgs={'ACL': 'private', 'ContentType': content_type},
                                    Config=config,
                                    )


def get_headers(domain, token=False):
    if token:
        return {'Content-Type': 'application/json', 'Authorization': f"token {token}"}
    else:
        token_res = requests.post(url=f'{domain}/api/api-token-auth',
                                  data={'username': settings.CL_USER,
                                        'password': settings.CL_PASS})
        return {'Content-Type': 'application/json', 'Authorization': f"token {token_res.json()['token']}"}


def render_to_pdf(template_src, context_dict, file_name):
    template = get_template(template_src)
    html = template.render(context_dict)
    #result = BytesIO()
    #pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    with open(f"data/{file_name}.pdf", 'wb+') as output:
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), output)

