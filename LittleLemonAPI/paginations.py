# paginations.py
from rest_framework.pagination import PageNumberPagination

class MenuItemPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'  
    max_page_size = 20 

class OrderPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'  
    max_page_size = 10 
