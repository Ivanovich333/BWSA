from django.shortcuts import render


def index(request):
    """
    Simple view to render the WebSocket test page.
    """
    return render(request, 'binance_websocket/index.html')
