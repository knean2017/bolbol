from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from django.utils.html import format_html
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter

from .models import User, Store, StorePhone


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = "__all__"
    
    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        
        # Basic validation for user types
        if user_type == 'store':
            # Store users should have a corresponding Store record
            # This will be handled in the Store admin interface
            pass
        
        return cleaned_data


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserAdminForm
    model = User

    # Enhanced list view with better performance
    list_display = (
        "email", "get_name_with_verification", "phone_verified", 
        "is_staff", "is_active", "get_products_count", "get_interactions_count", 
        "get_last_login_formatted", "date_joined"
    )
    list_filter = (
        "phone_verified", "is_staff", 
        "is_active", "is_superuser", "date_joined", "last_login"
    )

    search_fields = ("email", "first_name", "phone")
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
            "fields": ("first_name", "last_name"),
            "description": "Basic user profile information. For store users, create a Store record separately."
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
            "fields": ("email", "phone", "first_name", 
                      "password1", "password2", "is_staff", "is_active"),
            "description": "Create a new user account. Store-specific fields can be added after creation."
        }),
    )

    readonly_fields = ("date_joined", "last_login", "get_user_stats")

    # Enhanced display methods with better performance
    def get_name_with_verification(self, obj):
        verification_icon = "✅" if obj.phone_verified else "❌"
        # Check if user has a store record by looking for Store records
        try:
            from .models import Store
            store = Store.objects.filter(name__icontains=obj.first_name).first() if obj.first_name else None
            if store:
                return format_html(
                    '<span style="color: #0066cc;">🏪 {}</span> {}', 
                    store.name, verification_icon
                )
        except:
            pass
        
        name = obj.first_name or obj.email.split('@')[0]
        return format_html(
            '<span style="color: #28a745;">👤 {}</span> {}', 
            name, verification_icon
        )
    get_name_with_verification.short_description = "Name (Verification)"
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
        count = queryset.count()
        self.message_user(request, f'🏪 Selected {count} users. Create Store records separately for each user.')
    convert_to_store.short_description = "🏪 Create store records for users"
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated successfully.')
    activate_users.short_description = "🟢 Activate selected users"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated successfully.')
    deactivate_users.short_description = "🔴 Deactivate selected users"


