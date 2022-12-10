from django.http import HttpResponse
from django.shortcuts import redirect
from django import template


def unauthenticated(view_func):
	def wrapper_func(request, *args, **kwargs):
		if request.user.is_authenticated and request.user.groups.filter(name='customer').exists():
			return redirect('customer', request.user.id)
		if request.user.is_authenticated and request.user.groups.filter(name='cashier').exists():
			return redirect('cashier')
		else:
			return view_func(request, *args, **kwargs)
	return wrapper_func

def allowed_users(allowed_roles=[]):
	def decorator(view_func):
		def wrapper_func(request, *args, **kwargs):

			group = None
			if request.user.groups.exists():
				group = request.user.groups.all()[0].name

			if group in allowed_roles:
				return view_func(request, *args, **kwargs)
			else:
				return HttpResponse('You are not authorized to view this page')
		return wrapper_func
	return decorator

# def admin_only(view_func):
# 	def wrapper_function(request, *args, **kwargs):
# 		group = None
# 		if request.user.groups.exists():
# 			group = request.user.groups.all()[0].name

# 		if group == 'customer':
# 			return redirect('customer')
		
# 		if group == 'cashier':
# 			return redirect('cashier')

# 		if group == 'admin':
# 			return view_func(request, *args, **kwargs)

# 	return wrapper_function

# def unauthenticated_cust(view_func):
# 	def wrapper_func(request, *args, **kwargs):
# 		if request.user.is_authenticated:
# 			return redirect('customer')
# 		else:
# 			return view_func(request, *args, **kwargs)

# 	return wrapper_func

# def unauthenticated_cash(view_func):
#     def wrapper_func(request, *args, **kwargs):
#         if request.user.is_authenticated:
#             return redirect('cashier')
#         else:
#             return view_func(request, *args, **kwargs)

#     return wrapper_func