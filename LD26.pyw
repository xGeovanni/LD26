#Must add potato

import game as gameEngine
import pygame
import random
from math import ceil
from time import sleep

pygame.font.init()
pygame.mixer.init()

COLOURS = {"white" : (255, 255, 255),
           "black" : (0, 0, 0),
           "red" : (200, 0, 0),
           "bright_red" : (255, 32, 32),
           "green" : (0, 200, 0),
           "steel" : (224, 223, 219),
           "grey46" : (117, 117, 117),
           "lime" : (153, 253, 56),
           "dark_brown" : (101, 67, 33),
           "puke" : (165, 165, 2)}

SOUNDS_FOLDER = "Sounds/"
SCREENS_FOLDER = "Screens/"

SOUNDS = {"hurt" : pygame.mixer.Sound(SOUNDS_FOLDER + "Hit_Hurt9.ogg"),
          "shoot" : pygame.mixer.Sound(SOUNDS_FOLDER + "Laser_Shoot25.ogg"),
          "squelch" : pygame.mixer.Sound(SOUNDS_FOLDER + "Powerup10.ogg")}

for sound in SOUNDS.values():
    sound.set_volume(0.5)
                               
class Entity():
    def __init__(self, game,  x, y, colour, size, speed, sigma = None):
        self.game = game
        self.pos = pygame.math.Vector2(x, y)
        self.colour = colour
        self.size = size
        
        if sigma:
           self.speed = random.gauss(speed, sigma) 
        else:
            self.speed = speed
        
        self.rect = pygame.Rect(self.pos, self.size)
        self.direction = pygame.math.Vector2(0, 0)
        
    def draw(self):
        pygame.draw.rect(self.game.screen, self.colour, self.rect)
        
    def move(self):
        self.pos[0] += self.direction[0] * self.speed * self.game.deltaTime
        self.pos[1] += self.direction[1] * self.speed * self.game.deltaTime
        
        self.rect = pygame.Rect(self.pos, self.size)
        
    def update(self):
        self.move()
        
class Player(Entity):
    def __init__(self, game, bm, colour = COLOURS["red"], size = (32, 32),
                speed = 180, maxHealth = 100):
        
        x = (game.WIDTH - size[0]) / 2
        y = (game.HEIGHT - size[1]) / 2
        
        Entity.__init__(self, game, x, y, colour, size, speed)
        
        self.maxHealth = maxHealth
        self.health = self.maxHealth
        
        self.midpoint = pygame.math.Vector2(self.pos[0] + self.size[0] / 2,
                                            self.pos[1] + self.size[1] / 2)
       
        self.bm = bm
        
        self.timeBetweenHurtSounds = 0.5
        self.timeToHurtSound = 0
        
    def damage(self, amount):
        self.health -= amount
                
        if self.timeToHurtSound <= 0:
            SOUNDS["hurt"].play()
            self.timeToHurtSound = self.timeBetweenHurtSounds
        
    def update(self):
        self.move()
        
        self.midpoint = pygame.math.Vector2(self.pos[0] + self.size[0] / 2,
                                            self.pos[1] + self.size[1] / 2)
        
        for enemy in self.game.em.enemies:
            if self.rect.colliderect(enemy.rect) and hasattr(enemy, "damageRate"):
                self.damage(enemy.damageRate * self.game.deltaTime)                    
        
        self.timeToHurtSound -= self.game.deltaTime
        
        if self.health <= 0:
            self.die()
        
    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: #Left click
                self.fire()
            
        elif event.type == pygame.KEYDOWN:
            self.handleKey(event.key, True)
            
        elif event.type == pygame.KEYUP:
            self.handleKey(event.key, False)
    
    def handleKey(self, key, boolean):
        if key in (gameEngine.key("w"), gameEngine.key("up")):
            self.direction[1] = -1 * boolean
        elif key in (gameEngine.key("s"), gameEngine.key("down")):
            self.direction[1] = 1 * boolean
        elif key in (gameEngine.key("a"), gameEngine.key("left")):
            self.direction[0] = -1 * boolean
        elif key in (gameEngine.key("d"), gameEngine.key("right")):
            self.direction[0] = 1 * boolean
        
    def fire(self):
        try:
            bulletDirection = (pygame.math.Vector2(pygame.mouse.get_pos()) - self.midpoint).normalize()
            
            self.bm.addBullet(Bullet(self.game, self.midpoint, bulletDirection))
            #SOUNDS["shoot"].play()
            
        except ValueError:
            pass #Tried to normalize vector of (0, 0)
                 #as the player clicked on the midpoint
        
    def die(self):
        self.game.gameOver()
        
