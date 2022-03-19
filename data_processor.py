import time
class DataProcessor:
    def __init__(self, callbacks, mapper):
        self.callbacks = callbacks
        self.conn_callback = None
        self.mapper = mapper
    
    def set_connection_callback(self, conn_callback):
        self.conn_callback = conn_callback

    def on_connection(self, steps):
        self.conn_time = time.monotonic()
        if self.conn_callback:
            self.conn_callback(steps)

    def mark_loop(self, full):
        for callback in self.callbacks:
            if full:
                callback.on_full_loop()
            else:
                callback.on_half_loop()

    def map_data(self, stepNumber, steps, increasing):
        if increasing:
            return self.mapper.on_increasing(stepNumber, steps)
        else:
            return self.mapper.on_decreasing(stepNumber, steps)

    def process_data(self, data):
        data_time = time.monotonic() - self.conn_time
        response = data[0]
        stepNumber = data[1]
        steps = data[2]
        dir = data[3]
        input = self.map_data(stepNumber, steps, dir)
        for callback in self.callbacks:
            callback.on_data(data_time, input, response)

    def processor(self, data):
        if len(data) == 2:
            self.on_connection(data[1])
            data = [data[0]]

        if len(data) == 1:
            self.mark_loop(data[0])
        elif len(data) == 4:
            self.process_data(data)



                    
            