from django.urls import path
from . import views

urlpatterns = [
    path('menu-items/', views.menu_items),
    path('menu-items/<int:id>', views.single_item),
    path('groups/manager/users', views.managers),
    path('groups/manager/users/<int:pk>', views.remove_manager),
    path('groups/delivery_crew/users', views.delivery_crews),
    path('groups/delivery_crew/users/<int:pk>', views.remove_delivery_crew),
    path('cart/menu-items', views.CartViewSet.as_view({'get':'list', 'post':'create','delete':'delete'})),
    path('orders', views.OrderViewSet.as_view({'get':'list','post':'create'})),
    path('orders/<int:pk>', views.OrderViewSet.as_view({'get':'retrieve','patch':'patch'}))  
]