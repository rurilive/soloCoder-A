from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Project, ApiGroup, Environment, GlobalConfig
from .serializers import (
    ProjectSerializer, ApiGroupSerializer,
    EnvironmentSerializer, GlobalConfigSerializer
)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    @action(detail=True, methods=['get'])
    def groups(self, request, pk=None):
        project = self.get_object()
        groups = ApiGroup.objects.filter(project=project, parent=None)
        serializer = ApiGroupSerializer(groups, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def all_groups(self, request, pk=None):
        project = self.get_object()
        groups = ApiGroup.objects.filter(project=project)
        serializer = ApiGroupSerializer(groups, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def environments(self, request, pk=None):
        project = self.get_object()
        envs = Environment.objects.filter(project=project, is_active=True)
        serializer = EnvironmentSerializer(envs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def global_configs(self, request, pk=None):
        project = self.get_object()
        configs = GlobalConfig.objects.filter(project=project)
        serializer = GlobalConfigSerializer(configs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def default_environment(self, request, pk=None):
        project = self.get_object()
        env = Environment.objects.filter(project=project, is_default=True, is_active=True).first()
        if env:
            serializer = EnvironmentSerializer(env)
            return Response(serializer.data)
        return Response({'error': 'No default environment found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def set_default_environment(self, request, pk=None):
        project = self.get_object()
        env_id = request.data.get('environment_id')
        
        try:
            env = Environment.objects.get(id=env_id, project=project)
            env.is_default = True
            env.save()
            return Response({'success': True, 'message': 'Default environment updated'})
        except Environment.DoesNotExist:
            return Response({'error': 'Environment not found'}, status=status.HTTP_404_NOT_FOUND)


class ApiGroupViewSet(viewsets.ModelViewSet):
    queryset = ApiGroup.objects.all()
    serializer_class = ApiGroupSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        group = self.get_object()
        children = group.children.all()
        serializer = ApiGroupSerializer(children, many=True)
        return Response(serializer.data)


class EnvironmentViewSet(viewsets.ModelViewSet):
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset
    
    def perform_create(self, serializer):
        instance = serializer.save()
        if instance.is_default:
            Environment.objects.filter(project=instance.project).exclude(pk=instance.pk).update(is_default=False)
    
    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.is_default:
            Environment.objects.filter(project=instance.project).exclude(pk=instance.pk).update(is_default=False)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        env = self.get_object()
        env.is_default = True
        env.save()
        return Response({'success': True})
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        env = self.get_object()
        new_env = Environment.objects.create(
            project=env.project,
            name=f'{env.name} (复制)',
            type=env.type,
            host=env.host,
            description=env.description,
            is_default=False,
            is_active=True
        )
        serializer = EnvironmentSerializer(new_env)
        return Response(serializer.data)


class GlobalConfigViewSet(viewsets.ModelViewSet):
    queryset = GlobalConfig.objects.all()
    serializer_class = GlobalConfigSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project')
        config_type = self.request.query_params.get('type')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if config_type:
            queryset = queryset.filter(type=config_type)
        return queryset
    
    def perform_create(self, serializer):
        project_id = self.request.data.get('project')
        if project_id:
            serializer.save(project_id=project_id)
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def headers(self, request):
        project_id = request.query_params.get('project')
        queryset = self.get_queryset().filter(type='header', is_active=True)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def auth_configs(self, request):
        project_id = request.query_params.get('project')
        queryset = self.get_queryset().filter(type='auth', is_active=True)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def variables(self, request):
        project_id = request.query_params.get('project')
        queryset = self.get_queryset().filter(type='variable', is_active=True)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        config = self.get_object()
        config.is_active = not config.is_active
        config.save()
        return Response({'success': True, 'is_active': config.is_active})
    
    @action(detail=False, methods=['post'])
    def batch_save(self, request):
        project_id = request.data.get('project_id')
        configs_data = request.data.get('configs', [])
        
        if not project_id:
            return Response({'error': 'project_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        
        created = []
        updated = []
        errors = []
        
        for config_data in configs_data:
            config_id = config_data.get('id')
            
            try:
                if config_id:
                    try:
                        config = GlobalConfig.objects.get(id=config_id, project=project)
                        for key, value in config_data.items():
                            if key != 'id' and key != 'project':
                                setattr(config, key, value)
                        config.save()
                        updated.append(config.id)
                    except GlobalConfig.DoesNotExist:
                        errors.append({'id': config_id, 'error': 'Config not found'})
                else:
                    config = GlobalConfig.objects.create(
                        project=project,
                        name=config_data.get('name', ''),
                        type=config_data.get('type'),
                        auth_type=config_data.get('auth_type', 'none'),
                        config_data=config_data.get('config_data', {}),
                        is_active=config_data.get('is_active', True),
                        is_global=config_data.get('is_global', False)
                    )
                    created.append(config.id)
            except Exception as e:
                errors.append({'id': config_id, 'error': str(e)})
        
        return Response({
            'success': True,
            'created': created,
            'updated': updated,
            'errors': errors
        })


@never_cache
def home_view(request):
    return render(request, 'index.html')
