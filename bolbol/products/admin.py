from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.db.models import Count, Q, Avg, Max, Min, Sum
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Category, SubCategory, Attribute, City, Product, ProductDetail


# Custom Filter Classes
class ProductStatusFilter(SimpleListFilter):
    title = 'Product Status'
    parameter_name = 'status_filter'
    
    def lookups(self, request, model_admin):
        return (
            ('pending', '⏳ Pending Review'),
            ('accepted', '✅ Accepted'),
            ('rejected', '❌ Rejected'),
            ('expired', '⏰ Expired'),
        )
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class ProductPriceRangeFilter(SimpleListFilter):
    title = 'Price Range'
    parameter_name = 'price_range'
    
    def lookups(self, request, model_admin):
        return (
            ('0-50', '💰 0-50 ₼'),
            ('50-100', '💰 50-100 ₼'),
            ('100-500', '💰 100-500 ₼'),
            ('500-1000', '💰 500-1000 ₼'),
            ('1000+', '💰 1000+ ₼'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == '0-50':
            return queryset.filter(price__gte=0, price__lt=50)
        elif self.value() == '50-100':
            return queryset.filter(price__gte=50, price__lt=100)
        elif self.value() == '100-500':
            return queryset.filter(price__gte=100, price__lt=500)
        elif self.value() == '500-1000':
            return queryset.filter(price__gte=500, price__lt=1000)
        elif self.value() == '1000+':
            return queryset.filter(price__gte=1000)
        return queryset


class ProductPromotionFilter(SimpleListFilter):
    title = 'Promotion Level'
    parameter_name = 'promotion_filter'
    
    def lookups(self, request, model_admin):
        return (
            ('premium', '⭐ Premium'),
            ('basic', '📦 Basic'),
        )
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(promotion_level=self.value())
        return queryset


class ProductEngagementFilter(SimpleListFilter):
    title = 'Engagement Level'
    parameter_name = 'engagement_level'
    
    def lookups(self, request, model_admin):
        return (
            ('high', '🔥 High Engagement (10+ views)'),
            ('medium', '📈 Medium Engagement (5-10 views)'),
            ('low', '📉 Low Engagement (0-5 views)'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'high':
            return queryset.filter(views_count__gte=10)
        elif self.value() == 'medium':
            return queryset.filter(views_count__gte=5, views_count__lt=10)
        elif self.value() == 'low':
            return queryset.filter(views_count__lt=5)
        return queryset


class ProductAgeFilter(SimpleListFilter):
    title = 'Product Age'
    parameter_name = 'product_age'
    
    def lookups(self, request, model_admin):
        return (
            ('today', '📅 Posted Today'),
            ('week', '📅 This Week'),
            ('month', '📅 This Month'),
            ('old', '📅 Older than Month'),
        )
    
    def queryset(self, request, queryset):
        now = timezone.now()
        
        if self.value() == 'today':
            return queryset.filter(created_at__date=now.date())
        elif self.value() == 'week':
            week_ago = now - timedelta(days=7)
            return queryset.filter(created_at__gte=week_ago)
        elif self.value() == 'month':
            month_ago = now - timedelta(days=30)
            return queryset.filter(created_at__gte=month_ago)
        elif self.value() == 'old':
            month_ago = now - timedelta(days=30)
            return queryset.filter(created_at__lt=month_ago)
        return queryset


# Enhanced Form Classes
class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 60}),
            'title': forms.TextInput(attrs={'size': 60}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Group subcategories by main category in the display (with optgroups)
        if 'category' in self.fields:
            subcategories = SubCategory.objects.select_related('category').order_by('category__name', 'name')
            grouped_choices = {}
            
            for subcategory in subcategories:
                group_label = subcategory.category.name
                if group_label not in grouped_choices:
                    grouped_choices[group_label] = []
                grouped_choices[group_label].append((subcategory.id, subcategory.name))
            
            choices = [('', '---------')]
            for group, items in grouped_choices.items():
                choices.append((group, items))  # optgroup
            
            self.fields['category'].choices = choices
    
    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        promotion_level = cleaned_data.get('promotion_level')
        title = cleaned_data.get('title')
        
        # Enhanced validation
        if price is not None and price <= 0:
            raise forms.ValidationError("Price must be greater than 0.")
        
        if price is not None and price > 100000:
            self.add_error('price', 'Price seems unusually high. Please verify.')
        
        if title and len(title.strip()) < 5:
            raise forms.ValidationError("Product title must be at least 5 characters long.")
        
        # Promotion level validation
        if promotion_level == 'premium' and price is not None and price < 10:
            self.add_error('promotion_level', 'Premium promotion typically requires higher prices.')
        
        return cleaned_data


class ProductDetailInlineForm(forms.ModelForm):
    class Meta:
        model = ProductDetail
        fields = '__all__'
        widgets = {
            'value': forms.TextInput(attrs={'size': 30}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Group attributes by subcategory in the display (with optgroups)
        if 'attribute' in self.fields:
            attributes = Attribute.objects.select_related('subcategory__category').order_by('subcategory__category__name', 'subcategory__name', 'name')
            grouped_choices = {}
            
            for attribute in attributes:
                if attribute.subcategory:
                    group_label = f"{attribute.subcategory.category.name} → {attribute.subcategory.name}"
                else:
                    group_label = "No Category"
                
                if group_label not in grouped_choices:
                    grouped_choices[group_label] = []
                grouped_choices[group_label].append((attribute.id, attribute.name))
            
            choices = [('', '---------')]
            for group, items in grouped_choices.items():
                choices.append((group, items))  # optgroup
            
            self.fields['attribute'].choices = choices
    
    def clean(self):
        cleaned_data = super().clean()
        value = cleaned_data.get('value')
        
        # Basic validation for product detail values
        if value and len(value.strip()) < 1:
            raise forms.ValidationError("Product detail value cannot be empty.")
        
        return cleaned_data


class ProductDetailInline(admin.TabularInline):
    model = ProductDetail
    form = ProductDetailInlineForm
    extra = 1
    classes = ['collapse']
    verbose_name = "Product Specification"
    verbose_name_plural = "Product Specifications"
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('attribute', 'attribute__subcategory')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    
    list_display = [
        'title', 'get_owner_info', 'get_category_name', 'get_subcategory_link', 'city',
        'get_price_formatted', 'get_status_badge', 'get_promotion_badge', 'views_count', 
        'get_engagement_stats', 'get_product_age'
    ]
    
    list_filter = [
        ProductStatusFilter, ProductPriceRangeFilter, ProductPromotionFilter,
        ProductEngagementFilter, ProductAgeFilter,
        'is_barter_available', 'is_credit_available', 'is_delivery_available', 
        'category__category', 'city'
    ]
    
    search_fields = [
        'title', 'description', 'category__name', 'category__category__name',
        'owner__email', 'owner__first_name'
    ]
    
    readonly_fields = ['views_count', 'created_at', 'updated_at', 'get_analytics_summary']
    
    inlines = [ProductDetailInline]
    
    # Enhanced pagination
    list_per_page = 20
    list_max_show_all = 100
    
    # Optimize database queries
    list_select_related = [
        'owner', 'store', 'category', 'category__category', 'city'
    ]
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            comment_count=Count('comment', distinct=True),
            bookmark_count=Count('bookmark', distinct=True),
            detail_count=Count('productdetail', distinct=True)
        )
        return queryset
    
    fieldsets = (
        ('📋 Basic Information', {
            'fields': ('owner', 'store', 'title', 'description', 'category', 'city'),
            'description': 'Choose subcategory from the grouped list (Category → Subcategory). '
                           'Product details will show attributes grouped by subcategory. '
                           'If owner is a store user, you can also link to a specific Store record.'
        }),
        ('💰 Pricing & Features', {
            'fields': ('price', 'promotion_level', 'image', 'is_product_new')
        }),
        ('⚙️ Status & Availability', {
            'fields': ('status', 'is_mediator', 'is_barter_available', 'is_credit_available', 'is_delivery_available'),
        }),
        ('📊 Analytics & Engagement', {
            'fields': ('views_count', 'get_analytics_summary'),
            'classes': ['collapse']
        }),
        ('📅 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        })
    )
    
    actions = [
        'approve_products', 'reject_products', 'set_premium', 
        'set_basic', 'reset_views', 'bulk_enable_delivery', 'feature_products'
    ]
    
    # Enhanced display methods
    def get_owner_info(self, obj):
        if obj.owner:
            owner_url = reverse('admin:users_user_change', args=[obj.owner.pk])
            # Check if user might be a store by looking for Store records
            try:
                from users.models import Store
                store = Store.objects.filter(name__icontains=obj.owner.first_name).first() if obj.owner.first_name else None
                if store:
                    return format_html(
                        '<a href="{}" style="color: #0066cc;">🏪 {}</a><br><small>{}</small>',
                        owner_url, store.name, obj.owner.email
                    )
            except:
                pass
            
            return format_html(
                '<a href="{}" style="color: #28a745;">👤 {}</a><br><small>{}</small>',
                owner_url, obj.owner.first_name or obj.owner.email.split('@')[0], obj.owner.email
            )
        return "-"
    get_owner_info.short_description = 'Owner'
    get_owner_info.admin_order_field = 'owner__email'
    
    def get_subcategory_link(self, obj):
        if obj.category:
            subcategory_url = reverse('admin:products_subcategory_change', args=[obj.category.pk])
            return format_html('<a href="{}" style="color: #6f42c1;">📁 {}</a>', subcategory_url, obj.category.name)
        return "-"
    get_subcategory_link.short_description = 'Subcategory'
    get_subcategory_link.admin_order_field = 'category__name'
    
    def get_price_formatted(self, obj):
        if obj.price:
            if obj.price < 100:
                color = '#28a745'  # Green for low prices
                icon = '💵'
            elif obj.price < 500:
                color = '#007cba'  # Blue for medium prices
                icon = '💶'
            else:
                color = '#dc3545'  # Red for high prices
                icon = '💎'
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} {} ₼</span>',
                color, icon, obj.price
            )
        return "-"
    get_price_formatted.short_description = 'Price'
    get_price_formatted.admin_order_field = 'price'
    
    def get_promotion_badge(self, obj):
        if obj.promotion_level == 'premium':
            return format_html('<span style="color: #ffc107; font-weight: bold;">⭐ Premium</span>')
        return format_html('<span style="color: #6c757d;">📦 Basic</span>')
    get_promotion_badge.short_description = 'Promotion'
    get_promotion_badge.admin_order_field = 'promotion_level'
    
    def get_engagement_stats(self, obj):
        comment_count = getattr(obj, 'comment_count', 0)
        bookmark_count = getattr(obj, 'bookmark_count', 0)
        total_engagement = comment_count + bookmark_count
        
        if total_engagement >= 10:
            return format_html('<span style="color: #dc3545;">🔥 Hot ({} total)</span>', total_engagement)
        elif total_engagement >= 5:
            return format_html('<span style="color: #ffc107;">📈 Popular ({} total)</span>', total_engagement)
        elif total_engagement >= 1:
            return format_html('<span style="color: #28a745;">💬 {} 💗 {}</span>', comment_count, bookmark_count)
        else:
            return format_html('<span style="color: #6c757d;">😴 No engagement</span>')
    get_engagement_stats.short_description = 'Engagement'
    
    def get_product_age(self, obj):
        if obj.created_at:
            age = timezone.now() - obj.created_at
            if age.days == 0:
                return format_html('<span style="color: #28a745;">🆕 Today</span>')
            elif age.days <= 7:
                return format_html('<span style="color: #ffc107;">📅 {} days ago</span>', age.days)
            elif age.days <= 30:
                return format_html('<span style="color: #007cba;">📅 {} days ago</span>', age.days)
            else:
                return format_html('<span style="color: #6c757d;">📅 {} days ago</span>', age.days)
        return "-"
    get_product_age.short_description = 'Age'
    get_product_age.admin_order_field = 'created_at'
    
    def get_analytics_summary(self, obj):
        if obj.pk:
            comment_count = getattr(obj, 'comment_count', 0)
            bookmark_count = getattr(obj, 'bookmark_count', 0)
            detail_count = getattr(obj, 'detail_count', 0)
            age_days = (timezone.now() - obj.created_at).days
            
            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
                '<strong>Product Analytics:</strong><br>'
                '🕰️ Age: {} days<br>'
                '💬 Comments: {}<br>'
                '💗 Bookmarks: {}<br>'
                '📋 Details: {}<br>'
                '👁️ Views: {}<br>'
                '📊 Engagement Score: {}'
                '</div>',
                age_days, comment_count, bookmark_count, detail_count, 
                obj.views_count, comment_count + bookmark_count
            )
        return "No data available"
    get_analytics_summary.short_description = 'Analytics Overview'
    
    def get_status_badge(self, obj):
        status_colors = {
            'pending': '#ffc107',
            'accepted': '#28a745',
            'rejected': '#dc3545',
            'expired': '#6c757d'
        }
        status_icons = {
            'pending': '⏳',
            'accepted': '✅',
            'rejected': '❌',
            'expired': '⏰'
        }
        color = status_colors.get(obj.status, '#6c757d')
        icon = status_icons.get(obj.status, '❓')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_status_display() if obj.status else 'Unknown'
        )
    get_status_badge.short_description = 'Status'
    get_status_badge.admin_order_field = 'status'
    
    def get_category_name(self, obj):
        if obj.category and obj.category.category:
            category_url = reverse('admin:products_category_change', args=[obj.category.category.pk])
            return format_html('<a href="{}" style="color: #007cba;">📂 {}</a>', category_url, obj.category.category.name)
        return '-'
    get_category_name.short_description = 'Main Category'
    get_category_name.admin_order_field = 'category__category__name'
    
    # Enhanced Custom Actions
    def approve_products(self, request, queryset):
        updated = queryset.update(status='accepted')
        self.message_user(request, f'✅ {updated} products were approved successfully.')
    approve_products.short_description = "✅ Approve selected products"

    def reject_products(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'❌ {updated} products were rejected.')
    reject_products.short_description = "❌ Reject selected products"

    def set_premium(self, request, queryset):
        updated = queryset.update(promotion_level='premium')
        self.message_user(request, f'⭐ {updated} products were set to Premium.')
    set_premium.short_description = "⭐ Set to Premium"

    def set_basic(self, request, queryset):
        updated = queryset.update(promotion_level='basic')
        self.message_user(request, f'📦 {updated} products were set to Basic.')
    set_basic.short_description = "📦 Set to Basic"
    
    def reset_views(self, request, queryset):
        updated = queryset.update(views_count=0)
        self.message_user(request, f'🔄 {updated} products had their view counts reset.')
    reset_views.short_description = "🔄 Reset view counts"
    
    def bulk_enable_delivery(self, request, queryset):
        updated = queryset.update(is_delivery_available=True)
        self.message_user(request, f'🚚 {updated} products now offer delivery.')
    bulk_enable_delivery.short_description = "🚚 Enable delivery for selected"
    
    def feature_products(self, request, queryset):
        # Feature products by setting them to premium and accepted
        updated = queryset.update(promotion_level='premium', status='accepted')
        self.message_user(request, f'🌟 {updated} products have been featured (Premium + Accepted).')
    feature_products.short_description = "🌟 Feature selected products"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'get_subcategory_count', 'get_product_count', 'get_avg_price']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_per_page = 20
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            subcategory_count=Count('subcategory', distinct=True),
            product_count=Count('subcategory__product', distinct=True),
            avg_price=Avg('subcategory__product__price')
        )
    
    def get_subcategory_count(self, obj):
        count = getattr(obj, 'subcategory_count', 0)
        if count > 0:
            subcategories_url = reverse('admin:products_subcategory_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}" style="color: #28a745;">📁 {}</a>', subcategories_url, count)
        return "0"
    get_subcategory_count.short_description = 'Subcategories'
    get_subcategory_count.admin_order_field = 'subcategory_count'
    
    def get_product_count(self, obj):
        count = getattr(obj, 'product_count', 0)
        if count > 0:
            return format_html('<span style="color: #007cba;">🛍️ {}</span>', count)
        return "0"
    get_product_count.short_description = 'Total Products'
    get_product_count.admin_order_field = 'product_count'
    
    def get_avg_price(self, obj):
        avg_price = getattr(obj, 'avg_price', None)
        if avg_price:
            return format_html('<span style="color: #ffc107;">💰 {} ₼</span>', round(avg_price, 1))
        return "-"
    get_avg_price.short_description = 'Avg Price'
    get_avg_price.admin_order_field = 'avg_price'


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_category_link', 'description', 'get_product_count', 'get_attribute_count', 'get_avg_price']
    search_fields = ['name', 'category__name', 'description']
    list_filter = ['category']
    autocomplete_fields = ['category']
    list_select_related = ['category']
    list_per_page = 25
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            product_count=Count('product', distinct=True),
            attribute_count=Count('attribute', distinct=True),
            avg_price=Avg('product__price')
        )
    
    def get_category_link(self, obj):
        if obj.category:
            category_url = reverse('admin:products_category_change', args=[obj.category.pk])
            return format_html('<a href="{}" style="color: #0066cc;">📂 {}</a>', category_url, obj.category.name)
        return "-"
    get_category_link.short_description = 'Main Category'
    get_category_link.admin_order_field = 'category__name'
    
    def get_product_count(self, obj):
        count = getattr(obj, 'product_count', 0)
        if count > 0:
            products_url = reverse('admin:products_product_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}" style="color: #007cba;">🛍️ {}</a>', products_url, count)
        return "0"
    get_product_count.short_description = 'Products'
    get_product_count.admin_order_field = 'product_count'
    
    def get_attribute_count(self, obj):
        count = getattr(obj, 'attribute_count', 0)
        if count > 0:
            attributes_url = reverse('admin:products_attribute_changelist') + f'?subcategory__id__exact={obj.id}'
            return format_html('<a href="{}" style="color: #ffc107;">📋 {}</a>', attributes_url, count)
        return "0"
    get_attribute_count.short_description = 'Attributes'
    get_attribute_count.admin_order_field = 'attribute_count'
    
    def get_avg_price(self, obj):
        avg_price = getattr(obj, 'avg_price', None)
        if avg_price:
            return format_html('<span style="color: #28a745;">💰 {} ₼</span>', round(avg_price, 1))
        return "-"
    get_avg_price.short_description = 'Avg Price'
    get_avg_price.admin_order_field = 'avg_price'


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_product_count', 'get_active_products', 'get_avg_price']
    search_fields = ['name']
    ordering = ['name']
    list_per_page = 20
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            product_count=Count('product', distinct=True),
            active_product_count=Count('product', distinct=True, filter=Q(product__status='accepted')),
            avg_price=Avg('product__price')
        )
    
    def get_product_count(self, obj):
        count = getattr(obj, 'product_count', 0)
        if count > 0:
            products_url = reverse('admin:products_product_changelist') + f'?city__id__exact={obj.id}'
            return format_html('<a href="{}" style="color: #007cba;">🛍️ {}</a>', products_url, count)
        return "0"
    get_product_count.short_description = 'Total Products'
    get_product_count.admin_order_field = 'product_count'
    
    def get_active_products(self, obj):
        count = getattr(obj, 'active_product_count', 0)
        if count > 0:
            return format_html('<span style="color: #28a745;">✅ {}</span>', count)
        return "0"
    get_active_products.short_description = 'Active Products'
    get_active_products.admin_order_field = 'active_product_count'
    
    def get_avg_price(self, obj):
        avg_price = getattr(obj, 'avg_price', None)
        if avg_price:
            return format_html('<span style="color: #ffc107;">💰 {} ₼</span>', round(avg_price, 1))
        return "-"
    get_avg_price.short_description = 'Avg Price'
    get_avg_price.admin_order_field = 'avg_price'


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_subcategory_link', 'get_category_name', 'get_usage_count', 'get_popular_values']
    search_fields = ['name', 'subcategory__name', 'subcategory__category__name']
    list_filter = ['subcategory__category', 'subcategory']
    autocomplete_fields = ['subcategory']
    list_select_related = ['subcategory', 'subcategory__category']
    list_per_page = 30
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            usage_count=Count('productdetail', distinct=True)
        )
    
    def get_subcategory_link(self, obj):
        if obj.subcategory:
            subcategory_url = reverse('admin:products_subcategory_change', args=[obj.subcategory.pk])
            return format_html('<a href="{}" style="color: #0066cc;">📁 {}</a>', subcategory_url, obj.subcategory.name)
        return "-"
    get_subcategory_link.short_description = 'Subcategory'
    get_subcategory_link.admin_order_field = 'subcategory__name'
    
    def get_category_name(self, obj):
        if obj.subcategory and obj.subcategory.category:
            category_url = reverse('admin:products_category_change', args=[obj.subcategory.category.pk])
            return format_html('<a href="{}" style="color: #6f42c1;">📂 {}</a>', category_url, obj.subcategory.category.name)
        return '-'
    get_category_name.short_description = 'Main Category'
    get_category_name.admin_order_field = 'subcategory__category__name'
    
    def get_usage_count(self, obj):
        count = getattr(obj, 'usage_count', 0)
        if count > 0:
            details_url = reverse('admin:products_productdetail_changelist') + f'?attribute__id__exact={obj.id}'
            return format_html('<a href="{}" style="color: #28a745;">📊 {}</a>', details_url, count)
        return "0"
    get_usage_count.short_description = 'Used in Products'
    get_usage_count.admin_order_field = 'usage_count'
    
    def get_popular_values(self, obj):
        # Get most common values for this attribute
        values = obj.productdetail_set.values_list('value', flat=True)[:3]
        if values:
            return format_html('<span style="color: #17a2b8; font-size: 11px;">{}</span>', ', '.join(values))
        return "-"
    get_popular_values.short_description = 'Popular Values'


