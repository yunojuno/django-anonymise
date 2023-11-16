# Django Anonymiser

Django app for managing / tracking Django model anonymisation.

## Status
This is currently used internally only, and has not been published to
PyPI - use with caution.

## Background
We currently have a pattern of each model having its own `anonymise`
method, and a management command that iterates over each model calling
said method on each object. This works, but it's impossible to track -
we don't know which models, and which fields on those models, are
actually being anonymised, and the documentation suffers the same fate
as all documentation is that is not auto-generated.

This library adopts the pattern used by the `django-side-effects`
library of having a "registry" of anonymisers and a management command
that outputs the complete listing of all anonymisers and all fields
anonymised. This output can then be plugged into the
`django-project-checks` framework and stored in the repo as a "snapshot"
that is then checked in the CI pipeline, meaning it is guaranteed to be
up-to-date.

The anonymisation itself doesn't change - it's just shifting the code
around.

## Redaction vs. Anonymisation

This library contains two flavours of anonymisation - Redaction, and
Anonymisation. The two differ in how the data is overwritten:

Type | Implementation | Performance | Data
--- | --- | --- | ---
Redaction | SQL | Fast | Table level
Anonymisation | Python | Slow | Row level

### Redaction

Redaction is implemented as a single SQL `update` statement that wipes
an entire table in one go. It's very fast, but it's limited in the sense
that it cannot produce realistic data. In fact it may well render your
application unusable. It is recommended as the first step in data
anonymisation.

### Anonymisation

Anonymisation is an row-level operation that iterates over a
queryset and updates each object in turn. The main advantage is that
post-anonymisation you will have realistic, usable, data.

## Usage

As an example - this is a hypothetical User model's anonymisation today:

```python
# models.py
class User:

    def anonymise(self) -> None:
        self.first_name = "Fred"
        self.last_name = "Flinstone"
```
Using this library we remove the `anonymise` method and create and register
a new anonymiser that splits out each field:
```python
# anonymisers.py
@register_anonymiser
class UserAnonymiser(ModelAnonymiser):
    model = User

    def anonymise_first_name(self, obj: User) -> None:
        obj.first_name = "Fred"

    def anonymise_last_name(self, obj: User) -> None:
        obj.last_name = "Flintstone"

```
You should import the `anonymisers` module in your `apps.py` in order to
ensure that it is registered:
```python
# apps.py
from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "Users"

    def ready(self) -> None:
        super().ready()
        from . import anonymisers  # noqa F401
```

Once set up, running the `display_model_anonymisation` management command
will output a list of all models in the project, whether they have a
registered anonymiser, and then all model fields in the project and
whether they are anonymised.

The snapshot for this project itself is `tests/model_anonymisation.md`.

The output format of the snapshot can be overridden - it's rendered using
a Django template `templates/display_model_anonymisation.md`.