class HealthBar():
    def __init__(self, game, pos, size):
        self.game = game
        self.pos = pos
        
        self.redBarRect = pygame.Rect(pos, size)
        self.greenBarRect = self.redBarRect.copy()
        
        self.surface = pygame.Surface(size).convert()
        self.surface.set_alpha(128)
        
    def draw(self):
        pygame.draw.rect(self.surface, COLOURS["red"], self.redBarRect)
        pygame.draw.rect(self.surface, COLOURS["green"], self.greenBarRect)
        
        self.game.screen.blit(self.surface, self.pos)
        
    def update(self, health = None):
        """Health as a fraction of total"""
        
        if health is None:
            health = self.game.player.health / self.game.player.maxHealth

        self.greenBarRect.size = (self.redBarRect.size[0] * health, self.greenBarRect.size[1])
        #the green bar rect is inflated by the red bar rect length,
        #multiplied by the reciprocal of health multiplied be negative one.
        
class ScoreManager():        
    def __init__(self, game, pos, font, colour = COLOURS["black"]):
        self.game = game
        
        self.score = 0
        self.multiplier = 1
        
        self.colour = colour
        self.pos = pos
        
        self.font = font
        
        self.updateScoreImg()
    
    def updateScoreImg(self): 
        self.scoreImg = self.font.render(str(int(self.score)), True, self.colour).convert_alpha()
        self.scoreImg.set_alpha(128)
        self.scoreAsOfLastScoreImg = self.score
        
    def changeScore(self, change):
        self.score += change * self.multiplier
        
    def update(self):
        if not self.score == self.scoreAsOfLastScoreImg:
            self.updateScoreImg()
            
    def draw(self):
        self.game.screen.blit(self.scoreImg, self.pos)

class HUD():
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("Verdana, Lucida Console, Arial", 96)
        self.smallFont = pygame.font.SysFont("Verdana, Lucida Console, Arial", 48)
        
        healthBarRect = ((0, 0), (self.game.WIDTH * (3 / 4), self.game.HEIGHT / 8))
        scorePos = (self.game.WIDTH * (3 / 4), 0)
        
        self.healthBar = HealthBar(self.game, healthBarRect[0], healthBarRect[1])
        self.sm = ScoreManager(self.game, scorePos, self.font)
        
    def update(self):
        self.healthBar.update()
        self.sm.update()
        
    def draw(self):
        self.healthBar.draw()
        self.sm.draw()
        
class Bullet(Entity):
    def __init__(self, game, pos, direction, side = "player", colour = COLOURS["grey46"],
                size = (8, 8), speed = 300, damage = 6):
        Entity.__init__(self, game, pos[0], pos[1], colour, size, speed)
        
        self.direction = direction
        self.damage = damage
        self.side = side
        
    def draw(self):
        pygame.draw.ellipse(self.game.screen, self.colour, self.rect)
        
class BulletManager():
    def __init__(self, game):
        self.bullets = []
        self.game = game
        
    def addBullet(self, bullet):
        self.bullets.append(bullet)
        
    def delBullet(self, bullet):
        self.bullets.remove(bullet)
        del(bullet)
        
    def update(self):
        for bullet in self.bullets:
            bullet.update()
            
            if not bullet.rect.colliderect(self.game.SCREENRECT):
                self.delBullet(bullet)
            
            elif bullet.side == "player":
                collidedEnemy = bullet.rect.collidelist([enemy.rect for enemy in self.game.em.enemies])
                
                if collidedEnemy != -1:
                    self.game.em.damageEnemy(collidedEnemy, bullet)
                    self.delBullet(bullet)
                    
            elif bullet.side == "enemy":
                if bullet.rect.colliderect(self.game.player.rect):
                    self.game.player.damage(bullet.damage / 2)
                    self.delBullet(bullet)
                    
    
            
    def draw(self):
        for bullet in self.bullets:
            bullet.draw()

