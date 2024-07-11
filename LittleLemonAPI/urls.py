from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('menu-items/', views.MenuItemViewSet.as_view({'get': 'list'})),
    path('menu-items/<int:pk>', views.MenuItemViewSet.as_view({'get': 'retrieve'})),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('cart/menu-items', views.cart, name='cart'),
    path('category', views.CategoriesView.as_view(), name='category'),
    path('featured', views.featured, name='featured'),
    path('delivery', views.assign_delivery, name='delivery'),
    path('groups/manager/users', views.managers),
    path('groups/manager/users/<str:id>', views.single_manager),
    path('groups/delivery-crew/users', views.delivery_crew),
    path('groups/delivery-crew/users/<str:id>', views.single_delivery_crew),
    path('orders', views.OrdersViewSet.as_view()),
    path('orders/<int:id>', views.single_order),
    path('register', views.register_user),
]
