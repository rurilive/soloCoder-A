from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Project, ApiGroup
from .serializers import ProjectSerializer, ApiGroupSerializer


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
