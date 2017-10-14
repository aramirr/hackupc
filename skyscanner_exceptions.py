class SkyscannerException(Exception):
    def __init__(self, value):
        self.value = value
        self.msg = value
    def __str__(self):
        return repr(self.value)