#!/bin/sh
python transfer.py --env prod --portal-key ${PORTAL_KEY} --portal-secret-key ${PORTAL_SECRET_KEY} --google-service-account-credentials-base64 ${SA_SECRET}
