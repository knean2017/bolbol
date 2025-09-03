from django.contrib import admin
from django import forms
from django.utils.html import format_html
from .models import Category, SubCategory, Attribute, City, Product, ProductDetail


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
    
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



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'get_subcategory_count']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def get_subcategory_count(self, obj):
        count = obj.subcategory_set.count()
        if count > 0:
            return format_html('<span style="color: #28a745;">📁 {}</span>', count)
        return "0"
    get_subcategory_count.short_description = 'Subcategories'


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'description', 'get_product_count', 'get_attribute_count']
    search_fields = ['name', 'category__name', 'description']
    list_filter = ['category']
    autocomplete_fields = ['category']  # 🔍 searchable
    list_select_related = ['category']  # ⚡ faster
    
    def get_product_count(self, obj):
        count = obj.product_set.count()
        if count > 0:
            return format_html('<span style="color: #007cba;">🛍️ {}</span>', count)
        return "0"
    get_product_count.short_description = 'Products'
    
    def get_attribute_count(self, obj):
        count = obj.attribute_set.count()
        if count > 0:
            return format_html('<span style="color: #ffc107;">📋 {}</span>', count)
        return "0"
    get_attribute_count.short_description = 'Attributes'


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_product_count']
    search_fields = ['name']
    ordering = ['name']
    
    def get_product_count(self, obj):
        count = obj.product_set.count()
        if count > 0:
            return format_html('<span style="color: #007cba;">🛍️ {}</span>', count)
        return "0"
    get_product_count.short_description = 'Products'


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'subcategory', 'get_category_name']
    search_fields = ['name', 'subcategory__name', 'subcategory__category__name']
    list_filter = ['subcategory__category', 'subcategory']
    autocomplete_fields = ['subcategory']  # 🔍 searchable
    list_select_related = ['subcategory', 'subcategory__category']  # ⚡ faster
    
    def get_category_name(self, obj):
        return obj.subcategory.category.name if obj.subcategory and obj.subcategory.category else '-'
    get_category_name.short_description = 'Main Category'


class ProductDetailInlineForm(forms.ModelForm):
    class Meta:
        model = ProductDetail
        fields = '__all__'
    
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



class ProductDetailInline(admin.TabularInline):
    model = ProductDetail
    form = ProductDetailInlineForm
    extra = 2
    classes = ['collapse']  # 👌 collapsible inline


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    
    list_display = [
        'title', 'get_owner', 'get_category_name', 'category', 'city',
        'price', 'get_status_badge', 'promotion_level', 'views_count', 'created_at'
    ]
    
    list_filter = [
        'status', 'promotion_level', 'barter_available', 'credit_available',
        'delivery_available', 'category__category', 'city', 'created_at'
    ]
    
    search_fields = ['title', 'description', 'category__name', 'owner__email', 'owner__store_name']
    
    readonly_fields = ['views_count', 'created_at', 'updated_at']
    
    inlines = [ProductDetailInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'title', 'description', 'category', 'city'),
            'description': 'Choose subcategory from the grouped list (Category → Subcategory). '
                           'Product details will show attributes grouped by subcategory.'
        }),
        ('Pricing & Features', {
            'fields': ('price', 'promotion_level', 'image')
        }),
        ('Status & Availability', {
            'fields': ('status', 'barter_available', 'credit_available', 'delivery_available'),
        }),
        ('Analytics', {
            'fields': ('views_count',),
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        })
    )
    
    actions = ['approve_products', 'reject_products', 'set_premium', 'set_basic']
    
    def get_owner(self, obj):
        if obj.owner:
            if obj.owner.user_type == 'store' and obj.owner.store_name:
                return format_html('<span style="color: #0066cc;">🏪 {}</span>', obj.owner.store_name)
            return format_html('<span style="color: #28a745;">👤 {}</span>', obj.owner.first_name or obj.owner.email.split('@')[0])
        return "-"
    get_owner.short_description = 'Owner'
    
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
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.get_status_display() if obj.status else 'Unknown'
        )
    get_status_badge.short_description = 'Status'
    
    def get_category_name(self, obj):
        return obj.category.category.name if obj.category and obj.category.category else '-'
    get_category_name.short_description = 'Main Category'

    list_select_related = ['owner', 'category', 'category__category', 'city']  # ⚡ faster
    
    # Custom Actions
    def approve_products(self, request, queryset):
        updated = queryset.update(status='accepted')
        self.message_user(request, f'{updated} products were approved.')
    approve_products.short_description = "✅ Approve selected products"

    def reject_products(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} products were rejected.')
    reject_products.short_description = "❌ Reject selected products"

    def set_premium(self, request, queryset):
        updated = queryset.update(promotion_level='premium')
        self.message_user(request, f'{updated} products were set to Premium.')
    set_premium.short_description = "⭐ Set to Premium"

    def set_basic(self, request, queryset):
        updated = queryset.update(promotion_level='basic')
        self.message_user(request, f'{updated} products were set to Basic.')
    set_basic.short_description = "📦 Set to Basic"


@admin.register(ProductDetail)
class ProductDetailAdmin(admin.ModelAdmin):
    list_display = ['product', 'attribute', 'value', 'get_category_name']
    search_fields = ['product__title', 'attribute__name', 'value']
    list_filter = ['attribute__subcategory__category', 'attribute__subcategory']
    list_select_related = ['product', 'attribute', 'attribute__subcategory', 'attribute__subcategory__category']  # ⚡
    autocomplete_fields = ['product', 'attribute']
    
    def get_category_name(self, obj):
        if obj.attribute and obj.attribute.subcategory and obj.attribute.subcategory.category:
            return obj.attribute.subcategory.category.name
        return '-'
    get_category_name.short_description = 'Category'