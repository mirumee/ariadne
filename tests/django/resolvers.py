from ariadne.contrib.django.resolvers.serializer_mutation_resolver import SerializerMutationResolver

from .models import DummyModel
from .serializers import DummySerializer


class DummyMutationResolver(SerializerMutationResolver):
    serializer_class = DummySerializer
    partial = True
    model_lookup_field = "id"

    def get_queryset(self):
        return DummyModel.objects.all()

    def __call__(self, info, input, *args, **kwargs):
        mutated_object = DummyMutationResolver(info=info, input=input).create_or_update()
        return mutated_object


class DummyDeletionResolver(SerializerMutationResolver):
    serializer_class = DummySerializer
    partial = True
    model_lookup_field = "id"

    def get_queryset(self):
        return DummyModel.objects.all()

    def __call__(self, info, input, *args, **kwargs):
        deleted_object = DummyMutationResolver(info=info, input=input).delete()
        return deleted_object
