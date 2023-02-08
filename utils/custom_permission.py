from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            if request.user.user_type == "ACO" or request.user.user_type == "MGR" or request.user.user_type == "STF":

                return True
            else:
                return False
        except:
            return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.owner.user == request.user


class IsBrandManager(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            if request.user.user_type == "MGR":
                return True
            else:
                return False
        except:
            return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        else:
            manager = obj.manager.all().filter(user=request.user).exists()
            return manager


class IsOutletManager(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            if request.user.user_type == "STF":
                return True
            else:
                return False
        except:
            return False


class IsCustomer(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            if request.user.user_type == "CUS":
                return True
            else:
                return False
        except:
            return False


class EditMenu(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        elif request.user.user_type == "ACO":
            return obj.brand.owner.user == request.user

        else:
            manager = obj.brand.manager.all().filter(user=request.user).exists()
            return manager


class EditItem(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        elif request.user.user_type == "ACO":
            return obj.menu.brand.owner.user == request.user

        else:
            manager = obj.menu.brand.manager.all().filter(user=request.user).exists()
            return manager


class InventoryHandle(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # if request.method in permissions.SAFE_METHODS:
        #     return True
        try:

            if request.user.user_type == "ACO":
                return obj.outlet.brand.owner.user == request.user

            elif request.user.user_type == "MGR":
                manager = obj.outlet.brand.manager.all().filter(user=request.user).exists()
                return manager

            else:
                manager = obj.outlet.outlet_manager.all().filter(user=request.user).exists()
                return manager
        except:
            return False


class LiveOrderHandle(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.user_type == "CUS":
            return False

        return True

    def has_object_permission(self, request, view, obj):
        try:
            if request.user.user_type == "ACO":
                return obj.outlet.brand.owner.user == request.user

            elif request.user.user_type == "MGR":
                manager = obj.outlet.brand.manager.all().filter(user=request.user).exists()
                return manager


            elif request.user.user_type == "STF":
                outlet_manager = obj.outlet.outlet_manager.all().filter(user=request.user).exists()
                return outlet_manager

            else:
                return False
        except:
            return False
