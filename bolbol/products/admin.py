from django.contrib import admin
from django import forms
from .models import Category, SubCategory, Attribute, City, Product, ProductDetail


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Group subcategories by main category in the display
        if 'category' in self.fields:
            subcategories = SubCategory.objects.select_related('category').order_by('category__name', 'name')
            choices = [('', '---------')]
            
            current_category = None
            for subcategory in subcategories:
                if subcategory.category != current_category:
                    if current_category is not None:
                        choices.append(('', '---'))  # Separator
                    current_category = subcategory.category
                
                choice_label = f"{subcategory.category.name} → {subcategory.name}"
                choices.append((subcategory.id, choice_label))
            
            self.fields['category'].choices = choices


# Keep all other admin classes the same...
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


class ProductDetailInlineForm(forms.ModelForm):
    class Meta:
        model = ProductDetail
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Group attributes by subcategory in the display
        if 'attribute' in self.fields:
            attributes = Attribute.objects.select_related('subcategory__category').order_by('subcategory__category__name', 'subcategory__name', 'name')
            choices = [('', '---------')]
            
            current_subcategory = None
            for attribute in attributes:
                if attribute.subcategory != current_subcategory:
                    if current_subcategory is not None:
                        choices.append(('', '---'))  # Separator
                    current_subcategory = attribute.subcategory
                
                if attribute.subcategory:
                    choice_label = f"{attribute.subcategory.category.name} → {attribute.subcategory.name} → {attribute.name}"
                else:
                    choice_label = f"No Category → {attribute.name}"
                choices.append((attribute.id, choice_label))
            
            self.fields['attribute'].choices = choices


class ProductDetailInline(admin.TabularInline):
    model = ProductDetail
    form = ProductDetailInlineForm
    extra = 2


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
            'description': 'Choose subcategory from the grouped list (Category → Subcategory). Product details will show attributes grouped by subcategory.'
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


@admin.register(ProductDetail)
class ProductDetailAdmin(admin.ModelAdmin):
    list_display = ['product', 'attribute', 'value']
    search_fields = ['product__name', 'attribute__name', 'value']
    list_filter = ['attribute__subcategory__category']