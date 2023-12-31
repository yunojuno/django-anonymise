from unittest import mock

import freezegun
import pytest
from django.db import models

from anonymiser.db.functions import GenerateUuid4
from anonymiser.registry import ModelFieldSummary

from .anonymisers import BadUserAnonymiser, UserAnonymiser, UserRedacter
from .models import User


@pytest.mark.parametrize(
    "field_name,strategy",
    [
        ("first_name", UserAnonymiser.FieldRedactionStrategy.CUSTOM),
        # non-custom redactions of char fields
        ("last_name", UserAnonymiser.FieldRedactionStrategy.AUTO),
        ("biography", UserAnonymiser.FieldRedactionStrategy.AUTO),
        ("location", UserAnonymiser.FieldRedactionStrategy.AUTO),
        # date / UUID not redacted automatically
        ("date_of_birth", UserAnonymiser.FieldRedactionStrategy.AUTO),
        ("uuid", UserAnonymiser.FieldRedactionStrategy.AUTO),
    ],
)
def test_model_fields_redaction_strategy(
    field_name: str, strategy: str, user_anonymiser: UserAnonymiser
) -> None:
    field = User._meta.get_field(field_name)
    mfs = ModelFieldSummary(field)
    assert mfs.redaction_strategy == strategy


@pytest.mark.django_db
class TestAnonymisableUserModel:
    def test_anonymise_not_implemented(
        self, user: User, user_anonymiser: UserAnonymiser
    ) -> None:
        with pytest.raises(NotImplementedError):
            user_anonymiser.anonymise_field(user, User._meta.get_field("last_name"))

    def test_anonymise_first_name_field(
        self, user: User, user_anonymiser: UserAnonymiser
    ) -> None:
        assert user.first_name == "fred"
        user_anonymiser.anonymise_field(user, User._meta.get_field("first_name"))
        assert user.first_name == "Anonymous"

    def test_anonymise(self, user: User, user_anonymiser: UserAnonymiser) -> None:
        assert user.first_name == "fred"
        assert user.last_name == "flintstone"
        assert user.username == "testuser1"
        user_anonymiser.anonymise_object(user)
        assert user.first_name == "Anonymous"
        assert user.last_name == "flintstone"
        assert user.username == "testuser1"
        user.refresh_from_db()
        assert user.first_name == "fred"
        assert user.last_name == "flintstone"
        assert user.username == "testuser1"

    @mock.patch.object(UserAnonymiser, "post_anonymise_object")
    def test_post_anonymise_object(
        self,
        mock_post_anonymise: mock.MagicMock,
        user: User,
        user_anonymiser: UserAnonymiser,
    ) -> None:
        user_anonymiser.anonymise_object(user)
        mock_post_anonymise.assert_called_once_with(
            user, first_name=("fred", "Anonymous")
        )

    def test_get_anonymisable_fields(self, user_anonymiser: UserAnonymiser) -> None:
        assert user_anonymiser.get_anonymisable_fields() == [
            User._meta.get_field("first_name")
        ]


def test_bad_anonymiser() -> None:
    with pytest.raises(AttributeError):
        BadUserAnonymiser().anonymise_field(User(), "first_name")


@pytest.mark.django_db
class TestRedaction:
    def test_redact_queryset_none(
        self, user: User, user_redacter: UserRedacter
    ) -> None:
        assert user_redacter.redact_queryset(User.objects.none()) == 0

    def test_redact_queryset_one(self, user: User, user_redacter: UserRedacter) -> None:
        assert user_redacter.redact_queryset(User.objects.all()) == 1
        user.refresh_from_db()
        assert user.first_name == "FIRST_NAME"
        assert user.last_name == "LAST_NAME"
        assert user.email == f"user_{user.id}@example.com"
        assert user.extra_info == {"foo": "bar"}

    def test_redact_queryset_two(
        self,
        user: User,
        user2: User,
        user_redacter: UserRedacter,
    ) -> None:
        assert user_redacter.redact_queryset(User.objects.all()) == 2
        user.refresh_from_db()
        user2.refresh_from_db()
        # confirm that we haven't reused the same uuid for all objects
        assert user.uuid != user2.uuid

    def test_redact_queryset__field_overrides(
        self,
        user: User,
        user_redacter: UserRedacter,
    ) -> None:
        user_redacter.redact_queryset(User.objects.all(), location="Area 51")
        user.refresh_from_db()
        assert user.location == "Area 51"

    def test_redact_queryset__field_overrides__postgres(
        self,
        user: User,
        user_redacter: UserRedacter,
    ) -> None:
        uuid = user.uuid
        user_redacter.redact_queryset(User.objects.all(), uuid=GenerateUuid4())
        user.refresh_from_db()
        assert user.uuid != uuid

    @freezegun.freeze_time("2021-01-01")
    @mock.patch.object(UserRedacter, "get_model_fields")
    def test_auto_redact(
        self, mock_get_fields: mock.Mock, user_redacter: UserRedacter
    ) -> None:
        mock_get_fields.return_value = [
            # redact to 255 chars
            models.CharField(name="char_field", max_length=255),
            # redact to 400 chars
            models.TextField(name="text_field"),
            # redact to 400 chars
            models.DateTimeField(name="date_field"),
            # don't redact (choices)
            models.CharField(name="choices", max_length=255, choices=[("a", "A")]),
            # don't redact (unique)
            models.CharField(name="unique", max_length=255, unique=True),
            # don't redact (primary key)
            models.CharField(name="primary_key", max_length=255, primary_key=True),
            # don't redact (IntegerField, DateField, etc)
            models.IntegerField(name="integer_field"),
            models.DateField(name="date_field"),
        ]
        assert user_redacter.get_auto_redaction_values() == {
            "char_field": 255 * "X",
            "text_field": 400 * "X",
            "date_field": freezegun.api.FakeDate(2021, 1, 1),
        }


def test_model_fields_data() -> None:
    mfs = ModelFieldSummary(User._meta.get_field("first_name"))
    assert mfs.app_label == "tests"
    assert mfs.model == User
    assert mfs.label == "tests.User"
    assert mfs.model_name == "User"
    assert mfs.field_name == "first_name"
    assert mfs.field_type == "CharField"
    assert isinstance(mfs.anonymiser, UserAnonymiser)
    assert mfs.is_anonymised is True
    assert mfs.redaction_strategy == UserAnonymiser.FieldRedactionStrategy.CUSTOM
