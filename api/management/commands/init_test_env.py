"""
Django管理命令：初始化测试环境
"""

from django.core.management.base import BaseCommand
from api.models import Environment, TestCaseCategory


class Command(BaseCommand):
    help = '初始化测试环境和基础数据'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始初始化测试环境...'))
        
        # 创建默认环境
        environments = [
            {
                'name': '测试环境',
                'code': 'test',
                'base_url': 'http://httpbin.org',
                'description': '使用httpbin.org作为测试服务器',
                'is_active': True,
                'config': {
                    'timeout': 30,
                    'max_retries': 3,
                    'verify_ssl': False
                }
            },
            {
                'name': '本地环境',
                'code': 'local',
                'base_url': 'http://localhost:8080',
                'description': '本地开发服务器',
                'is_active': True,
                'config': {
                    'timeout': 10,
                    'max_retries': 1,
                    'verify_ssl': False
                }
            }
        ]
        
        for env_data in environments:
            env, created = Environment.objects.get_or_create(
                code=env_data['code'],
                defaults=env_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ 创建环境: {env.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  - 环境已存在: {env.name}'))
        
        # 确保测试用例分类存在
        categories_count = TestCaseCategory.objects.count()
        if categories_count == 0:
            self.stdout.write(self.style.WARNING('  ⚠ 测试用例分类为空，请手动创建'))
        else:
            self.stdout.write(self.style.SUCCESS(f'  ✓ 测试用例分类已存在: {categories_count}个'))
        
        self.stdout.write(self.style.SUCCESS('\n初始化完成！'))
        self.stdout.write('\n下一步：')
        self.stdout.write('  1. 访问 http://localhost:8000/admin/ 登录管理后台')
        self.stdout.write('  2. 创建接口和测试用例')
        self.stdout.write('  3. 执行测试')
