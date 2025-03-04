# Generated by Django 5.1.6 on 2025-03-04 11:44

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PriceUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticker_symbol', models.CharField(db_index=True, help_text='Trading pair (e.g., BTC/USDT)', max_length=20, verbose_name='Ticker Symbol')),
                ('price', models.DecimalField(decimal_places=10, help_text='Current price of the trading pair', max_digits=30, verbose_name='Price')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True, help_text='Time when the price update was recorded', verbose_name='Timestamp')),
                ('volume', models.DecimalField(blank=True, decimal_places=10, help_text='Trading volume in the base asset', max_digits=30, null=True, verbose_name='Volume')),
                ('high_24h', models.DecimalField(blank=True, decimal_places=10, help_text='Highest price in the last 24 hours', max_digits=30, null=True, verbose_name='24h High')),
                ('low_24h', models.DecimalField(blank=True, decimal_places=10, help_text='Lowest price in the last 24 hours', max_digits=30, null=True, verbose_name='24h Low')),
                ('exchange', models.CharField(default='Binance', help_text='Source exchange for this price data', max_length=50, verbose_name='Exchange')),
            ],
            options={
                'verbose_name': 'Price Update',
                'verbose_name_plural': 'Price Updates',
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['ticker_symbol', 'timestamp'], name='binance_web_ticker__7ec17d_idx')],
            },
        ),
    ]
