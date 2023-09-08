## Model Field Anonymisation Summary
{% for model, fields in models.items %}
### {{ model }}
App | Model | Field | Type | Anonymisable
--- | ---   | ---   | ---  | ---{% for field in fields %}
{{ field.app }} | {{ field.model }} | {{ field.field_name }} | {{ field.field_type }} | {% if field.is_anonymisable %}X{% else %}-{% endif %}{% endfor %}
{% endfor %}
