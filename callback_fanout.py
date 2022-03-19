from gc import callbacks


class CallbackFanout:
    def __init__(self) -> None:
        self.callbacks = []

    def add_callback(self, callback):
        self.callbacks.append(callback)
    
    def remove_callback(self, callback):
        while callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def callback(self, *args):
        for callback in self.callbacks:
            callback(*args)
