{%- from tpldir ~ "/map.jinja" import lbhealth with context %}

lbhealth Service:
  service.running:
    - name: {{ lbhealth.service.name }}.socket
    - enable: True
