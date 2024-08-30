from django.utils import timezone
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from .models import CustomUser, FriendRequest
from .serializers import CustomUserSerializer, FriendRequestSerializer, RegisterSerializer, LoginSerializer, UserSerializer
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils.timezone import now, timedelta
from rest_framework import status, views

class UserSearchView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination
    pagination_class.page_size = 10
    serializer_class = UserSerializer  # Specify the serializer class

    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        if '@' in query:
            return CustomUser.objects.filter(email__iexact=query)
        return CustomUser.objects.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query))

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data})
    
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "User logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'password2')

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class SendFriendRequestView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        to_user_id = request.data.get('to_user_id')
        if not to_user_id:
            return Response({"error": "Missing 'to_user_id' parameter"}, status=status.HTTP_400_BAD_REQUEST)

        to_user = CustomUser.objects.get(id=to_user_id)

        one_minute_ago = now() - timedelta(minutes=1)
        sent_requests = FriendRequest.objects.filter(from_user=request.user, created_at__gte=one_minute_ago)
        if sent_requests.count() >= 3:
            return Response({"error": "You cannot send more than 3 friend requests per minute."},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)

        friend_request, created = FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
        if not created:
            return Response({"error": "Friend request already sent."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"success": "Friend request sent."}, status=status.HTTP_201_CREATED)

class RespondToFriendRequestView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        request_id = request.data.get('request_id')
        action = request.data.get('action')

        if not request_id or not action:
            return Response({"error": "Request ID and action are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            friend_request = FriendRequest.objects.get(id=request_id, to_user=request.user)
        except FriendRequest.DoesNotExist:
            return Response({"error": "Friend request not found."}, status=status.HTTP_404_NOT_FOUND)

        if action == 'accept':
            friend_request.is_accepted = True
            friend_request.accepted_at = timezone.now()
            friend_request.save()
            return Response({"success": "Friend request accepted."}, status=status.HTTP_200_OK)
        elif action == 'reject':
            friend_request.rejected_at = timezone.now()
            friend_request.delete()
            return Response({"success": "Friend request rejected."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)
        
class ListFriendsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CustomUser.objects.filter(
            Q(sent_requests__to_user=self.request.user, sent_requests__is_accepted=True) |
            Q(received_requests__from_user=self.request.user, received_requests__is_accepted=True)
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return Response({"friends": list(queryset.values('id', 'email', 'first_name', 'last_name'))})

class ListPendingRequestsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FriendRequest.objects.filter(to_user=self.request.user, is_accepted=False)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return Response({"pending_requests": list(queryset.values('id', 'from_user__id', 'from_user__email'))})
    

class ListUsers(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        users = CustomUser.objects.all()
        serializer = CustomUserSerializer(users, many=True)
        return Response(serializer.data)
    

class ListPendingFriendRequestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        print(f"Request User: {request.user}")

        try:
            pending_requests = FriendRequest.objects.filter(to_user=request.user, is_accepted=False)
            
            print("Pending Requests:")
            for req in pending_requests:
                print(f"ID: {req.id}, From User ID: {req.from_user.id}, To User ID: {req.to_user.id}, Is Accepted: {req.is_accepted}, Created At: {req.created_at}")

            serializer = FriendRequestSerializer(pending_requests, many=True)
            
            print("Serialized Data:")
            print(serializer.data)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error retrieving pending requests: {e}")
            return Response({"error": "An error occurred while retrieving pending requests."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
