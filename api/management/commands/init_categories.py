from django.core.management.base import BaseCommand
from api.models import TestCaseCategory

class Command(BaseCommand):
    help = 'Initialize default TestCaseCategories'

    def handle(self, *args, **kwargs):
        categories = {
            "positive": {
                "name": "正向",
                "sub": [
                    {"code": "positive_necessary", "name": "仅传必要字段"},
                    {"code": "positive_valid", "name": "语义合法"},
                    {"code": "positive_enum", "name": "覆盖枚举组合"},
                    {"code": "positive_other", "name": "其他正向"},
                ]
            },
            "negative": {
                "name": "负向",
                "sub": [
                    {"code": "negative_invalid_class", "name": "无效类"},
                    {"code": "negative_missing_required", "name": "缺失必填字段"},
                    {"code": "negative_format_error", "name": "格式错误"},
                    {"code": "negative_type_error", "name": "类型错误"},
                    {"code": "negative_semantic_invalid", "name": "语义非法"},
                    {"code": "negative_other", "name": "其他负向"},
                ]
            },
            "boundary": {
                "name": "边界",
                "sub": [
                    {"code": "boundary_max_min", "name": "极大值/极小值"},
                    {"code": "boundary_out_of_range", "name": "超出最大/最小边界值"},
                    {"code": "boundary_null_empty", "name": "NULL/零值/空值"},
                    {"code": "boundary_length", "name": "字符串过长/过短"},
                    {"code": "boundary_time", "name": "时间边界"},
                    {"code": "boundary_file_size", "name": "文件大小边界"},
                    {"code": "boundary_array", "name": "数组边界（空数组、超长数组）"},
                ]
            },
            "security": {
                "name": "安全性",
                "sub": [
                    {"code": "security_auth", "name": "鉴权控制"},
                    {"code": "security_sql_injection", "name": "SQL注入"},
                    {"code": "security_fuzz", "name": "模糊输入"},
                    {"code": "security_xss", "name": "XSS注入"},
                    {"code": "security_cmd_injection", "name": "命令行注入"},
                    {"code": "security_json_injection", "name": "JSON注入"},
                    {"code": "security_nosql_injection", "name": "NoSQL注入"},
                    {"code": "security_jwt", "name": "JWT / Token 安全（过期）"},
                    {"code": "security_rate_limit", "name": "速率限制（过快点击）"},
                ]
            }
        }

        for p_code, p_data in categories.items():
            parent, created = TestCaseCategory.objects.get_or_create(
                code=p_code,
                defaults={'name': p_data['name']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created Parent: {p_data["name"]}'))
            
            for sub in p_data['sub']:
                _, sub_created = TestCaseCategory.objects.get_or_create(
                    code=sub['code'],
                    defaults={
                        'name': sub['name'],
                        'parent': parent
                    }
                )
                if sub_created:
                    self.stdout.write(f'  - Created Sub: {sub["name"]}')

        self.stdout.write(self.style.SUCCESS('All categories initialized.'))
