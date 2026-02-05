#!/bin/sh
igvf_to_crossref --portal-key ${PORTAL_KEY} --portal-secret-key ${PORTAL_SECRET_KEY} --crossref-login ${CROSSREF_LOGIN} --crossref-password ${CROSSREF_PASSWORD} \
--crossref-server ${CROSSREF_SERVER} --igvf-server ${IGVF_SERVER} --limit 1000
