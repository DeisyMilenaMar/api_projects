from django.urls import path
from binance_trader_api.views import TransactionCreateView

app_name = 'binance_trader_api'

urlpatterns = [
    path(
        'transactions/create/',
        TransactionCreateView.as_view(),
        name='transactions_create'
    ),
]