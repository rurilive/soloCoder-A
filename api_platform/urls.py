"""
URL configuration for api_platform project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from projects.views import ProjectViewSet, ApiGroupViewSet
from apis.views import ApiDefinitionViewSet, ApiTestHistoryViewSet
from mock_server.views import MockConfigViewSet, MockLogViewSet, MockServerViewSet
from test_runner.views import (
    TestCaseViewSet, TestSuiteViewSet, TestRunViewSet, 
    TestResultViewSet, BatchTestViewSet
)

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'groups', ApiGroupViewSet, basename='apigroup')
router.register(r'apis', ApiDefinitionViewSet, basename='apidefinition')
router.register(r'test-history', ApiTestHistoryViewSet, basename='apitesthistory')
router.register(r'mock-configs', MockConfigViewSet, basename='mockconfig')
router.register(r'mock-logs', MockLogViewSet, basename='mocklog')
router.register(r'test-cases', TestCaseViewSet, basename='testcase')
router.register(r'test-suites', TestSuiteViewSet, basename='testsuite')
router.register(r'test-runs', TestRunViewSet, basename='testrun')
router.register(r'test-results', TestResultViewSet, basename='testresult')
router.register(r'batch-tests', BatchTestViewSet, basename='batchtest')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    re_path(r'^mock/(?P<path>.*)$', MockServerViewSet.as_view({'get': 'handle_mock', 'post': 'handle_mock', 'put': 'handle_mock', 'delete': 'handle_mock', 'patch': 'handle_mock', 'head': 'handle_mock', 'options': 'handle_mock'}), name='mock-server'),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
]
