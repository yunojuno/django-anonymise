# Model Anonymisation Snapshot

## Registered model anonymisers
Model | Anonymiser
--- | ---
admin.LogEntry | -
auth.Group | -
auth.Permission | -
contenttypes.ContentType | -
sessions.Session | -
tests.User | UserAnonymiser

## Model field anonymisation
App | Model | Field | Type | Anonymised
--- | ---   | ---   | ---  | ---
admin | LogEntry | id | AutoField | -
admin | LogEntry | object_repr | CharField | -
admin | LogEntry | action_time | DateTimeField | -
admin | LogEntry | content_type | ForeignKey | -
admin | LogEntry | user | ForeignKey | -
admin | LogEntry | action_flag | PositiveSmallIntegerField | -
admin | LogEntry | change_message | TextField | -
admin | LogEntry | object_id | TextField | -
auth | Group | id | AutoField | -
auth | Group | name | CharField | -
auth | Group | permissions | ManyToManyField | -
auth | Permission | id | AutoField | -
auth | Permission | codename | CharField | -
auth | Permission | name | CharField | -
auth | Permission | content_type | ForeignKey | -
contenttypes | ContentType | id | AutoField | -
contenttypes | ContentType | app_label | CharField | -
contenttypes | ContentType | model | CharField | -
sessions | Session | session_key | CharField | -
sessions | Session | expire_date | DateTimeField | -
sessions | Session | session_data | TextField | -
tests | User | id | AutoField | -
tests | User | is_active | BooleanField | -
tests | User | is_staff | BooleanField | -
tests | User | is_superuser | BooleanField | -
tests | User | first_name | CharField | X
tests | User | last_name | CharField | -
tests | User | password | CharField | -
tests | User | username | CharField | -
tests | User | date_joined | DateTimeField | -
tests | User | last_login | DateTimeField | -
tests | User | email | EmailField | -
tests | User | groups | ManyToManyField | -
tests | User | user_permissions | ManyToManyField | -
```