class Enemy(Entity):
    def __init__(self, game, em, type, scoreValue,  x, y, maxHealth, colour, size, speed):
        self.maxHealth = maxHealth
        self.health = self.maxHealth
        self.em = em
        self.type = type
        self.scoreValue = scoreValue
        
        self.fireChance = 0
        
        self.baseTimeUntilFire = .5
        self.timeUntilFire = self.baseTimeUntilFire
        
        Entity.__init__(self, game, x, y, colour, size, speed, sigma = 20)
        
    def calcDirection(self):
        return (self.game.player.pos - self.pos).normalize()
    
    def specificUpdate(self):
        pass
    
    def update(self):
        self.move()
        
        if self.fireChance:
            self.timeUntilFire -= self.game.deltaTime
            
            if self.timeUntilFire <= 0 and random.randrange(self.fireChance) == 0:
                self.fire()
                self.timeUntilFire = self.baseTimeUntilFire
        
        if self.health <= 0:
            self.die()
            
        self.specificUpdate()
            
    def fire(self, misaim = 10):        
        midpoint = pygame.math.Vector2(self.pos[0] + self.size[0] / 2,
                                       self.pos[1] + self.size[1] / 2)
        try:
            shotPoint = pygame.math.Vector2([random.gauss(i, misaim) for i in self.game.player.midpoint])
            bulletDirection = (shotPoint - midpoint).normalize()
            
            self.game.bm.addBullet(Bullet(self.game, midpoint, bulletDirection, "enemy", colour = COLOURS["black"]))
            
            SOUNDS["shoot"].play()
        except ValueError:
            pass #player.midpoint and shotpoint are exactly alligned, and therefore it attempted
                 # to normalise a vector of zero
            
    def damage(self, amount):
        self.health -= amount
        
    def die(self):
        self.em.delEnemy(self)
        self.game.hud.sm.changeScore(self.scoreValue)

        
class Slime(Enemy):
    def __init__(self, game, em,  x, y, generation, size = (32, 32),
                 maxGenerations = 3, damageRate = 4):
        self.generation = generation
        self.maxGenerations = maxGenerations
        
        self.damageRate = damageRate / self.generation ** 2
        
        size = [size[0] / self.generation, size[1] / self.generation]
        
        Enemy.__init__(self, game, em, "slime", 30 / self.generation, x, y,
                       1, COLOURS["lime"], size, 150)
        
        self.upperSize = self.rect.size[1]
        self.lowerSize = self.rect.size[1] * 0.75
        
        self.animationLength = 1 #Frames
        
        self.shrinking = True #If false then growing
        
    def animate(self):
        if self.shrinking:
            self.size[1] -= (self.upperSize - self.lowerSize) / self.animationLength * self.game.deltaTime
        
        else:
            self.size[1] += (self.upperSize - self.lowerSize) / self.animationLength * self.game.deltaTime
        
        if self.rect.size[1] >= self.upperSize:
            self.shrinking = True
            
        elif self.rect.size[1] <= self.lowerSize:
            self.shrinking = False
            
    def specificUpdate(self):
        if self.generation < 3:
            self.animate()
        
    def die(self):
        if self.generation < self.maxGenerations:
            self.em.spawnSlimes(2, self.generation, self.pos, True)
        
        self.game.hud.sm.changeScore(self.scoreValue)
        self.em.delEnemy(self)
        
class Gunman(Enemy):
    def __init__(self, game, em, x, y, fireChance = 80):
        self.campPoint = pygame.math.Vector2(random.randrange(game.WIDTH),
                                             random.randrange(game.HEIGHT))
        
        Enemy.__init__(self, game, em, "gunman", 200, x, y, 30, COLOURS["dark_brown"], (28, 28), 80)
        
        self.fireChance = fireChance
        
    def calcDirection(self):
        if not self.rect.collidepoint(self.campPoint):
            return (self.campPoint - self.pos).normalize()
        else:
            return pygame.math.Vector2(0, 0)
    
class Zombie(Enemy):
    def __init__(self, game, em, x, y, damageRate = 10):
        Enemy.__init__(self, game, em, "zombie", 50, x, y, 10, COLOURS["puke"], (24, 24), 200)
        
        self.damageRate = damageRate
        
    def draw(self):
        pygame.draw.ellipse(self.game.screen, self.colour, self.rect)
        
