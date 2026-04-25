import requests
import json
import time
import base64
from urllib.parse import urljoin
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import ApiDefinition, ApiTestHistory
from .serializers import ApiDefinitionSerializer, ApiTestHistorySerializer
from projects.models import Environment, GlobalConfig, Project, ApiGroup
from .document_generator import DocumentGenerator


def apply_global_configs(request_headers, request_params, project, environment_id=None):
    """
    应用全局配置（Headers、认证、环境变量）
    """
    global_configs = GlobalConfig.objects.filter(
        project=project, 
        is_active=True, 
        is_global=True
    )
    
    for config in global_configs:
        if config.type == 'header':
            header_key = config.config_data.get('key')
            header_value = config.config_data.get('value', '')
            if header_key and header_key not in request_headers:
                request_headers[header_key] = header_value
        
        elif config.type == 'auth':
            auth_type = config.auth_type
            config_data = config.config_data
            
            if auth_type == 'bearer':
                token = config_data.get('token', '')
                prefix = config_data.get('prefix', 'Bearer')
                header_name = config_data.get('header_name', 'Authorization')
                if header_name not in request_headers:
                    request_headers[header_name] = f'{prefix} {token}' if prefix else token
            
            elif auth_type == 'basic':
                username = config_data.get('username', '')
                password = config_data.get('password', '')
                header_name = config_data.get('header_name', 'Authorization')
                credentials = f'{username}:{password}'.encode('utf-8')
                base64_credentials = base64.b64encode(credentials).decode('utf-8')
                if header_name not in request_headers:
                    request_headers[header_name] = f'Basic {base64_credentials}'
            
            elif auth_type == 'apikey':
                header_name = config_data.get('header_name', 'X-API-Key')
                api_key = config_data.get('api_key', '')
                if header_name not in request_headers:
                    request_headers[header_name] = api_key
    
    return request_headers, request_params


def get_base_url(project, environment_id=None):
    """
    获取基础URL（优先使用选择的环境，否则使用默认环境，最后使用项目base_url）
    """
    if environment_id:
        try:
            env = Environment.objects.get(id=environment_id, project=project, is_active=True)
            return env.host, env
        except Environment.DoesNotExist:
            pass
    
    default_env = Environment.objects.filter(project=project, is_default=True, is_active=True).first()
    if default_env:
        return default_env.host, default_env
    
    return project.base_url if project.base_url else '', None


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
        
        environment_id = request.data.get('environment_id')
        apply_global = request.data.get('apply_global', True)
        
        base_url, used_environment = get_base_url(project, environment_id)
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
        
        if apply_global:
            request_headers, request_params = apply_global_configs(
                request_headers, request_params, project, environment_id
            )
        
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
                error_message=None,
                environment_id=environment_id,
                used_environment_name=used_environment.name if used_environment else None
            )
            
            return Response({
                'success': True,
                'data': {
                    'test_id': test_history.id,
                    'environment': {
                        'id': environment_id,
                        'name': used_environment.name if used_environment else None
                    } if used_environment else None,
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
                error_message=str(e),
                environment_id=environment_id,
                used_environment_name=used_environment.name if used_environment else None
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

    @action(detail=True, methods=['get'])
    def document(self, request, pk=None):
        """
        生成单个API的文档
        GET /api/apis/{id}/document/?doc_format=json|markdown|postman
        """
        api = self.get_object()
        doc_format = request.query_params.get('doc_format', 'json').lower()
        base_url = request.query_params.get('base_url', '')
        
        if not base_url and api.project:
            base_url = api.project.base_url or ''
        
        project_name = api.project.name if api.project else "API Documentation"
        
        try:
            document = DocumentGenerator.generate_document(
                [api],
                format=doc_format,
                project_name=project_name,
                base_url=base_url
            )
            
            if doc_format == 'markdown':
                return Response({
                    'success': True,
                    'format': 'markdown',
                    'document': document
                })
            else:
                return Response(document)
                
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def batch_document(self, request):
        """
        批量生成API文档
        GET /api/apis/batch_document/?project={project_id}&group={group_id}&doc_format=json|markdown|postman
        
        参数:
            project: 项目ID（可选，如果不提供则需要group）
            group: 分组ID（可选，如果不提供则需要project）
            doc_format: 文档格式（json, markdown, postman）
            base_url: 基础URL（可选，默认使用项目base_url）
        """
        project_id = request.query_params.get('project')
        group_id = request.query_params.get('group')
        doc_format = request.query_params.get('doc_format', 'json').lower()
        base_url = request.query_params.get('base_url', '')
        
        if not project_id and not group_id:
            return Response({
                'success': False,
                'error': '请提供 project 或 group 参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        apis = ApiDefinition.objects.filter(is_active=True)
        project_name = "API Documentation"
        
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
                apis = apis.filter(project=project)
                project_name = project.name
                if not base_url:
                    base_url = project.base_url or ''
            except Project.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'项目不存在: {project_id}'
                }, status=status.HTTP_404_NOT_FOUND)
        
        if group_id:
            try:
                group = ApiGroup.objects.get(id=group_id)
                apis = apis.filter(group=group)
                if not project_id and group.project:
                    project_name = f"{group.project.name} - {group.name}"
                    if not base_url:
                        base_url = group.project.base_url or ''
                else:
                    project_name = group.name
            except ApiGroup.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'分组不存在: {group_id}'
                }, status=status.HTTP_404_NOT_FOUND)
        
        apis = apis.order_by('created_at')
        
        if not apis.exists():
            return Response({
                'success': False,
                'error': '没有找到匹配的API'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            document = DocumentGenerator.generate_document(
                list(apis),
                format=doc_format,
                project_name=project_name,
                base_url=base_url
            )
            
            if doc_format == 'markdown':
                return Response({
                    'success': True,
                    'format': 'markdown',
                    'project_name': project_name,
                    'api_count': apis.count(),
                    'document': document
                })
            else:
                return Response(document)
                
        except ValueError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ApiTestHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ApiTestHistory.objects.all()
    serializer_class = ApiTestHistorySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        api_id = self.request.query_params.get('api')
        if api_id:
            queryset = queryset.filter(api_id=api_id)
        return queryset
