from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import connection
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core import serializers

import json
import re
from .models import *
from .forms import *
from .decorators import *
from .models import Order

crv = None

def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]

@unauthenticated
def home(request):
    return render(request, 'inventory/home.html')

@login_required(login_url='loginCash')
@allowed_users(allowed_roles=['cashier', 'owner'])
def stonk(request):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM inventory_stock")
    data = dictfetchall(cursor)
    return render(request, 'inventory/stock.html', {'data': data})

@login_required(login_url='loginCash')
@allowed_users(allowed_roles=['cashier', 'owner'])
def createStock(request):
    form = StockForm()
    if request.method == 'POST':
        form = StockForm(request.POST)
        if form.is_valid():
            form.save()
            return stonk(request)
    context = {'form': form}

    return render(request, 'inventory/stock_form.html', context)

@login_required(login_url='loginCash')
@allowed_users(allowed_roles=['cashier', 'owner'])
def updateStock(request, pk):
    stockObj = stock.objects.get(sku=pk)
    form = StockForm(instance=stockObj)
    if request.method == 'POST':
        form = StockForm(request.POST, instance=stockObj)
        if form.is_valid():
            form.save()
            return stonk(request)
    context = {'form': form}
    return render(request, 'inventory/stock_form.html', context)

@unauthenticated
def registerCust(request):
    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            Customer.objects.create(
                user = user,
                )
            username = form.cleaned_data.get('username')
            messages.success(request, 'Account was created successfully for ' + username)
            return redirect('loginCust')
    context = {'form': form}
    return render(request, 'inventory/registercust.html', context)

@unauthenticated
def registerCash(request):
    # if User().is_authenticated:
    #     return redirect('cashier')
    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            group = Group.objects.get(name='cashier')
            user.groups.add(group)
            username = form.cleaned_data.get('username')
            messages.success(request, 'Account was created successfully for ' + username)
            return redirect('loginCash')
    context = {'form': form}
    return render(request, 'inventory/registercash.html', context)

@unauthenticated
def registerOwner(request):
    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_superuser = True
            user.save()
            group = Group.objects.get(name='owner')
            user.groups.add(group)
            username = form.cleaned_data.get('username')
            messages.success(request, 'Account was created successfully for ' + username)
            return loginOwner(request)
    context = {'form': form}
    return render(request, 'inventory/registerowner.html', context)

