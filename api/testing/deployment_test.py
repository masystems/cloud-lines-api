import requests
import sys

# test build deployment

print(f"Domain: {sys.argv[1]}") # http://localhost:8001
print(f"Username: {sys.argv[2]}") # myusername
print(f"Password: {sys.argv[3]}") # supersecretpassword

## Get the token
token_res = requests.post(url=f'{sys.argv[1]}/api-token-auth/', data={'username': sys.argv[2], 'password': sys.argv[3]})
print(token_res.json())

## create header
headers = {'Content-Type': 'application/json', 'Authorization': f"token {token_res.json()['token']}"}

## get pedigrees
data = '{"queue_id": 61}'

post_res = requests.post(url=f'{sys.argv[1]}/api/tasks/new_large_tier/', headers=headers, data=data)
print(post_res.request.body)
print(post_res.text)
#print(f"{sys.argv[1]}/api/services/")
#service_get = requests.get(url=f"https://cloud-lines.com/api/services/")
#print(service_get.json()['results'])
