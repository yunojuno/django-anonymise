# Model Anonymisation Snapshot

## Registered model anonymisers
Model | Anonymiser
--- | ---{% for model,anonymiser in model_anonymisers.items %}
{{ model }} | {{ anonymiser|default:"-" }} {% endfor %}

## Model field anonymisation
App | Model | Field | Type | Anonymised
--- | ---   | ---   | ---  | ---{% for field in model_fields %}
{{ field.app }} | {{ field.model }} | {{ field.field_name }} | {{ field.field_type }} | {% if field.is_anonymisable %}X{% else %}-{% endif %}{% endfor %}
