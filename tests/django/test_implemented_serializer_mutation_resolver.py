import pytest
from rest_framework.exceptions import ValidationError

from tests.django.models import DummyModel
from tests.django.resolvers import DummyDeletionResolver, DummyMutationResolver


@pytest.fixture
def create_via_resolver():
    resolver = DummyMutationResolver(request={}, data={"text": "Hello there"})
    instance = resolver.create_or_update()
    return instance


@pytest.fixture
def update_via_resolver():
    dummy = DummyModel(text="Goodbye")
    dummy.save()
    resolver = DummyMutationResolver(
        request={}, data={"id": dummy.id, "text": "Hello there"}
    )
    instance = resolver.create_or_update()
    return instance


@pytest.fixture
def partial_update_via_resolver():
    dummy = DummyModel(text="Goodbye")
    dummy.save()
    resolver = DummyMutationResolver(
        request={}, data={"id": dummy.id, "extra": "Hello there"}
    )
    resolver.partial = True
    instance = resolver.create_or_update()
    return instance


@pytest.fixture
def delete_via_resolver():
    dummy = DummyModel(text="Goodbye")
    dummy.save()
    resolver = DummyDeletionResolver(request={}, data={"id": dummy.id})
    original_instance = resolver.destroy()
    return original_instance


@pytest.fixture
def create_via_resolver_callable():
    instance = DummyMutationResolver().__call__(info={}, input={"text": "Hello there"})
    return instance


@pytest.fixture
def delete_via_resolver_callable():
    dummy = DummyModel(text="Goodbye")
    dummy.save()
    instance = DummyDeletionResolver().__call__(info={}, input={"id": dummy.id})
    return instance


@pytest.mark.django_db
def test_dummy_mutation_resolver_created(
    create_via_resolver,
):  # pylint: disable=unused-argument
    instance = create_via_resolver
    assert instance


@pytest.mark.django_db
def test_dummy_mutation_resolver_create_set_input_value(
    create_via_resolver,
):  # pylint: disable=unused-argument
    instance = create_via_resolver
    assert instance.text == "Hello there"


@pytest.mark.django_db
def test_dummy_mutation_resolver_create_model_persisted(
    create_via_resolver,
):  # pylint: disable=unused-argument
    assert DummyModel.objects.count() == 1


@pytest.mark.django_db
def test_dummy_mutation_resolver_updated(
    update_via_resolver,
):  # pylint: disable=unused-argument
    instance = update_via_resolver
    assert instance


@pytest.mark.django_db
def test_dummy_mutation_resolver_update_set_input_value(
    update_via_resolver,
):  # pylint: disable=unused-argument
    instance = update_via_resolver
    assert instance.text == "Hello there"


@pytest.mark.django_db
def test_dummy_mutation_resolver_model_updated(
    update_via_resolver,
):  # pylint: disable=unused-argument
    assert DummyModel.objects.count() == 1


@pytest.mark.django_db
def test_dummy_mutation_resolver_fail_to_lookup():  # pylint: disable=unused-argument
    resolver = DummyMutationResolver(request={}, data={"id": -1, "text": "Hello there"})
    with pytest.raises(DummyModel.DoesNotExist):
        resolver.create_or_update()


@pytest.mark.django_db
def test_dummy_mutation_resolver_partial_updated(
    partial_update_via_resolver,
):  # pylint: disable=unused-argument
    instance = partial_update_via_resolver
    assert instance


@pytest.mark.django_db
def test_dummy_mutation_resolver_partial_update_set_input_value(  # pylint: disable=unused-argument
    partial_update_via_resolver,
):
    instance = partial_update_via_resolver
    assert instance.extra == "Hello there"


@pytest.mark.django_db
def test_dummy_mutation_resolver_partial_update_unchanged_for_value_not_provided(  # pylint: disable=unused-argument
    partial_update_via_resolver,
):
    instance = partial_update_via_resolver
    assert instance.text == "Goodbye"


@pytest.mark.django_db
def test_dummy_mutation_resolver_model_partial_updated(
    partial_update_via_resolver,
):  # pylint: disable=unused-argument
    assert DummyModel.objects.count() == 1


@pytest.mark.django_db
def test_partial_update_with_partial_disabled():
    dummy = DummyModel(text="Goodbye")
    dummy.save()
    resolver = DummyMutationResolver(
        request={}, data={"id": dummy.id, "extra": "Hello there"}
    )
    resolver.partial = False
    with pytest.raises(ValidationError):
        resolver.create_or_update()


@pytest.mark.django_db
def test_delete_returns_original_value(
    delete_via_resolver,
):  # pylint: disable=unused-argument
    instance = delete_via_resolver
    assert instance.text == "Goodbye"


@pytest.mark.django_db
def test_delete_actually_deletes(
    delete_via_resolver,
):  # pylint: disable=unused-argument
    assert DummyModel.objects.count() == 0


@pytest.mark.django_db
def test_delete_lookup_failure():
    resolver = DummyDeletionResolver(request={}, data={"id": -1})
    with pytest.raises(DummyModel.DoesNotExist):
        resolver.destroy()


@pytest.mark.django_db
def test_create_callable_creates(
    create_via_resolver_callable,
):  # pylint: disable=unused-argument
    assert DummyModel.objects.count() == 1


@pytest.mark.django_db
def test_create_callable_value(
    create_via_resolver_callable,
):  # pylint: disable=unused-argument
    instance = create_via_resolver_callable
    assert instance.text == "Hello there"


@pytest.mark.django_db
def test_deletion_callable_deletes(
    delete_via_resolver_callable,
):  # pylint: disable=unused-argument
    assert DummyModel.objects.count() == 0


@pytest.mark.django_db
def test_deletion_callable_value(
    delete_via_resolver_callable,
):  # pylint: disable=unused-argument
    instance = delete_via_resolver_callable
    assert instance.text == "Goodbye"
