# views.py
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from django.db import transaction

from .models import MenuItem, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, CartSerializer, OrderSerializer 
from .permissions import IsManagerOrReadOnly, IsCustomer, IsDeliveryCrew, IsManager
from .services import OrderService

# Create your views here.

class MenuItemViewSet(ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsManagerOrReadOnly]

class CartsView(APIView):
    permission_classes = [IsCustomer]

    def get(self, request):
        cart_items = Cart.objects.filter(user = request.user)
        serializer = CartSerializer(cart_items, many=True)
        return Response(serializer.data, status= status.HTTP_200_OK)
    
    def post(self, request):
        serializer = CartSerializer(data = request.data)
        serializer.is_valid(raise_exception=True)

        menuitem = serializer.validated_data['menuitem']
        quantity = serializer.validated_data['quantity']
        unit_price = menuitem.price
        price = quantity * unit_price

        cart_item, created = Cart.objects.update_or_create(
            user = request.user,
            menuitem = menuitem,
            defaults = {
                "quantity" : quantity,
                "unit_price" : unit_price,
                "price" : price
            }

        )

        serializer_cart_item = CartSerializer(cart_item)

        return Response(serializer_cart_item.data, status= status.HTTP_201_CREATED)

    def delete(self, request):
        Cart.objects.filter(user=request.user).delete()
        return Response(
            {"message": "Cart cleared."},
            status=status.HTTP_200_OK
        )
    

class OrderViewSet(ModelViewSet):
    serializer_class = OrderSerializer

    def get_permissions(self):
        base_permissions = super().get_permissions()

        # Add your custom permissions on top
        if self.action == 'create':
            return base_permissions + [IsCustomer()]
        if self.action in ['update', 'destroy']:
            return base_permissions + [IsManager()]
        if self.action == 'partial_update':
            return base_permissions + [IsManager() | IsDeliveryCrew()]
        
        return base_permissions 
        
    def get_queryset(self):
        if self.request.user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        
        if self.request.user.groups.filter(name='Delivery Crew').exists():
            return Order.objects.filter(delivery_crew=self.request.user)
        
        return Order.objects.filter(user=self.request.user)
        
    def create(self, request, *args, **kwargs):
        order = OrderService.create_from_cart(request.user)
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def partial_update(self, request, *args, **kwargs):

        # Check if user is delivery crew and trying to update disallowed fields
        if self.request.user.groups.filter(name='Delivery Crew').exists():
            requested_fields = list(request.data.keys())
            allowed_fields = {"status"}  # use a set for faster lookup
        
            if not set(requested_fields).issubset(allowed_fields):
                return Response(
                {"error": "Delivery Crew can only update the order status"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().partial_update(request, *args, **kwargs)
        












