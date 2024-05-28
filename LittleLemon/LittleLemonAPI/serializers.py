import datetime
from decimal import Decimal
from rest_framework import serializers
from .models import MenuItem, Category, Cart, Order, OrderItem
from rest_framework.validators import UniqueValidator
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']

class RequirableBooleanField(serializers.BooleanField):
    default_empty_html = serializers.empty

class MenuItemSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=255, validators=[UniqueValidator(queryset=MenuItem.objects.all())])
    price = serializers.DecimalField(max_digits=6, min_value=0.1, decimal_places=2)
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    featured = RequirableBooleanField(required=True)
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category', 'category_id']
        depth = 1

    def validate_category_id(self, value):
        if not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError("Category with the given ID does not exist.")
        return value

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')
        
class CartSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.IntegerField(write_only=True)
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    price = serializers.SerializerMethodField(method_name='calculate_price')
    class Meta:
        model = Cart
        fields = ['user_id', 'menuitem', 'quantity', 'unit_price', 'price', 'menuitem_id']
        depth = 1  
    def calculate_price(self, cart):
        result = cart.unit_price * cart.quantity
        result = round(Decimal(result),2)
        return result
    
    def validate_menuitem_id(self, value):
        try:
            MenuItem.objects.get(id=value)
        except ObjectDoesNotExist:
            raise serializers.ValidationError('MenuItem with this id does not exists.')
        return value
       
    def create(self, validated_data):
        menuitem = MenuItem.objects.get(id=validated_data['menuitem_id'])
        unit_price = menuitem.price
        quantity = validated_data['quantity']
        price = unit_price*quantity
        validated_data['unit_price'] = unit_price
        validated_data['price']= price
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'menuitem_id' in validated_data:
            menuitem = MenuItem.objects.get(id=validated_data['menuitem_id'])
            validated_data['unit_price'] = menuitem.price
        return super().update(instance, validated_data)
    
class OrderItemSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(queryset = Order.objects.all(), write_only=True)
    title = serializers.CharField(source='menuitem.title', read_only=True)
    menuitem = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all(), write_only=True)
    class Meta:
        model=OrderItem
        fields = ['order','menuitem','title','quantity','unit_price','price']
    
    
class OrderSerializer(serializers.ModelSerializer):
    delivery_crew = UserSerializer(read_only=True)
    delivery_crew_id = serializers.IntegerField(write_only=True)
    user_id = serializers.IntegerField(write_only=True)
    status = serializers.BooleanField(default=0)
    total = serializers.DecimalField(max_digits=6, decimal_places=2,)
    date = serializers.DateField(read_only=True)
    order_items = OrderItemSerializer(many=True, source='orderitem_set', read_only=True)
     
    class Meta:
        model = Order
        fields = ['delivery_crew', 'user_id','status', 'total', 'date', 'order_items', 'delivery_crew_id']
         
    def create(self, validated_data):
        validated_data['date'] = datetime.date.today()
        return super().create(validated_data)
    
    def validate_delivery_crew_id(self, value):
        try:
            # Check if a User object with the provided ID exists in the database
            user = User.objects.get(pk=value)
        except User.DoesNotExist:
            # If the User object does not exist, raise a validation error
            raise serializers.ValidationError("Delivery crew with this ID does not exist.")
        return value



    