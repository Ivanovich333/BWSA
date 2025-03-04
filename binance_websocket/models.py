from django.db import models
from django.utils.translation import gettext_lazy as _

class PriceUpdate(models.Model):
    ticker_symbol = models.CharField(
        _('Ticker Symbol'),
        max_length=20,
        help_text=_('Trading pair (e.g., BTC/USDT)'),
        db_index=True
    )
    
    price = models.DecimalField(
        _('Price'),
        max_digits=30,
        decimal_places=10,
        help_text=_('Current price of the trading pair')
    )
    
    timestamp = models.DateTimeField(
        _('Timestamp'),
        auto_now_add=True,
        help_text=_('Time when the price update was recorded'),
        db_index=True
    )
    
    volume = models.DecimalField(
        _('Volume'),
        max_digits=30,
        decimal_places=10,
        null=True,
        blank=True,
        help_text=_('Trading volume in the base asset')
    )
    
    high_24h = models.DecimalField(
        _('24h High'),
        max_digits=30,
        decimal_places=10,
        null=True,
        blank=True,
        help_text=_('Highest price in the last 24 hours')
    )
    
    low_24h = models.DecimalField(
        _('24h Low'),
        max_digits=30,
        decimal_places=10,
        null=True,
        blank=True,
        help_text=_('Lowest price in the last 24 hours')
    )
    
    exchange = models.CharField(
        _('Exchange'),
        max_length=50,
        default='Binance',
        help_text=_('Source exchange for this price data')
    )
    
    class Meta:
        verbose_name = _('Price Update')
        verbose_name_plural = _('Price Updates')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ticker_symbol', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.ticker_symbol} @ {self.price} ({self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})"
