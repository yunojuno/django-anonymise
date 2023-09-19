from unittest import mock

import pytest
from django.db import models

from anonymiser.db.functions import GenerateUuid4
from anonymiser.models import FieldSummaryData

from .anonymisers import BadUserAnonymiser, UserAnonymiser, UserRedacter
from .models import User


def test_model_fields_summary(user_anonymiser: UserAnonymiser) -> None:
    assert user_anonymiser.get_model_field_summary() == [
        FieldSummaryData(User._meta.get_field("id"), False),
        FieldSummaryData(User._meta.get_field("password"), False),
        FieldSummaryData(User._meta.get_field("last_login"), False),
        FieldSummaryData(User._meta.get_field("is_superuser"), False),
        FieldSummaryData(User._meta.get_field("username"), False),
        FieldSummaryData(User._meta.get_field("first_name"), True),
        FieldSummaryData(User._meta.get_field("last_name"), False),
        FieldSummaryData(User._meta.get_field("email"), False),
        FieldSummaryData(User._meta.get_field("is_staff"), False),
        FieldSummaryData(User._meta.get_field("is_active"), False),
        FieldSummaryData(User._meta.get_field("date_joined"), False),
        FieldSummaryData(User._meta.get_field("uuid"), False),
        FieldSummaryData(User._meta.get_field("location"), False),
        FieldSummaryData(User._meta.get_field("biography"), False),
        FieldSummaryData(User._meta.get_field("date_of_birth"), False),
        FieldSummaryData(User._meta.get_field("groups"), False),
        FieldSummaryData(User._meta.get_field("user_permissions"), False),
    ]


def test_model_fields_data(user_anonymiser: UserAnonymiser) -> None:
    fsd = FieldSummaryData(User._meta.get_field("first_name"), True)
    assert fsd.app == "tests"
    assert fsd.model == "User"
    assert fsd.field_name == "first_name"
    assert fsd.field_type == "CharField"
    assert fsd.is_anonymisable is True


@pytest.mark.django_db
class TestAnonymisableUserModel:
    def test_anonymise_not_implemented(
        self, user: User, user_anonymiser: UserAnonymiser
    ) -> None:
        with pytest.raises(NotImplementedError):
            user_anonymiser.anonymise_field(user, "last_name")

    def test_anonymise_first_name_field(
        self, user: User, user_anonymiser: UserAnonymiser
    ) -> None:
        assert user.first_name == "fred"
        user_anonymiser.anonymise_field(user, "first_name")
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

    def test_anonymise_queryset(
        self, user: User, user_anonymiser: UserAnonymiser
    ) -> None:
        assert user_anonymiser.anonymise_queryset(User.objects.none()) == 0
        assert user_anonymiser.anonymise_queryset(User.objects.all()) == 1

    @mock.patch.object(UserAnonymiser, "get_model_fields")
    def test_auto_redact(
        self, mock_get_fields: mock.Mock, user_anonymiser: UserAnonymiser
    ) -> None:
        mock_get_fields.return_value = [
            # redact to 255 chars
            models.CharField(name="char_field", max_length=255),
            # redact to 400 chars
            models.TextField(name="text_field"),
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
        assert user_anonymiser.auto_field_redactions() == {
            "char_field": 255 * "X",
            "text_field": 400 * "X",
        }


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

    @pytest.mark.parametrize(
        "auto_redact,location,biography",
        [
            (True, 255 * "X", 400 * "X"),
            (False, "London", "I am a test user"),
        ],
    )
    def test_redact_queryset__auto_redact(
        self,
        user: User,
        user_redacter: UserRedacter,
        auto_redact: bool,
        location: str,
        biography: str,
    ) -> None:
        user_redacter.redact_queryset(User.objects.all(), auto_redact=auto_redact)
        user.refresh_from_db()
        # auto-redacted fields
        assert user.location == location
        assert user.biography == biography

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
