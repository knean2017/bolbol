from django.urls import path

from .views import CommentAPIView, BookmarkAPIView


urlpatterns = [
    path("bookmarks/", BookmarkAPIView.as_view(), name="bookmarks"),
    path("comments/", CommentAPIView.as_view(), name="comments"),
]