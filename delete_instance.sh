#!/bin/bash

echo "*****WARNING THIS IS DESTRUCTIVE******"
echo "DELETING $1 IN 10 SECONDS"
sleep 10

echo "Delete API GW"

for rest_api_id in $(aws apigateway get-rest-apis --region eu-west-2 --query 'items[?name==`cloudlines-$1-$1`].id' --output text)
do 
    aws apigateway delete-base-path-mapping --domain-name $1.cloud-lines.com --base-path "(none)"
    aws apigateway delete-rest-api --region eu-west-2 --rest-api-id $rest_api_id
done

echo "Delete RDS"
aws rds delete-db-instance --db-instance-identifier $1 --skip-final-snapshot

echo "Delete lambda"
aws lambda delete-function --function-name cloudlines-$1-$1

echo "Delete dir"
rm -Rf /opt/instances/$1
