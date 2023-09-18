from unittest import mock

import pytest

from anonymiser.models import FieldSummaryData

from .anon import BadUserAnonymiser, UserAnonymiser
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


def test_bad_anonymiser() -> None:
    with pytest.raises(AttributeError):
        BadUserAnonymiser().anonymise_field(User(), "first_name")
