import requests
import sys


print(f"Domain: {sys.argv[1]}") # https://demo.cloud-lines.com
print(f"Username: {sys.argv[2]}") # myusername
print(f"Password: {sys.argv[3]}") # supersecretpassword

## Get the token
token_res = requests.post(url=f'{sys.argv[1]}/api-token-auth/', data={'username': sys.argv[2], 'password': sys.argv[3]})
print(token_res.json())

## create header
headers = {'Content-Type': 'application/json', 'Authorization': f"token {token_res.json()['token']}"}

## get pedigrees
data = '{"domain": "https://dev.cloud-lines.com", "account": 4}'

post_res = requests.post(url=f'{sys.argv[1]}/api/custom_fields/update_fields/', headers=headers, data=data)
print(post_res.request.body)
print(post_res.text)