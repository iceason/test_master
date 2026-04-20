from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (DirectoryViewSet, InterfaceViewSet, TestCaseViewSet, TestCaseCategoryViewSet,
                   ExportTestCasesView, ObtainTokenView, RefreshTokenView, CurrentUserView, TaskStatusView,
                   EnvironmentViewSet, TestExecutionBatchViewSet, TestExecutionViewSet,
                   YamlExportView, YamlImportView,
                   ImportOpenAPIView, ImportOpenAPIPreviewView,
                   ProjectViewSet, UserListView,
                   RegistrationInviteCreateView, RegisterInviteValidateView, RegisterWithInviteView)
from .metrics import PrometheusMetricsView
from .testing_views import (
    ExecutorMachineViewSet, BuildPlanViewSet, BuildExecutionViewSet,
    BuildTriggerView, JenkinsWebhookView, ReportUploadView,
    EmailTemplateViewSet,
)

router = DefaultRouter()
router.register(r'directories', DirectoryViewSet)
router.register(r'interfaces', InterfaceViewSet)
router.register(r'testcases', TestCaseViewSet)
router.register(r'categories', TestCaseCategoryViewSet)
router.register(r'environments', EnvironmentViewSet)
router.register(r'execution-batches', TestExecutionBatchViewSet)
router.register(r'executions', TestExecutionViewSet)
# Testing module
router.register(r'executor-machines', ExecutorMachineViewSet)
router.register(r'build-plans', BuildPlanViewSet)
router.register(r'build-executions', BuildExecutionViewSet)
router.register(r'email-templates', EmailTemplateViewSet)
# Project management
router.register(r'projects', ProjectViewSet, basename='project')

urlpatterns = [
    path('export/', ExportTestCasesView.as_view(), name='export_testcases'),
    path('yaml/export/', YamlExportView.as_view(), name='yaml_export'),
    path('yaml/import/', YamlImportView.as_view(), name='yaml_import'),
    path('import-openapi/', ImportOpenAPIView.as_view(), name='import_openapi'),
    path('import-openapi/preview/', ImportOpenAPIPreviewView.as_view(), name='import_openapi_preview'),
    path('token/', ObtainTokenView.as_view(), name='token'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('registration-invites/', RegistrationInviteCreateView.as_view(), name='registration_invite_create'),
    path('register/validate/', RegisterInviteValidateView.as_view(), name='register_invite_validate'),
    path('register/', RegisterWithInviteView.as_view(), name='register_with_invite'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/me', CurrentUserView.as_view(), name='current_user'),
    path('tasks/<str:task_id>/', TaskStatusView.as_view(), name='task_status'),
    path('metrics/', PrometheusMetricsView.as_view(), name='prometheus_metrics'),
    # Testing module - external endpoints
    path('build-trigger/<str:trigger_token>/', BuildTriggerView.as_view(), name='build_trigger'),
    path('jenkins-webhook/', JenkinsWebhookView.as_view(), name='jenkins_webhook'),
    path('upload-report/<int:execution_id>/', ReportUploadView.as_view(), name='upload_report'),
    path('', include(router.urls)),
]
