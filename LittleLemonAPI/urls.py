# urls.py
from . import views
from rest_framework.routers import DefaultRouter
from django.urls import path

router = DefaultRouter()
router.register('menu-items', views.MenuItemViewSet)

urlpatterns = [
    *router.urls,
    path('cart/menu-items/', views.CartsView.as_view()),
    path('orders/', views.OrdersView.as_view()),
    path('orders/<int:pk>', views.OrderDetailView.as_view()),
] 
