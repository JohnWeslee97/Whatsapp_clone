from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    #path('admin/', admin.site.urls),#
    path('', include('chat.urls')),
] + static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'chat' / 'static')
handler404 = 'chat.views.error_404'
handler500 = 'chat.views.error_500'
handler403 = 'chat.views.error_403'