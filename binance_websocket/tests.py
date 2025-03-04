from django.test import TestCase
from decimal import Decimal
from .models import PriceUpdate

class PriceUpdateModelTest(TestCase):
    
    def setUp(self):
        self.price_update = PriceUpdate.objects.create(
            ticker_symbol='BTC/USDT',
            price=Decimal('50000.00'),
            volume=Decimal('10.5'),
            high_24h=Decimal('51000.00'),
            low_24h=Decimal('49000.00')
        )
    
    def test_price_update_creation(self):
        self.assertEqual(PriceUpdate.objects.count(), 1)
        self.assertEqual(self.price_update.ticker_symbol, 'BTC/USDT')
        self.assertEqual(self.price_update.price, Decimal('50000.00'))
        
    def test_string_representation(self):
        self.assertTrue(self.price_update.ticker_symbol in str(self.price_update))
        self.assertTrue(str(self.price_update.price) in str(self.price_update))
        
    def test_price_update_filtering(self):
        PriceUpdate.objects.create(
            ticker_symbol='ETH/USDT',
            price=Decimal('2000.00'),
            volume=Decimal('20.5')
        )
        
        btc_updates = PriceUpdate.objects.filter(ticker_symbol='BTC/USDT')
        eth_updates = PriceUpdate.objects.filter(ticker_symbol='ETH/USDT')
        
        self.assertEqual(btc_updates.count(), 1)
        self.assertEqual(eth_updates.count(), 1)
        self.assertEqual(PriceUpdate.objects.count(), 2)
