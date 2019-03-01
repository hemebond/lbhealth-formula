{%- from tpldir ~ "/map.jinja" import lbhealth with context %}

{%- if 'checks' in lbhealth %}
lbhealth Config:
  file.serialize:
    - name: /etc/lbhealth.json
    - formatter: json
    - dataset: {{ lbhealth.checks | tojson }}
{%- endif %}
