#!/usr/bin/env bash
# Needs to be in postdeploy to ensure the cert & nginx config aren't destroyed
# by autoscaling:
# https://medium.com/edataconsulting/how-to-get-a-ssl-certificate-running-in-aws-elastic-beanstalk-using-certbot-6daa9baa3997
certbot --nginx --non-interactive --agree-tos -m 'andromeda.yelton@gmail.com' --domains 'hamlet.andromedayelton.com'
