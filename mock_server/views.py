import time
import json
import re
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import MockConfig, MockLog
from .serializers import MockConfigSerializer, MockLogSerializer
from apis.models import ApiDefinition


class MockConfigViewSet(viewsets.ModelViewSet):
    queryset = MockConfig.objects.all()
    serializer_class = MockConfigSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        api_id = self.request.query_params.get('api')
        if api_id:
            queryset = queryset.filter(api_id=api_id)
        return queryset

    def perform_create(self, serializer):
        instance = serializer.save()
        if instance.is_default:
            MockConfig.objects.filter(api=instance.api).exclude(pk=instance.pk).update(is_default=False)

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.is_default:
            MockConfig.objects.filter(api=instance.api).exclude(pk=instance.pk).update(is_default=False)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        mock_config = self.get_object()
        mock_config.is_default = True
        mock_config.save()
        MockConfig.objects.filter(api=mock_config.api).exclude(pk=mock_config.pk).update(is_default=False)
        return Response({'success': True})


class MockLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MockLog.objects.all()
    serializer_class = MockLogSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        api_id = self.request.query_params.get('api')
        mock_config_id = self.request.query_params.get('mock_config')
        if api_id:
            queryset = queryset.filter(api_id=api_id)
        if mock_config_id:
            queryset = queryset.filter(mock_config_id=mock_config_id)
        return queryset


@csrf_exempt
def mock_server_handler(request, path):
    method = request.method
    
    mock_path = path
    
    apis = ApiDefinition.objects.filter(method=method, is_active=True)
    
    api = None
    for a in apis:
        api_path = a.path.lstrip('/')
        target_path = mock_path.lstrip('/')
        
        if match_path(api_path, target_path):
            api = a
            break
    
    if not api:
        return JsonResponse({
            'error': 'Mock API not found',
            'path': mock_path,
            'method': method
        }, status=404)
    
    mock_configs = MockConfig.objects.filter(api=api, is_active=True)
    
    mock_config = mock_configs.filter(is_default=True).first()
    if not mock_config:
        mock_config = mock_configs.first()
    
    if not mock_config:
        return JsonResponse({
            'error': 'No mock config found for this API',
            'api': api.name
        }, status=404)
    
    if mock_config.delay_ms > 0:
        time.sleep(mock_config.delay_ms / 1000.0)
    
    request_headers = dict(request.headers)
    request_body = request.body.decode('utf-8') if request.body else None
    request_query_params = dict(request.GET)
    
    response_status = mock_config.status_code
    response_headers = mock_config.response_headers or {}
    response_body = mock_config.response_body_raw or json.dumps(mock_config.response_body, ensure_ascii=False)
    
    MockLog.objects.create(
        mock_config=mock_config,
        api=api,
        request_method=method,
        request_path=mock_path,
        request_headers=request_headers,
        request_body=request_body,
        request_query_params=request_query_params,
        response_status=response_status,
        response_headers=response_headers,
        response_body=response_body
    )
    
    content_type = response_headers.get('Content-Type', 'application/json')
    
    headers_without_content_type = {k: v for k, v in response_headers.items() if k.lower() != 'content-type'}
    
    if content_type.startswith('application/json'):
        try:
            json_body = json.loads(response_body)
            return JsonResponse(json_body, status=response_status, headers=headers_without_content_type)
        except:
            pass
    
    return HttpResponse(
        response_body,
        status=response_status,
        content_type=content_type,
        headers=headers_without_content_type
    )


def match_path(pattern, path):
    if pattern == path:
        return True
    
    pattern_parts = pattern.split('/')
    path_parts = path.split('/')
    
    if len(pattern_parts) != len(path_parts):
        return False
    
    for p_part, t_part in zip(pattern_parts, path_parts):
        if p_part.startswith('{') and p_part.endswith('}'):
            continue
        if p_part.startswith(':'):
            continue
        if p_part != t_part:
            return False
    
    return True


@method_decorator(csrf_exempt, name='dispatch')
class MockServerViewSet(viewsets.ViewSet):
    pass
