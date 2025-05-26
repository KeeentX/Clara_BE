from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Chat, QandA
from .serializers import ChatSerializer, QandASerializer
from research.models import ResearchResult, Politician
from accounts.auth_utils import get_user_from_token

class ChatView(APIView):
    """
    API endpoint for creating and retrieving chats.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]  # Require authentication for all methods

    def post(self, request):
        """Create a new chat"""
        # Get politician and position from request data
        politician_name = request.data.get('politician')
        position = request.data.get('position', '')

        if not politician_name:
            return Response(
                {'error': 'Politician name is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get user from token
        user = request.user

        # Call the research API to get research report
        try:
            # Format the URL with the politician name and position as query param
            research_url = f"/research/{politician_name}/"
            if position:
                research_url += f"?position={position}"

            # Make the request to the research API
            # Since this is an internal API call, we'll use the Django view directly
            from research.views import research_politician
            from django.http import HttpRequest

            # Create a mock request
            mock_request = HttpRequest()
            mock_request.method = 'GET'
            mock_request.GET = {'position': position} if position else {}

            # Call the research view
            response = research_politician(mock_request, politician_name)

            # Get the research result ID from the response
            if hasattr(response, 'data') and 'id' in response.data:
                research_report_id = response.data['id']
                research_report = ResearchResult.objects.get(id=research_report_id)
            else:
                research_report = None

        except Exception as e:
            # If research API call fails, continue without research report
            research_report = None

        # Create the chat
        chat = Chat.objects.create(
            politician=politician_name,
            user=user,
            research_report=research_report
        )

        serializer = ChatSerializer(chat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        """Get all chats for the authenticated user with limit and offset"""
        # Get limit and offset from query parameters, with defaults
        limit = int(request.query_params.get('limit', 10))
        offset = int(request.query_params.get('offset', 0))

        # Get chats for the authenticated user with limit and offset
        chats = Chat.objects.filter(user=request.user)[offset:offset+limit]

        serializer = ChatSerializer(chats, many=True)
        return Response(serializer.data)


class TemporaryChatView(APIView):
    """
    API endpoint for retrieving temporary chats (no user_id).
    """
    permission_classes = [AllowAny]

    def get(self, request, chat_id=None):
        """Get a temporary chat by ID"""
        if not chat_id:
            return Response(
                {'error': 'Chat ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get the temporary chat (user_id is None)
            chat = Chat.objects.get(id=chat_id, user=None)
            serializer = ChatSerializer(chat)
            return Response(serializer.data)
        except Chat.DoesNotExist:
            return Response(
                {'error': 'Temporary chat not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class ChatDetailView(APIView):
    print("ChatDetailView")
    """
    API endpoint for retrieving, updating, and deleting a specific chat.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]  # Allow both authenticated and unauthenticated users

    def delete(self, request, chat_id):
        """Delete a chat"""
        try:
            chat = Chat.objects.get(id=chat_id)

            # Get user from token if available
            user = get_user_from_token(request)

            if user:
                # Authenticated user can only delete their own chats
                if chat.user != user:
                    return Response(
                        {'error': 'You can only delete your own chats'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            else:
                # Unauthenticated user can only delete temporary chats (user=None)
                if chat.user is not None:
                    return Response(
                        {'error': 'Authentication required to delete this chat'}, 
                        status=status.HTTP_401_UNAUTHORIZED
                    )

            # Delete the chat
            chat.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Chat.DoesNotExist:
            return Response(
                {'error': 'Chat not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class QuestionView(APIView):
    """
    API endpoint for creating questions and answers.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create a new question and answer"""
        chat_id = request.data.get('chat_id')
        question = request.data.get('question')

        if not chat_id or not question:
            return Response(
                {'error': 'Chat ID and question are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            chat = Chat.objects.get(id=chat_id)

            # Create a default answer
            answer = f"This is a default answer for your question: {question}"

            # Create the Q&A
            qanda = QandA.objects.create(
                chat=chat,
                question=question,
                answer=answer
            )

            serializer = QandASerializer(qanda)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Chat.DoesNotExist:
            return Response(
                {'error': 'Chat not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class ChatQandAView(APIView):
    """
    API endpoint for retrieving QandA sets for a specific chat.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, chat_id):
        """Get all QandA sets for a specific chat with limit and offset"""
        # Get limit and offset from query parameters, with defaults
        limit = int(request.query_params.get('limit', 10))
        offset = int(request.query_params.get('offset', 0))

        try:
            # Check if the chat exists and belongs to the authenticated user
            chat = Chat.objects.get(id=chat_id, user=request.user)

            # Get QandA sets for the chat with limit and offset
            qanda_sets = QandA.objects.filter(chat=chat)[offset:offset+limit]

            serializer = QandASerializer(qanda_sets, many=True)
            return Response(serializer.data)

        except Chat.DoesNotExist:
            return Response(
                {'error': 'Chat not found or you do not have permission to access it'}, 
                status=status.HTTP_404_NOT_FOUND
            )
