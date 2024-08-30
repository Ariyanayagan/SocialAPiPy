from django.urls import path
from .views import ListFriendsView, ListPendingFriendRequestsView, ListPendingRequestsView, ListUsers, LogoutView, RegisterView, LoginView, RespondToFriendRequestView, SendFriendRequestView, UserProfileView, UserSearchView  
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),  # This should match /api/login/
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_reset_confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('search-users/', UserSearchView.as_view(), name='search_users'),
    path('send-friend-request/', SendFriendRequestView.as_view(), name='send_friend_request'),
    path('respond-friend-request/', RespondToFriendRequestView.as_view(), name='respond_friend_request'),
    path('friends/', ListFriendsView.as_view(), name='list_friends'),
    path('pending-requests/', ListPendingRequestsView.as_view(), name='pending_requests'),
    path('users/', ListUsers.as_view(), name='list_users'),
    path('pending-friend-requests/', ListPendingFriendRequestsView.as_view(), name='list_pending_friend_requests'),
]
