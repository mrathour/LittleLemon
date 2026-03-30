# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import MenuItem, Category, Cart, OrderItem, Order


class CategorySerializer(serializers.ModelSerializer):

    class Meta :
        model = Category
        fields = '__all__'

class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset = Category.objects.all(), 
        source = 'category', 
        write_only = True
    )

    class Meta :
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category', 'category_id']


class CartMenuItemSerializer(serializers.ModelSerializer):

    class Meta :
        model = MenuItem
        fields = ['id', 'title']

class CartSerializer(serializers.ModelSerializer):
    menuitem = serializers.PrimaryKeyRelatedField(
        queryset = MenuItem.objects.all(),
        write_only = True
    )

    menuitem_details = CartMenuItemSerializer(
        source = 'menuitem',
        read_only= True
    )

    unit_price = serializers.DecimalField(
        max_digits=6, decimal_places=2, read_only=True
    )

    price = serializers.DecimalField(
        max_digits=6, decimal_places=2, read_only=True
    )

    class Meta:
        model = Cart
        fields = [
            'id',
            'menuitem',         # write-only → accepts ID on POST
            'menuitem_details',  # read-only  → returns {id, title, price}
            'quantity',
            'unit_price',
            'price'
        ]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Quantity must be at least 1."
            )
        return value
        
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "menuitem", "quantity", "unit_price", "price"]

class OrderSerializer(serializers.ModelSerializer):
    orderitems = OrderItemSerializer( source='items', many=True, read_only=True )

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')

        # Guard against missing request context
        if not request:
            return fields

        if not request.user.groups.filter(name='Manager').exists():
            fields.pop('user', None)

        return fields
    
    class Meta:
        model = Order
        fields = [
            'id',
            'user',          
            'delivery_crew',
            'status',
            'total',
            'date',
            'orderitems'     
        ]

class UserSerializer(serializers.ModelSerializer):
    
    class meta:
        User = get_user_model
        model = User
        fields = ['username','email','name']
    
