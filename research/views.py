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

@csrf_exempt
@require_http_methods(["GET"])
@api_view(['GET'])
def get_research_report(request, report_id):
    """
    API endpoint to retrieve a research report by its ID.
    
    Parameters:
    - report_id: The ID of the research report to retrieve
    - include_sources: Whether to include sources in response (default: False)
    """
    logger.info(f"Request for research report: {report_id}")
    
    include_sources = request.query_params.get('include_sources', '').lower() == 'true'
    
    try:
        # Try to find the research report in the database
        research_report = ResearchResult.objects.get(id=report_id)
        
        # Serialize the report
        serializer = ResearchResultSerializer(research_report)
        response_data = serializer.data
        
        # Explicitly add politician_id to the response
        response_data['politician_id'] = research_report.politician.id if research_report.politician else None
        
        # Process response according to parameters
        if include_sources and 'sources' in response_data:
            # Filter out problematic sources with corrupt content
            if isinstance(response_data['sources'], list):
                filtered_sources = []
                for source in response_data['sources']:
                    # Check if content appears to be binary or corrupt
                    if source.get('content') and isinstance(source['content'], str):
                        # Filter out sources with binary content or very short corrupt content
                        if not (source['content'].startswith('����') or 
                                any(c for c in source['content'] if ord(c) > 127 and ord(c) < 32)):
                            filtered_sources.append(source)
                    else:
                        # Keep sources without content or with null content
                        filtered_sources.append(source)
                response_data['sources'] = filtered_sources
        elif not include_sources and 'sources' in response_data:
            del response_data['sources']
                    
        # Add metadata
        response_data['metadata'] = {
            'age_days': (timezone.now() - research_report.created_at).days,
        }
        
        return Response(response_data)
        
    except ResearchResult.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Research report not found',
        }, status=404)
        
    except Exception as e:
        # Handle any unexpected errors
        logger.error(f"Unexpected error retrieving research report: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}",
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@api_view(['GET'])
def get_politicians(request):
    """
    API endpoint to retrieve all politicians or filter by name.
    
    Query parameters:
    - name: Filter politicians by name (optional, case-insensitive partial match)
    - limit: Maximum number of politicians to return (optional, default: 20)
    - offset: Number of politicians to skip (optional, default: 0)
    """
    logger.info("Request for all politicians")
    
    # Get query parameters
    name_filter = request.GET.get('name', '')
    limit = int(request.GET.get('limit', 20))
    offset = int(request.GET.get('offset', 0))
    
    try:
        # Query the database
        query = Politician.objects.all()
        
        # Apply name filter if provided
        if name_filter:
            query = query.filter(name__icontains=name_filter)
            
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        query = query.order_by('name')[offset:offset+limit]
        
        # Serialize the results
        serializer = PoliticianSerializer(query, many=True)
        
        return Response({
            'success': True,
            'count': total_count,
            'results': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error retrieving politicians: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@api_view(['GET'])
def get_politician(request, politician_id):
    """
    API endpoint to retrieve a specific politician by ID.
    """
    logger.info(f"Request for politician with ID: {politician_id}")
    
    try:
        # Try to find the politician in the database
        politician = Politician.objects.get(id=politician_id)
        
        # Serialize the politician
        serializer = PoliticianSerializer(politician)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Politician.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Politician not found'
        }, status=404)
        
    except Exception as e:
        logger.error(f"Error retrieving politician: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        }, status=500)