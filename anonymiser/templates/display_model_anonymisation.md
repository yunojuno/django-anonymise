**DEMO PURPOSES ONLY**
## Model field anonymisation
App | Model | Field | Type | Anonymise | Redact
--- | --- | ---   | ---  | --- | ---{% for model,fields in model_fields.items %}{% for field in fields %}
{{ field.app_name }} | {{ field.model_name }} | {{ field.field_name }} | {{ field.field_type }} | {{ field.is_anonymised|default:"-" }} | {{ field.redaction_strategy|default:"-"|upper }}{% endfor %}{% endfor %}
