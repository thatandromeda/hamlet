#!/usr/bin/env bash
# Add autorenew script to crontab, but only if it isn't already there.
if !(grep -F 'certbot renew' /etc/crontab) ; then
  echo "0 0,12 * * * root /opt/certbot/bin/python -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew -q" | sudo tee -a /etc/crontab > /dev/null
fi
