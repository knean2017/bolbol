from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from django.utils.html import format_html

from .models import User, Bookmark


class BookmarkInline(admin.TabularInline):
    model = Bookmark
    extra = 0
    autocomplete_fields = ['product']
    readonly_fields = ['get_product_price']
    
    def get_product_price(self, obj):
        if obj.product:
            return f"{obj.product.price} ₼"
        return "-"
    get_product_price.short_description = "Product Price"


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = "__all__"
    
    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        store_name = cleaned_data.get('store_name')
        
        # Validation: Store users must have store_name
        if user_type == 'store' and not store_name:
            raise forms.ValidationError("Store users must have a store name.")
        
        return cleaned_data


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserAdminForm
    model = User
    inlines = [BookmarkInline]

    # Enhanced list view with more relevant fields
    list_display = (
        "email", "get_name", "user_type", "phone_verified", 
        "is_staff", "is_active", "get_products_count", "get_bookmarks_count", "date_joined"
    )
    list_filter = (
        "user_type", "phone_verified", "is_staff", 
        "is_active", "is_superuser", "date_joined"
    )

    search_fields = ("email", "first_name", "phone", "store_name")
    ordering = ("-date_joined",)

    # Custom fieldsets based on user type
    fieldsets = (
        ("🔐 Authentication", {
            "fields": ("email", "phone", "password", "phone_verified")
        }),
        ("👤 Personal Information", {
            "fields": ("first_name", "user_type")
        }),
        ("🏪 Store Information", {
            "fields": ("store_name", "store_description", "store_logo", 
                      "store_address", "store_working_hours"),
            "classes": ("collapse",),
            "description": "Only applicable for Store users"
        }),
        ("🔑 Permissions", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            "classes": ("collapse",)
        }),
        ("📅 Important Dates", {
            "fields": ("last_login", "date_joined"),
            "classes": ("collapse",)
        }),
    )

    add_fieldsets = (
        ("🆕 Create New User", {
            "classes": ("wide",),
            "fields": ("email", "phone", "first_name", "user_type", 
                      "password1", "password2", "is_staff", "is_active"),
        }),
    )

    readonly_fields = ("date_joined", "last_login")

    # Custom display methods
    def get_name(self, obj):
        if obj.user_type == 'store' and obj.store_name:
            return format_html(
                '<span style="color: #0066cc;">🏪 {}</span>', 
                obj.store_name
            )
        return obj.first_name or obj.email.split('@')[0]
    get_name.short_description = "Name/Store"
    get_name.admin_order_field = "first_name"

    def get_products_count(self, obj):
        count = obj.product_set.count()
        if count > 0:
            return format_html(
                '<span style="color: #007cba;">🛍️ {}</span>', 
                count
            )
        return "0"
    get_products_count.short_description = "Products"

    def get_bookmarks_count(self, obj):
        count = obj.bookmark_set.count()
        if count > 0:
            return format_html(
                '<span style="color: #28a745;">❤️ {}</span>', 
                count
            )
        return "0"
    get_bookmarks_count.short_description = "Bookmarks"

    # Custom actions
    actions = ['verify_phone', 'unverify_phone', 'convert_to_store']

    def verify_phone(self, request, queryset):
        updated = queryset.update(phone_verified=True)
        self.message_user(request, f'{updated} users had their phone verified.')
    verify_phone.short_description = "✅ Verify phone for selected users"

    def unverify_phone(self, request, queryset):
        updated = queryset.update(phone_verified=False)
        self.message_user(request, f'{updated} users had their phone unverified.')
    unverify_phone.short_description = "❌ Unverify phone for selected users"

    def convert_to_store(self, request, queryset):
        updated = queryset.update(user_type='store')
        self.message_user(request, f'{updated} users converted to store type.')
    convert_to_store.short_description = "🏪 Convert to store users"


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("user", "get_product_name", "get_product_price", "get_user_type")
    search_fields = ("user__email", "product__title", "user__store_name")
    list_filter = ("product__category", "user__user_type")
    autocomplete_fields = ["user", "product"]

    def get_product_name(self, obj):
        if obj.product:
            return obj.product.title
        return "-"
    get_product_name.short_description = "Product"

    def get_product_price(self, obj):
        if obj.product:
            return f"{obj.product.price} ₼"
        return "-"
    get_product_price.short_description = "Price"

    def get_user_type(self, obj):
        if obj.user:
            if obj.user.user_type == 'store':
                return format_html('<span style="color: #0066cc;">🏪 Store</span>')
            return format_html('<span style="color: #28a745;">👤 Individual</span>')
        return "-"
    get_user_type.short_description = "User Type"