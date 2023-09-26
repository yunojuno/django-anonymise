**DEMO PURPOSES ONLY**
## Model field anonymisation
App | Model | Field | Type | Anonymise | Redact
--- | --- | ---   | ---  | --- | ---{% for model,fields in model_fields.items %}{% for field in fields %}
{{ field.app_label }} | {{ field.model_name }} | {{ field.field_name }} | {{ field.field_type }} | {% if field.is_anonymised %}X{% else %}-{% endif %} | {{ field.redaction_strategy|default:"-"|upper }}{% endfor %}{% endfor %}
