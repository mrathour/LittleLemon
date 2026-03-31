# urls.py
from . import views
from rest_framework.routers import DefaultRouter
from django.urls import path

router = DefaultRouter()
router.register('menu-items', views.MenuItemViewSet)
router.register('orders', views.OrderViewSet, basename='order')

urlpatterns = [
    *router.urls,
    path('cart/menu-items/', views.CartsView.as_view()),
    path('groups/<str:role>/users/', views.GroupManagementView.as_view()),
    path('groups/<str:role>/users/<int:pk>/', views.GroupManagementView.as_view()),
] 
