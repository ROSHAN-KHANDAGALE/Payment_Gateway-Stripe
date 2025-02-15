import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True


class Users(AbstractUser, BaseModel):
    USER_ROLE_CHOICES = [
        ('Admin', "Admin"),
        ('User', "User")
    ]
    
    username = None 
    role = models.CharField(max_length=10, choices=USER_ROLE_CHOICES)
    first_name = models.CharField(max_length=255, null=True, blank=True) 
    last_name = models.CharField(max_length=255, null=True, blank=True)  
    email = models.EmailField(max_length=255, null=True, blank=True, unique=True)
    password = models.CharField(max_length=255, null=True, blank=True) 
    phone_number = models.CharField(max_length=255, null=True, blank=True) 
    address = models.TextField(null=True, blank=True)
    zipcode = models.CharField(max_length=255, null=True, blank=True) 
    city = models.CharField(max_length=255, null=True, blank=True) 
    state = models.CharField(max_length=255, null=True, blank=True) 
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    
    REQUIRED_FIELDS = [ 'password',]
    USERNAME_FIELD = 'email'
    
    def __str__(self):
        return self.email


class Subscription(BaseModel):
    status_choices = [("active", "Active"), ("canceled", "Canceled"), ("paid", "Paid")]

    product_id = models.CharField(max_length=255)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="user_subscriptions")
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)
    trial_end_date = models.DateTimeField(null=True, blank=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=50, choices=status_choices)

    def __str__(self):
        return f"Subscription {self.stripe_subscription_id} - {self.payment_status}"
