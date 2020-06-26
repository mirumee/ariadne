from unittest import mock

import pytest


from ariadne.contrib.django.resolvers import SerializerMutationResolver


class MockSerializer:
    def __init__(self, *args, **kwargs):
        pass

    def is_valid(self, raise_exception):
        return True

    def save(self):
        return "ZZZ"


class MockInstance:
    def __init__(self, *args, **kwargs):
        self.counter = 0

    def delete(self):
        self.counter += 1


class MockQueryset:
    def __init__(self, *args, **kwargs):
        pass

    def get(self, *args, **kwargs):
        return "AWAKE"


def test_init_without_serializer_class_raises_error():
    with pytest.raises(RuntimeError):
        SerializerMutationResolver()


def test_init_default_with_serializer_class():
    resolver_class = SerializerMutationResolver
    resolver_class.serializer_class = "Fake"
    resolver = resolver_class()
    assert resolver.serializer_class == "Fake"


def test_init_call_clean_input_data_called():
    resolver_class = SerializerMutationResolver
    resolver_class.serializer_class = "Fake"
    with mock.patch(
        "ariadne.contrib.django.resolvers.SerializerMutationResolver.get_clean_input_data"
    ) as mocked_fxn:
        resolver_class()
        assert mocked_fxn.call_count == 1


def test_get_queryset_raises_error():
    resolver_class = SerializerMutationResolver
    resolver_class.serializer_class = "Fake"
    resolver = resolver_class()
    with pytest.raises(RuntimeError):
        resolver.get_queryset()


def test_get_lookup_dictionary_happy_path():
    resolver_class = SerializerMutationResolver
    resolver_class.serializer_class = "Fake"
    resolver = resolver_class(data={"id": "meow", "not_id": "oink"})
    lookup_data = resolver.get_lookup_dictionary()
    assert lookup_data == {"id": "meow"}


def test_get_lookup_dictionary_without_lookup_val():
    resolver_class = SerializerMutationResolver
    resolver_class.serializer_class = "Fake"
    resolver = resolver_class(data={"not_id": "oink"})
    with pytest.raises(KeyError):
        resolver.get_lookup_dictionary()


def test_get_instance_with_lookup_field_in_input_data():
    resolver_class = SerializerMutationResolver
    resolver_class.serializer_class = "Fake"
    resolver = resolver_class(data={"id": "abc"})
    with mock.patch(
        "ariadne.contrib.django.resolvers.SerializerMutationResolver.get_queryset"
    ) as mocked_fxn:
        mocked_fxn.return_value = MockQueryset()
        instance = resolver.get_instance()
        assert instance == "AWAKE"


def test_get_instance_without_lookup_field_in_input_data():
    resolver_class = SerializerMutationResolver
    resolver_class.serializer_class = "Fake"
    resolver = resolver_class(data={"not_id": "oink"})
    instance = resolver.get_instance()
    assert instance is None


def test_get_context_with_request():
    resolver_class = SerializerMutationResolver
    resolver_class.serializer_class = "Fake"
    resolver = resolver_class(request={"not_id": "oink"})
    context = resolver.get_context()
    assert context == {"request": {"not_id": "oink"}}


def test_get_context_with_request_none():
    resolver_class = SerializerMutationResolver
    resolver_class.serializer_class = "Fake"
    resolver = resolver_class()
    context = resolver.get_context()
    assert context == {"request": None}


def test_clean_input_with_conversion_flag_true():
    resolver_class = SerializerMutationResolver
    resolver_class.serializer_class = "Fake"
    resolver_class.convert_input_to_snake_case = True
    resolver = resolver_class()
    data = resolver.get_clean_input_data(input_data={"animalSounds": {"aPig": "oink"}})
    assert data == {"animal_sounds": {"a_pig": "oink"}}


def test_clean_input_with_conversion_flag_false():
    resolver_class = SerializerMutationResolver
    resolver_class.serializer_class = "Fake"
    resolver = resolver_class()
    resolver_class.convert_input_to_snake_case = False
    data = resolver.get_clean_input_data(input_data={"animalSounds": {"aPig": "oink"}})
    assert data == {"animalSounds": {"aPig": "oink"}}


def test_create_or_update_calls_perform_create_or_update():
    resolver_class = SerializerMutationResolver
    resolver_class.serializer_class = MockSerializer
    resolver = resolver_class()
    with mock.patch(
        "ariadne.contrib.django.resolvers.SerializerMutationResolver.perform_create_or_update"
    ) as mocked_fxn:
        resolver.create_or_update()
        assert mocked_fxn.call_count == 1


def test_create_or_update_faux_creates():
    resolver_class = SerializerMutationResolver
    resolver_class.serializer_class = MockSerializer
    resolver = resolver_class()
    instance = resolver.create_or_update()
    assert instance == "ZZZ"


def test_perform_create_or_update():
    resolver_class = SerializerMutationResolver
    resolver_class.serializer_class = MockSerializer
    resolver = resolver_class()
    instance = resolver.perform_create_or_update(serializer=MockSerializer())
    assert instance == "ZZZ"


def test_destroy_calls_perform_destroy():
    resolver_class = SerializerMutationResolver
    resolver_class.serializer_class = MockSerializer
    resolver = resolver_class()
    with mock.patch(
        "ariadne.contrib.django.resolvers.SerializerMutationResolver.perform_destroy"
    ) as mocked_fxn:
        resolver.destroy()
        assert mocked_fxn.call_count == 1


def test_destroy_faux_destroys():
    resolver_class = SerializerMutationResolver
    resolver_class.serializer_class = MockSerializer
    resolver = resolver_class()
    with mock.patch(
        "ariadne.contrib.django.resolvers.SerializerMutationResolver.get_instance"
    ) as mocked_fxn:
        mocked_fxn.return_value = MockInstance()
        deleted_instance = resolver.destroy()
        assert deleted_instance.counter >= 1
