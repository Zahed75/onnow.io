from django.shortcuts import get_object_or_404


class GetSerializerClassMixin(object):

    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return super().get_serializer_class()

class PermissionPolicyMixin:
    def check_permissions(self, request):
        try:
            handler = getattr(self, request.method.lower())
        except AttributeError:
            handler = None

        if (
            handler
            and self.permission_classes_per_method
            and self.permission_classes_per_method.get(handler.__name__)
        ):
            self.permission_classes = self.permission_classes_per_method.get(handler.__name__)

        super().check_permissions(request)


# class MultipleFieldLookupMixin(object):
#
#     def get_object(self):
#         queryset = self.get_queryset()
#         queryset = self.filter_queryset(queryset)
#         filter = {}
#         for field in self.lookup_fields:
#             if self.kwargs[field]:
#                 filter[field] = self.kwargs[field]
#         obj = get_object_or_404(queryset, **filter)  # Lookup the object
#         self.check_object_permissions(self.request, obj)
#         print(obj)
#         return obj