#!/bin/bash

## usage
# delete_instance.sh site_name site_name_safe
## e.g.
# delete_instance.sh test-1 test1

echo "*****WARNING THIS IS DESTRUCTIVE******"
echo "DELETING $1 IN 10 SECONDS"
sleep 10

echo "Delete API GW"

for rest_api_id in $(aws apigateway get-rest-apis --region eu-west-2 --query 'items[?name==`cloudlines-$2-$2`].id' --output text)
do 
    aws apigateway delete-base-path-mapping --domain-name $1.cloud-lines.com --base-path "(none)"
    aws apigateway delete-rest-api --region eu-west-2 --rest-api-id $rest_api_id
done

echo "Delete RDS"
aws rds delete-db-instance --db-instance-identifier $2 --skip-final-snapshot

echo "Delete lambda"
aws lambda delete-function --function-name cloudlines-$2-$2

echo "Delete cloudformation"
aws cloudformation delete-stack \
    --stack-name cloudlines-$2-$2

echo "Delete dir"
rm -Rf /opt/instances/$2
