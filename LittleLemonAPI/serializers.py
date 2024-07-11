from rest_framework import serializers
from .models import MenuItem, Cart, Order, OrderItem, Category
from rest_framework.validators import UniqueTogetherValidator
from django.contrib.auth.models import User, Group


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['title', 'slug']


class MenuItemSerializer (serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ('title', 'price', 'featured', 'category')

    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='title',
    )


class CartSerializer (serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['user', 'menuitem', 'quantity', 'unit_price', 'price']


class OrderSerializer (serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )


class OrderItemSerializer (serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username']



