from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Politician, ResearchResult
from .services.pipeline_service import ResearchPipeline
from .serializers import PoliticianSerializer, ResearchResultSerializer
from django.utils import timezone
from datetime import timedelta
import json
import logging

# Set up logger
logger = logging.getLogger("Research View")

@csrf_exempt
@require_http_methods(["GET", "POST"])
@api_view(['GET', 'POST'])
def research_politician(request, name):
    """
    API endpoint to research a politician by name.
    
    GET: Retrieve existing research if available
    POST: Force a new research to be conducted
    
    Additional query parameters:
    - position: Filter by position (e.g., "Senator", "Mayor")
    - max_age: Maximum age of cached results in days (default: 7)
    - include_sources: Whether to include sources in response (default: False)
    - detailed: Whether to return detailed results (default: False)
    """
    logger.info(f"Research request for politician: {name}")
    
    # Get parameters from query string
    position = request.GET.get('position', '')

    if not position:
        logger.error("Position parameter is required but not provided.")
        return Response({
            'success': False,
            'error': "Position parameter is required."
        }, status=400)

    max_age = int(request.GET.get('max_age', 7))
    include_sources = request.GET.get('include_sources', '').lower() == 'true'
    detailed = request.GET.get('detailed', '').lower() == 'true'
    
    # Normalize name for search
    normalized_name = name.strip().lower()
    logger.info(f"Parameters: position={position}, max_age={max_age}, include_sources={include_sources}, detailed={detailed}")

    try:
        # Try to find the politician in the database
        try:
            # Find politician by name only
            politician = Politician.objects.get(name__iexact=normalized_name)
            logger.info(f"Found politician in database: {politician.name}")
            
            # Check if we have recent research for this politician and position
            latest_research = None
            try:
                if position:
                    # Filter by both politician and position
                    latest_research = ResearchResult.objects.filter(
                        politician=politician,
                        position__iexact=position
                    ).order_by('-created_at').first()
                else:
                    # Get the latest research for this politician regardless of position
                    latest_research = ResearchResult.objects.filter(
                        politician=politician
                    ).order_by('-created_at').first()
            except Exception as e:
                logger.error(f"Error retrieving latest research: {str(e)}")
            
            force_refresh = request.method == 'POST'
            current_time = timezone.now()
            
            if (latest_research and 
                current_time - latest_research.created_at < timedelta(days=max_age) and 
                not force_refresh):
                # Use existing research
                logger.info(f"Using existing research (age: {(current_time - latest_research.created_at).days} days)")
                research_result = latest_research
            else:
                # Conduct new research
                logger.info(f"Conducting new research for {politician.name}, position: {position}")
                pipeline = ResearchPipeline()
                research_result = pipeline.research_politician(politician.name, position)
                
        except Politician.DoesNotExist:
            # Politician not found, conduct new research
            logger.info(f"Politician not found in database, conducting new research")
            pipeline = ResearchPipeline()
            research_result = pipeline.research_politician(normalized_name, position)
        
        # Handle different result types
        if isinstance(research_result, ResearchResult):
            # Result is a ResearchResult model instance
            logger.info(f"Processing ResearchResult model instance")
            serializer = ResearchResultSerializer(research_result)
            response_data = serializer.data
            
            # Process response according to parameters
            if not include_sources and 'sources' in response_data:
                del response_data['sources']
                            
            # Add metadata
            response_data['metadata'] = {
                'is_fresh': (timezone.now() - research_result.created_at).days < max_age,
                'age_days': (timezone.now() - research_result.created_at).days,
                'request_method': request.method
            }
            
            return Response(response_data)
            
        elif isinstance(research_result, dict):
            # Result is a dictionary (error case or partial results)
            logger.info(f"Processing dictionary result")
            if 'error' in research_result:
                # Error case
                response_data = {
                    'success': False,
                    'error': research_result.get('error', 'An unknown error occurred'),
                }
                if 'content_list' in research_result:
                    response_data['content_list'] = [
                        {'url': item.get('url', ''), 'title': item.get('title', '')} 
                        for item in research_result.get('content_list', [])
                    ]
                return Response(response_data, status=400)
            else:
                # Regular dictionary result
                return Response(research_result)
        else:
            # Result is likely a content list
            logger.info(f"Processing content list or unknown result type")
            return Response({
                'success': True,
                'message': 'Research in progress, partial results returned',
                'content_list': research_result if isinstance(research_result, list) else [],
                'name': normalized_name,
                'position': position
            })
            
    except Exception as e:
        # Handle any unexpected errors
        logger.error(f"Unexpected error in research_politician view: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}",
            'name': normalized_name,
            'position': position
        }, status=500)