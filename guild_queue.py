import threading

class Guild_Queue_Item:
    def __init__(self, thread, audio):
        self.thread = thread
        self.audio = audio

    