from gui import GUI


def run_gui():
    gui = GUI()
    while gui.running:
        try:
            gui()
        except KeyboardInterrupt:
            gui.running = False


if __name__ == "__main__":
    run_gui()
