class SoberanoError(Exception):
    pass

class SoberanoHTTPError(SoberanoError):
    def __init__(self, status_code: int, text: str):
        super().__init__(f"HTTP {status_code}: {text}")
        self.status_code = status_code
        self.text = text
