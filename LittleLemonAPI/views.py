# views.py
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
User = get_user_model()

from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import MenuItem, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, CartSerializer, OrderSerializer, UserSerializer
from .permissions import IsManagerOrReadOnly, IsCustomer, IsDeliveryCrew, IsManager
from .services import OrderService
from .paginations import MenuItemPagination, OrderPagination

# Create your views here.

class MenuItemViewSet(ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAuthenticated, IsManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    pagination_class = MenuItemPagination
    search_fields = ['title']
    filterset_fields = ['featured', 'category']
    ordering_fields = ['price']

class CartsView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]
    

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
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    pagination_class = OrderPagination
    search_fields = ['user__username', 'delivery_crew__username']
    filterset_fields = ['status']
    ordering_fields = ['total', 'date',]


    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsCustomer()]
        if self.action in ['update', 'destroy']:
            return [IsAuthenticated(), IsManager()]
        if self.action == 'partial_update':
            return [IsAuthenticated(), IsManager() | IsDeliveryCrew()]
        
        return [IsAuthenticated()]
        
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
        
GROUP_NAME_MAP = {
    'manager': 'Manager',
    'delivery-crew': 'Delivery Crew',
}

class GroupManagementView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get_group(self, role):
        group_name = GROUP_NAME_MAP.get(role)
        if not group_name:
            return None
        return get_object_or_404(Group, name=group_name)

    def get(self, request, role):
        group = self.get_group(role)
        if not group:
            return Response(
                {"error": "Invalid role."},
                status=status.HTTP_404_NOT_FOUND
            )
        users = User.objects.filter(groups=group)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, role):
        group = self.get_group(role)
        if not group:
            return Response(
                {"error": "Invalid role."},
                status=status.HTTP_404_NOT_FOUND
            )
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)

        if user.groups.filter(name=group.name).exists():
            return Response(
                {"error": "User is already in this group."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.groups.add(group)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, role, pk):
        group = self.get_group(role)
        if not group:
            return Response(
                {"error": "Invalid role."},
                status=status.HTTP_404_NOT_FOUND
            )
        user = get_object_or_404(User, pk=pk)

        if not user.groups.filter(name=group.name).exists():
            return Response(
                {"error": "User does not belong to this group."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.groups.remove(group)
        return Response(
            {"message": f"{user.username} removed from {group.name}."},
            status=status.HTTP_200_OK
        )





    











