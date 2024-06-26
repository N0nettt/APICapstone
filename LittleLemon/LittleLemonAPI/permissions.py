from rest_framework.permissions import BasePermission

class isManagerOrAdmin(BasePermission):
    
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Manager').exists() or request.user.is_superuser