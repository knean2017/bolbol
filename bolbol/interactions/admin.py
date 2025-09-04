from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Bookmark, Comment


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = (
        "get_user_info", "get_product_info", "get_product_price", 
        "get_user_type", "created_at", "get_product_category"
    )
    list_filter = (
        "product__category", "user__user_type", "created_at",
        "product__status", "product__city"
    )
    search_fields = (
        "user__email", "user__first_name", "user__store_name",
        "product__title", "product__description"
    )
    autocomplete_fields = ["user", "product"]
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    
    # Enhanced list per page
    list_per_page = 25
    list_max_show_all = 100
    
    # Custom display methods
    def get_user_info(self, obj):
        if obj.user:
            user_link = reverse("admin:users_user_change", args=[obj.user.pk])
            if obj.user.user_type == 'store' and obj.user.store_name:
                return format_html(
                    '<a href="{}" style="color: #0066cc;">🏪 {}</a><br><small>{}</small>',
                    user_link, obj.user.store_name, obj.user.email
                )
            else:
                return format_html(
                    '<a href="{}" style="color: #28a745;">👤 {}</a><br><small>{}</small>',
                    user_link, obj.user.first_name or obj.user.email.split('@')[0], obj.user.email
                )
        return "-"
    get_user_info.short_description = "User"
    get_user_info.admin_order_field = "user__email"
    
    def get_product_info(self, obj):
        if obj.product:
            product_link = reverse("admin:products_product_change", args=[obj.product.pk])
            status_colors = {
                'pending': '#ffc107',
                'accepted': '#28a745', 
                'rejected': '#dc3545'
            }
            status_color = status_colors.get(obj.product.status, '#6c757d')
            return format_html(
                '<a href="{}"><strong>{}</strong></a><br>'
                '<span style="color: {}; font-size: 11px;">● {}</span>',
                product_link, obj.product.title[:30] + ('...' if len(obj.product.title) > 30 else ''),
                status_color, obj.product.status.upper()
            )
        return "-"
    get_product_info.short_description = "Product"
    get_product_info.admin_order_field = "product__title"
    
    def get_product_price(self, obj):
        if obj.product:
            return format_html(
                '<span style="color: #007cba; font-weight: bold;">{} ₼</span>',
                obj.product.price
            )
        return "-"
    get_product_price.short_description = "Price"
    get_product_price.admin_order_field = "product__price"
    
    def get_user_type(self, obj):
        if obj.user:
            if obj.user.user_type == 'store':
                return format_html('<span style="color: #0066cc;">🏪 Store</span>')
            return format_html('<span style="color: #28a745;">👤 Individual</span>')
        return "-"
    get_user_type.short_description = "User Type"
    get_user_type.admin_order_field = "user__user_type"
    
    def get_product_category(self, obj):
        if obj.product and obj.product.category:
            return obj.product.category.name
        return "-"
    get_product_category.short_description = "Category"
    get_product_category.admin_order_field = "product__category__name"
    
    # Custom actions
    actions = ['delete_selected_bookmarks', 'export_bookmark_data']
    
    def delete_selected_bookmarks(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} bookmarks deleted successfully.')
    delete_selected_bookmarks.short_description = "🗑️ Delete selected bookmarks"
    
    def export_bookmark_data(self, request, queryset):
        # This could be expanded to actually export data
        count = queryset.count()
        self.message_user(request, f'{count} bookmarks selected for export.')
    export_bookmark_data.short_description = "📊 Export bookmark data"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "get_user_info", "get_product_info", "get_comment_preview", 
        "created_at", "get_user_type"
    )
    list_filter = (
        "created_at", "user__user_type", "product__category", 
        "product__status", "product__city"
    )
    search_fields = (
        "user__email", "user__first_name", "user__store_name",
        "product__title", "comment"
    )
    autocomplete_fields = ["user", "product"]
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    
    # Enhanced list per page
    list_per_page = 25
    list_max_show_all = 100
    
    # Fieldsets for detailed view
    fieldsets = (
        ("💬 Comment Information", {
            "fields": ("user", "product", "comment")
        }),
        ("📅 Timestamps", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        })
    )
    
    readonly_fields = ("created_at",)
    
    # Custom display methods
    def get_user_info(self, obj):
        if obj.user:
            user_link = reverse("admin:users_user_change", args=[obj.user.pk])
            if obj.user.user_type == 'store' and obj.user.store_name:
                return format_html(
                    '<a href="{}" style="color: #0066cc;">🏪 {}</a><br><small>{}</small>',
                    user_link, obj.user.store_name, obj.user.email
                )
            else:
                return format_html(
                    '<a href="{}" style="color: #28a745;">👤 {}</a><br><small>{}</small>',
                    user_link, obj.user.first_name or obj.user.email.split('@')[0], obj.user.email
                )
        return "-"
    get_user_info.short_description = "User"
    get_user_info.admin_order_field = "user__email"
    
    def get_product_info(self, obj):
        if obj.product:
            product_link = reverse("admin:products_product_change", args=[obj.product.pk])
            status_colors = {
                'pending': '#ffc107',
                'accepted': '#28a745', 
                'rejected': '#dc3545'
            }
            status_color = status_colors.get(obj.product.status, '#6c757d')
            return format_html(
                '<a href="{}"><strong>{}</strong></a><br>'
                '<span style="color: {}; font-size: 11px;">● {}</span>',
                product_link, obj.product.title[:25] + ('...' if len(obj.product.title) > 25 else ''),
                status_color, obj.product.status.upper()
            )
        return "-"
    get_product_info.short_description = "Product"
    get_product_info.admin_order_field = "product__title"
    
    def get_comment_preview(self, obj):
        if obj.comment:
            preview = obj.comment[:50] + ('...' if len(obj.comment) > 50 else '')
            return format_html(
                '<span style="font-style: italic; color: #495057;">"{}"{}</span>',
                preview, ' <span style="color: #6c757d;">({} chars)</span>'.format(len(obj.comment))
            )
        return "-"
    get_comment_preview.short_description = "Comment Preview"
    
    def get_user_type(self, obj):
        if obj.user:
            if obj.user.user_type == 'store':
                return format_html('<span style="color: #0066cc;">🏪 Store</span>')
            return format_html('<span style="color: #28a745;">👤 Individual</span>')
        return "-"
    get_user_type.short_description = "User Type"
    get_user_type.admin_order_field = "user__user_type"
    
    # Custom actions
    actions = ['delete_selected_comments', 'moderate_comments']
    
    def delete_selected_comments(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} comments deleted successfully.')
    delete_selected_comments.short_description = "🗑️ Delete selected comments"
    
    def moderate_comments(self, request, queryset):
        # This could be expanded for comment moderation
        count = queryset.count()
        self.message_user(request, f'{count} comments selected for moderation.')
    moderate_comments.short_description = "🛡️ Moderate selected comments"


# Custom admin site title and header
admin.site.site_header = "BolBol Interactions Admin"
admin.site.site_title = "Interactions Admin"
admin.site.index_title = "Welcome to BolBol Interactions Administration"
