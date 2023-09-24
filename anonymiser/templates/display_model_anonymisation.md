## Model field anonymisation
App | Model | Field | Type | Anonymise | Redacte
--- | ---   | ---   | ---  | --- | ---{% for model,fields in anonymised_models.items %}{% for field in fields %}
{{ field.app }} | {{ field.model }} | {{ field.field_name }} | {{ field.field_type }} | {{ field.is_anonymised|default:"-" }} | {{ field.redaction_strategy|default:"-"|upper }}{% endfor %}{% endfor %}
