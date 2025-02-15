from django.contrib import admin
from .models import Subscription

# Register your models here.
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_id', 'community', 'user', 'stripe_subscription_id', 'trial_end_date', 'payment_amount', 'payment_status')
    list_filter = ('payment_status', 'community', 'user')
    search_fields = ('stripe_subscription_id', 'community__name', 'user__email')
    
admin.site.register(Subscription, SubscriptionAdmin)
