import tkinter as tk
import threading
import os
import pygame


def handle_click(param):
    print(f"Clicked button: {param}")
    game.update_text(param)


def build_button_grid():
    root = tk.Tk()
    root.title("Moves")

    # Window positioning
    tk_x = pygame_x + pygame_width
    tk_y = pygame_y - 30
    root.geometry(f"+{tk_x}+{tk_y}")

    data = [
        ["e4", "e5", "Ngf3"],
        [None, "exf8=Q+", "d4"],
        ["c4", "c5", None]
    ]

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    for i, row in enumerate(data):
        for j, val in enumerate(row):
            if val:
                tk.Button(frame, text=val, width=6, height=1, padx=2, pady=2,
                          command=lambda v=val: handle_click(v)).grid(row=i, column=j, padx=2, pady=2)
            else:
                tk.Label(frame, text="").grid(row=i, column=j)

    # Check regularly if pygame has finished
    def check_shutdown():
        if shutdown_event.is_set():
            root.destroy()
        else:
            root.after(100, check_shutdown)

    check_shutdown()
    root.mainloop()

# Assuming your main Pygame loop is like this:


class MyGame:

    def __init__(self):
        self.screen = None
        self.running = True
        self.text = ""
        self.font = None

    def run(self):
        pygame.init()
        self.screen = pygame.display.set_mode((pygame_width, pygame_height))
        pygame.display.set_caption("Pygame Window")
        self.font = pygame.font.SysFont(None, 28)

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.screen.fill((0, 0, 0))

            # Draw current text at the top center
            if self.text:
                text_surface = self.font.render(
                    self.text, True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=(320, 20))
                self.screen.blit(text_surface, text_rect)

            pygame.display.flip()

        pygame.quit()
        shutdown_event.set()

    def update_text(self, new_text):
        self.text = new_text


# Step 1: Set Pygame window position
pygame_x = 100
pygame_y = 100
pygame_width = 640
pygame_height = 480
os.environ['SDL_VIDEO_WINDOW_POS'] = f"{pygame_x},{pygame_y}"

shutdown_event = threading.Event()

# Create and start the Pygame thread
game = MyGame()
game_thread = threading.Thread(target=game.run)
game_thread.start()

# Run the Tkinter window in the main thread
build_button_grid()
