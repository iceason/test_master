from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class Directory(models.Model):
    name = models.CharField(max_length=100, verbose_name="目录名称")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_directories', verbose_name="父级目录")
    level = models.IntegerField(default=1, verbose_name="层级")
    order = models.IntegerField(default=0, verbose_name="排序")
    description = models.TextField(blank=True, default='', verbose_name="项目描述")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_directories',
        verbose_name="创建人",
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "目录"
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['parent']),
        ]

    def save(self, *args, **kwargs):
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1
            
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProjectMember(models.Model):
    """项目成员（权限管理）"""
    ROLE_CHOICES = (
        ('owner', '所有者'),
        ('admin', '管理员'),
        ('member', '成员'),
        ('viewer', '观察者'),
    )

    project = models.ForeignKey(
        Directory, on_delete=models.CASCADE, related_name='members',
        verbose_name="所属项目",
        limit_choices_to={'parent__isnull': True},
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='project_memberships', verbose_name="用户",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member', verbose_name="角色")
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="加入时间")

    class Meta:
        verbose_name = "项目成员"
        verbose_name_plural = verbose_name
        unique_together = ('project', 'user')
        ordering = ['joined_at']
        indexes = [
            models.Index(fields=['project', 'user']),
        ]

    def __str__(self):
        return f"{self.user} - {self.project.name} ({self.get_role_display()})"


class Interface(models.Model):
    METHOD_CHOICES = (
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
        ('PATCH', 'PATCH'),
    )

    name = models.CharField(max_length=100, verbose_name="接口名称")
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE, related_name='interfaces', verbose_name="所属目录")
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default='GET', verbose_name="请求方法")
    path = models.CharField(max_length=255, verbose_name="接口路径")
    schema = models.JSONField(default=dict, blank=True, verbose_name="接口定义")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "接口"
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['directory']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['method', 'path'], name='unique_method_path')
        ]

    def __str__(self):
        return self.name


class TestCaseCategory(models.Model):
    name = models.CharField(max_length=50, verbose_name="类型名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="类型编码")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_categories', verbose_name="父级类型")
    description = models.TextField(blank=True, verbose_name="类型描述")

    class Meta:
        verbose_name = "测试用例类型"
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.name


class TestCase(models.Model):
    interface = models.ForeignKey(Interface, on_delete=models.CASCADE, related_name='testcases', verbose_name="所属接口")
    project = models.ForeignKey(Directory, on_delete=models.SET_NULL, null=True, blank=True, related_name='testcases', verbose_name="所属项目")
    category = models.ForeignKey(TestCaseCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='testcases', verbose_name="用例类型")
    name = models.CharField(max_length=500, verbose_name="用例名称")
    description = models.TextField(blank=True, verbose_name="用例描述")
    test_field = models.CharField(max_length=100, blank=True, verbose_name="测试字段")
    request_data = models.JSONField(default=dict, blank=True, verbose_name="请求数据") # 对应接口参数
    expected_value = models.JSONField(default=dict, blank=True, verbose_name="期望值") # 新增
    expected_response = models.JSONField(default=dict, blank=True, verbose_name="预期响应") # 保留旧字段兼容
    # 新增用例类型字段
    TEST_TYPE_CHOICES = (
        ('positive', '正向'),
        ('negative', '负向'),
        ('boundary', '边界值'),
        ('security', '安全性'),
    )
    test_type = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES, null=True, blank=True, verbose_name="用例类型")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "测试用例"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['interface']),
            models.Index(fields=['project']),
        ]

    def save(self, *args, **kwargs):
        if not self.project_id and self.interface_id:
            self.project = self._resolve_root_directory()
        super().save(*args, **kwargs)

    def _resolve_root_directory(self):
        """沿目录树向上找到根目录（项目）"""
        try:
            d = self.interface.directory
            while d.parent_id is not None:
                d = d.parent
            return d
        except Exception:
            return None

    def __str__(self):
        return self.name


