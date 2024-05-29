from django.db import IntegrityError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import MenuItem, Cart, Order
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.pagination import PageNumberPagination
from .serializers import *
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from .permissions import isManagerOrAdmin
from django.core.paginator import Paginator, EmptyPage
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
# Create your views here.

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def menu_items(request):
    #List all the menu items
    if request.method == 'GET':
        items = MenuItem.objects.select_related('category').all()
        category_name = request.query_params.get('category')
        to_price = request.query_params.get('to_price')
        search = request.query_params.get('search')
        ordering = request.query_params.get('ordering')
        perpage = request.query_params.get('perpage', default=100)
        page = request.query_params.get('page', default=1)
        if category_name:
            items = items.filter(category__title = category_name)
        if to_price:
            items = items.filter(price__lte=to_price)
        if search:
            items = items.filter(title__contains=search)
        if ordering:
            ordering_fields = ordering.split(',')
            items = items.order_by(*ordering_fields)
        paginator = Paginator(items, per_page=perpage)
        try:
            items = paginator.page(number=page)
        except EmptyPage:
            items = []    
        serialized_data = MenuItemSerializer(items, many=True, context={'request': request})
        return Response(serialized_data.data, status.HTTP_200_OK)
    #Add the new user with POST method
    if request.method == 'POST':
        user = request.user
        if user.groups.filter(name = 'Manager').exists():
            serialized_item = MenuItemSerializer(data = request.data)
            serialized_item.is_valid(raise_exception=True)
            serialized_item.save()
            return Response(serialized_item.validated_data, status.HTTP_201_CREATED)
        return Response({'detail':'You dont have permission to perform this action'}, status.HTTP_401_UNAUTHORIZED)
            
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def single_item(request, id):
    #List single menu item by id
    if request.method == 'GET':
        item = get_object_or_404(MenuItem, pk=id)
        serialized_item = MenuItemSerializer(item, context={'request': request})
        return Response(serialized_item.data, status.HTTP_200_OK)
    #Patch user by id
    if request.method == 'PATCH':
        user = request.user
        if user.groups.filter(name='Manager').exists() or user.is_superuser:
            if not request.data:
                return Response({'detail':'No data provided'}, status.HTTP_400_BAD_REQUEST)
            item = get_object_or_404(MenuItem, pk=id)
            serializer = MenuItemSerializer(item, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status.HTTP_200_OK)
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        return Response({'detail':'You dont have permission to perform this action'}, status.HTTP_401_UNAUTHORIZED)
    #Put user by id
    if request.method == 'PUT':
        user = request.user
        if user.groups.filter(name='Manager').exists() or user.is_superuser:
            item = get_object_or_404(MenuItem, pk=id)
            serializer = MenuItemSerializer(item, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status.HTTP_200_OK)
            return Response({'Error':serializer.errors}, status.HTTP_400_BAD_REQUEST)
        return Response({'detail':'You dont have permission to perform this action'}, status.HTTP_401_UNAUTHORIZED)
    #Delete user by id
    if request.method == 'DELETE':
        user = request.user
        if user.groups.filter(name='Manager').exists():
            item = get_object_or_404(MenuItem, pk=id)
            item.delete()
            return Response({'detail':'The object has been deleted'}, status.HTTP_200_OK)
        return Response({'detail':'You dont have permission to perform this action'}, status.HTTP_401_UNAUTHORIZED)   
    
@api_view(['GET','POST'])
@permission_classes([isManagerOrAdmin])
def managers(request):
    #List all the managers
    if request.method == 'GET':
        users = User.objects.filter(groups__name='Manager').values('username', 'email')
        return Response(users, status.HTTP_200_OK)   
    #Add user to manager group by POST method
    if request.method == 'POST':
        try:
            username = request.data['username']
            user = get_object_or_404(User, username=username)
            managers = Group.objects.get(name='Manager')
            managers.user_set.add(user)
            return Response({'message':'ok'},status.HTTP_201_CREATED)
        except:
             return Response({'message':'error'}, status.HTTP_400_BAD_REQUEST)
       
@api_view(['DELETE'])
@permission_classes([isManagerOrAdmin])    
#Remove user from manager group by id
def remove_manager(request, pk):
    user = get_object_or_404(User, pk=pk)
    managers = Group.objects.get(name='Manager')
    managers.user_set.remove(user)
    return Response({'message':'The user has been removed.'}, status.HTTP_200_OK)
    
@api_view(['GET','POST'])
@permission_classes([isManagerOrAdmin])
def delivery_crews(request):
    #List users in delivery crew group
    if request.method == 'GET':
        users = User.objects.filter(groups__name='Delivery Crew').values('username', 'email')
        return Response(users,status.HTTP_200_OK)
    #Add user to delivery crew group by POST method
    if request.method == 'POST':
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)
        managers = Group.objects.get(name='Delivery Crew')
        managers.user_set.add(user)
        return Response({'message':'ok'},status.HTTP_201_CREATED)

         
