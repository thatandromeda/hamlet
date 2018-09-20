#!/usr/bin/env bash
set -e
# Loadvars
. /opt/python/current/env

# Check if there is certificate on S3 that we can use

ACCOUNT_ID=214921548711
REGION=us-east-2

echo $ACCOUNT_ID
echo $REGION

URL="s3://elasticbeanstalk-$REGION-$ACCOUNT_ID/ssl/$LE_SSL_DOMAIN/ssl.conf"

echo 'copying certificate'

# Copy cert to S3 regardless of outcome

aws s3 cp /etc/httpd/conf.d/ssl.conf s3://elasticbeanstalk-$REGION-$ACCOUNT_ID/ssl/$LE_SSL_DOMAIN/ssl.conf
aws s3 cp /etc/letsencrypt/live/$LE_SSL_DOMAIN/cert.pem s3://elasticbeanstalk-$REGION-$ACCOUNT_ID/ssl/$LE_SSL_DOMAIN/cert.pem
aws s3 cp /etc/letsencrypt/live/$LE_SSL_DOMAIN/privkey.pem s3://elasticbeanstalk-$REGION-$ACCOUNT_ID/ssl/$LE_SSL_DOMAIN/privkey.pem
aws s3 cp /etc/letsencrypt/live/$LE_SSL_DOMAIN/fullchain.pem s3://elasticbeanstalk-$REGION-$ACCOUNT_ID/ssl/$LE_SSL_DOMAIN/fullchain.pem