class Environment(models.Model):
    """测试环境配置"""
    name = models.CharField(max_length=50, unique=True, verbose_name="环境名称")
    code = models.CharField(max_length=20, unique=True, verbose_name="环境代码")
    project = models.ForeignKey(
        Directory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='environments',
        verbose_name="关联项目",
        limit_choices_to={'parent__isnull': True},
    )
    base_url = models.URLField(verbose_name="基础URL")
    token = models.CharField(max_length=500, blank=True, default='', verbose_name="Token")
    description = models.TextField(blank=True, verbose_name="描述")
    config = models.JSONField(default=dict, blank=True, verbose_name="环境配置")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "测试环境"
        verbose_name_plural = verbose_name
        ordering = ['id']
    
    def __str__(self):
        return self.name


class TestExecutionBatch(models.Model):
    """测试执行批次"""
    batch_id = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name="批次ID")
    name = models.CharField(max_length=200, verbose_name="批次名称")
    
    # 触发信息
    TRIGGER_TYPE_CHOICES = (
        ('web', 'Web UI'),
        ('api', 'REST API'),
        ('cli', '命令行'),
        ('cron', '定时任务'),
    )
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPE_CHOICES, verbose_name="触发方式")
    executor = models.CharField(max_length=100, blank=True, verbose_name="执行人")
    environment = models.ForeignKey(Environment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="执行环境")
    
    # 统计信息
    total_cases = models.IntegerField(default=0, verbose_name="总用例数")
    passed_cases = models.IntegerField(default=0, verbose_name="通过用例数")
    failed_cases = models.IntegerField(default=0, verbose_name="失败用例数")
    error_cases = models.IntegerField(default=0, verbose_name="错误用例数")
    
    # 执行状态
    STATUS_CHOICES = (
        ('pending', '等待中'),
        ('running', '执行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="执行状态")
    
    # 时间信息
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="开始时间")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="结束时间")
    duration_ms = models.IntegerField(null=True, blank=True, verbose_name="执行耗时(ms)")
    
    # Celery任务ID
    celery_task_id = models.CharField(max_length=255, blank=True, verbose_name="Celery任务ID")
    
    class Meta:
        verbose_name = "测试执行批次"
        verbose_name_plural = verbose_name
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['batch_id']),
            models.Index(fields=['-started_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.batch_id}"
    
    @property
    def success_rate(self):
        """成功率"""
        if self.total_cases == 0:
            return 0.0
        return (self.passed_cases / self.total_cases) * 100


class TestExecution(models.Model):
    """测试执行记录"""
    execution_id = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name="执行ID")
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='executions', verbose_name="测试用例")
    batch = models.ForeignKey(TestExecutionBatch, on_delete=models.CASCADE, null=True, blank=True, related_name='execution_records', verbose_name="所属批次")
    
    # 执行状态
    STATUS_CHOICES = (
        ('pending', '等待中'),
        ('running', '执行中'),
        ('passed', '通过'),
        ('failed', '失败'),
        ('error', '错误'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="执行状态")
    
    # 请求详情
    request_url = models.TextField(verbose_name="请求URL")
    request_method = models.CharField(max_length=10, verbose_name="请求方法")
    request_headers = models.JSONField(default=dict, verbose_name="请求头")
    request_body = models.JSONField(default=dict, blank=True, verbose_name="请求体")
    
    # 响应详情
    response_status = models.IntegerField(null=True, blank=True, verbose_name="响应状态码")
    response_headers = models.JSONField(default=dict, blank=True, verbose_name="响应头")
    response_body = models.JSONField(default=dict, blank=True, verbose_name="响应体")
    response_time_ms = models.IntegerField(null=True, blank=True, verbose_name="响应时间(ms)")
    
    # 断言结果
    assertions_passed = models.IntegerField(default=0, verbose_name="通过断言数")
    assertions_failed = models.IntegerField(default=0, verbose_name="失败断言数")
    assertion_details = models.JSONField(default=list, blank=True, verbose_name="断言详情")
    
    # 错误信息
    error_message = models.TextField(blank=True, verbose_name="错误信息")
    error_traceback = models.TextField(blank=True, verbose_name="错误堆栈")
    
    # 重试信息
    retry_count = models.IntegerField(default=0, verbose_name="重试次数")
    parent_execution = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="父执行记录")
    
    # 时间信息
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="开始时间")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="结束时间")
    duration_ms = models.IntegerField(null=True, blank=True, verbose_name="执行耗时(ms)")
    
    class Meta:
        verbose_name = "测试执行记录"
        verbose_name_plural = verbose_name
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['execution_id']),
            models.Index(fields=['test_case', '-started_at']),
            models.Index(fields=['batch', '-started_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.test_case.name} - {self.execution_id}"


# ---------------------------------------------------------------------------
# 测试执行模块 - 执行机管理 & 构建计划
# ---------------------------------------------------------------------------

class ExecutorMachine(models.Model):
    """执行机（构建代理/Runner）"""
    OS_CHOICES = (
        ('linux', 'Linux'),
        ('windows', 'Windows'),
        ('macos', 'macOS'),
    )
    STATUS_CHOICES = (
        ('online', '在线'),
        ('offline', '离线'),
        ('busy', '忙碌'),
    )

    name = models.CharField(max_length=100, unique=True, verbose_name="名称")
    hostname = models.CharField(max_length=255, verbose_name="主机名")
    ip_address = models.GenericIPAddressField(verbose_name="IP 地址")
    port = models.IntegerField(default=22, verbose_name="端口")
    os_type = models.CharField(max_length=20, choices=OS_CHOICES, default='linux', verbose_name="操作系统")
    labels = models.JSONField(default=list, blank=True, verbose_name="标签")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline', verbose_name="状态")
    description = models.TextField(blank=True, verbose_name="描述")
    jenkins_node_name = models.CharField(max_length=255, blank=True, verbose_name="Jenkins 节点名")
    jenkins_url = models.URLField(blank=True, verbose_name="Jenkins 服务器地址")
    jenkins_username = models.CharField(max_length=255, blank=True, verbose_name="Jenkins 用户名")
    jenkins_token = models.CharField(max_length=255, blank=True, verbose_name="Jenkins Token")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "执行机"
        verbose_name_plural = verbose_name
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.ip_address})"


