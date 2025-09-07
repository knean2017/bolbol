from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q, Avg, Max, Min
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from datetime import datetime, timedelta
from django import forms

from .models import Bookmark, Comment


# Custom Filter Classes
class ActivityDateFilter(SimpleListFilter):
    title = 'Activity Date'
    parameter_name = 'activity_date'
    
    def lookups(self, request, model_admin):
        return (
            ('today', '📅 Today'),
            ('yesterday', '📅 Yesterday'),
            ('this_week', '📅 This Week'),
            ('this_month', '📅 This Month'),
            ('last_month', '📅 Last Month'),
        )
    
    def queryset(self, request, queryset):
        now = timezone.now()
        
        if self.value() == 'today':
            return queryset.filter(created_at__date=now.date())
        elif self.value() == 'yesterday':
            yesterday = now.date() - timedelta(days=1)
            return queryset.filter(created_at__date=yesterday)
        elif self.value() == 'this_week':
            start_week = now - timedelta(days=now.weekday())
            return queryset.filter(created_at__gte=start_week.replace(hour=0, minute=0, second=0, microsecond=0))
        elif self.value() == 'this_month':
            start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return queryset.filter(created_at__gte=start_month)
        elif self.value() == 'last_month':
            first_day_this_month = now.replace(day=1)
            last_month = first_day_this_month - timedelta(days=1)
            start_last_month = last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return queryset.filter(created_at__gte=start_last_month, created_at__lt=first_day_this_month)
        return queryset


class ProductStatusFilter(SimpleListFilter):
    title = 'Product Status'
    parameter_name = 'product_status'
    
    def lookups(self, request, model_admin):
        return (
            ('pending', '⏳ Pending'),
            ('accepted', '✅ Accepted'),
            ('rejected', '❌ Rejected'),
            ('expired', '⏰ Expired'),
        )
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(product__status=self.value())
        return queryset


