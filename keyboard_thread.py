import threading


class KeyboardThread(threading.Thread):

    def __init__(self, text: str, input_cbk=None, name='keyboard-input-thread'):
        self.input_cbk = input_cbk
        self.text = text
        self.is_run = True
        super(KeyboardThread, self).__init__(name=name)
        self.start()

    def run(self):
        while self.is_run:
            self.input_cbk(input(self.text))  # waits to get input + Return

    def stop(self):
        self.is_run = False
