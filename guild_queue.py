import threading

class Guild_Queue_Item:
    def __init__(self, thread):
        #thread check_queue is running on
        self.thread = thread
        #audio that is currently playing
        self.audio = None
        #queue of items to be played
        self.queue = []

    def add_song(self, song_info):
        self.queue.append(song_info)

    