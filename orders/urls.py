from django.urls import path
from . import views
from .views import *
urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('order_complete/', views.order_complete, name='order_complete'),
    path('payment/success/', CheckoutSuccessView.as_view(), name='success'),
]
 