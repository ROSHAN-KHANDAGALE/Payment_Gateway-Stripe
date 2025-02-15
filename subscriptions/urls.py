from django.urls import path
from .views import *

# Create your urls here
urlpatterns = [
    path("stripe-success", SuccessTemplateView.as_view(), name="stripe_success"),
    path("stripe-cancel", CancelTemplateView.as_view(), name="stripe_cancel"),
    path("product-list", StripProductListView.as_view(), name="product_list"),
    path("user-subscriptions", SubscriptionByUserView.as_view(), name="user_subscriptions"),
    path("user-subscription-information/<int:user_id>", ProductsByUserIDView.as_view(),name="user_subscription_information"),
    path("update-subscription-price", SubscriptionPriceUpdate.as_view(), name="update_subscription_price"),
    path("multi-community-subscription", MultiCommunitySubscriptionAndSave.as_view(), name="multi_community_subscription"),
    path("subscription-cancelation", SubscriptionPlanCancellationView.as_view(), name="subscription_cancelation"),
    path("trial-subscription", FreeTrialSubscription.as_view(), name="trial_subscription"),
    path("revenue-subscription", ProductRevenueView.as_view(), name="revenue_subscription"),
    path("webhook", stripe_webhook, name="webhook"),
]