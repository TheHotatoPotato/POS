from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('stock/', views.stonk, name='stock'),
    path('create_stock/', views.createStock, name='create_stock'),
    path('update_stock/<str:pk>/', views.updateStock, name='update_stock'),
    path('registerCust/', views.registerCust, name='registerCust'),
    path('registerCash/', views.registerCash, name='registerCash'),
    path('loginCust/', views.loginCust, name='loginCust'),
    path('loginCash/', views.loginCash, name='loginCash'),
    path('logout/', views.logoutAny, name='logout'),
    path('cashier/', views.cashier, name='cashier'),
    path('cashier/<str:pk>', views.chooseCust, name='chooseCust'),
    path('customer/<str:pk>', views.customer, name='customer'),
    path('update_item/', views.updateItem, name='update_item'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('refund/<str:pk>', views.refund, name='refund'),
    path('flushCart/', views.flushCart, name='flush'),
    path('owner/', views.Owner, name='owner'),
    path('loginOwner/', views.loginOwner, name='loginOwner'),
    path('registerOwner/', views.registerOwner, name='registerOwner'),
    path('change_password/', views.change_password, name='change_password'),
    path('search_cust/', views.search_cust, name='search_cust'),
]