class UserEngagementFilter(SimpleListFilter):
    title = 'User Engagement Level'
    parameter_name = 'engagement_level'
    
    def lookups(self, request, model_admin):
        return (
            ('high', '🔥 High Engagement (5+ interactions)'),
            ('medium', '📈 Medium Engagement (2-4 interactions)'),
            ('low', '📉 Low Engagement (1 interaction)'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'high':
            active_users = queryset.values('user').annotate(
                interaction_count=Count('user')
            ).filter(interaction_count__gte=5).values_list('user', flat=True)
            return queryset.filter(user__in=active_users)
        elif self.value() == 'medium':
            active_users = queryset.values('user').annotate(
                interaction_count=Count('user')
            ).filter(interaction_count__gte=2, interaction_count__lt=5).values_list('user', flat=True)
            return queryset.filter(user__in=active_users)
        elif self.value() == 'low':
            active_users = queryset.values('user').annotate(
                interaction_count=Count('user')
            ).filter(interaction_count=1).values_list('user', flat=True)
            return queryset.filter(user__in=active_users)
        return queryset


# Enhanced Form Classes
class BookmarkAdminForm(forms.ModelForm):
    class Meta:
        model = Bookmark
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        product = cleaned_data.get('product')
        
        # Validate that user cannot bookmark their own product
        if user and product and product.owner == user:
            raise forms.ValidationError("Users cannot bookmark their own products.")
        
        # Validate product status
        if product and product.status not in ['accepted', 'pending']:
            raise forms.ValidationError("Cannot bookmark rejected or expired products.")
        
        return cleaned_data


class CommentAdminForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = '__all__'
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'cols': 60}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        comment = cleaned_data.get('comment')
        product = cleaned_data.get('product')
        
        # Validate comment length
        if comment and len(comment.strip()) < 5:
            raise forms.ValidationError("Comments must be at least 5 characters long.")
        
        if comment and len(comment) > 1000:
            raise forms.ValidationError("Comments cannot exceed 1000 characters.")
        
        # Validate product status
        if product and product.status != 'accepted':
            raise forms.ValidationError("Can only comment on accepted products.")
        
        return cleaned_data


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    form = BookmarkAdminForm
    list_display = (
        "get_user_info", "get_product_info", "get_product_price", 
        "get_user_type", "get_bookmark_age", "get_product_category",
        "get_product_engagement"
    )
    list_filter = (
        ActivityDateFilter, ProductStatusFilter, UserEngagementFilter,
        "product__category", "product__city",
        "product__promotion_level"
    )
    search_fields = (
        "user__email", "user__first_name",
        "product__title", "product__description", "product__owner__email"
    )
    autocomplete_fields = ["user", "product"]
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    
    # Enhanced pagination and performance
    list_per_page = 30
    list_max_show_all = 150
    list_select_related = ['user', 'product', 'product__owner', 'product__category', 'product__city']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Annotate with engagement metrics
        queryset = queryset.annotate(
            product_comment_count=Count('product__comment', distinct=True),
            product_bookmark_count=Count('product__bookmark', distinct=True)
        )
        return queryset
    
    # Enhanced fieldsets for detailed view
    fieldsets = (
        ("❤️ Bookmark Information", {
            "fields": ("user", "product"),
            "description": "User bookmark relationship with product"
        }),
        ("📅 Activity Details", {
            "fields": ("created_at", "get_bookmark_analytics"),
            "classes": ("collapse",)
        })
    )
    
    readonly_fields = ("created_at", "get_bookmark_analytics")
    
    # Custom display methods
    def get_user_info(self, obj):
        if obj.user:
            user_link = reverse("admin:users_user_change", args=[obj.user.pk])
            if obj.user.first_name:
                # Check if user might be a store by looking for Store records
                try:
                    from users.models import Store
                    store = Store.objects.filter(name__icontains=obj.user.first_name).first()
                    if store:
                        return format_html(
                            '<a href="{}" style="color: #0066cc;">🏪 {}</a><br><small>{}</small>',
                            user_link, store.name, obj.user.email
                        )
                except:
                    pass
            
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
            # Check if user might be a store by looking for Store records
            try:
                from users.models import Store
                store = Store.objects.filter(name__icontains=obj.user.first_name).first() if obj.user.first_name else None
                if store:
                    return format_html('<span style="color: #0066cc;">🏪 Store</span>')
            except:
                pass
            return format_html('<span style="color: #28a745;">👤 Individual</span>')
        return "-"
    get_user_type.short_description = "User Type"
    get_user_type.admin_order_field = "user__email"
    
    def get_product_category(self, obj):
        if obj.product and obj.product.category:
            category_url = reverse('admin:products_subcategory_change', args=[obj.product.category.pk])
            return format_html(
                '<a href="{}" style="color: #6f42c1;">📁 {}</a>',
                category_url, obj.product.category.name
            )
        return "-"
    get_product_category.short_description = "Category"
    get_product_category.admin_order_field = "product__category__name"
    
    def get_bookmark_age(self, obj):
        if obj.created_at:
            age = timezone.now() - obj.created_at
            if age.days > 30:
                color = '#dc3545'  # Red for old bookmarks
                icon = '🔴'
            elif age.days > 7:
                color = '#ffc107'  # Yellow for week-old bookmarks
                icon = '🟡'
            else:
                color = '#28a745'  # Green for recent bookmarks
                icon = '🟢'
            
            if age.days > 0:
                return format_html(
                    '<span style="color: {};">{} {} days ago</span>',
                    color, icon, age.days
                )
            else:
                hours = age.seconds // 3600
                return format_html(
                    '<span style="color: #28a745;">🟢 {} hours ago</span>',
                    hours
                )
        return "-"
    get_bookmark_age.short_description = "Bookmark Age"
    get_bookmark_age.admin_order_field = "created_at"
    
    def get_product_engagement(self, obj):
        comment_count = getattr(obj, 'product_comment_count', 0)
        bookmark_count = getattr(obj, 'product_bookmark_count', 0)
        
        engagement_score = comment_count + bookmark_count
        
        if engagement_score >= 10:
            return format_html('<span style="color: #28a745;">🔥 Hot ({} interactions)</span>', engagement_score)
        elif engagement_score >= 5:
            return format_html('<span style="color: #ffc107;">📈 Popular ({} interactions)</span>', engagement_score)
        elif engagement_score >= 1:
            return format_html('<span style="color: #007cba;">📉 Normal ({} interactions)</span>', engagement_score)
        else:
            return format_html('<span style="color: #6c757d;">😴 Low (0 interactions)</span>')
    get_product_engagement.short_description = "Product Engagement"
    
    def get_bookmark_analytics(self, obj):
        if obj.pk:
            # Get analytics data
            age = timezone.now() - obj.created_at
            comment_count = getattr(obj, 'product_comment_count', 0)
            bookmark_count = getattr(obj, 'product_bookmark_count', 0)
            
            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
                '<strong>Bookmark Analytics:</strong><br>'
                '🕰️ Age: {} days<br>'
                '💬 Product Comments: {}<br>'
                '❤️ Total Bookmarks: {}<br>'
                '📈 Engagement Score: {}'
                '</div>',
                age.days, comment_count, bookmark_count, comment_count + bookmark_count
            )
        return "No data available"
    get_bookmark_analytics.short_description = 'Bookmark Analytics'
    
    # Enhanced Custom actions
    actions = ['delete_selected_bookmarks', 'export_bookmark_data', 'analyze_bookmark_patterns', 'notify_users_about_updates']
    
    def delete_selected_bookmarks(self, request, queryset):
        count = queryset.count()
        # Get user emails for notification
        user_emails = list(queryset.values_list('user__email', flat=True).distinct())
        queryset.delete()
        self.message_user(request, f'🗑️ {count} bookmarks deleted successfully. Affected users: {len(user_emails)}')
    delete_selected_bookmarks.short_description = "🗑️ Delete selected bookmarks"
    
    def export_bookmark_data(self, request, queryset):
        count = queryset.count()
        total_value = sum([b.product.price for b in queryset if b.product and b.product.price])
        self.message_user(request, f'📊 {count} bookmarks selected for export. Total bookmarked value: {total_value} ₼')
    export_bookmark_data.short_description = "📊 Export bookmark data"
    
    def analyze_bookmark_patterns(self, request, queryset):
        # Analyze bookmark patterns
        categories = queryset.values('product__category__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        if categories:
            top_category = categories[0]
            self.message_user(request, f'📈 Analysis complete: Most bookmarked category is "{top_category["product__category__name"]}" with {top_category["count"]} bookmarks')
        else:
            self.message_user(request, '📈 No bookmark patterns found in selection')
    analyze_bookmark_patterns.short_description = "📈 Analyze bookmark patterns"
    
    def notify_users_about_updates(self, request, queryset):
        unique_users = queryset.values_list('user__email', flat=True).distinct().count()
        self.message_user(request, f'📧 Notification queued for {unique_users} users about their bookmarked products')
    notify_users_about_updates.short_description = "📧 Notify users about updates"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    form = CommentAdminForm
    
    list_display = (
        "get_user_info", "get_product_info", "get_comment_preview", 
        "get_comment_age", "get_user_type", "get_comment_length",
        "get_comment_sentiment"
    )
    list_filter = (
        ActivityDateFilter, ProductStatusFilter, UserEngagementFilter,
        "product__category", 
        "product__city", "product__promotion_level"
    )
    search_fields = (
        "user__email", "user__first_name",
        "product__title", "comment", "product__owner__email"
    )
    autocomplete_fields = ["user", "product"]
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    
    # Enhanced pagination and performance
    list_per_page = 30
    list_max_show_all = 150
    list_select_related = ['user', 'product', 'product__owner', 'product__category', 'product__city']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Annotate with engagement metrics
        queryset = queryset.annotate(
            user_comment_count=Count('user__comment', distinct=True),
            product_total_comments=Count('product__comment', distinct=True)
        )
        return queryset
    
    # Enhanced fieldsets for detailed view
    fieldsets = (
        ("💬 Comment Information", {
            "fields": ("user", "product", "comment"),
            "description": "User comment on product"
        }),
        ("📅 Activity & Analytics", {
            "fields": ("created_at", "get_comment_analytics"),
            "classes": ("collapse",)
        })
    )
    
    readonly_fields = ("created_at", "get_comment_analytics")
    
    # Custom display methods
    def get_user_info(self, obj):
        if obj.user:
            user_link = reverse("admin:users_user_change", args=[obj.user.pk])
            if obj.user.first_name:
                # Check if user might be a store by looking for Store records
                try:
                    from users.models import Store
                    store = Store.objects.filter(name__icontains=obj.user.first_name).first()
                    if store:
                        return format_html(
                            '<a href="{}" style="color: #0066cc;">🏪 {}</a><br><small>{}</small>',
                            user_link, store.name, obj.user.email
                        )
                except:
                    pass
            
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
            preview = obj.comment[:60] + ('...' if len(obj.comment) > 60 else '')
            # Add sentiment indicator based on keywords
            positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'perfect', 'best']
            negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'disappointing']
            
            comment_lower = obj.comment.lower()
            is_positive = any(word in comment_lower for word in positive_words)
            is_negative = any(word in comment_lower for word in negative_words)
            
            if is_positive and not is_negative:
                sentiment_icon = '😊'  # Positive
                sentiment_color = '#28a745'
            elif is_negative and not is_positive:
                sentiment_icon = '🙁'  # Negative
                sentiment_color = '#dc3545'
            else:
                sentiment_icon = '😐'  # Neutral
                sentiment_color = '#6c757d'
            
            return format_html(
                '<span style="font-style: italic; color: #495057;">"{}"{}</span> '
                '<span style="color: {};">{}</span>',
                preview, 
                ' <span style="color: #6c757d;">({} chars)</span>'.format(len(obj.comment)),
                sentiment_color, sentiment_icon
            )
        return "-"
    get_comment_preview.short_description = "Comment Preview"
    
    def get_comment_age(self, obj):
        if obj.created_at:
            age = timezone.now() - obj.created_at
            if age.days > 30:
                color = '#dc3545'  # Red for old comments
                icon = '🔴'
            elif age.days > 7:
                color = '#ffc107'  # Yellow for week-old comments
                icon = '🟡'
            else:
                color = '#28a745'  # Green for recent comments
                icon = '🟢'
            
            if age.days > 0:
                return format_html(
                    '<span style="color: {};">{} {} days ago</span>',
                    color, icon, age.days
                )
            else:
                hours = age.seconds // 3600
                return format_html(
                    '<span style="color: #28a745;">🟢 {} hours ago</span>',
                    hours
                )
        return "-"
    get_comment_age.short_description = "Comment Age"
    get_comment_age.admin_order_field = "created_at"
    
    def get_comment_length(self, obj):
        if obj.comment:
            length = len(obj.comment)
            if length > 200:
                return format_html('<span style="color: #dc3545;">📝 Long ({} chars)</span>', length)
            elif length > 100:
                return format_html('<span style="color: #ffc107;">📝 Medium ({} chars)</span>', length)
            else:
                return format_html('<span style="color: #28a745;">📝 Short ({} chars)</span>', length)
        return "-"
    get_comment_length.short_description = "Length"
    
    def get_comment_sentiment(self, obj):
        if obj.comment:
            positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'perfect', 'best', 'wonderful', 'awesome']
            negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'disappointing', 'poor', 'useless']
            
            comment_lower = obj.comment.lower()
            positive_count = sum(1 for word in positive_words if word in comment_lower)
            negative_count = sum(1 for word in negative_words if word in comment_lower)
            
            if positive_count > negative_count:
                return format_html('<span style="color: #28a745;">😊 Positive</span>')
            elif negative_count > positive_count:
                return format_html('<span style="color: #dc3545;">🙁 Negative</span>')
            else:
                return format_html('<span style="color: #6c757d;">😐 Neutral</span>')
        return "-"
    get_comment_sentiment.short_description = "Sentiment"
    
    def get_comment_analytics(self, obj):
        if obj.pk:
            age = timezone.now() - obj.created_at
            user_comment_count = getattr(obj, 'user_comment_count', 0)
            product_total_comments = getattr(obj, 'product_total_comments', 0)
            
            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
                '<strong>Comment Analytics:</strong><br>'
                '🕰️ Age: {} days<br>'
                '💬 User Total Comments: {}<br>'
                '📋 Product Total Comments: {}<br>'
                '📝 Comment Length: {} chars'
                '</div>',
                age.days, user_comment_count, product_total_comments, len(obj.comment or '')
            )
        return "No data available"
    get_comment_analytics.short_description = 'Comment Analytics'
    
    def get_user_type(self, obj):
        if obj.user:
            # Check if user might be a store by looking for Store records
            try:
                from users.models import Store
                store = Store.objects.filter(name__icontains=obj.user.first_name).first() if obj.user.first_name else None
                if store:
                    return format_html('<span style="color: #0066cc;">🏪 Store</span>')
            except:
                pass
            return format_html('<span style="color: #28a745;">👤 Individual</span>')
        return "-"
    get_user_type.short_description = "User Type"
    get_user_type.admin_order_field = "user__email"
    
    # Custom actions
    actions = ['delete_selected_comments', 'moderate_comments', 'analyze_comment_sentiment', 'export_comments', 'flag_inappropriate_comments']
    
    def delete_selected_comments(self, request, queryset):
        count = queryset.count()
        user_count = queryset.values_list('user__email', flat=True).distinct().count()
        queryset.delete()
        self.message_user(request, f'🗑️ {count} comments deleted successfully from {user_count} users.')
    delete_selected_comments.short_description = "🗑️ Delete selected comments"
    
    def moderate_comments(self, request, queryset):
        # Enhanced moderation with analytics
        total_count = queryset.count()
        long_comments = queryset.filter(comment__isnull=False).extra(
            where=["LENGTH(comment) > 200"]
        ).count()
        
        self.message_user(request, f'🛡️ {total_count} comments selected for moderation. {long_comments} are lengthy comments requiring attention.')
    moderate_comments.short_description = "🛡️ Moderate selected comments"
    
    def analyze_comment_sentiment(self, request, queryset):
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'perfect', 'best']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible']
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for comment in queryset:
            if comment.comment:
                comment_lower = comment.comment.lower()
                is_positive = any(word in comment_lower for word in positive_words)
                is_negative = any(word in comment_lower for word in negative_words)
                
                if is_positive and not is_negative:
                    positive_count += 1
                elif is_negative and not is_positive:
                    negative_count += 1
                else:
                    neutral_count += 1
        
        self.message_user(request, f'📊 Sentiment Analysis: 😊 {positive_count} positive, 🙁 {negative_count} negative, 😐 {neutral_count} neutral comments')
    analyze_comment_sentiment.short_description = "📊 Analyze comment sentiment"
    
    def export_comments(self, request, queryset):
        total_chars = sum(len(c.comment or '') for c in queryset)
        avg_length = total_chars // queryset.count() if queryset.count() > 0 else 0
        self.message_user(request, f'📊 {queryset.count()} comments selected for export. Average length: {avg_length} characters')
    export_comments.short_description = "📊 Export selected comments"
    
    def flag_inappropriate_comments(self, request, queryset):
        flagged_words = ['spam', 'fake', 'scam', 'fraud']
        flagged_count = 0
        
        for comment in queryset:
            if comment.comment:
                comment_lower = comment.comment.lower()
                if any(word in comment_lower for word in flagged_words):
                    flagged_count += 1
        
        self.message_user(request, f'🚩 {flagged_count} potentially inappropriate comments found out of {queryset.count()} selected')
    flag_inappropriate_comments.short_description = "🚩 Flag inappropriate comments"


# Enhanced admin site configuration
admin.site.site_header = "BolBol Interactions Administration"
admin.site.site_title = "BolBol Interactions Admin"
admin.site.index_title = "Welcome to BolBol Interactions Management Portal"
