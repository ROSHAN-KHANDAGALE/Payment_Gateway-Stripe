from datetime import datetime, timedelta
from django.utils import timezone
import json
import uuid
import stripe
from rest_framework.response import Response
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, pagination
from rest_framework.views import APIView
from subscriptions import utils, constants
from .models import ClaimCommunityRequest, Users
from .serializer import *
from.models import Subscription
from rest_framework.permissions import IsAuthenticated


# Create your views here.
stripe.api_key = settings.STRIPE_SECRET_KEY


class CustomPagination(pagination.PageNumberPagination):
    """
    A Custome Pagination for Search Filters
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# Template API to show success page
class SuccessTemplateView(APIView):
    """
    Template API to show success page
    """

    def get(self, request):
        return render(request, "../templates/Payment-Template/success.html")


# Template API to show Cancel page
class CancelTemplateView(APIView):
    """
    Template API to show cancel page
    """

    def get(self, request):
        return render(request, "../templates/Payment-Template/cancel.html")


"""
GET() To fetch all Avalailable Products and POST() Payment Gateway API
"""
class StripProductListView(APIView):
    permission_classes = [IsAuthenticated]
    """
    API to Retrieve List of all the available products in Stripe
    """

    def get(self, request, *args, **kwargs):
        try:
            products = stripe.Product.list()

            product_data = []

            for product in products.auto_paging_iter():
                if product.default_price:
                    try:
                        default_price = stripe.Price.retrieve(product.default_price)
                        product_info = {
                            "id": product.id,
                            "name": product.name,
                            "description": product.description,
                            "metadata": {
                                "Type": product.metadata
                            },
                            "default_price": {
                                "id": default_price.id,
                                "unit_amount": default_price.unit_amount / 100,
                                "currency": default_price.currency,
                                "recurring": default_price.recurring,
                            },
                        }
                    except stripe.error.StripeError as e:
                        return utils.error_response(
                            message=constants.MESSAGES["STRIPE_ERROR"],
                            errors=str(e),
                            status_code=status.HTTP_400_BAD_REQUEST,
                        )
                else:
                    product_info = {
                        "id": product.id,
                        "name": product.name,
                        "description": product.description,
                        "default_price": None,
                    }

                product_data.append(product_info)

            return utils.success_response(
                message=constants.MESSAGES["PRODUCT_RETRIVED"],
                data=product_data,
                status_code=status.HTTP_200_OK,
                api_status_code=status.HTTP_200_OK,
            )

        except stripe.error.StripeError as e:
            return utils.error_response(
                message=constants.MESSAGES["STRIPE_ERROR"],
                errors=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return utils.error_response(
                message=constants.MESSAGES["UNEXPECTED_ERROR"],
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    """
    POST API to initialize the stripe Payment gateway service.
    """
    def post(self, request, *args, **kwargs):
        try:
            product_id = request.data.get("product_id")
            user_email = request.data.get("user_email")
            user_name = request.data.get("user_name")

            if not product_id or not user_email or not user_name:
                return utils.error_response(
                    message=constants.MESSAGES["FIELDS_MISSING"],
                    errors=constants.MESSAGES["REQUIRED_FIELDS"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            try:
                product = stripe.Product.retrieve(product_id)
                if not product:
                    return utils.error_response(
                        message=constants.MESSAGES["PRODUCT_NOT_FOUND"],
                        errors=constants.MESSAGES["PRODUCT_ID_MISSING"],
                        status_code=status.HTTP_404_NOT_FOUND,
                    )
            except stripe.error.StripeError as e:
                return utils.error_response(
                    message=constants.MESSAGES["STRIPE_ERROR"],
                    errors=str(e),
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            if product.default_price:
                try:
                    default_price = stripe.Price.retrieve(product.default_price)
                except stripe.error.StripeError as e:
                    return utils.error_response(
                        message=constants.MESSAGES["STRIPE_ERROR"],
                        errors=str(e),
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

                # Payment Session 
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    line_items=[
                        {
                            "price": default_price.id,
                            "quantity": 1,
                        }
                    ],
                    mode="subscription",
                    success_url="http://localhost:8000/stripe-success",
                    cancel_url="http://localhost:8000/stripe-cancel",
                    customer_email=user_email,
                )

                return utils.success_response(
                    message=constants.MESSAGES["SESSION_GENERATED"],
                    data=checkout_session.url,
                    status_code=status.HTTP_200_OK,
                    api_status_code=status.HTTP_200_OK,
                )

            else:
                return utils.error_response(
                    message=constants.MESSAGES["PRICE_FIELD_NOT_FOUND"],
                    errors=constants.MESSAGES["PRICE_NOT_FOUND"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        except stripe.error.StripeError as e:
            return utils.error_response(
                message=constants.MESSAGES["STRIPE_ERROR"],
                errors=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return utils.error_response(
                message=constants.MESSAGES["UNEXPECTED_ERROR"],
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


"""
To fetch All Available Customer's List
"""
class CustomerListView(APIView):
    permission_classes = [IsAuthenticated]
    
    """
    API to Retrieve All Available Customer's List from stripe
    """

    def get(self, request, *args, **kwargs):
        try:
            customers = stripe.Customer.list()

            customer_data = []

            for customer in customers.auto_paging_iter():
                customer_info = {
                    "id": customer.id,
                    "email": customer.email,
                    "name": customer.name,
                }

                customer_data.append(customer_info)

            return utils.success_response(
                message=constants.MESSAGES["CUSTOMER_FOUND"],
                data=customer_data,
                status_code=status.HTTP_200_OK,
                api_status_code=status.HTTP_200_OK,
            )
        except stripe.error.StripeError as e:
            return utils.error_response(
                message=constants.MESSAGES["STRIPE_ERROR"],
                errors=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class SubscriptionByUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    """
    API view to retrieve all products purchased by customers with relevant details.
    Supports search by customer name or product name.
    """

    def get(self, request):
        try:
            search_query = request.GET.get("search", "").lower().strip()

            customers = stripe.Customer.list(limit=50)

            if not customers.data:
                return utils.error_response(
                    message=constants.MESSAGES["CUSTOMER_NOT_FOUND"],
                    errors=constants.MESSAGES["UNAVAILABLE_CUSTOMERS"],
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            customer_data = []

            for customer in customers["data"]:
                customer_name = customer.get("name", "N/A")

                subscriptions = stripe.Subscription.list(customer=customer["id"], limit=10)

                for sub in subscriptions["data"]:
                    for item in sub["items"]["data"]:
                        product = stripe.Product.retrieve(item["plan"]["product"]) 
                        product_name = product.get("name", "Unknown Product")

                        if search_query and search_query not in customer_name.lower() and search_query not in product_name.lower():
                            continue 

                        customer_data.append({
                            "customer_name": customer_name,
                            "product_name": product_name,
                            "purchased_date": sub["created"],
                            "amount_paid": item["price"]["unit_amount"] / 100,  
                            "currency": item["price"]["currency"],
                        })

            paginator = CustomPagination()
            paginated_data = paginator.paginate_queryset(customer_data, request)

            return paginator.get_paginated_response(paginated_data)

        except Exception as e:
            return utils.error_response(
                message=constants.MESSAGES["UNEXPECTED_ERROR"],
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SubscriptionPriceUpdate(APIView):
    permission_classes = [IsAuthenticated]
    
    """
    API view to update the price of a subscription for a product.
    """
    def put(self, request, *args, **kwargs):
        product_id = request.data.get("product_id")
        new_price = request.data.get("price")
        interval = request.data.get("interval", "month")
 
        if not product_id or not new_price:
            return utils.error_response(
                message="Product ID and price are required.",
                errors="Missing product ID or price.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            # Retrieve the product by ID
            product = stripe.Product.retrieve(product_id)
 
            if not product:
                return utils.error_response(
                    message=constants.MESSAGES["PRODUCT_NOT_FOUND"],
                    errors=constants.MESSAGES["PRODUCT_ID_MISSING"],
                    status_code=status.HTTP_404_NOT_FOUND,
                )
 
            # Step 1: Create a new price for the product
            new_price_obj = stripe.Price.create(
                unit_amount=int(new_price * 100),  # Convert price to cents
                currency="usd",
                product=product.id,
                recurring={"interval": interval},
            )
 
            new_price_id = new_price_obj.id  # This is the new price ID
 
            # Step 2: Set the new price as the default price for the product
            stripe.Product.modify(
                product_id,
                default_price=new_price_id,
            )
 
            # Step 3: Update all active subscriptions to use the new price
            subscriptions = stripe.Subscription.list(limit=100, expand=["data.items"])
 
            updated_subscriptions = []
 
            for subscription in subscriptions.auto_paging_iter():
                for item in subscription["items"]["data"]:
                    if item["price"]["product"] == product.id:
                        # Update the subscription to use the new price
                        updated_subscription = stripe.Subscription.modify(
                            subscription.id,
                            items=[{
                                "id": item.id,
                                "price": new_price_id, 
                            }],
                        )
 
                        updated_subscriptions.append(updated_subscription.id)

            return utils.success_response(
                message="Subscription price for the product updated successfully.",
                data=updated_subscription,
                status_code=status.HTTP_200_OK,
                api_status_code=status.HTTP_200_OK,
            )
 
        except stripe.error.StripeError as e:
            return utils.error_response(
                message=f"Stripe Error: {str(e)}",
                errors=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

class ProductsByUserIDView(APIView):
    permission_classes = [IsAuthenticated]
    
    """
    API view to retrieve all products purchased by a customer using user ID.
    """

    def get(self, request, user_id):
        try:
            # Fetch user from database
            user = Users.objects.filter(id=user_id).first()

            if not user:
                return utils.error_response(
                    message=constants.MESSAGES["USER_NOT_FOUND"],
                    errors="User ID does not exist.",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            user_email = user.email

            # Search for the customer in Stripe by email
            customers = stripe.Customer.list(email=user_email).get("data", [])

            if not customers:
                return utils.error_response(
                    message=constants.MESSAGES["CUSTOMER_NOT_FOUND"],
                    errors="No customer found with this email in Stripe.",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            # Use the first customer found
            customer_id = customers[0]["id"]

            # Retrieve subscriptions for this customer
            subscriptions = stripe.Subscription.list(customer=customer_id).get("data", [])

            if not subscriptions:
                return utils.error_response(
                    message="No active subscriptions found",
                    errors="This customer does not have any active subscriptions.",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            product_data = []

            # Loop through each subscription to get product details
            for subscription in subscriptions:
                for item in subscription["items"]["data"]:
                    product_id = item["price"]["product"]
                    product = stripe.Product.retrieve(product_id)

                    product_info = {
                        "subscription_id": subscription["id"],
                        "product_id": product["id"],
                        "product_name": product.get("name", "N/A"),
                        "product_description": product.get("description", "N/A"),
                        "product_type": product.get("type", "N/A"),
                        "quantity": item.get("quantity", 1),
                        "price_amount": item["price"]["unit_amount"] / 100,  # Convert to dollars
                        "currency": item["price"]["currency"].upper(),
                        "interval": item["price"].get("recurring", {}).get("interval", "none"),
                    }

                    product_data.append(product_info)

            return utils.success_response(
                message="Products retrieved successfully",
                data=product_data,
                status_code=status.HTTP_200_OK,
                api_status_code=status.HTTP_200_OK,
            )

        except stripe.error.InvalidRequestError as e:
            return utils.error_response(
                message="Invalid request to Stripe",
                errors=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        except stripe.error.RateLimitError:
            return utils.error_response(
                message="Stripe API rate limit exceeded",
                errors="Too many requests to Stripe. Please try again later.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        except stripe.error.StripeError as e:
            return utils.error_response(
                message="Stripe API Error",
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            return utils.error_response(
                message="Unexpected error occurred",
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MultiCommunitySubscriptionAndSave(APIView):
    permission_classes = [IsAuthenticated]
    
    """
    API to create a subscription for multiple selected Community.
    """
    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        product_ids = request.data.get("product_id")
        community_ids = request.data.get("community_id")

        if not user_id or not product_ids or not community_ids:
            return utils.error_response(
                message=constants.MESSAGES["MISSING_FIELDS"],
                errors=constants.MESSAGES["FIELDS_NOT_AVAILABLE"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure product_ids is a list (split by commas if necessary)
        if isinstance(product_ids, str):
            product_ids = product_ids.split(",")

        if not isinstance(product_ids, list):
            return utils.error_response(
                message=constants.MESSAGES["INVALID_ID_FORMAT"],
                errors=constants.MESSAGES["INVALID_PRODUCT_IDS_FORMAT"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Validate community_ids as UUIDs
        try:
            community_uuids = [str(uuid.UUID(community_id)) for community_id in community_ids]
        except ValueError:
            return utils.error_response(
                message=constants.MESSAGES["INVALID_UUID"],
                errors=constants.MESSAGES["INVALID_UUID_FORMAT"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch valid community objects
        communities = ClaimCommunityRequest.objects.filter(
            claim_for_community_id_id__in=community_uuids,
            status__in=['accept', 'pending']
        )

        if communities.count() != len(community_uuids):
            return utils.error_response(
                message=constants.MESSAGES["SUBSCRIPTION_ERROR"],
                errors=constants.MESSAGES["SUBSCRIPTION_ERROR"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            # Fetch user instance
            user_instance = Users.objects.get(id=user_id)
            user_email = user_instance.email  

            # Calculate total price based on number of communities
            line_items = []
            for product_id in product_ids:
                product_id = product_id.strip()
                try:
                    product = stripe.Product.retrieve(product_id)
                    if product.default_price:
                        default_price = stripe.Price.retrieve(product.default_price)
                        price_per_unit = default_price.unit_amount
                        total_price = price_per_unit * len(communities)

                        line_items.append({
                            "price_data": {
                                "currency": "usd",
                                "product": product.id,
                                "unit_amount": total_price,
                                "recurring": {"interval": "month"}
                            },
                            "quantity": 1
                        })
                    else:
                        return utils.error_response(
                            message=constants.MESSAGES["PRICE_FIELD_NOT_FOUND"],
                            errors=constants.MESSAGES["PRICE_NOT_FOUND"],
                            status_code=status.HTTP_400_BAD_REQUEST,
                        )

                except stripe.error.StripeError as e:

                    return utils.error_response(
                        message=constants.MESSAGES["STRIPE_API_ERROR"],
                        errors=str(e),
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            # Create the Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=line_items,
                mode="subscription",
                metadata={
                    'user_id': str(user_id),
                    'community_id': json.dumps(community_uuids),  
                    'product_id': json.dumps(product_ids),
                },
                success_url="https://meanstack.smartdatainc.com:9287/stripe-success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url="http://localhost:8003/payment/stripe-cancel",
                customer_email=user_email,
            )

            return utils.success_response(
                message=constants.MESSAGES["SESSION_GENERATED"],
                data={
                    "checkout_session": checkout_session.url,
                    "user_id": user_id,
                    "product_id": product_ids,
                    "community_id": community_ids,
                },
                status_code=status.HTTP_200_OK,
                api_status_code=status.HTTP_200_OK,
            )

        except Exception as e:            
            return utils.error_response(
                message=constants.MESSAGES["STRIPE_ERROR"],
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

"""
Stripe Webhook Handler for Subscription Payment Gateway 
"""
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.WEBHOOK_SECRET

    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        event_type = event["type"]
        event_data = event["data"]["object"]

        if event_type == "checkout.session.completed":
            session_id = event_data.get("id")
            subscription_id = event_data.get("subscription")
            payment_status = event_data.get("payment_status", "unknown")
            amount_total = event_data.get("amount_total", 0) / 100 
            metadata = event_data.get("metadata", {})
            trial_end_date = event_data.get("trial_end_date") # This is a Unix timestamp
 
            # If trial_end is present, convert it to a datetime object
            if trial_end_date:
                trial_end_date = datetime.fromtimestamp(trial_end_date)
 
            if not metadata:
                return JsonResponse({"status": "error", "message": "Missing metadata"}, status=400)
            
            if not metadata:
                return JsonResponse({"status": "error", "message": "Missing metadata"}, status=400)

            try:
                community_ids = json.loads(metadata.get("community_id", "[]"))
            except json.JSONDecodeError:
                return JsonResponse({"status": "error", "message": "Invalid community_id format"}, status=400)

            user_id = metadata.get("user_id")

            try:
                product_ids = json.loads(metadata.get("product_id", "[]"))
            except json.JSONDecodeError:
                return JsonResponse({"status": "error", "message": "Invalid product_id format"}, status=400)


            if not community_ids or not user_id:
                return JsonResponse({"status": "error", "message": "Missing community_id or user_id"}, status=400)

            # Validate and fetch community objects
            try:
                community_uuid_list = [uuid.UUID(cid) for cid in community_ids]
            except ValueError:
                return JsonResponse({"status": "error", "message": "Invalid UUID in community_id"}, status=400)

            communities = ClaimCommunityRequest.objects.filter(claim_for_community_id_id__in=community_uuid_list)
            user = Users.objects.filter(id=user_id).first()

            if not user:
                return JsonResponse({"status": "error", "message": "User not found"}, status=400)

            if communities.count() != len(community_uuid_list):
                return JsonResponse({"status": "error", "message": "One or more communities not found"}, status=400)

            # Store or update subscription details for each community
            if subscription_id:
                for community in communities:
                    community_info_instance = CommunityInformation.objects.filter(
                        id=community.claim_for_community_id_id
                    ).first()

                    if not community_info_instance:
                        continue

                    for product_id in product_ids:
                        subscription, created = Subscription.objects.update_or_create(
                            stripe_subscription_id=subscription_id,
                            community=community_info_instance,
                            user=user,
                            product_id=product_id.strip(),
                            defaults={
                                "payment_status": payment_status,
                                "payment_amount": amount_total / len(communities),
                                "trial_end_date" : trial_end_date
                            }
                        )

            return JsonResponse({"status": "success"}, status=200)


        return JsonResponse({"status": "success"}, status=200)

    except Exception as e:
        return JsonResponse({"status": "error", "message": "Unexpected error", "details": str(e)}, status=500)


class SubscriptionPlanCancellationView(APIView):
    permission_classes = [IsAuthenticated]
    
    """
    GET METHOD FOR SUBSCRIPTION Plan Fetching
    """
    def get(self, request, *args, **kwargs):
        stripe_subscription_plan = stripe.Subscription.list(limit=10)
        
        filtered_data = [
            {
                "id": sub["id"],
                "object": sub["object"],
                "billing_cycle_anchor": sub["billing_cycle_anchor"],
                "cancel_at_period_end": sub["cancel_at_period_end"],
                "collection_method": sub["collection_method"],
                "created": sub["created"],
                "currency": sub["currency"],
                "current_period_end": sub["current_period_end"],
                "current_period_start": sub["current_period_start"],
                "customer": sub["customer"],
                "default_payment_method": sub.get("default_payment_method"),
                "items": {
                    "object": sub["items"]["object"],
                    "data": [
                        {
                            "id": item["id"],
                            "object": item["object"],
                            "created": item["created"],
                            "plan": {
                                "id": item["plan"]["id"],
                                "object": item["plan"]["object"],
                                "active": item["plan"]["active"],
                                "billing_scheme": item["plan"]["billing_scheme"],
                                "created": item["plan"]["created"],
                                "currency": item["plan"]["currency"],
                                "interval": item["plan"]["interval"],
                                "interval_count": item["plan"]["interval_count"],
                                "livemode": item["plan"]["livemode"],
                                "product": item["plan"]["product"],
                                "usage_type": item["plan"]["usage_type"],
                            },
                            "price": {
                                "id": item["price"]["id"],
                                "object": item["price"]["object"],
                                "active": item["price"]["active"],
                                "billing_scheme": item["price"]["billing_scheme"],
                                "created": item["price"]["created"],
                                "currency": item["price"]["currency"],
                                "livemode": item["price"]["livemode"],
                                "product": item["price"]["product"],
                                "recurring": item["price"]["recurring"],
                                "tax_behavior": item["price"].get("tax_behavior"),
                                "type": item["price"]["type"],
                                "unit_amount": item["price"]["unit_amount"],
                                "unit_amount_decimal": item["price"]["unit_amount_decimal"],
                            },
                            "quantity": item["quantity"],
                            "subscription": item["subscription"],
                        }
                        for item in sub["items"]["data"]
                    ],
                    "total_count": sub["items"]["total_count"],
                    "url": sub["items"]["url"],
                },
                "plan": {
                    "id": sub["plan"]["id"],
                    "object": sub["plan"]["object"],
                    "active": sub["plan"]["active"],
                    "billing_scheme": sub["plan"]["billing_scheme"],
                    "created": sub["plan"]["created"],
                    "currency": sub["plan"]["currency"],
                    "interval": sub["plan"]["interval"],
                    "interval_count": sub["plan"]["interval_count"],
                    "livemode": sub["plan"]["livemode"],
                    "product": sub["plan"]["product"],
                    "usage_type": sub["plan"]["usage_type"],
                },
                "quantity": sub["quantity"],
                "start_date": sub["start_date"],
                "status": sub["status"],
                "trial_settings": sub["trial_settings"],
            }
            for sub in stripe_subscription_plan["data"]
        ]

        return utils.success_response(
            message=constants.MESSAGES["SUBSCRIPTION_PLAN_FETCHED"],
            data=filtered_data,
            status_code=status.HTTP_200_OK,
            api_status_code=status.HTTP_200_OK,
        )
                
    
    """
    POST METHOD FOR Subscription Plan Cancellation
    """
    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        subscription_id = request.data.get("subscription_id")

        if not user_id or not subscription_id:
            return utils.error_response(
                message=constants.MESSAGES["MISSING_FIELDS"],
                errors="User ID and Subscription ID are required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch user email from User table
        user = Users.objects.filter(id=user_id).first()

        if not user:
            return utils.error_response(
                message=constants.MESSAGES["USER_NOT_FOUND"],
                errors="User id does not exists",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        user_email = user.email 
            
        try:
            customers = stripe.Customer.list(email=user_email).get("data", [])
            
            if not customers:
                return utils.error_response(
                    message=constants.MESSAGES["CUSTOMER_NOT_FOUND"],
                    errors="Customer not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            
            customer = customers[0]
            
            subscription = stripe.Subscription.retrieve(subscription_id)

            if subscription["customer"] != customer["id"]:
                return utils.error_response(
                    message=constants.MESSAGES["INVALID_SUBSCRIPTION_ID"],
                    errors="Subscription does not belong to this user",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
                
            stripe.Subscription.delete(subscription_id)
            
            return utils.success_response(
                message=constants.MESSAGES["SUBSCRIPTION_CANCELLATION_SUCCESS"],
                data=None,
                status_code=status.HTTP_200_OK,
                api_status_code=status.HTTP_200_OK,
            )
        except stripe.error.InvalidRequestError as e:
            return utils.error_response(
                message=constants.MESSAGES["STRIPE_ERROR"],
                errors=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except stripe.error.StripeError as e:
            return utils.error_response(
                message=constants.MESSAGES["STRIPE_API_ERROR"],
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return utils.error_response(
                message=constants.MESSAGES["UNEXPECTED_ERROR"],
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FreeTrialSubscription(APIView):
    
    """
    API to create a free trial subscription for multiple selected Communities.
    """
    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        product_ids = request.data.get("product_id")
        community_ids = request.data.get("community_id")
 
        if not user_id or not product_ids or not community_ids:
            return utils.error_response(
                message=constants.MESSAGES["MISSING_FIELDS"],
                errors=constants.MESSAGES["FIELDS_NOT_AVAILABLE"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
 
        # Ensure product_ids is a list (split by commas if necessary)
        if isinstance(product_ids, str):
            product_ids = product_ids.split(",")
 
        if not isinstance(product_ids, list):
            return utils.error_response(
                message=constants.MESSAGES["INVALID_PRODUCT_ID_FORMAT"],
                errors=constants.MESSAGES["INVALID_ID_FORMAT"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
    
        # Validate community_ids as UUIDs
        try:
            community_uuids = [str(uuid.UUID(community_id)) for community_id in community_ids]
        except ValueError:
            return utils.error_response(
                message=constants.MESSAGES["INVALID_UUID"],
                errors=constants.MESSAGES["INVALID_UUID_FORMAT"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            
        # Fetch valid ClaimCommunityRequest objects with accepted or pending status
        claim_requests = ClaimCommunityRequest.objects.filter(
            claim_for_community_id_id__in=community_uuids,
            status__in=['accept', 'pending']  # Only accept or pending status
        )
 
        # Check if all the community_ids have valid claim requests with accepted or pending status
        valid_community_uuids = list(claim_requests.values_list('claim_for_community_id_id', flat=True))
 
        # If the number of valid communities doesn't match the input, return an error
        if len(valid_community_uuids) != len(community_uuids):
            invalid_communities = set(community_uuids) - set(valid_community_uuids)
            return utils.error_response(
                message=constants.MESSAGES["INVALID_COMMUNITY_STATUS"],
                errors=f"Communities with IDs {invalid_communities} are not in a valid state (accepted or pending).",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
 
        try:
            # Fetch user instance
            user_instance = Users.objects.get(id=user_id)
            user_email = user_instance.email  
 
            # Check if the user already has an active free trial for any of the communities
            active_free_trial_subscriptions = Subscription.objects.filter(
                user=user_instance,
                payment_status="paid",
                community__id__in=valid_community_uuids,
                trial_end_date__gt=timezone.now() 
            )
 
            if active_free_trial_subscriptions.exists():
                return utils.error_response(
                    message=constants.MESSAGES["ALREADY_ACTIVE_FREE_TRIAL"],
                    errors="Cannot purchase multiple free trials for the same community",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
 
            # Check if all the products have a default price of 0 (for free trial)
            line_items = []
            for product_id in product_ids:
                product_id = product_id.strip()
                try:
                    product = stripe.Product.retrieve(product_id)
                    if product.default_price:
                        default_price = stripe.Price.retrieve(product.default_price)
                        price_per_unit = default_price.unit_amount
 
                        # Ensure the price is zero for a free trial
                        if price_per_unit != 0:
                            return utils.error_response(
                                message=constants.MESSAGES["THIS_PRODUCT_IS_NOT_FREE"],
                                errors="Ensure you are using a free trial product.",
                                status_code=status.HTTP_400_BAD_REQUEST,
                            )
                            
                        # Add line item for the subscription
                        line_items.append({
                            "price_data": {
                                "currency": "usd",
                                "product": product.id,
                                "unit_amount": price_per_unit,  
                                "recurring": {"interval": "month"}
                            },
                            "quantity": 1
                        })
                    else:
                        return utils.error_response(
                            message=constants.MESSAGES["THIS_PRODUCT_IS_NOT_FREE"],
                            errors="Ensure you are using a free trial product.",
                            status_code=status.HTTP_400_BAD_REQUEST,
                        )
 
                except stripe.error.StripeError as e:
                    return utils.error_response(
                        message=constants.MESSAGES["STRIPE_API_ERROR"],
                        errors=str(e),
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
                    
            trial_end_date = timezone.now() + timedelta(days=30)
            # Create the Stripe subscription session with free trial
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=line_items,
                mode="subscription",
                metadata={
                     'user_id': str(user_id),
                     'community_id': json.dumps([str(community_uuid) for community_uuid in valid_community_uuids]),
                     'product_id': json.dumps(product_ids),
                     'trial_end_date':str(trial_end_date)
                     
                     },
 
                success_url="http://localhost:8003/payment/stripe-success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url="http://localhost:8003/payment/stripe-cancel",
                customer_email=user_email,
            )
            
            return utils.success_response(
                message=constants.MESSAGES["SESSION_GENERATED"],
                data={"session_url": checkout_session.url},
                status_code=status.HTTP_200_OK,
                api_status_code=status.HTTP_200_OK
            )
 
        except Exception as e:
            return utils.error_response(
                message=constants.MESSAGES["UNEXPECTED_ERROR"],
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ProductRevenueView(APIView):
    """
    API to calculate total price collection for each product in Stripe.
    """

    def get(self, request):
        try:
            # Get search query parameters (if provided)
            search_state = request.GET.get("Search_State", "").lower().strip()
            search_service = request.GET.get("Search_Service", "").lower().strip()
            search_product = request.GET.get("Search_Product", "").lower().strip()
            search_month = request.GET.get("Search_Month", "").lower().strip()
            search_year = request.GET.get("Search_Year", "").lower().strip()

            product_revenue = {}

            # Fetch all subscriptions (limit to avoid overload)
            subscriptions = stripe.Subscription.list(limit=100)

            for sub in subscriptions["data"]:
                for item in sub["items"]["data"]:
                    price = item["price"]
                    product_id = price["product"]

                    # Fetch product details
                    product = stripe.Product.retrieve(product_id)
                    product_name = product.get("name", "Unknown Product")
                    currency = price["currency"]
                    purchased_date = sub["created"]  # UNIX timestamp

                    # Convert date to readable format for filtering
                    from datetime import datetime

                    purchase_date = datetime.utcfromtimestamp(purchased_date)
                    purchase_month = str(purchase_date.month)
                    purchase_year = str(purchase_date.year)

                    total_price = (price["unit_amount"] / 100) * item["quantity"]

                    # Apply search filters
                    if (
                        (not search_product or search_product in product_name.lower()) and
                        (not search_month or search_month == purchase_month) and
                        (not search_year or search_year == purchase_year)
                    ):
                        if product_id in product_revenue:
                            product_revenue[product_id]["total_revenue"] += total_price
                        else:
                            product_revenue[product_id] = {
                                "product_name": product_name,
                                "total_revenue": total_price,
                                "currency": currency,
                            }

            # Convert dictionary to list format
            revenue_data = list(product_revenue.values())

            # Apply Pagination
            paginator = CustomPagination()
            paginated_data = paginator.paginate_queryset(revenue_data, request)
            # success response data
            return paginator.get_paginated_response(
                {
                    "message": constants.MESSAGES["REVENUE_CALCULATED"],
                    "data": paginated_data,
                }
            )

        except Exception as e:
            return utils.error_response(
                message=constants.MESSAGES["UNEXPECTED_ERROR"],
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            
            