class BuildPlan(models.Model):
    """构建计划"""
    STATUS_CHOICES = (
        ('active', '启用'),
        ('disabled', '禁用'),
    )

    name = models.CharField(max_length=200, verbose_name="计划名称")
    description = models.TextField(blank=True, verbose_name="描述")
    executor_machine = models.ForeignKey(
        ExecutorMachine, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='build_plans', verbose_name="执行机"
    )
    environment = models.ForeignKey(
        Environment, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='build_plans', verbose_name="执行环境"
    )

    # Jenkins 配置（服务器地址和凭据已移至 ExecutorMachine）
    jenkins_job_name = models.CharField(max_length=255, blank=True, verbose_name="Jenkins Job 名称")

    # 源码管理
    git_repo_url = models.CharField(max_length=500, blank=True, verbose_name="Git 仓库地址")
    git_branch = models.CharField(max_length=100, default='main', blank=True, verbose_name="Git 分支")
    git_credential_id = models.CharField(
        max_length=100, blank=True, default='',
        verbose_name="Jenkins 凭证 ID",
        help_text="Jenkins 中配置的 Credentials ID，如 github-user",
    )
    workspace_cleanup = models.BooleanField(default=True, verbose_name="构建前清理工作空间")

    # 报告配置
    report_enabled = models.BooleanField(default=False, verbose_name="启用报告上传")
    report_command = models.TextField(blank=True, verbose_name="报告生成命令")

    # 定时执行
    cron_expression = models.CharField(max_length=100, blank=True, verbose_name="Cron 表达式")
    is_cron_enabled = models.BooleanField(default=False, verbose_name="启用定时执行")
    repeat_run_times = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        verbose_name="重复执行次数",
        help_text="点击一次立即构建时，自动触发的轮次（1~20）",
    )
    REPEAT_FAILURE_POLICY_CHOICES = (
        ('continue_all', '继续全部轮次'),
        ('stop_on_first_fail', '首次失败即停止'),
    )
    repeat_failure_policy = models.CharField(
        max_length=30,
        choices=REPEAT_FAILURE_POLICY_CHOICES,
        default='continue_all',
        verbose_name="重复执行失败策略",
    )

    # 环境变量
    environment_variables = models.JSONField(
        default=list, blank=True, verbose_name="环境变量",
        help_text='[{"key": "FOO", "value": "bar", "secret": false}, ...]'
    )

    # Jenkinsfile 原始文本（文本编辑模式时保存）
    jenkinsfile_text = models.TextField(
        blank=True, default='', verbose_name="Jenkinsfile 文本",
    )

    # 通知配置
    notification_config = models.JSONField(
        default=dict, blank=True, verbose_name="通知配置",
        help_text='{"email": {"enabled": false, "recipients": []}, "webhook": {"enabled": false, "url": "", "type": "dingtalk"}, "dingtalk": {"enabled": false, "group_ids": [], "template_id": null}}'
    )

    # 外部触发
    trigger_token = models.CharField(max_length=64, unique=True, blank=True, verbose_name="触发 Token")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="状态")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='build_plans', verbose_name="创建人"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "构建计划"
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['trigger_token']),
        ]

    def save(self, *args, **kwargs):
        if not self.trigger_token:
            self.trigger_token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BuildStep(models.Model):
    """构建步骤"""
    ON_FAILURE_CHOICES = (
        ('stop', '停止'),
        ('continue', '继续'),
        ('retry', '重试'),
    )

    build_plan = models.ForeignKey(
        BuildPlan, on_delete=models.CASCADE, related_name='steps', verbose_name="所属构建计划"
    )
    order = models.IntegerField(default=0, verbose_name="步骤序号")
    name = models.CharField(max_length=200, verbose_name="步骤名称")
    script = models.TextField(blank=True, verbose_name="执行脚本")
    timeout = models.IntegerField(default=120, verbose_name="超时秒数")
    on_failure = models.CharField(max_length=20, choices=ON_FAILURE_CHOICES, default='stop', verbose_name="失败策略")

    class Meta:
        verbose_name = "构建步骤"
        verbose_name_plural = verbose_name
        ordering = ['order']

    def __str__(self):
        return f"[{self.order}] {self.name}"


