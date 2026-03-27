from rest_framework import serializers
from .models import Review
from django.contrib.auth import get_user_model

User = get_user_model()


class ReviewerSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'full_name']


class ReviewSerializer(serializers.ModelSerializer):
    buyer          = ReviewerSerializer(read_only=True)
    is_mine        = serializers.SerializerMethodField()

    class Meta:
        model  = Review
        fields = [
            'id', 'buyer', 'rating', 'title', 'body',
            'seller_reply', 'seller_reply_at',
            'is_verified_purchase', 'helpful_count',
            'created_at', 'is_mine',
        ]

    def get_is_mine(self, obj):
        request = self.context.get('request')
        return request and request.user.id == obj.buyer_id


class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Review
        fields = ['rating', 'title', 'body']

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value


class SellerReplySerializer(serializers.Serializer):
    seller_reply = serializers.CharField(max_length=1000)


class ProductRatingSummarySerializer(serializers.Serializer):
    average_rating = serializers.FloatField()
    total_reviews  = serializers.IntegerField()
    stars          = serializers.DictField(child=serializers.IntegerField())
