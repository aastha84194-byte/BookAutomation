"""
Root URL Configuration
=======================
All API routes are namespaced under /api/.
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def api_root(request):
    """Landing endpoint that shows available API routes."""
    return JsonResponse(
        {
            "message": "📚 BookAutomation API",
            "version": "1.0.0",
            "endpoints": {
                "books_list": "/api/books/",
                "book_detail": "/api/books/<id>/",
                "recommendations": "/api/books/<id>/recommendations/",
                "upload_book": "POST /api/books/upload/",
                "trigger_scrape": "POST /api/books/scrape/",
                "qa_query": "POST /api/qa/",
                "chat_history": "/api/chat/history/",
                "genres": "/api/genres/",
                "stats": "/api/stats/",
                "admin": "/admin/",
            },
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("bookapp.urls")),
    path("", api_root),
]
