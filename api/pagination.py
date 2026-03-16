from rest_framework.pagination import PageNumberPagination


class FlexiblePageNumberPagination(PageNumberPagination):
    """
    Extends PageNumberPagination to support:
    - ?page_size=N  — override page size per request
    - ?no_page=true — disable pagination entirely
    """
    page_size_query_param = 'page_size'
    max_page_size = 10000

    def paginate_queryset(self, queryset, request, view=None):
        if request.query_params.get('no_page', '').lower() in ('true', '1', 'yes'):
            return None
        return super().paginate_queryset(queryset, request, view)
