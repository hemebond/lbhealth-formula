# -*- coding: utf-8 -*-
# vim: ft=sls

include:
  - lbhealth.install
  - lbhealth.service
  - lbhealth.config

extend:
  lbhealth Service:
    service.running:
      - watch:
        - lbhealth Reload SystemD Modules
