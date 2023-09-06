from unittest import mock

import pytest

from anonymise.models import AnonymisableModel, FieldSummaryTuple

from .models import User


def test_get_subclasses() -> None:
    assert AnonymisableModel.get_subclasses() == [User]


@pytest.mark.django_db
class TestAnonymisableUserModel:
    @pytest.fixture
    def user(self) -> User:
        return User.objects.create_user(
            username="testuser", first_name="fred", last_name="flintstone"
        )

    def test_anonymise_not_implemented(self, user: User) -> None:
        with pytest.raises(NotImplementedError):
            user.anonymise_field(User._meta.get_field("last_name"))

    def test_anonymise_first_name_field(self, user: User) -> None:
        assert user.first_name == "fred"
        user.anonymise_first_name_field()
        assert user.first_name == "Anonymous"

    def test_anonymise(self, user: User) -> None:
        assert user.first_name == "fred"
        assert user.last_name == "flintstone"
        assert user.username == "testuser"
        user.anonymise()
        assert user.first_name == "Anonymous"
        assert user.last_name == "flintstone"
        assert user.username == "testuser"
        user.refresh_from_db()
        assert user.first_name == "fred"
        assert user.last_name == "flintstone"
        assert user.username == "testuser"

    @mock.patch.object(User, "post_anonymise")
    def test_post_anonymise(
        self, mock_post_anonymise: mock.MagicMock, user: User
    ) -> None:
        user.anonymise()
        mock_post_anonymise.assert_called_once_with(first_name=("fred", "Anonymous"))

    def test_get_anonymisable_fields(self) -> None:
        assert User.get_anonymisable_fields() == [User._meta.get_field("first_name")]

    def test_get_anonymisable_fields_summary(self) -> None:
        assert User.get_anonymisable_fields_summary() == [
            FieldSummaryTuple(
                app="tests",
                model="User",
                field="id",
                type="AutoField",
                is_anonymisable=False,
            ),
            FieldSummaryTuple(
                app="tests",
                model="User",
                field="is_active",
                type="BooleanField",
                is_anonymisable=False,
            ),
            FieldSummaryTuple(
                app="tests",
                model="User",
                field="is_staff",
                type="BooleanField",
                is_anonymisable=False,
            ),
            FieldSummaryTuple(
                app="tests",
                model="User",
                field="is_superuser",
                type="BooleanField",
                is_anonymisable=False,
            ),
            FieldSummaryTuple(
                app="tests",
                model="User",
                field="first_name",
                type="CharField",
                is_anonymisable=True,
            ),
            FieldSummaryTuple(
                app="tests",
                model="User",
                field="last_name",
                type="CharField",
                is_anonymisable=False,
            ),
            FieldSummaryTuple(
                app="tests",
                model="User",
                field="password",
                type="CharField",
                is_anonymisable=False,
            ),
            FieldSummaryTuple(
                app="tests",
                model="User",
                field="username",
                type="CharField",
                is_anonymisable=False,
            ),
            FieldSummaryTuple(
                app="tests",
                model="User",
                field="date_joined",
                type="DateTimeField",
                is_anonymisable=False,
            ),
            FieldSummaryTuple(
                app="tests",
                model="User",
                field="last_login",
                type="DateTimeField",
                is_anonymisable=False,
            ),
            FieldSummaryTuple(
                app="tests",
                model="User",
                field="email",
                type="EmailField",
                is_anonymisable=False,
            ),
            FieldSummaryTuple(
                app="tests",
                model="User",
                field="groups",
                type="ManyToManyField",
                is_anonymisable=False,
            ),
            FieldSummaryTuple(
                app="tests",
                model="User",
                field="user_permissions",
                type="ManyToManyField",
                is_anonymisable=False,
            ),
        ]
