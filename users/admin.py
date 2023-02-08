from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import OutletManager, Owner, Manager, Otp, TemporaryEmail

User = get_user_model()


class UserAdminConfig(UserAdmin):
    model = User
    search_fields = ('email', 'name')
    list_filter = ('email', 'user_type', 'is_active', 'is_staff')
    ordering = ('-name',)
    list_display = ('__str__', 'email', 'user_type', 'is_active', 'is_staff', 'verified','phone_number')
    fieldsets = (
        (None, {'fields': ('email', 'username', 'user_type', 'password', 'name', "phone_number")}),
        ('Permissions',
         {
             'fields': (
                 'is_active',
                 'is_staff',
                 'is_superuser',
                 'verified',
                 'groups',
                 'user_permissions'
             )
         }),
    )

    # fieldsets to add a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'name', 'phone_number', 'user_type', 'password1', 'password2', 'is_active',
                'is_staff', 'verified',
                'groups', 'user_permissions')}
         ),
    )


admin.site.register(User, UserAdminConfig)
admin.site.register(Owner)
admin.site.register(Otp)
admin.site.register(Manager)
admin.site.register(OutletManager)
admin.site.register(TemporaryEmail)