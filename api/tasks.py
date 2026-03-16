from __future__ import annotations

from celery import shared_task
from asgiref.sync import async_to_sync
from .models import Interface
from .test_case_generator import TestCaseGenerator


@shared_task(bind=True)
def generate_test_cases_task(self, interface_id: int, category_ids: list[int] | None = None) -> str:
    interface = Interface.objects.get(id=interface_id)
    generator = TestCaseGenerator(interface)
    async_to_sync(generator.generate)(category_ids or [])
    return "ok"