@admin.register(ProductDetail)
class ProductDetailAdmin(admin.ModelAdmin):
    list_display = [
        'get_product_link', 'get_attribute_info', 'get_value_preview', 
        'get_category_hierarchy', 'get_product_status'
    ]
    search_fields = ['product__title', 'attribute__name', 'value']
    list_filter = [
        'attribute__subcategory__category', 'attribute__subcategory', 
        'product__status', 'product__promotion_level'
    ]
    list_select_related = [
        'product', 'product__owner', 'attribute', 
        'attribute__subcategory', 'attribute__subcategory__category'
    ]
    autocomplete_fields = ['product', 'attribute']
    list_per_page = 30
    
    # Fieldsets for better organization
    fieldsets = (
        ('📋 Product Detail Information', {
            'fields': ('product', 'attribute', 'value'),
            'description': 'Specify the product attribute and its value'
        }),
    )
    
    # Enhanced display methods
    def get_product_link(self, obj):
        if obj.product:
            product_url = reverse('admin:products_product_change', args=[obj.product.pk])
            return format_html(
                '<a href="{}" style="color: #007cba;"><strong>{}</strong></a>',
                product_url, obj.product.title[:30] + ('...' if len(obj.product.title) > 30 else '')
            )
        return "-"
    get_product_link.short_description = 'Product'
    get_product_link.admin_order_field = 'product__title'
    
    def get_attribute_info(self, obj):
        if obj.attribute:
            attribute_url = reverse('admin:products_attribute_change', args=[obj.attribute.pk])
            return format_html(
                '<a href="{}" style="color: #6f42c1;">📋 {}</a>',
                attribute_url, obj.attribute.name
            )
        return "-"
    get_attribute_info.short_description = 'Attribute'
    get_attribute_info.admin_order_field = 'attribute__name'
    
    def get_value_preview(self, obj):
        if obj.value:
            preview = obj.value[:50] + ('...' if len(obj.value) > 50 else '')
            return format_html(
                '<span style="font-weight: bold; color: #495057;">{}</span>',
                preview
            )
        return "-"
    get_value_preview.short_description = 'Value'
    
    def get_category_hierarchy(self, obj):
        if obj.attribute and obj.attribute.subcategory and obj.attribute.subcategory.category:
            category = obj.attribute.subcategory.category
            subcategory = obj.attribute.subcategory
            category_url = reverse('admin:products_category_change', args=[category.pk])
            subcategory_url = reverse('admin:products_subcategory_change', args=[subcategory.pk])
            
            return format_html(
                '<a href="{}" style="color: #007cba;">📂 {}</a> → '
                '<a href="{}" style="color: #6f42c1;">📁 {}</a>',
                category_url, category.name, subcategory_url, subcategory.name
            )
        return '-'
    get_category_hierarchy.short_description = 'Category → Subcategory'
    
    def get_product_status(self, obj):
        if obj.product:
            status_colors = {
                'pending': '#ffc107',
                'accepted': '#28a745',
                'rejected': '#dc3545',
                'expired': '#6c757d'
            }
            status_icons = {
                'pending': '⏳',
                'accepted': '✅',
                'rejected': '❌',
                'expired': '⏰'
            }
            color = status_colors.get(obj.product.status, '#6c757d')
            icon = status_icons.get(obj.product.status, '❓')
            return format_html(
                '<span style="color: {}; font-size: 12px;">{} {}</span>',
                color, icon, obj.product.status.upper()
            )
        return "-"
    get_product_status.short_description = 'Product Status'
    get_product_status.admin_order_field = 'product__status'
    
    # Custom actions
    actions = ['delete_selected_details', 'export_details', 'validate_values']
    
    def delete_selected_details(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'🗑️ {count} product details deleted successfully.')
    delete_selected_details.short_description = "🗑️ Delete selected product details"
    
    def export_details(self, request, queryset):
        count = queryset.count()
        unique_products = queryset.values_list('product', flat=True).distinct().count()
        self.message_user(request, f'📊 {count} product details selected for export from {unique_products} products.')
    export_details.short_description = "📊 Export selected details"
    
    def validate_values(self, request, queryset):
        empty_values = queryset.filter(value__isnull=True).count()
        short_values = queryset.extra(where=["LENGTH(value) < 2"]).count()
        self.message_user(request, f'✅ Validation complete: {empty_values} empty values, {short_values} values too short.')
    validate_values.short_description = "✅ Validate selected values"


# Enhanced admin site configuration
admin.site.site_header = "BolBol Products Administration"
admin.site.site_title = "BolBol Products Admin"
admin.site.index_title = "Welcome to BolBol Products Management Portal"