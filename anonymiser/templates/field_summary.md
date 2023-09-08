App | Model | Field | Type | Anonymised
--- | ---   | ---   | ---  | ---
{% for field in fields %}{{field.app|ljust:10}} | {{ field.model|ljust:25 }} | {{ field.field|ljust:25 }} | {{ field.type|ljust:15}} | {% if field.is_anonymisable %}X{% endif %}
{% endfor %}