class BuildExecution(models.Model):
    """构建执行记录"""
    TRIGGER_TYPE_CHOICES = (
        ('manual', '手动触发'),
        ('cron', '定时任务'),
        ('api', '外部 API'),
        ('jenkins_webhook', 'Jenkins Webhook'),
    )
    STATUS_CHOICES = (
        ('pending', '等待中'),
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    )
    REPORT_TYPE_CHOICES = (
        ('none', '无'),
        ('allure', 'Allure'),
        ('junit', 'JUnit'),
    )

    build_plan = models.ForeignKey(
        BuildPlan, on_delete=models.CASCADE, related_name='executions', verbose_name="所属构建计划"
    )
    executor_machine = models.ForeignKey(
        ExecutorMachine, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='build_executions', verbose_name="执行机"
    )
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPE_CHOICES, default='manual', verbose_name="触发方式")
    triggered_by = models.CharField(max_length=100, blank=True, verbose_name="触发人/来源")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="执行状态")

    # Jenkins 信息
    jenkins_build_number = models.IntegerField(null=True, blank=True, verbose_name="Jenkins 构建号")
    jenkins_build_url = models.URLField(blank=True, verbose_name="Jenkins 构建链接")

    # 日志
    log_text = models.TextField(blank=True, verbose_name="构建日志")
    log_file = models.FileField(upload_to='build_logs/', blank=True, verbose_name="日志文件")

    # 测试报告
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, default='none', verbose_name="报告类型")
    report_url = models.URLField(blank=True, verbose_name="报告链接")
    report_data = models.JSONField(default=dict, blank=True, verbose_name="报告数据")

    # 时间
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="开始时间")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="结束时间")
    duration_ms = models.IntegerField(null=True, blank=True, verbose_name="执行耗时(ms)")

    # Celery
    celery_task_id = models.CharField(max_length=255, blank=True, verbose_name="Celery 任务ID")
    callback_url = models.URLField(blank=True, verbose_name="结果回调地址")
    callback_notified = models.BooleanField(default=False, verbose_name="是否已回调")
    callback_notified_at = models.DateTimeField(null=True, blank=True, verbose_name="回调时间")
    callback_last_response = models.TextField(blank=True, verbose_name="回调响应摘要")

    class Meta:
        verbose_name = "构建执行记录"
        verbose_name_plural = verbose_name
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['build_plan', '-started_at']),
            models.Index(fields=['status']),
            models.Index(fields=['-started_at']),
        ]

    def __str__(self):
        return f"{self.build_plan.name} #{self.id}"

    @property
    def duration_display(self):
        if self.duration_ms is None:
            return '-'
        seconds = self.duration_ms / 1000
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = seconds / 60
        return f"{minutes:.1f}m"