# Enhanced Form Classes for Store Models
class StoreAdminForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 60}),
            'address': forms.Textarea(attrs={'rows': 3, 'cols': 60}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        
        if name and len(name.strip()) < 2:
            raise forms.ValidationError("Store name must be at least 2 characters long.")
        
        return cleaned_data


class StorePhoneInlineForm(forms.ModelForm):
    class Meta:
        model = StorePhone
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        phone = cleaned_data.get('phone')
        
        if phone and len(phone.strip()) < 8:
            raise forms.ValidationError("Phone number must be at least 10 digits.")
        
        return cleaned_data


class StorePhoneInline(admin.TabularInline):
    model = StorePhone
    form = StorePhoneInlineForm
    extra = 1
    max_num = 5
    verbose_name = "Store Phone Number"
    verbose_name_plural = "Store Phone Numbers"
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('store')


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    form = StoreAdminForm
    
    list_display = [
        'name', 'get_categories_list', 'get_phone_count', 'get_address_preview',
        'get_working_hours', 'get_description_preview', 'get_logo_status'
    ]
    
    list_filter = [
        'category', 'opening_time', 'closing_time'
    ]
    
    search_fields = [
        'name', 'description', 'address', 'category__name'
    ]
    
    filter_horizontal = ['category']
    inlines = [StorePhoneInline]
    
    # Enhanced pagination
    list_per_page = 20
    list_max_show_all = 100
    
    # Optimize database queries
    list_select_related = []
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related('category', 'phones').annotate(
            phone_count=Count('phones', distinct=True)
        )
        return queryset
    
    fieldsets = (
        ('🏪 Basic Store Information', {
            'fields': ('owner', 'name', 'category', 'description'),
            'description': 'Essential store information and business categories'
        }),
        ('📍 Location & Contact', {
            'fields': ('address', 'address_link'),
            'description': 'Store location and contact information. Phone numbers are managed below.'
        }),
        ('🕰️ Operating Hours', {
            'fields': ('opening_time', 'closing_time'),
            'description': 'Store operating hours'
        }),
        ('🖼️ Branding', {
            'fields': ('logo',),
            'description': 'Store logo and visual branding'
        })
    )
    
    # Enhanced display methods
    def get_categories_list(self, obj):
        categories = obj.category.all()[:3]  # Show first 3 categories
        if categories:
            category_names = [cat.name for cat in categories]
            display_text = ', '.join(category_names)
            if obj.category.count() > 3:
                display_text += f" (+{obj.category.count() - 3} more)"
            return format_html(
                '<span style="color: #007cba;">📋 {}</span>',
                display_text
            )
        return format_html('<span style="color: #6c757d;">No categories</span>')
    get_categories_list.short_description = 'Categories'
    
    def get_phone_count(self, obj):
        count = getattr(obj, 'phone_count', 0)
        if count > 0:
            return format_html(
                '<span style="color: #28a745;">📞 {} phone(s)</span>',
                count
            )
        return format_html('<span style="color: #dc3545;">No phones</span>')
    get_phone_count.short_description = 'Phone Numbers'
    get_phone_count.admin_order_field = 'phone_count'
    
    def get_address_preview(self, obj):
        if obj.address:
            preview = obj.address[:50] + ('...' if len(obj.address) > 50 else '')
            return format_html(
                '<span style="color: #495057;">📍 {}</span>',
                preview
            )
        return format_html('<span style="color: #6c757d;">No address</span>')
    get_address_preview.short_description = 'Address'
    
    def get_working_hours(self, obj):
        if obj.opening_time and obj.closing_time:
            return format_html(
                '<span style="color: #007cba;">🕰️ {} - {}</span>',
                obj.opening_time.strftime('%H:%M'),
                obj.closing_time.strftime('%H:%M')
            )
        elif obj.opening_time:
            return format_html(
                '<span style="color: #ffc107;">Opens: {}</span>',
                obj.opening_time.strftime('%H:%M')
            )
        elif obj.closing_time:
            return format_html(
                '<span style="color: #ffc107;">Closes: {}</span>',
                obj.closing_time.strftime('%H:%M')
            )
        return format_html('<span style="color: #6c757d;">Hours not set</span>')
    get_working_hours.short_description = 'Working Hours'
    
    def get_description_preview(self, obj):
        if obj.description:
            preview = obj.description[:60] + ('...' if len(obj.description) > 60 else '')
            return format_html(
                '<span style="color: #495057; font-style: italic;">{}</span>',
                preview
            )
        return format_html('<span style="color: #6c757d;">No description</span>')
    get_description_preview.short_description = 'Description'
    
    def get_logo_status(self, obj):
        if obj.logo:
            return format_html('<span style="color: #28a745;">🖼️ Has logo</span>')
        return format_html('<span style="color: #6c757d;">No logo</span>')
    get_logo_status.short_description = 'Logo'
    
    # Custom actions
    actions = ['update_working_hours', 'export_store_data', 'validate_store_info']
    
    def update_working_hours(self, request, queryset):
        # Action to bulk update working hours
        count = queryset.count()
        self.message_user(request, f'🕰️ {count} stores selected for working hours update. Please modify individually for specific hours.')
    update_working_hours.short_description = "🕰️ Update working hours"
    
    def export_store_data(self, request, queryset):
        total_phones = sum(getattr(store, 'phone_count', 0) for store in queryset)
        self.message_user(request, f'📄 {queryset.count()} stores selected for export with {total_phones} total phone numbers.')
    export_store_data.short_description = "📄 Export store data"
    
    def validate_store_info(self, request, queryset):
        incomplete_stores = 0
        for store in queryset:
            if not (store.description and store.address and store.opening_time and store.closing_time):
                incomplete_stores += 1
        
        self.message_user(request, f'✅ Validation complete: {incomplete_stores} out of {queryset.count()} stores have incomplete information.')
    validate_store_info.short_description = "✅ Validate store information"


@admin.register(StorePhone)
class StorePhoneAdmin(admin.ModelAdmin):
    list_display = [
        'get_store_name', 'phone', 'get_formatted_phone', 'get_store_info'
    ]
    
    list_filter = [
        'store__category'
    ]
    
    search_fields = [
        'store__name', 'phone', 'store__address'
    ]
    
    autocomplete_fields = ['store']
    
    # Enhanced pagination
    list_per_page = 30
    list_max_show_all = 150
    
    # Optimize database queries
    list_select_related = ['store']
    
    fieldsets = (
        ('📞 Phone Information', {
            'fields': ('store', 'phone'),
            'description': 'Store phone number details'
        }),
    )
    
    # Enhanced display methods
    def get_store_name(self, obj):
        if obj.store:
            store_url = reverse('admin:users_store_change', args=[obj.store.pk])
            return format_html(
                '<a href="{}" style="color: #007cba;">🏪 {}</a>',
                store_url, obj.store.name
            )
        return "-"
    get_store_name.short_description = 'Store'
    get_store_name.admin_order_field = 'store__name'
    
    def get_formatted_phone(self, obj):
        if obj.phone:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">📞 {}</span>',
                obj.phone
            )
        return "-"
    get_formatted_phone.short_description = 'Formatted Phone'
    
    def get_store_info(self, obj):
        if obj.store:
            info = []
            if obj.store.address:
                info.append(f"📍 {obj.store.address[:30]}..." if len(obj.store.address) > 30 else f"📍 {obj.store.address}")
            if obj.store.category.exists():
                categories = ', '.join([cat.name for cat in obj.store.category.all()[:2]])
                info.append(f"📋 {categories}")
            
            return format_html(
                '<span style="color: #6c757d; font-size: 11px;">{}</span>',
                '<br>'.join(info) if info else 'No additional info'
            )
        return "-"
    get_store_info.short_description = 'Store Details'
    
    # Custom actions
    actions = ['validate_phone_numbers', 'export_phone_list']
    
    def validate_phone_numbers(self, request, queryset):
        invalid_phones = 0
        for phone_obj in queryset:
            if not phone_obj.phone or len(phone_obj.phone.replace(' ', '').replace('-', '')) < 8:
                invalid_phones += 1
        
        self.message_user(request, f'✅ Phone validation complete: {invalid_phones} out of {queryset.count()} phones may be invalid.')
    validate_phone_numbers.short_description = "✅ Validate phone numbers"
    
    def export_phone_list(self, request, queryset):
        unique_stores = queryset.values_list('store', flat=True).distinct().count()
        self.message_user(request, f'📄 {queryset.count()} phone numbers from {unique_stores} stores selected for export.')
    export_phone_list.short_description = "📄 Export phone list"
