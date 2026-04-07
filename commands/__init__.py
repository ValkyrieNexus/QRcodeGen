from commands.generateQR import entry as generateQR_entry

commands = [generateQR_entry]


def start():
    for cmd in commands:
        cmd.start()


def stop():
    for cmd in commands:
        cmd.stop()
