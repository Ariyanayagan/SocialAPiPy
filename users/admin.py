from django.contrib import admin
from .models import CustomUser, FriendRequest

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')

@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = ('id', 'from_user', 'to_user', 'is_accepted', 'created_at')
    
    # Fields to search
    search_fields = ('from_user__email', 'to_user__email')
    
    # Optional: add filters for better admin experience
    list_filter = ('is_accepted', 'created_at')

    # Optional: add ordering for the list view
    ordering = ('-created_at',)

    # Optional: add pagination
    list_per_page = 20

    # Optional: customize the form for creating/updating
    # form = FriendRequestForm  # If you have a custom form

    def get_queryset(self, request):
        # Optionally customize the queryset
        queryset = super().get_queryset(request)
        return queryset

    def get_search_results(self, request, queryset, search_term):
        # Customize search results if needed
        return super().get_search_results(request, queryset, search_term)
