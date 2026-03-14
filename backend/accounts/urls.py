from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, me, login_view, register_view

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')

urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('me/', me, name='me'),
    path('', include(router.urls)),
]
