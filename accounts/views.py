from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import PoliticianPicks
from research.models import Politician
from .serializers import RegisterSerializer, LoginSerializer, PoliticianPicksSerializer
from datetime import timedelta

class RegisterView(APIView):
    """
    API endpoint for user registration.
    """
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'User registered successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """
    API endpoint for user login.
    """
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(username=username, password=password)

            if user is not None:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': 'Login successful',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                    },
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AnonymousTokenView(APIView):
    """
    API endpoint for generating temporary anonymous tokens.
    These tokens expire after 24 hours and are used for initial visits
    where users can use the chat app without the need to login.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # Create a temporary token
        refresh = RefreshToken()

        # Set token expiration to 24 hours
        refresh.set_exp(lifetime=timedelta(hours=24))

        # Add a claim to identify this as an anonymous token
        refresh['is_anonymous'] = True

        return Response({
            'message': 'Temporary anonymous token generated successfully',
            'tokens': {
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_politician(request, politician_id):
    """Add a politician to the user's picks"""
    politician = get_object_or_404(Politician, pk=politician_id)
    
    # Get or create politician picks for the user
    picks, created = PoliticianPicks.objects.get_or_create(user=request.user)
    
    # Add the politician to user's picks
    picks.politicians.add(politician)
    
    serializer = PoliticianPicksSerializer(picks)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_politician(request, politician_id):
    """Remove a politician from the user's picks"""
    politician = get_object_or_404(Politician, pk=politician_id)
    
    try:
        picks = PoliticianPicks.objects.get(user=request.user)
        picks.politicians.remove(politician)
        
        serializer = PoliticianPicksSerializer(picks)
        return Response(serializer.data)
    except PoliticianPicks.DoesNotExist:
        return Response(
            {"detail": "No politician picks found for this user."}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_picks(request, user_id=None):
    """Get politician picks for a user"""
    if user_id and user_id != request.user.id:
        # Only allow viewing other users' picks if needed
        # You might want to add additional permission checks here
        user = get_object_or_404(User, pk=user_id)
    else:
        user = request.user
    
    try:
        picks = PoliticianPicks.objects.get(user=user)
        serializer = PoliticianPicksSerializer(picks)
        return Response(serializer.data)
    except PoliticianPicks.DoesNotExist:
        return Response({"politicians": []})