class Tank(Enemy):
    def __init__(self, game, em, x, y, fireChance = 100):
        if x < 0 or x > game.WIDTH:
            size = (48, 32)
        else:
            size = (32, 48)
        
        Enemy.__init__(self, game, em, "tank", 500, x, y, 100, COLOURS["steel"], size, 50)
        
        if x < 0:
            self.direction[0] = 1
        elif x > self.game.WIDTH:
            self.direction[0] = -1
        elif y < 0:
            self.direction[1] = 1
        else:
            self.direction[1] = -1
            
        self.fireChance = fireChance
        
    def calcDirection(self):
        return self.direction
        
    def specificUpdate(self):
        if not self.rect.colliderect(self.game.SCREENRECT):
            self.em.delEnemy(self)
        
class EnemyManager():
    def __init__(self, game, spawnRate = 180, damper = 14):
        self.enemies = []
        
        self.game = game
        self.spawnRate = spawnRate    
        
        self.damper = damper #Dampener for the increase of spawn rate over time
        
        self.spawnSpots = self.createSpawnSpots()
        
        self.baseTimeToSpawn = 1
        self.timeToSpawn = self.baseTimeToSpawn
        
        self.timeBetweenCalcDirection = .1
        self.timeToCalcDirection = 0
        
    def createSpawnSpots(self, desiredAmount = 16, deviation = 0.2):
        """Should optimise"""
        
        spawnSpots = []
        
        while len(spawnSpots) < desiredAmount:
            new = (random.randrange(round(self.game.WIDTH * -deviation),
                                    round(self.game.WIDTH * (1 + deviation))),
                   random.randrange(round(self.game.HEIGHT * -deviation),
                                    round(self.game.HEIGHT * (1 + deviation))))
        
            if not self.game.SCREENRECT.collidepoint(new):
                spawnSpots.append(new)
                
        return spawnSpots
                
    def addEnemy(self, enemy):
        self.enemies.append(enemy)
        
    def damageEnemy(self, enemy, bullet):
        """Do not confuse with delEnemy. This will split slimes"""
        
        if isinstance(enemy, int):
            enemy = self.enemies[enemy]
        
        enemy.damage(bullet.damage)
    
    def delEnemy(self, enemy):
        self.enemies.remove(enemy)
        del(enemy)

    def spawnSlimes(self, num = 1, baseGeneration = 0, pos = None, variation = False, sigma = 20):
        if pos is None:
            pos = random.choice(self.spawnSpots)
        
        for i in range(num):
            if variation:
                self.addEnemy(Slime(self.game, self, random.gauss(pos[0], sigma), random.gauss(pos[1], sigma), baseGeneration + 1))
            
            else:
                self.addEnemy(Slime(self.game, self, pos[0], pos[1], baseGeneration + 1))
            
        if baseGeneration == 1:
            SOUNDS["squelch"].play()
            
    def spawnEnemies(self, num = 1):
        toSpawn = random.randrange(20)
        pos = random.choice(self.spawnSpots)
        
        if toSpawn in range(13):
            self.spawnSlimes(pos = pos)
            
        elif toSpawn in range(16):
            self.addEnemy(Zombie(self.game, self, pos[0], pos[1]))
        
        elif toSpawn in range(18):
            self.addEnemy(Gunman(self.game, self, pos[0], pos[1]))
            
        else:
            self.addEnemy(Tank(self.game, self, pos[0], pos[1]))
            
    def calcDirections(self):
        for enemy in self.enemies:
            enemy.direction = enemy.calcDirection()
        
    def update(self):
        for enemy in self.enemies:
            enemy.update()
            
        self.timeToSpawn -= self.game.deltaTime
        self.timeToCalcDirection -= self.game.deltaTime
            
        if self.timeToSpawn <= 0 and random.randrange(ceil(self.spawnRate / (self.game.timeElapsed / self.damper))) == 0:
            self.spawnEnemies()
            self.timeToSpawn = self.baseTimeToSpawn
            
        if self.timeToCalcDirection <= 0:
            self.calcDirections()
            
    def draw(self):
        for enemy in self.enemies:
            enemy.draw()
            
