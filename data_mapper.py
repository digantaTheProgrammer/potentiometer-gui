class DataMapper:
    def on_increasing(self, stepNumber, steps):
        return  stepNumber/steps
    
    def on_decreasing(self, stepNumber, steps):
        return (steps-stepNumber)/steps
