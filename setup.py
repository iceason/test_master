"""
TestMaster安装配置
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='testmaster',
    version='1.0.0',
    author='TestMaster Team',
    description='工业级API测试工具',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        'Django>=4.2',
        'djangorestframework>=3.14',
        'requests>=2.28',
        'PyYAML>=6.0',
        'click>=8.0',
        'celery>=5.3',
        'redis>=5.0',
    ],
    entry_points={
        'console_scripts': [
            'testmaster=cli.test_runner:cli',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)
