import copy
from typing import Any

from ariadne import convert_camel_case_to_snake


class SerializerMutationResolver:
    partial = False
    lookup_field = "id"
    serializer_class = None
    convert_input_to_snake_case = False

    def __init__(
        self, request: Any = None, data: dict = None, *args, **kwargs,
    ) -> None:
        self.request = request

        if data is None:
            data = {}
        self.input_data = self.get_clean_input_data(data)

        if not self.serializer_class:
            raise RuntimeError(
                "You must define serializer_class as a ModelSerializer class"
            )

    def get_queryset(self) -> Any:
        raise RuntimeError(f"get_queryset must be defined in {self.__class__}")

    def get_lookup_dictionary(self) -> dict:
        return {self.lookup_field: self.input_data[self.lookup_field]}

    def get_instance(self) -> Any:
        if self.input_data.get(self.lookup_field, None):
            queryset = self.get_queryset()
            lookup_dict = self.get_lookup_dictionary()
            instance = queryset.get(**lookup_dict)
        else:
            instance = None

        return instance

    def get_context(self) -> dict:
        context = {"request": self.request}
        return context

    def get_clean_input_data(self, input_data: dict) -> dict:
        def convert_to_snake_case(value):
            if isinstance(value, dict):
                return {
                    convert_camel_case_to_snake(key): convert_to_snake_case(value)
                    for key, value in value.items()
                }
            else:
                return value

        if not self.convert_input_to_snake_case:
            return input_data
        return convert_to_snake_case(input_data)

    def create_or_update(self) -> Any:
        instance = self.get_instance()
        context = self.get_context()

        serializer = self.serializer_class(
            instance, data=self.input_data, context=context, partial=self.partial
        )
        serializer.is_valid(raise_exception=True)
        mutated_instance = self.perform_create_or_update(serializer)

        return mutated_instance

    def perform_create_or_update(self, serializer) -> Any:
        return serializer.save()

    def destroy(self) -> Any:
        instance = self.get_instance()
        original_instance = copy.deepcopy(instance)
        self.perform_destroy(instance)
        return original_instance

    def perform_destroy(self, instance):
        if instance:
            instance.delete()