class EmailTemplate(models.Model):
    """邮件通知模板"""
    VARIABLE_HELP = (
        ('plan_name', '构建计划名称'),
        ('status', '构建状态(小写)'),
        ('status_upper', '构建状态(大写)'),
        ('status_emoji', '状态表情'),
        ('trigger_type', '触发方式'),
        ('triggered_by', '触发人'),
        ('duration', '执行耗时'),
        ('jenkins_url', 'Jenkins 构建链接'),
        ('timestamp', '执行时间'),
    )

    name = models.CharField(max_length=100, verbose_name="模板名称")
    subject = models.CharField(
        max_length=255, verbose_name="邮件主题",
        default="{{status_emoji}} [Test Master] {{plan_name}} - {{status_upper}}",
    )
    DEFAULT_BODY = (
        "══════════════════════════════════════\n"
        "  {{status_emoji}} 自动化测试执行报告\n"
        "══════════════════════════════════════\n"
        "\n"
        "【基本信息】\n"
        "  构建计划：{{plan_name}}\n"
        "  执行结果：{{status_upper}}\n"
        "  执行时间：{{timestamp}}\n"
        "  执行耗时：{{duration}}\n"
        "\n"
        "【触发信息】\n"
        "  触发方式：{{trigger_type}}\n"
        "  触发人员：{{triggered_by}}\n"
        "\n"
        "【构建详情】\n"
        "  Jenkins 链接：{{jenkins_url}}\n"
        "  （点击上方链接可查看完整构建日志与测试产物）\n"
        "\n"
        "──────────────────────────────────────\n"
        "  说明：\n"
        "  · SUCCESS  — 所有测试步骤执行通过\n"
        "  · FAILED   — 存在失败的测试步骤，请及时排查\n"
        "  · CANCELLED — 构建被手动取消\n"
        "──────────────────────────────────────\n"
        "\n"
        "此邮件由 Test Master 自动发送，请勿直接回复。\n"
        "如有疑问请联系测试团队。\n"
    )

    body = models.TextField(
        verbose_name="邮件正文",
        default=DEFAULT_BODY,
    )
    is_default = models.BooleanField(default=False, verbose_name="默认模板")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "邮件模板"
        verbose_name_plural = "邮件模板"
        ordering = ['-is_default', '-updated_at']

    def __str__(self):
        return f"{self.name} {'(默认)' if self.is_default else ''}"

    def save(self, *args, **kwargs):
        if self.is_default:
            EmailTemplate.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def render(self, context: dict) -> tuple:
        subject = self.subject
        body = self.body
        for key, value in context.items():
            placeholder = '{{' + key + '}}'
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))
        return subject, body


