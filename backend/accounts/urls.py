from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, me, login_view, hr_users_list_create, hr_user_delete

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')

urlpatterns = [
    path('login/', login_view, name='login'),
    path('me/', me, name='me'),
    path('hr-users/', hr_users_list_create, name='hr-users-list-create'),
    path('hr-users/<int:pk>/', hr_user_delete, name='hr-user-delete'),
    path('', include(router.urls)),
]
