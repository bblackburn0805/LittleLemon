from datetime import datetime, date
from decimal import Decimal
from urllib import request

from django.core.paginator import EmptyPage, Paginator
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from .customPaginator import CustomPagination
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.decorators import throttle_classes
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, CartSerializer, OrderSerializer, CategorySerializer, \
    UserSerializer

"""
    ----------------------------------
    http://127.0.0.1:8000/api/category
    -------------------------------------
"""


@throttle_classes([UserRateThrottle, AnonRateThrottle])
class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


"""
    ----------------------------------
    http://127.0.0.1:8000/api/menu-items
    -------------------------------------
"""
@throttle_classes([UserRateThrottle, AnonRateThrottle])
class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    pagination_class = CustomPagination
    ordering_fields = ['title', 'featured', 'category',]
    filterSet_fields = ['category',]
    search_fields = ['category', 'price']

    def post(self, request, *args, **kwargs):
        if not is_manager(request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)
        item = MenuItemSerializer(data=request.data)
        if item.is_valid():
            item.save()
        return Response(item.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        if not is_manager(request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = MenuItemSerializer(data=request.data)
        if serializer.is_valid():
            menu_item = MenuItem.objects.get(pk=self.kwargs.get('pk'))
            menu_item.title = serializer.data['title']
            menu_item.price = serializer.data['price']
            menu_item.featured = serializer.data['featured']
            menu_item.category = Category.objects.get(title=serializer.data['category'])
            menu_item.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        if not is_manager(request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)
        menu_item = MenuItem.objects.get(pk=self.kwargs.get('pk'))
        menu_item.delete()
        return Response({"message": "Menu Item deleted."}, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        menu_item = MenuItem.objects.get(pk=self.kwargs.get('pk'))
        if request.data.get('title'):
            menu_item.title = request.data.get('title')
        if request.data.get('price'):
            menu_item.price = request.data.get('price')
        if request.data.get('featured'):
            menu_item.featured = request.data.get('featured')
        if request.data.get('category'):
            menu_item.category = Category.objects.get(title=request.data.get('category'))
        menu_item.save()
        return Response({"message": "Menu Item patched."}, status=status.HTTP_200_OK)


"""
    ----------------------------------
    http://127.0.0.1:8000/api/cart/menu-items
    -------------------------------------
"""
@api_view(['POST', 'GET', 'DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def cart(request):
    if request.method == 'GET':
        queryset = Cart.objects.all().filter(user=request.user)
        serializer_class = CartSerializer(queryset, many=True)
        return Response(serializer_class.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        user = User.objects.get(username=request.user)
        menuitem = MenuItem.objects.get(title=request.data['menuitem'])
        quantity = request.data['quantity']
        unit_price = menuitem.price
        price = Decimal(menuitem.price) * Decimal(quantity)

        Cart.objects.create(
            user=user, menuitem=menuitem, quantity=quantity,
            unit_price=unit_price, price=price
        )
        return Response({"message": "New cart item created"}, status=status.HTTP_201_CREATED)

    elif request.method == 'DELETE':
        cartItems = Cart.objects.all().filter(user=request.user)
        for cartItem in cartItems:
            cartItem.delete()
        return Response({"message": "Cart items deleted."}, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
    ----------------------------------
    http://127.0.0.1:8000/api/groups/manager/users
    -------------------------------------
"""
@api_view(['GET', 'POST', 'DELETE'])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def managers(request):
    if not is_manager(request.user):
        return Response(status=status.HTTP_403_FORBIDDEN)

    managers = Group.objects.get(name='Manager')

    if request.method == 'GET':
        serializer = UserSerializer(managers.user_set.all(), many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    if request.method == 'POST':
        user = get_object_or_404(User, username=request.data['username'])
        managers.user_set.add(user)
        return Response({"message": "User added to manager group."}, status.HTTP_200_OK)

    if request.method == 'DELETE':
        user = get_object_or_404(User, username=request.data['username'])
        managers.user_set.remove(user)
        return Response({"message": "User removed from manager group."}, status.HTTP_200_OK)


"""
    ----------------------------------
    http://127.0.0.1:8000/api/manager/users/1
    -------------------------------------
"""
@api_view(['GET', 'DELETE'])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def single_manager(request, id):
    if not is_manager(request.user):
        return Response({"message": "Not a Manager"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.get(username=id):
        user = User.objects.get(username=id)
        managers = Group.objects.get(name='Manager')

        if request.method == 'GET':
            return Response(UserSerializer(User.objects.get(username=id)).data)

        if request.method == 'DELETE':
            managers.user_set.remove(user)
            return Response({"message": "ok"}, status.HTTP_200_OK)

    else:
        return Response(status=status.HTTP_404_NOT_FOUND)


"""
    ----------------------------------
    http://127.0.0.1:8000/api/delivery-crew/users
    -------------------------------------
"""
@api_view(['GET', 'POST'])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def delivery_crew(request):
    if not is_manager(request.user):
        return Response(status=status.HTTP_403_FORBIDDEN)

    delivery_crew = Group.objects.get(name='Delivery')

    if request.method == 'GET':
        serializer = UserSerializer(delivery_crew.user_set.all(), many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    if request.method == 'POST':
        user = get_object_or_404(User, username=request.data['username'])
        delivery_crew.user_set.add(user)
        return Response({"message": "User added to delivery group."}, status.HTTP_200_OK)
"""
    ----------------------------------
    http://127.0.0.1:8000/api/delivery-crew/users/1
    -------------------------------------
"""


@api_view(['GET', 'DELETE'])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def single_delivery_crew(request, id):
    if not is_manager(request.user):
        return Response({"message": "Not a Manager"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.get(username=id):
        user = User.objects.get(username=id)
        delivery_crew = Group.objects.get(name='Delivery')

        if request.method == 'GET':
            return Response(UserSerializer(User.objects.get(username=id)).data)

        if request.method == 'DELETE':
            delivery_crew.user_set.remove(user)
            return Response({"message": "ok"}, status.HTTP_200_OK)

    else:
        return Response(status=status.HTTP_404_NOT_FOUND)


"""
    ----------------------------------
    http://127.0.0.1:8000/api/delivery
    -------------------------------------
"""
@api_view(['POST', 'DELETE'])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def assign_delivery(request):
    if not is_manager(request.user):
        return Response({"message": "Not a Manager"}, status=status.HTTP_400_BAD_REQUEST)

    if request.data.get('order'):
        orderID = request.data['order']
        username = request.data['username']
        order = Order.objects.get(pk=orderID)
        delivery_crew = User.objects.get(username=username)
        if request.method == 'POST':
            order.delivery_crew = delivery_crew
            order.save()
            return Response({"message": "User assigned to this order's delivery crew"}, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            order.delivery_crew = None
            order.save()
            return Response({"message": "Delivery crew removed"}, status=status.HTTP_200_OK)

    elif request.data.get('username'):
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)
        delivery_crew = Group.objects.get(name='Delivery')
        if request.method == 'POST':
            delivery_crew.user_set.add(user)
        elif request.method == 'DELETE':
            delivery_crew.user_set.remove(user)
        return Response({"message": "User assigned to Delivery group"}, status=status.HTTP_200_OK)


"""
    ----------------------------------
    http://127.0.0.1:8000/api/featured
    -------------------------------------
"""
@api_view(['POST', 'GET'])
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def featured(request):
    if request.method == 'GET':
        queryset = MenuItem.objects.filter(featured=True)
        serializer_class = MenuItemSerializer(queryset, many=True)
        return Response(serializer_class.data, status=status.HTTP_200_OK)

    if not is_manager(request.user):
        return Response({"message": "Not a Manager"}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'POST':
        current_featured = MenuItem.objects.filter(featured=True)
        for item in current_featured:
            item.featured = False
            item.save()

        item_title = request.data['title']

        if item_title:
            item = MenuItem.objects.get(title=item_title)
            item.featured = True
            item.save()
            return Response({"message": "Featured item updated"}, status.HTTP_200_OK)

    return Response({"message": "error"}, status.HTTP_400_BAD_REQUEST)


"""
    ----------------------------------
    http://127.0.0.1:8000/api/orders
    -------------------------------------
"""
@throttle_classes([UserRateThrottle, AnonRateThrottle])
class OrdersViewSet(generics.ListAPIView):
    serializer_class = OrderSerializer
    pagination_class = CustomPagination
    serializer = OrderSerializer
    queryset = Order.objects.all()
    ordering_fields = ['user', 'delivery_crew', 'status', 'date']
    filterSet_fields = ['user', 'delivery_crew', 'status', 'date']
    search_fields = ['user', 'delivery_crew', 'status', 'date']

    managers = Group.objects.get(name='Manager')
    delivery_crew = Group.objects.get(name='Delivery')

    def get(self, request, *args, **kwargs):
        user = request.user
        user_groups = user.groups.all()

        if user_groups.contains(self.managers):
            self.queryset = Order.objects.all()
            self.serializer = OrderSerializer(self.queryset, many=True)
            # return Response(serializer.data, status=status.HTTP_200_OK)

        elif user_groups.contains(self.delivery_crew):
            self.queryset = self.queryset.filter(delivery_crew=user)
            self.serializer = OrderSerializer(self.queryset, many=True)
            # return Response(serializer.data, status=status.HTTP_200_OK)

        # --- User is a customer  --- #
        else:
            self.queryset = self.queryset.filter(user=user)
            self.serializer = OrderSerializer(self.queryset, many=True)
            # return Response(serializer.data, status=status.HTTP_200_OK)
        return self.get_paginated_response(
            self.paginate_queryset(self.serializer.data))

    def post(self, request, *args, **kwargs):
        user = request.user
        print("----------------here-----------------------")
        cart = Cart.objects.all().filter(user=user)
        total = Decimal(0.0)

        for item in cart:
            orderItem = OrderItem.objects.create(
                order=user, menuitem=item.menuitem, quantity=item.quantity,
                unit_price=item.unit_price, price=item.price
            )

            total = total + Decimal(orderItem.price)
            orderItem.save()
            item.delete()

        newOrder = Order.objects.create(
            user=user, total=total, date=date.today()
        )
        newOrder.save()
        return Response({"message": "Order items created"}, status=status.HTTP_200_OK)


"""
    ----------------------------------
    http://127.0.0.1:8000/api/orders/1
    -------------------------------------
"""
@throttle_classes([UserRateThrottle, AnonRateThrottle])
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def single_order(request, id):
    user = request.user
    managers = Group.objects.get(name='Manager')
    delivery_crew = Group.objects.get(name='Delivery')
    user_groups = user.groups.all()
    order = Order.objects.get(pk=id)

    if request.method == 'GET':
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        if user_groups.contains(managers):
            order.delivery_crew = request.data['delivery_crew']
            order.status = request.data['status']
            order.save()
            return Response({"message": "Order put"}, status=status.HTTP_200_OK)

        # -- Purposely leaving customer out. The customer should not be able to
        #   edit an order once it's been placed. They can call to edit/delete
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    elif request.method == 'PATCH':
        if user_groups.contains(managers):
            if request.data.get('delivery_crew'):
                order.delivery_crew = request.data['delivery_crew']
            if request.data.get('status'):
                order.status = request.data['status']
            order.save()
            return Response({"message": "Order patched"}, status=status.HTTP_200_OK)

        elif user_groups.contains(delivery_crew):
            order.status = request.data['status']
            order.save()
            return Response({"message": "Order patched"}, status=status.HTTP_200_OK)

        # -- Purposely leaving customer out. The customer should not be able to
        #   edit an order once it's been placed. They can call to edit/delete
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    elif request.method == 'DELETE':
        if not user_groups.contains(managers):
            return Response(status=status.HTTP_403_FORBIDDEN)
        order.delete()
        return Response({"message": "Order deleted"}, status=status.HTTP_200_OK)



@throttle_classes([UserRateThrottle, AnonRateThrottle])
@api_view(['POST'])
def register_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')

    newUser = User.objects.create_user(
        username=username,
        password=password,
        email=email
    )
    newUser.save()
    return Response({"message": "User created"}, status=status.HTTP_201_CREATED)


@throttle_classes([UserRateThrottle, AnonRateThrottle])
@api_view(['POST'])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')


"""
    ------------------------------
    Custom functions for DRY
    -----------------------------
"""
def is_manager(user):
    if user.groups.contains(Group.objects.get(name='Manager')) or user.is_superuser:
        return True
    return False


def is_delivery(user):
    if user.groups.contains(Group.objects.get(name='Delivery')) or user.is_superuser:
        return True
    return False
