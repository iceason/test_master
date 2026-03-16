#!/usr/bin/env python3
"""
TestMaster CLI - API测试命令行工具

支持独立运行和Django集成两种模式
"""

import click
import sys
import os
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_django():
    """设置Django环境"""
    # 添加项目根目录到Python路径
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # 设置Django设置模块
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TestCaseGenerator.settings')
    
    try:
        import django
        django.setup()
    except Exception as e:
        logger.error(f"Django初始化失败: {e}")
        sys.exit(1)


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """TestMaster - 工业级API测试工具"""
    pass


@cli.command()
@click.option('--yaml', '-y', type=click.Path(exists=True), help='YAML配置文件路径')
@click.option('--env', '-e', default='test', help='运行环境 (test/staging/prod)')
@click.option('--parallel', '-p', is_flag=True, help='并发执行测试用例')
@click.option('--report', '-r', type=click.Path(), help='报告输出目录')
@click.option('--format', '-f', type=click.Choice(['html', 'json', 'junit']), default='html', help='报告格式')
def run(yaml, env, parallel, report, format):
    """执行测试用例"""
    setup_django()
    
    from api.executor.core import TestExecutor, ExecutorConfig
    from api.executor.yaml_plugin import YamlPlugin
    
    if not yaml:
        click.echo("错误: 必须指定YAML配置文件 (--yaml)", err=True)
        sys.exit(1)
    
    try:
        # 加载YAML配置
        yaml_path = Path(yaml)
        yaml_content = yaml_path.read_text(encoding='utf-8')
        
        plugin = YamlPlugin()
        config_data = __import__('yaml').safe_load(yaml_content)
        
        # 创建执行器配置
        executor_config = ExecutorConfig(
            environment=env,
            report_dir=report
        )
        
        # 执行测试
        click.echo(f"🚀 开始执行测试 - 环境: {env}")
        click.echo(f"📁 配置文件: {yaml}")
        
        if config_data.get('type') == 'testcases':
            # 执行测试用例
            test_cases = config_data.get('testcases', [])
            click.echo(f"📝 测试用例数: {len(test_cases)}")
            
            executor = TestExecutor(executor_config)
            
            if parallel:
                click.echo("⚡ 并发执行模式")
                # TODO: 实现并发执行
            else:
                click.echo("📋 顺序执行模式")
                result = executor.execute_batch(test_cases)
                
                # 输出结果
                click.echo("\n" + "="*60)
                click.echo(f"✅ 执行完成")
                click.echo(f"总用例数: {result.total_cases}")
                click.echo(f"✓ 通过: {result.passed_cases} ({result.success_rate:.1f}%)")
                click.echo(f"✗ 失败: {result.failed_cases}")
                click.echo(f"⚠ 错误: {result.error_cases}")
                click.echo(f"⏱ 耗时: {result.duration_ms}ms")
                click.echo("="*60)
                
                # 保存报告
                if report:
                    report_path = Path(report)
                    report_path.mkdir(parents=True, exist_ok=True)
                    
                    import json
                    report_file = report_path / f'test_result_{env}.json'
                    report_file.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
                    click.echo(f"\n📊 报告已保存: {report_file}")
                
                # 退出码
                if result.failed_cases > 0 or result.error_cases > 0:
                    sys.exit(1)
        else:
            click.echo(f"❌ 不支持的YAML类型: {config_data.get('type')}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ 执行失败: {e}", err=True)
        logger.exception("执行异常")
        sys.exit(1)


@cli.command()
@click.argument('interface_id', type=int)
@click.option('--category', '-c', multiple=True, type=int, help='用例分类ID（可多次指定）')
def generate(interface_id, category):
    """生成测试用例"""
    setup_django()
    
    from api.models import Interface
    from api.test_case_generator import TestCaseGenerator
    from asgiref.sync import async_to_sync
    
    try:
        interface = Interface.objects.get(id=interface_id)
        click.echo(f"🔧 生成测试用例 - 接口: {interface.name} ({interface.method} {interface.path})")
        
        generator = TestCaseGenerator(interface)
        category_ids = list(category) if category else None
        
        count = async_to_sync(generator.generate)(category_ids)
        
        click.echo(f"✅ 成功生成 {count} 个测试用例")
        
    except Interface.DoesNotExist:
        click.echo(f"❌ 接口不存在: ID={interface_id}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ 生成失败: {e}", err=True)
        logger.exception("生成异常")
        sys.exit(1)


@cli.command()
@click.option('--scope', '-s', type=click.Choice(['testcase', 'interface', 'environment']), required=True, help='导出范围')
@click.option('--ids', '-i', multiple=True, type=int, help='ID列表（可多次指定）')
@click.option('--output', '-o', type=click.Path(), required=True, help='输出文件路径')
def export(scope, ids, output):
    """导出YAML配置"""
    setup_django()
    
    from api.executor.yaml_plugin import YamlPlugin
    
    if not ids:
        click.echo("❌ 必须指定至少一个ID", err=True)
        sys.exit(1)
    
    try:
        plugin = YamlPlugin()
        yaml_content = plugin.export_to_yaml(scope, list(ids))
        
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(yaml_content, encoding='utf-8')
        
        click.echo(f"✅ 已导出 {len(ids)} 个{scope}到: {output}")
        
    except Exception as e:
        click.echo(f"❌ 导出失败: {e}", err=True)
        logger.exception("导出异常")
        sys.exit(1)


