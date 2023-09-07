from unittest import mock

import pytest

from anonymiser.decorators import register_anonymiser
from anonymiser.models import FieldSummaryTuple
from anonymiser.registry import _registry, anonymisable_models, register

from .anon import UserAnonymiser
from .models import User


@pytest.fixture
def user_anonymiser() -> UserAnonymiser:
    return UserAnonymiser()


def test_registry() -> None:
    assert anonymisable_models() == []
    register(UserAnonymiser)
    assert anonymisable_models() == [User]


def test_register_anonymiser() -> None:
    _registry.clear()
    assert anonymisable_models() == []
    assert register_anonymiser(UserAnonymiser) == UserAnonymiser
    assert anonymisable_models() == [User]


def test_model_fields_summary(user_anonymiser: UserAnonymiser) -> None:
    assert set(user_anonymiser.get_model_field_summary()) == {
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
    }


@pytest.mark.django_db
class TestAnonymisableUserModel:
    @pytest.fixture
    def user(self) -> User:
        return User.objects.create_user(
            username="testuser", first_name="fred", last_name="flintstone"
        )

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
        assert user.username == "testuser"
        user_anonymiser.anonymise_object(user)
        assert user.first_name == "Anonymous"
        assert user.last_name == "flintstone"
        assert user.username == "testuser"
        user.refresh_from_db()
        assert user.first_name == "fred"
        assert user.last_name == "flintstone"
        assert user.username == "testuser"

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
