import pygame
import sys
import threading

try:
    from grid import Grid
except ImportError:
    raise ImportWarning("Grid library is unavailable, do not attempt to use Grids")
    
def getKeycodes():
    """A method to get all the keycodes
     used in pygame in to a dictionary"""
    
    keycodes = {item[2:].lower() : eval("pygame." + item)
                for item in dir(pygame) if "K_" in item}
    
    return keycodes

KEYCODES = getKeycodes()

def key(key):
    return KEYCODES[key]

class Renderer(threading.Thread):
    def __init__(self, RENDERRATE, *renderFuncs):
        self.clock = pygame.time.Clock()
        
        self.renderFuncs = renderFuncs
        self.RENDERRATE = RENDERRATE
        self.deltaTime = self.clock.tick(self.RENDERRATE)

        threading.Thread.__init__(self)
        
    def run(self):
        while True:
            self.deltaTime = self.clock.tick(self.RENDERRATE)
            
            for func in self.renderFuncs:
                func()
                
class Game():
    def __init__(self, WIDTH, HEIGHT, gridsize = None,
                 FRAMERATE = 0, RENDERRATE = None, fillcolour = (0, 0, 0),
                 fullscreen = False):
        
        if fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
            
        self.SCREENSIZE = self.screen.get_size()
        self.SCREENRECT = pygame.Rect((0, 0), self.SCREENSIZE)
        self.WIDTH, self.HEIGHT = self.SCREENSIZE
            
        self.fillcolour = fillcolour
        
        self.returnValue = None
        self.dirtyRects = []
        self.oldDirtyRects = []
        
        self.clock = pygame.time.Clock()
        self.FRAMERATE = FRAMERATE
        
        if RENDERRATE is None:
            self.renderer = None
        else:
            self.renderer = Renderer(RENDERRATE, self.render, self.updateDisplay)
        
        self.deltaTime = self.clock.tick(self.FRAMERATE)
        
        if gridsize:
            self.grid = Grid(self.screen, gridsize)
            
        self.ended = False

    def updateDisplay(self):
        #self.screen.unlock()
        
        if self.dirtyRects:
            pygame.display.update(self.dirtyRects + self.oldDirtyRects)
        else:
            pygame.display.update()
        
        #self.screen.lock()

        self.screen.fill(self.fillcolour)
        
    def setup(self):
        """Hook for setup"""
        pass
        
    def update(self):
        """Hook for game update"""
        pass
    
    def render(self):
        """Hook for game render"""
        pass
    
    def handleEvent(self, event):
        """Hook for event handling"""
        pass
    
    def handleInputs(self):
        """Input handling"""
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
                
            else:
                self.handleEvent(event)
        
    def run(self):
        self.setup()
        
        if self.renderer:
            self.renderer.start()
        
        while True:
            
            self.deltaTime = self.clock.tick(self.FRAMERATE) / 1000
                
            self.oldDirtyRects = self.dirtyRects
            self.dirtyRects = []
            
            self.update()
            
            if not self.renderer:
                self.render()
                self.updateDisplay()
            
            self.handleInputs()
            
            if self.returnValue is not None:
                return self.returnValue
    
    def quit(self):
        self.ended = True
        pygame.quit()
        sys.exit(0)