@cli.command()
@click.argument('yaml_file', type=click.Path(exists=True))
@click.option('--mode', '-m', type=click.Choice(['merge', 'replace']), default='merge', help='导入模式')
def import_yaml(yaml_file, mode):
    """导入YAML配置"""
    setup_django()
    
    from api.executor.yaml_plugin import YamlPlugin
    
    try:
        yaml_path = Path(yaml_file)
        yaml_content = yaml_path.read_text(encoding='utf-8')
        
        plugin = YamlPlugin()
        result = plugin.import_from_yaml(yaml_content, mode)
        
        click.echo(f"✅ 导入完成 - 模式: {mode}")
        click.echo(f"📊 结果统计:")
        for key, value in result.items():
            click.echo(f"  {key}: {value}")
        
    except Exception as e:
        click.echo(f"❌ 导入失败: {e}", err=True)
        logger.exception("导入异常")
        sys.exit(1)


@cli.command()
@click.option('--case-id', '-c', type=int, help='测试用例ID')
@click.option('--env', '-e', type=int, required=True, help='环境ID')
def execute(case_id, env):
    """执行单个测试用例（集成模式）"""
    setup_django()
    
    from api.models import TestCase, Environment
    from api.executor.core import TestExecutor, ExecutorConfig
    
    try:
        test_case = TestCase.objects.get(id=case_id)
        environment = Environment.objects.get(id=env)
        
        click.echo(f"🚀 执行测试用例: {test_case.name}")
        click.echo(f"🌍 环境: {environment.name} ({environment.base_url})")
        
        executor_config = ExecutorConfig(
            environment=environment.code,
            base_url=environment.base_url,
            **environment.config
        )
        executor = TestExecutor(executor_config)
        
        env_config = {
            'base_url': environment.base_url,
            **environment.config
        }
        result = executor.execute_test_case(test_case, env_config)
        
        # 输出结果
        click.echo("\n" + "="*60)
        if result.status == 'passed':
            click.echo(f"✅ 测试通过")
        elif result.status == 'failed':
            click.echo(f"❌ 测试失败")
        else:
            click.echo(f"⚠️  执行错误")
        
        click.echo(f"状态码: {result.response_status}")
        click.echo(f"响应时间: {result.response_time_ms}ms")
        click.echo(f"断言: {result.assertions_passed}✓ / {result.assertions_failed}✗")
        
        if result.error_message:
            click.echo(f"错误: {result.error_message}")
        
        click.echo("="*60)
        
        # 退出码
        if result.status != 'passed':
            sys.exit(1)
            
    except TestCase.DoesNotExist:
        click.echo(f"❌ 测试用例不存在: ID={case_id}", err=True)
        sys.exit(1)
    except Environment.DoesNotExist:
        click.echo(f"❌ 环境不存在: ID={env}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ 执行失败: {e}", err=True)
        logger.exception("执行异常")
        sys.exit(1)


@cli.command()
def list_environments():
    """列出所有环境"""
    setup_django()
    
    from api.models import Environment
    
    try:
        environments = Environment.objects.filter(is_active=True)
        
        if not environments.exists():
            click.echo("暂无环境配置")
            return
        
        click.echo("可用环境:")
        click.echo("="*60)
        for env in environments:
            click.echo(f"ID: {env.id} | {env.name} ({env.code})")
            click.echo(f"   URL: {env.base_url}")
            if env.description:
                click.echo(f"   描述: {env.description}")
            click.echo()
        
    except Exception as e:
        click.echo(f"❌ 查询失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--output-dir', '-o', type=click.Path(), required=True, help='输出目录')
def sync_export(output_dir):
    """同步数据库到YAML文件（版本控制）"""
    setup_django()
    
    from api.executor.yaml_plugin import YamlPlugin
    
    try:
        plugin = YamlPlugin()
        plugin.sync_db_to_yaml(output_dir)
        
        click.echo(f"✅ 已同步数据库到: {output_dir}")
        
    except Exception as e:
        click.echo(f"❌ 同步失败: {e}", err=True)
        logger.exception("同步异常")
        sys.exit(1)


@cli.command()
@click.argument('yaml_dir', type=click.Path(exists=True))
@click.option('--mode', '-m', type=click.Choice(['merge', 'replace']), default='merge', help='导入模式')
def sync_import(yaml_dir, mode):
    """同步YAML文件到数据库（部署初始化）"""
    setup_django()
    
    from api.executor.yaml_plugin import YamlPlugin
    
    try:
        plugin = YamlPlugin()
        results = plugin.sync_yaml_to_db(yaml_dir, mode)
        
        click.echo(f"✅ 已同步YAML到数据库 - 模式: {mode}")
        click.echo("📊 结果统计:")
        for key, value in results.items():
            click.echo(f"\n{key}:")
            for k, v in value.items():
                click.echo(f"  {k}: {v}")
        
    except Exception as e:
        click.echo(f"❌ 同步失败: {e}", err=True)
        logger.exception("同步异常")
        sys.exit(1)


if __name__ == '__main__':
    cli()