class DingTalkGroup(models.Model):
    """钉钉群机器人配置（强制加签）"""
    name = models.CharField(max_length=100, unique=True, verbose_name="群组名称")
    webhook_url = models.URLField(verbose_name="Webhook 地址")
    secret = models.CharField(max_length=255, verbose_name="签名密钥")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    description = models.TextField(blank=True, default='', verbose_name="描述")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "钉钉群组"
        verbose_name_plural = "钉钉群组"
        ordering = ['name']

    def __str__(self):
        return self.name


class DingTalkTemplate(models.Model):
    """钉钉消息模板"""
    VARIABLE_HELP = (
        ('plan_name', '构建计划名称'),
        ('status', '构建状态(小写)'),
        ('status_upper', '构建状态(大写)'),
        ('status_emoji', '状态表情'),
        ('trigger_type', '触发方式'),
        ('triggered_by', '触发人'),
        ('duration', '执行耗时'),
        ('jenkins_url', 'Jenkins 构建链接'),
        ('timestamp', '执行时间'),
    )

    name = models.CharField(max_length=100, unique=True, verbose_name="模板名称")
    title_template = models.CharField(
        max_length=255,
        default='{{status_emoji}} [Test Master] {{plan_name}} - {{status_upper}}',
        verbose_name="标题模板",
    )
    body_template = models.TextField(
        default=(
            "## {{status_emoji}} 自动化构建通知\n\n"
            "### 基本信息\n"
            "- 构建计划：{{plan_name}}\n"
            "- 执行结果：{{status_upper}}\n"
            "- 执行时间：{{timestamp}}\n"
            "- 执行耗时：{{duration}}\n\n"
            "### 触发信息\n"
            "- 触发方式：{{trigger_type}}\n"
            "- 触发人：{{triggered_by}}\n\n"
            "### 构建详情\n"
            "- Jenkins 链接：{{jenkins_url}}\n\n"
            "---\n"
            "说明：\n"
            "- SUCCESS：所有步骤执行通过\n"
            "- FAILED：存在失败步骤，请及时排查\n"
            "- CANCELLED：构建被取消\n"
        ),
        verbose_name="正文模板",
    )
    is_default = models.BooleanField(default=False, verbose_name="默认模板")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    description = models.TextField(blank=True, default='', verbose_name="描述")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "钉钉模板"
        verbose_name_plural = "钉钉模板"
        ordering = ['-is_default', '-updated_at']

    def __str__(self):
        return f"{self.name} {'(默认)' if self.is_default else ''}"

    def save(self, *args, **kwargs):
        if self.is_default:
            DingTalkTemplate.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def render(self, context: dict) -> tuple:
        title = self.title_template
        body = self.body_template
        for key, value in context.items():
            placeholder = '{{' + key + '}}'
            title = title.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))
        return title, body


class RegistrationInvite(models.Model):
    """一次性注册邀请链接（有有效期，使用后失效）"""
    token = models.CharField(max_length=64, unique=True, db_index=True, verbose_name='邀请令牌')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_registration_invites',
        verbose_name='创建人',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    expires_at = models.DateTimeField(verbose_name='过期时间')
    used_at = models.DateTimeField(null=True, blank=True, verbose_name='使用时间')
    registered_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registration_via_invite',
        verbose_name='注册用户',
    )

    class Meta:
        verbose_name = '注册邀请'
        verbose_name_plural = '注册邀请'
        ordering = ['-created_at']

    def __str__(self):
        return f'Invite {self.token[:8]}…'
