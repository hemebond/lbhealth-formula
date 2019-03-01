{%- from tpldir ~ "/map.jinja" import lbhealth with context %}

lbhealth Script:
  file.managed:
    - name: {{ lbhealth.working_dir }}/lbhealth.py
    - source: salt://lbhealth/files/lbhealth.py
    - mode: 0755

lbhealth Socket File:
  file.managed:
    - name: /etc/systemd/system/{{ lbhealth.service.name }}.socket
    - source: salt://lbhealth/files/socket.tmpl
    - template: jinja
    - mode: 0644
    - defaults:
        lbhealth: {{ lbhealth | json }}

lbhealth Service File:
  file.managed:
    - name: /etc/systemd/system/{{ lbhealth.service.name }}@.service
    - source: salt://lbhealth/files/service.tmpl
    - template: jinja
    - mode: 0644
    - defaults:
        lbhealth: {{ lbhealth | json }}
lbhealth Service File (old):
  file.absent:
    - name: /etc/systemd/system/{{ lbhealth.service.name }}.service

lbhealth Reload SystemD Modules:
  module.run:
    - name: service.systemctl_reload
    - onchanges:
      - file: lbhealth Socket File
      - file: lbhealth Service File
