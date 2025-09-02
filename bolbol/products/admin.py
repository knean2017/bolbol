from django.contrib import admin
from django import forms
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
    list_display = ['name', 'description']
    search_fields = ['name']
    ordering = ['name']


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'description']
    search_fields = ['name', 'category__name']
    list_filter = ['category']
    autocomplete_fields = ['category']  # 🔍 searchable
    list_select_related = ['category']  # ⚡ faster


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'subcategory']
    search_fields = ['name', 'subcategory__name']
    list_filter = ['subcategory__category', 'subcategory']
    autocomplete_fields = ['subcategory']  # 🔍 searchable
    list_select_related = ['subcategory', 'subcategory__category']  # ⚡ faster


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
        'name', 'get_category_name', 'category', 'city',
        'price', 'promotion_level', 'created_at'
    ]
    
    list_filter = [
        'promotion_level', 'barter_available', 'credit_available',
        'category__category', 'city'
    ]
    
    search_fields = ['name', 'description', 'category__name']
    
    readonly_fields = ['created_at', 'updated_at']
    
    inlines = [ProductDetailInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'city'),
            'description': 'Choose subcategory from the grouped list (Category → Subcategory). '
                           'Product details will show attributes grouped by subcategory.'
        }),
        ('Pricing & Features', {
            'fields': ('price', 'promotion_level', 'image')
        }),
        ('Availability Options', {
            'fields': ('barter_available', 'credit_available', 'delivery_available'),
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        })
    )
    
    def get_category_name(self, obj):
        return obj.category.category.name if obj.category and obj.category.category else '-'
    get_category_name.short_description = 'Main Category'

    list_select_related = ['category', 'category__category', 'city']  # ⚡ faster


@admin.register(ProductDetail)
class ProductDetailAdmin(admin.ModelAdmin):
    list_display = ['product', 'attribute', 'value']
    search_fields = ['product__name', 'attribute__name', 'value']
    list_filter = ['attribute__subcategory__category']
    list_select_related = ['product', 'attribute', 'attribute__subcategory', 'attribute__subcategory__category']  # ⚡