@unauthenticated
def loginOwner(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('owner')
        else:
            messages.info(request, 'Username OR password is incorrect')
    return render(request, 'inventory/loginowner.html')

@unauthenticated
def loginCust(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('customer', pk=user.id)
        else:
            messages.info(request, 'Username OR password is incorrect')
    return render(request, 'inventory/logincust.html')

@unauthenticated
def loginCash(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return cashier(request)
        else:
            messages.info(request, 'Username OR password is incorrect')
    return render(request, 'inventory/logincash.html')

@login_required(login_url='loginOwner')
def Owner(request):
    # to show products
    product_cursor = connection.cursor()
    product_cursor.execute("SELECT * FROM inventory_stock")
    data = dictfetchall(product_cursor)
    skus = len(data)
    # to get orders
    order_cursor = connection.cursor()
    order_cursor.execute("SELECT count(*) FROM inventory_order")
    order_data = dictfetchall(order_cursor)[0]['count(*)']
    # unique customers
    customer_cursor = connection.cursor()
    customer_cursor.execute("SELECT count(*) FROM inventory_customer")
    customer_data = dictfetchall(customer_cursor)[0]['count(*)']
    # total sales
    orders_all = Order.objects.all()
    sales = 0
    for order_ in orders_all:
        sales += order_.get_cart_total
    # make context dict
    context = {'products': data, 'orders': order_data, 'customers': customer_data, 'sales': sales, 'skus': skus}
    return render(request, 'inventory/owner.html', context)

def logoutAny(request):
    logout(request)
    return home(request)

@login_required(login_url='loginCust')
def customer(request, pk):
    customer = Customer.objects.get(user_id=pk)
    cursor = connection.cursor()
    query = 'SELECT * FROM auth_user WHERE id = ' + pk
    cursor.execute(query)
    data = dictfetchall(cursor)
    try:
        order = Order.objects.filter(customer=customer.id)
        for ouda in order:
            items = ouda.orderitem_set.all()
        items = []
    except:
        items = []
    cotext = {'data': data, 'items': items, 'order': order, 'customer': customer}
    return render(request, 'inventory/customer.html', cotext)

@login_required(login_url='loginCash')
@allowed_users(allowed_roles=['cashier'])
def cashier(request, external_context=None):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM auth_user WHERE is_superuser = 0")
    product_cursor = connection.cursor()
    product_cursor.execute("SELECT * FROM inventory_stock")
    data = dictfetchall(cursor)    
    data_ = dictfetchall(product_cursor)
    context = {'customers': data, 'products': data_}
    if external_context:
        # get chosen customer's order history
        customer = crv[0]['id']
        customer = Customer.objects.get(user_id=customer)
        orders = Order.objects.filter(customer=customer, complete=1)
        context.update(external_context)
        context.update({'orders': orders})
    else:
        context.update({'chosen': crv})
    return render(request, 'inventory/cashier.html', context)

@login_required(login_url='loginCash')
def chooseCust(request, pk):
    cursor_0 = connection.cursor()
    query = 'SELECT * FROM auth_user WHERE id = ' + pk
    cursor_0.execute(query)
    data_0 = dictfetchall(cursor_0)
    external_context = {'chosen': data_0}
    global crv
    crv = data_0
    return cashier(request, external_context)

@login_required(login_url='loginCash')
# remove carts with incomplete status before choosing a new customer
def flushCart(request):
    try:
        incompleteOrders = Order.objects.filter(complete=0)
        for incompleteOrder in incompleteOrders:
            orderItem_ = orderItem.objects.filter(orderid=incompleteOrder)
            for oudaIteam in orderItem_:
                stock_inventory = stock.objects.get(sku=oudaIteam.stock.sku)
                stock_inventory.quantity += oudaIteam.quantity
                stock_inventory.save()
                oudaIteam.delete()
            incompleteOrder.delete()
    except:
        pass
    return cashier(request)

@login_required(login_url='loginCash')
@allowed_users(allowed_roles=['cashier'])
def cart(request):
    global crv
    if crv:
        customer = crv[0]['id']
        customer = Customer.objects.get(user_id=customer)
        order, created = Order.objects.get_or_create(customer=customer, complete=0)
        items = order.orderitem_set.all()
    else:
        items = []
        order = []
        customer = ""

    payment = PaymentMethodForm()
    loyalty = LoyaltyPointsForm()
    if request.method == 'POST':
        if 'points_to_use' in request.POST:
            points_to_use = int(request.POST['points_to_use'])
            if points_to_use > customer.loyalty_points:
                messages.info(request, 'You do not have enough points to use')
                return redirect('cart')
            else:
                customer.loyalty_points -= points_to_use
                customer.save()
                order.loyalty_used = True
                order.loyalty_points_user = points_to_use
                order.save()
                return redirect('cart')
        else:
            payment = PaymentMethodForm(request.POST)
            if payment.is_valid():
                payment.save()
                return checkout(request)
    context = {'items': items, 'customer': crv, 'order': order, 'payment': payment, 'customerObj': customer, 'loyalty': loyalty}
    return render(request, 'inventory/cart.html', context)

@login_required(login_url='loginCash')
def updateItem(request):
    data = json.loads(request.body)
    global crv
    productId = data['productId']
    action = data['action']
    customer = crv[0]['id']
    customer = Customer.objects.get(user_id=customer)
    product = stock.objects.get(sku=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    orderItem_, created = orderItem.objects.get_or_create(orderid=order, stock=product)
    if action == 'add':
        if stock.objects.get(sku=productId).quantity >= 1:
            stock_inventory = stock.objects.get(sku=productId)
            stock_inventory.quantity -= 1
            orderItem_.quantity = (orderItem_.quantity + 1)
    elif action == 'remove':
        stock_inventory = stock.objects.get(sku=productId)
        stock_inventory.quantity += 1
        stock_inventory.save()
        orderItem_.quantity = (orderItem_.quantity - 1)
    order.save()
    orderItem_.save()
    stock_inventory.save()
    if orderItem_.quantity <= 0:
        orderItem_.delete()
    return JsonResponse('Item was added', safe=False)

@login_required(login_url='loginCash')
def checkout(request):
    global crv
    customer = crv[0]['id']
    customer = Customer.objects.get(user_id=customer)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    items = order.orderitem_set.all()
    order.complete = True
    order.total_price = order.get_cart_total
    if order.loyalty_used:
        customer.loyalty_points += order.get_cart_total - order.loyalty_points_user
    else:
        customer.loyalty_points += order.get_cart_total
    order.save()
    customer.save()
    return cashier(request)
    
@login_required(login_url='loginCash')
def refund(request, pk):
    order_ = Order.objects.get(id=pk)
    status = order_.refundOrder
    return cashier(request)


def change_password(request):
    if request.method == 'POST':
        form = Password_Change_Form(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            password = user.password
            messages.success(request, 'Your password was successfully updated!')
            if request.user.groups.filter(name='customer').exists():
                return redirect('loginCust')
            elif request.user.groups.filter(name='cashier').exists():
                return redirect('loginCash')
            elif request.user.groups.filter(name='owner').exists():
                return redirect('loginOwner')
            else:
                return redirect('home')
        else:
            messages.info(request, 'Please correct the error below.')
            
    else:
        form = Password_Change_Form(request.user)
    return render(request, 'inventory/change_password.html', {
        'form': form
    })
    
#add search functionality in cashier page to search for a customer
def search_cust(request):
    if request.GET.get('search_cust'):
        searched = request.GET.get('search_cust')
        try:
            customers = Customer.objects.filter(user__first_name__contains=searched)
            pk = customers.values_list('user_id', flat=True)
            return redirect('chooseCust', pk=pk[0])
        except:
            pass
        
    return render(request, 'inventory/cashier.html')
