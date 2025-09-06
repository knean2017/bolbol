from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from django.utils.html import format_html
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import User


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = "__all__"
        widgets = {
            'store_description': forms.Textarea(attrs={'rows': 3, 'cols': 40}),
            'store_address': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        store_name = cleaned_data.get('store_name')
        
        # Enhanced validation for store users
        if user_type == 'store':
            if not store_name:
                raise forms.ValidationError("Store users must have a store name.")
            if not cleaned_data.get('store_description'):
                self.add_error('store_description', 'Store description is recommended for store users.')
        
        return cleaned_data


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserAdminForm
    model = User

    # Enhanced list view with better performance
    list_display = (
        "email", "get_name_with_verification", "user_type", "phone_verified", 
        "is_staff", "is_active", "get_products_count", "get_interactions_count", 
        "get_last_login_formatted", "date_joined"
    )
    list_filter = (
        "user_type", "phone_verified", "is_staff", 
        "is_active", "is_superuser", "date_joined", "last_login"
    )

    search_fields = ("email", "first_name", "phone", "store_name")
    ordering = ("-date_joined",)
    list_per_page = 25
    list_max_show_all = 100
    
    # Optimize database queries
    list_select_related = ()
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Prefetch related data to reduce database queries
        queryset = queryset.annotate(
            products_count=Count('product', distinct=True),
            bookmarks_count=Count('bookmark', distinct=True, filter=Q(bookmark__isnull=False))
        )
        return queryset

    # Enhanced fieldsets with better organization
    fieldsets = (
        ("🔐 Authentication & Contact", {
            "fields": ("email", "phone", "password", "phone_verified"),
            "description": "Core authentication and contact information"
        }),
        ("👤 Personal Information", {
            "fields": ("first_name", "last_name", "user_type"),
            "description": "Basic user profile information"
        }),
        ("🏪 Store Information", {
            "fields": ("store_name", "store_description", "store_logo", 
                      "store_address", "store_working_hours"),
            "classes": ("collapse",),
            "description": "Only applicable for Store/Business users. Fill these fields for store accounts."
        }),
        ("🔑 Permissions & Access", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            "classes": ("collapse",),
            "description": "User permissions and access control"
        }),
        ("📅 Activity & Timestamps", {
            "fields": ("last_login", "date_joined"),
            "classes": ("collapse",),
            "description": "User activity and registration information"
        }),
    )

    add_fieldsets = (
        ("🆕 Create New User", {
            "classes": ("wide",),
            "fields": ("email", "phone", "first_name", "user_type", 
                      "password1", "password2", "is_staff", "is_active"),
            "description": "Create a new user account. Store-specific fields can be added after creation."
        }),
    )

    readonly_fields = ("date_joined", "last_login", "get_user_stats")

    # Enhanced display methods with better performance
    def get_name_with_verification(self, obj):
        verification_icon = "✅" if obj.phone_verified else "❌"
        if obj.user_type == 'store' and obj.store_name:
            return format_html(
                '<span style="color: #0066cc;">🏪 {}</span> {}', 
                obj.store_name, verification_icon
            )
        name = obj.first_name or obj.email.split('@')[0]
        return format_html(
            '<span style="color: #28a745;">👤 {}</span> {}', 
            name, verification_icon
        )
    get_name_with_verification.short_description = "Name/Store (Verification)"
    get_name_with_verification.admin_order_field = "first_name"

    def get_products_count(self, obj):
        count = getattr(obj, 'products_count', 0)
        if count > 0:
            products_url = reverse('admin:products_product_changelist') + f'?owner__id__exact={obj.id}'
            return format_html(
                '<a href="{}" style="color: #007cba;">🛍️ {}</a>', 
                products_url, count
            )
        return "0"
    get_products_count.short_description = "Products"
    get_products_count.admin_order_field = "products_count"

    def get_interactions_count(self, obj):
        # More efficient: get bookmarks count from annotation
        bookmarks_count = getattr(obj, 'bookmarks_count', 0)
        
        # Get comments count (could be optimized further with annotations if needed)
        from interactions.models import Comment
        comments_count = Comment.objects.filter(user=obj).count()
        
        total = bookmarks_count + comments_count
        if total > 0:
            return format_html(
                '<span style="color: #28a745;">❤️ {} 💬 {}</span>', 
                bookmarks_count, comments_count
            )
        return "0"
    get_interactions_count.short_description = "Interactions"

    def get_last_login_formatted(self, obj):
        if obj.last_login:
            return format_html(
                '<span style="color: #28a745;">{}</span>',
                obj.last_login.strftime('%Y-%m-%d %H:%M')
            )
        return format_html('<span style="color: #dc3545;">Never</span>')
    get_last_login_formatted.short_description = "Last Login"
    get_last_login_formatted.admin_order_field = "last_login"

    def get_user_stats(self, obj):
        if obj.pk:
            stats = []
            stats.append(f"Products: {getattr(obj, 'products_count', 0)}")
            stats.append(f"Bookmarks: {getattr(obj, 'bookmarks_count', 0)}")
            
            from interactions.models import Comment
            comments_count = Comment.objects.filter(user=obj).count()
            stats.append(f"Comments: {comments_count}")
            
            return format_html('<br>'.join(stats))
        return "Save user to see statistics"
    get_user_stats.short_description = "User Statistics"

    # Enhanced custom actions
    actions = ['verify_phone', 'unverify_phone', 'convert_to_store', 'activate_users', 'deactivate_users']

    def verify_phone(self, request, queryset):
        updated = queryset.update(phone_verified=True)
        self.message_user(request, f'{updated} users had their phone verified successfully.')
    verify_phone.short_description = "✅ Verify phone for selected users"

    def unverify_phone(self, request, queryset):
        updated = queryset.update(phone_verified=False)
        self.message_user(request, f'{updated} users had their phone unverified.')
    unverify_phone.short_description = "❌ Unverify phone for selected users"

    def convert_to_store(self, request, queryset):
        individual_users = queryset.filter(user_type='individual')
        updated = individual_users.update(user_type='store')
        self.message_user(request, f'{updated} users converted to store type. Please ensure they have store information filled.')
    convert_to_store.short_description = "🏪 Convert to store users"
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated successfully.')
    activate_users.short_description = "🟢 Activate selected users"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated successfully.')
    deactivate_users.short_description = "🔴 Deactivate selected users"
