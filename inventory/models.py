from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Customer(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    loyalty_points = models.IntegerField(default=0, null=True)

    def __str__(self):
        return self.user.first_name

class stock(models.Model):
    sku = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100, null=True)
    price = models.IntegerField(null=True)
    quantity = models.IntegerField(default=0, null=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    choices = (
        ('Card', 'Card'),
        ('Cash', 'Cash'),
    )
    customer = models.ForeignKey(Customer, null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    payment_method = models.CharField(max_length=100, choices=choices, null=True, default='Cash')
    complete = models.BooleanField(default=False)
    refund_status = models.BooleanField(default=False)
    loyalty_used = models.BooleanField(default=False)
    loyalty_points_user = models.IntegerField(default=0, null=True)

    @property
    def get_cart_total(self): 
        if self.loyalty_used:
            orderitems = self.orderitem_set.all()
            total = sum([item.get_total for item in orderitems])
            total -= (self.loyalty_points_user * 0.1)
            return total
        else:
            orderitems = self.orderitem_set.all()
            total = sum([item.get_total for item in orderitems])
            return total 

    @property
    def refundOrder(self):
        orderitems = self.orderitem_set.all()
        for item in orderitems:
            stock_inventory = stock.objects.get(sku=item.stock.sku)
            stock_inventory.quantity += item.quantity
            stock_inventory.save()
        self.refund_status = True
        self.save()
        return self.refund_status

    def __str__(self):
        return f"order #{str(self.id)}"


class orderItem(models.Model):
    stock = models.ForeignKey(stock, null=True, on_delete=models.SET_NULL)
    orderid = models.ForeignKey(Order, null=True, on_delete=models.SET_NULL)
    quantity = models.IntegerField(null=True, default=0)

    @property
    def get_total(self):
        total = self.stock.price * self.quantity
        return total
    
    def __str__(self):
        return f"{self.stock.name} | {self.orderid.customer}"
