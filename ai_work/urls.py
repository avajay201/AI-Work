from django.contrib import admin
from django.urls import path
from .views import work, gen_res, download_img
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', work, name='work'),
    path('gen-res/', gen_res, name='gen-res'),
    path('download-img/<img_name>/', download_img, name='download_img'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)