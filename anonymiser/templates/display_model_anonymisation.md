# Model Anonymisation Snapshot

## Registered model anonymisers
Model | Anonymiser
--- | ---{% for model,anonymiser in model_anonymisers.items %}
{{ model }} | {{ anonymiser|default:"-" }} {% endfor %}

## Model field anonymisation
App | Model | Field | Type | Anonymise | Redacte
--- | ---   | ---   | ---  | --- | ---{% for field in anonymised_models %}
{{ field.app }} | {{ field.model }} | {{ field.field_name }} | {{ field.field_type }} | {% if field.is_anonymised %}X{% else %}-{% endif %} | {{ field.redaction_strategy|default:"-" }}{% endfor %}
