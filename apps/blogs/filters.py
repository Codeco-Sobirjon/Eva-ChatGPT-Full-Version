import django_filters
from django_filters import rest_framework as filters
from .models import Blog
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count


class BlogFilter(filters.FilterSet):
    title = filters.CharFilter(field_name="title", lookup_expr="icontains")
    created_at = filters.DateFromToRangeFilter(field_name="created_at", label="Filter by creation date range")
    new = filters.BooleanFilter(method="filter_new", label="New Blogs")
    old = filters.BooleanFilter(method="filter_old", label="Old Blogs")
    popular = filters.BooleanFilter(method="filter_popular", label="Popular Blogs")

    class Meta:
        model = Blog
        fields = ['title', 'created_at']

    def filter_new(self, queryset, name, value):
        if value:
            thirty_days_ago = timezone.now() - timedelta(days=30)
            return queryset.filter(created_at__gte=thirty_days_ago)
        return queryset

    def filter_old(self, queryset, name, value):
        if value:
            one_year_ago = timezone.now() - timedelta(days=365)
            return queryset.filter(created_at__lte=one_year_ago)
        return queryset

    def filter_popular(self, queryset, name, value):
        if value:
            return queryset.annotate(view_count=Count('views')).order_by('-view_count')
        return queryset
