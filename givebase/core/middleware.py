# core/middleware.py

class COOPMiddleware:
    """
    Middleware to set Cross-Origin-Opener-Policy headers for Base Account SDK.
    
    Base Account SDK requires COOP to NOT be 'same-origin' so it can 
    communicate with the Base Account app via popup.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Remove or set COOP to allow popups
        # Options: None, 'unsafe-none', or 'same-origin-allow-popups'
        response['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
        
        # Also set COEP if needed
        response['Cross-Origin-Embedder-Policy'] = 'unsafe-none'
        
        return response