print('Python Code starting...')

import importlib
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image

import constants


# window dimensions
WIN_H = 420
WIN_W = 700


class SplashScreen(tk.Tk):
    '''
        Window that displays a photo background with the name of the 
        application. The current version and progress of modules being 
        loaded is also displayed.
    '''
    

    def __init__(self):
        super().__init__()
        
        # hides the outer frame of the window
        self.overrideredirect(1)
        
        #self.img_path = constants.MEDIA_DIR.joinpath('loading_background.jpg')
        self.img_path = 'load_bg.jpg'
        
        self.img = None

        self.progress_var = tk.IntVar()
        
        self._center_window()
        self._make_widgets()
        self.focus()
        
        
    def _center_window(self):
        x_offset = (self.winfo_screenwidth() - int(WIN_W)) // 2
        y_offset = (self.winfo_screenheight() - int(WIN_H)) // 2
        
        self.geometry(f'{WIN_W}x{WIN_H}+{x_offset}+{y_offset}')
        

    def _make_widgets(self):
        self.img = ImageTk.PhotoImage(Image.open(self.img_path))
        
        background = ttk.Label(self, image=self.img)
        background.pack()
        
        self.loading_lbl = tk.Label(
            self, anchor='w', text='Loading...', bg='white', 
            )
        self.loading_lbl.pack(fill='x')

        progress_bar = ttk.Progressbar(
            self, length=WIN_W - 3, maximum=len(constants.MODULES), 
            variable=self.progress_var
            )
        progress_bar.pack(fill='x')
        
        
    def _import_modules(self):
        '''
            Dynamically loads each module in the constant list of modules.
            Updates a label in self with the name of the module and a
            progress bar that indicates the progress of the modules.
        '''
        self.update()
        
        for i, module in enumerate(constants.MODULES, start=1):
            print(f'Loading {module}...')
            self.loading_lbl.configure(text=f'Loading {module}')
            
            self.update()
             
            importlib.import_module(module)
     
            self.progress_var.set(i)
            self.update()
            
        self.destroy()


if __name__ == '__main__':
    splash_screen = SplashScreen()
    splash_screen._import_modules()

    from controller import Controller

    app = Controller()
    app.main()