@api_view(['DELETE'])
@permission_classes([isManagerOrAdmin])
#Remove user from delivery crew group by id
def remove_delivery_crew(request, pk):
    user = get_object_or_404(User, pk=pk)
    delivery_crew = Group.objects.get(name='Delivery Crew')
    delivery_crew.user_set.remove(user)
    return Response({'message':'The user has been removed'}, status.HTTP_200_OK)

class CartViewSet(viewsets.ViewSet):
    permission_classes =[IsAuthenticated]
    #Get all menu items from cart for loggedin user
    def list(self, request):
        user = request.user
        queryset = Cart.objects.filter(user=user)
        serializer = CartSerializer(queryset, many=True)
        return Response(serializer.data)
    #Create cart with new menu item for loggedin user
    def create(self, request):
        cart_data = request.data.copy()
        cart_data['user_id'] = request.user.id 
        serializer = CartSerializer(data=cart_data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'The item has been added'})
        except IntegrityError:
            return Response({"error": "The combination of menu item and user already exists in the cart."}, status=status.HTTP_400_BAD_REQUEST)
    #Delete all the carts created by loggedin user
    def delete(self, request):
        carts = Cart.objects.filter(user_id=request.user_id)
        carts.delete()
        return Response({'message':'All menu items deleted'})
       
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = ['total', 'date']
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ['user__username']
    def list(self, request, *args, **kwargs):
        if request.user.groups.filter(name='Manager').exists() or request.user.is_superuser:
            orders = self.queryset
        elif request.user.groups.filter(name='Delivery Crew').exists():
            orders = Order.objects.filter(delivery_crew=request.user)
        else:
            orders = Order.objects.filter(user=request.user)

        #Apply ordering filter
        ordering = self.request.query_params.get('ordering')
        if ordering:
            ordering_fields = ordering.split(',')
            orders = orders.order_by(*ordering_fields)
        else:
            orders = orders.order_by('date')
            
        #Apply search filter
        search = self.request.query_params.get('search')
        if search:
            search_filter = SearchFilter()
            orders = search_filter.filter_queryset(self.request, orders, self)

        # Apply pagination
        paginator = PageNumberPagination()
        paginated_orders = paginator.paginate_queryset(orders, request)
        
        serializer = self.get_serializer(paginated_orders, many=True)
        return paginator.get_paginated_response(serializer.data)
    def create(self, request):
        user = request.user
        cart_items = Cart.objects.filter(user=user)
        #Check if cart is empty
        if not cart_items:
            return Response({'message':'Your cart is empty'},status.HTTP_400_BAD_REQUEST)     
        order_data = {
            'user_id' : request.user.id,
            'total': sum(cart_item.price for cart_item in cart_items)
           }
        order_serializer = OrderSerializer(data=order_data)
        order_serializer.is_valid(raise_exception=True)
        order_serializer.save()
        order = order_serializer.instance
        order_item_data = []
        for cart_item in cart_items:
            order_item_data.append({
                    'order': order.id,
                    'menuitem': cart_item.menuitem_id,
                    'quantity': cart_item.quantity,
                    'unit_price': cart_item.unit_price,
                    'price': cart_item.price
                })
        order_item_serializer = OrderItemSerializer(data=order_item_data, many=True)
        order_item_serializer.is_valid(raise_exception=True)
        order_item_serializer.save()
        #Delete all the items from cart
        cart_items.delete()
        return Response({'message':'Order created successfully.'}, status.HTTP_201_CREATED)
    def retrieve(self, request, pk=None):
        order = get_object_or_404(Order, id=pk)
        if request.user == order.user or request.user.groups.filter(name='Manager').exists() or request.user.is_superuser:
            serializer = OrderSerializer(order)
            return Response(serializer.data, status.HTTP_200_OK)
        return Response({'message':'cant access this order'},status.HTTP_403_FORBIDDEN)
    def patch(self, request, pk=None):
        order = get_object_or_404(Order, id=pk)
        if request.user.groups.filter(name='Manager').exists() or request.user.is_superuser:
            if not request.data.get('delivery_crew_id') and not request.data.get('status'):
                return Response({'error':'Not provided data for "delivery_crew_id" or "status" fields'}, status.HTTP_400_BAD_REQUEST)
            serializer = OrderSerializer(order, data=request.data, partial=True)
        elif request.user.groups.filter(name='Delivery Crew').exists():
             if order.delivery_crew != request.user:
                return Response({'message': 'You do not have permission to access this order'}, status=status.HTTP_401_UNAUTHORIZED)
             if 'status' not in request.data:
                return Response({'error': 'No data provided for "status" field'}, status=status.HTTP_400_BAD_REQUEST)
             serializer = OrderSerializer(order, data=request.data, partial=True)
        else:
            return Response({'detail':'You dont have permission to perform this action'}, status.HTTP_401_UNAUTHORIZED)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status.HTTP_200_OK)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk=None):
        if request.user.groups.filter(name='Manager').exists() or request.user.is_superuser:
            order = get_object_or_404(Order,id=pk)
            order.delete()
            return Response({'message':'Order successfully deleted'}, status.HTTP_200_OK)
        return Response({'detail':'You dont have permission to perform this action'}, status.HTTP_401_UNAUTHORIZED)
    
        
        
        
        
    
            
             