class Cursor():
    def __init__(self, game, colour = COLOURS["bright_red"], radius = 4):
        pygame.mouse.set_visible(False)
        self.game = game
        self.radius = radius
        
        self.colour = colour
        
    def draw(self):
        pos = [i + self.radius for i in pygame.mouse.get_pos()]
        
        pygame.draw.circle(self.game.screen, self.colour, pos, self.radius * 2, 1)
        
        pygame.draw.circle(self.game.screen, self.colour,
                           pos, self.radius)

class MinimalDeathmatch(gameEngine.Game):
    def __init__(self):
        gameEngine.Game.__init__(self, 0, 0, gameName = "Minimal Deathmatch", fillcolour = COLOURS["white"], FRAMERATE = 60, fullscreen = True)

    def setup(self):
        self.em = EnemyManager(self)
        self.bm = BulletManager(self)
        self.hud = HUD(self)
        self.player = Player(self, self.bm)
        
        self.cursor = Cursor(self)
        
        pygame.mixer.music.load(SOUNDS_FOLDER + "music.ogg")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
        
        self.muted = False
        self.firstFrame = True
        
        self.timeElapsed = 0

    def update(self):
        
        self.timeElapsed += self.deltaTime
        
        self.player.update()
        self.bm.update()
        self.em.update()
        self.hud.update()

    def render(self):
        self.bm.draw()
        self.player.draw()
        self.em.draw()
        self.hud.draw()
        self.cursor.draw()

    def handleEvent(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == gameEngine.key("escape"):
                pygame.display.iconify()
                
            elif event.key == gameEngine.key("m"):
                self.toggleMute()
            
        self.player.handleEvent(event)
        
    def toggleMute(self, vol = 0.5):
        if self.muted:
            for sound in SOUNDS.values():
                sound.set_volume(vol)
            pygame.mixer.music.set_volume(vol)
            self.muted = False
        
        else:
            for sound in SOUNDS.values():
                sound.set_volume(0)
            pygame.mixer.music.set_volume(0)
            self.muted = True
            
    def title(self):
        if self.aspectRatio == (4, 3):
            img = pygame.image.load(SCREENS_FOLDER + "Title4x3.png").convert()
            
        else:
            img = pygame.image.load(SCREENS_FOLDER + "Title16x9.png").convert()
            #Using 16x9 as default.
            
        img = pygame.transform.scale(img, (self.WIDTH, self.HEIGHT))
                                     
        self.screen.blit(img, (0, 0))
        pygame.display.update()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                             
                elif event.type == pygame.KEYDOWN:
                    if event.key == gameEngine.key("escape"):
                        pygame.display.iconify()
                    else:
                        return
        
    def gameOver(self, fadeout = 3000):
        pygame.mixer.music.fadeout(fadeout)
        sleep(fadeout / 1000)
        
        self.screen.fill(COLOURS["black"])
        
        text = (self.hud.font.render("Game Over", True, COLOURS["red"], COLOURS["black"]),
                self.hud.font.render("You lasted " + str(int(self.timeElapsed)) + " seconds", True, COLOURS["red"], COLOURS["black"]),
                self.hud.font.render("You scored " + str(int(self.hud.sm.score)) + " points", True, COLOURS["red"], COLOURS["black"]),
                self.hud.smallFont.render("Press any key to exit", True, COLOURS["red"], COLOURS["black"]))
        
        self.screen.blit(text[0], ((self.WIDTH - text[0].get_width()) / 2, 0))
        self.screen.blit(text[3], ((self.WIDTH - text[3].get_width()) / 2, (self.HEIGHT - text[3].get_height())))
        
        cumulativeHeight = (self.HEIGHT - sum([item.get_height() for item in text])) / 2
        
        for item in text[1 : 3]:
            self.screen.blit(item, ((self.WIDTH - item.get_width()) / 2, cumulativeHeight))
            cumulativeHeight += item.get_height()
            
        pygame.display.update()
        pygame.event.clear()
        
        while True:
            for event in pygame.event.get():
                if event.type in (pygame.QUIT, pygame.KEYDOWN):
                    self.quit()

def main():
    game = MinimalDeathmatch()
    game.run()

if __name__ == "__main__":
    main()
    