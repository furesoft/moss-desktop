from gui import GUI

gui = GUI()
while gui.running:
    try:
        gui()
    except KeyboardInterrupt:
        gui.running = False