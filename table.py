class Event():
    def __init__(self, name, description, start_time, end_time, repeats, repeat_freq):
        self.name = name
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.repeats = repeats
        self.repeat_freq = repeat_freq