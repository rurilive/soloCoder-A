import requests
import json
import time
from urllib.parse import urljoin
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import ApiDefinition, ApiTestHistory
from .serializers import ApiDefinitionSerializer, ApiTestHistorySerializer


class ApiDefinitionViewSet(viewsets.ModelViewSet):
    queryset = ApiDefinition.objects.all()
    serializer_class = ApiDefinitionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project')
        group_id = self.request.query_params.get('group')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        return queryset

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        api = self.get_object()
        project = api.project
        
        base_url = project.base_url if project.base_url else ''
        path = api.path
        if not path.startswith('/'):
            path = '/' + path
        
        if base_url and not base_url.startswith(('http://', 'https://')):
            base_url = 'http://' + base_url
        
        url = urljoin(base_url, path) if base_url else path
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        method = api.method
        request_headers = {}
        request_params = {}
        request_body = None
        
        for param in api.request_headers:
            if param.get('enabled', True) and param.get('key'):
                request_headers[param['key']] = param.get('value', '')
        
        for param in api.request_params:
            if param.get('enabled', True) and param.get('key'):
                request_params[param['key']] = param.get('value', '')
        
        if api.request_body and api.request_body_type == 'json':
            request_body = api.request_body
        
        if request.data.get('url'):
            url = request.data.get('url')
        if request.data.get('method'):
            method = request.data.get('method')
        if request.data.get('headers'):
            request_headers.update(request.data.get('headers', {}))
        if request.data.get('params'):
            request_params.update(request.data.get('params', {}))
        if request.data.get('body'):
            request_body = request.data.get('body')
        
        start_time = time.time()
        try:
            kwargs = {
                'headers': request_headers,
                'params': request_params,
                'timeout': 30,
            }
            
            if method in ['POST', 'PUT', 'PATCH'] and request_body:
                if api.request_body_type == 'json' or request.data.get('body_type') == 'json':
                    kwargs['json'] = request_body
                else:
                    kwargs['data'] = request_body
            
            response = requests.request(method, url, **kwargs)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            is_success = 200 <= response.status_code < 300
            
            try:
                response_body = response.json()
                response_body_str = json.dumps(response_body, ensure_ascii=False, indent=2)
            except:
                response_body_str = response.text
            
            response_headers = dict(response.headers)
            
            test_history = ApiTestHistory.objects.create(
                api=api,
                request_url=url,
                request_method=method,
                request_headers=request_headers,
                request_body=json.dumps(request_body, ensure_ascii=False) if request_body else None,
                response_status=response.status_code,
                response_headers=response_headers,
                response_body=response_body_str,
                response_time=response_time,
                is_success=is_success,
                error_message=None
            )
            
            return Response({
                'success': True,
                'data': {
                    'test_id': test_history.id,
                    'request': {
                        'url': url,
                        'method': method,
                        'headers': request_headers,
                        'params': request_params,
                        'body': request_body
                    },
                    'response': {
                        'status': response.status_code,
                        'status_text': response.reason,
                        'headers': response_headers,
                        'body': response_body_str,
                        'time_ms': response_time
                    },
                    'is_success': is_success
                }
            })
            
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            test_history = ApiTestHistory.objects.create(
                api=api,
                request_url=url,
                request_method=method,
                request_headers=request_headers,
                request_body=json.dumps(request_body, ensure_ascii=False) if request_body else None,
                response_status=0,
                response_headers={},
                response_body=None,
                response_time=response_time,
                is_success=False,
                error_message=str(e)
            )
            
            return Response({
                'success': False,
                'error': str(e),
                'test_id': test_history.id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def test_history(self, request, pk=None):
        api = self.get_object()
        history = api.test_history.all()[:20]
        serializer = ApiTestHistorySerializer(history, many=True)
        return Response(serializer.data)


class ApiTestHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ApiTestHistory.objects.all()
    serializer_class = ApiTestHistorySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        api_id = self.request.query_params.get('api')
        if api_id:
            queryset = queryset.filter(api_id=api_id)
        return queryset
