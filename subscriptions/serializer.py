from rest_framework import serializers
from .models import Subscription
from .models import CommunityInformation
from rest_framework import serializers
from django.core.exceptions import ValidationError
from uuid import UUID
from .models import Subscription

# Create your serializers here.
class SubscriptionPlanSerializer(serializers.ModelSerializer):
    product_id = serializers.CharField(required=True)
    community_id = serializers.ListField(child=serializers.CharField(), required=True)
    user_id = serializers.IntegerField(required=True)

    class Meta:
        model = Subscription
        fields = ["product_id", "community_id", "user_id"]

    def validate(self, data):
        return data
