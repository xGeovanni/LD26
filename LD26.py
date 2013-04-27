import game
import pygame
import random
from math import ceil

pygame.font.init()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
BRIGHT_RED = (255, 32, 32)
GREEN = (0, 200, 0)

def meanVector(a, b, weights):
    return pygame.math.Vector2((a[0] * weights[0] + b[0] * weights[1]) / 2,
                               (a[1] * weights[0] + b[1] * weights[1]) / 2)
                               
class Entity():
    def __init__(self, hg,  x, y, colour, size, speed):
        self.hg = hg
        self.pos = pygame.math.Vector2(x, y)
        self.colour = colour
        self.size = size
        self.speed = speed
        
        self.rect = pygame.Rect(self.pos, self.size)
        self.direction = pygame.math.Vector2(0, 0)
        
    def draw(self):
        pygame.draw.rect(self.hg.screen, self.colour, self.rect)
        
    def move(self):
        self.pos[0] += self.direction[0] * self.speed * self.hg.deltaTime
        self.pos[1] += self.direction[1] * self.speed * self.hg.deltaTime
        
        self.rect = pygame.Rect(self.pos, self.size)
        
    def update(self):
        self.move()
        
class Player(Entity):
    def __init__(self, hg, bm, colour = (200, 0, 0), size = (32, 32),
                speed = 180, maxHealth = 100):
        
        x = (hg.WIDTH - size[0]) / 2
        y = (hg.HEIGHT - size[1]) / 2
        
        Entity.__init__(self, hg, x, y, colour, size, speed)
        
        self.maxHealth = maxHealth
        self.health = self.maxHealth
        self.healthLossRate = 4
        
        self.bm = bm
        
    def update(self):
        self.move()
        
        for enemy in self.hg.em.enemies:
            if self.rect.colliderect(enemy.rect):
                self.health -= self.healthLossRate / (enemy.generation ** 2) * self.hg.deltaTime
        
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
        if key == game.key("w"):
            self.direction[1] = -1 * boolean
        elif key == game.key("s"):
            self.direction[1] = 1 * boolean
        elif key == game.key("a"):
            self.direction[0] = -1 * boolean
        elif key == game.key("d"):
            self.direction[0] = 1 * boolean
        
    def fire(self):
        midpoint = pygame.math.Vector2(self.pos[0] + self.size[0] / 2,
                                       self.pos[1] + self.size[1] / 2)
        try:
            bulletDirection = (pygame.math.Vector2(pygame.mouse.get_pos()) - midpoint).normalize()
        
            self.bm.addBullet(Bullet(self.hg, midpoint, bulletDirection))
            
        except ValueError:
            pass #Tried to normalize vector of (0, 0)
                 #as the player clicked on the midpoint
        
    def die(self):
        pass
        
class HealthBar():
    def __init__(self, hg, pos, size):
        self.hg = hg
        self.pos = pos
        
        self.redBarRect = pygame.Rect(pos, size)
        self.greenBarRect = self.redBarRect.copy()
        
        self.surface = pygame.Surface(size).convert()
        self.surface.set_alpha(128)
        
    def draw(self):
        pygame.draw.rect(self.surface, RED, self.redBarRect)
        pygame.draw.rect(self.surface, GREEN, self.greenBarRect)
        
        self.hg.screen.blit(self.surface, self.pos)
        
    def update(self, health = None):
        """Health as a fraction of total"""
        
        if health is None:
            health = self.hg.player.health / self.hg.player.maxHealth

        self.greenBarRect.size = (self.redBarRect.size[0] * health, self.greenBarRect.size[1])
        #the green bar rect is inflated by the red bar rect length,
        #multiplied by the reciprocal of health multiplied be negative one.
        
class ScoreManager():        
    def __init__(self, hg, pos, colour = BLACK):
        self.hg = hg
        
        self.score = 0
        self.multiplier = 1
        
        self.colour = colour
        self.pos = pos
        
        self.font = pygame.font.SysFont("Verdana, Lucida Console, Arial", 96)
        
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
        self.hg.screen.blit(self.scoreImg, self.pos)

class HUD():
    def __init__(self, hg):
        self.hg = hg
        
        healthBarRect = ((0, 0), (self.hg.WIDTH * (3 / 4), self.hg.HEIGHT / 8))
        scorePos = (self.hg.WIDTH * (3 / 4), 0)
        
        self.healthBar = HealthBar(self.hg, healthBarRect[0], healthBarRect[1])
        self.sm = ScoreManager(self.hg, scorePos)
        
    def update(self):
        self.healthBar.update()
        self.sm.update()
        
    def draw(self):
        self.healthBar.draw()
        self.sm.draw()
        
class Bullet(Entity):
    def __init__(self, hg, pos, direction, colour = (117, 117, 117),
                size = (8, 8), speed = 300):
        Entity.__init__(self, hg, pos[0], pos[1], colour, size, speed)
        
        self.direction = direction
        
    def draw(self):
        pygame.draw.ellipse(self.hg.screen, self.colour, self.rect)
        
class BulletManager():
    def __init__(self, hg):
        self.bullets = []
        self.hg = hg
        
    def addBullet(self, bullet):
        self.bullets.append(bullet)
        
    def delBullet(self, bullet):
        self.bullets.remove(bullet)
        del(bullet)
        
    def update(self):
        for bullet in self.bullets:
            bullet.update()
            
            if not bullet.rect.colliderect(self.hg.SCREENRECT):
                self.delBullet(bullet)
                
            collidedEnemy = bullet.rect.collidelist([enemy.rect for enemy in self.hg.em.enemies])
            
            if collidedEnemy != -1:
                self.hg.em.killEnemy(collidedEnemy)
                self.delBullet(bullet)
            
    def draw(self):
        for bullet in self.bullets:
            bullet.draw()

class Enemy(Entity):
    def __init__(self, hg, x, y, generation = 1, colour = (191, 255, 0), size = (32, 32), speed = 150):
        self.generation = generation
        size = (size[0] / generation, size[1] / generation)
        
        Entity.__init__(self, hg, x, y, colour, size, speed)
        
        
    def calcDirection(self):
        self.direction = (self.hg.player.pos - self.pos).normalize()
    
    def update(self):        
        self.calcDirection()
        self.move()
        
class EnemyManager():
    def __init__(self, hg, spawnRate = 2000, damper = 15, maxGenerations = 3):
        self.enemies = []
        
        self.hg = hg
        self.spawnRate = spawnRate
        self.maxGenerations = maxGenerations
        
        self.baseScore = 30
        
        self.damper = damper #Dampener for the increase of spawn rate over time
        
        self.spawnSpots = self.createSpawnSpots()
        
        self.baseTimeToSpawn = 0.1
        self.timeToSpawn = self.baseTimeToSpawn
        
    def createSpawnSpots(self, desiredAmount = 16, deviation = 0.2):
        """Should optimise"""
        
        spawnSpots = []
        
        while len(spawnSpots) < desiredAmount:
            new = (random.randrange(round(self.hg.WIDTH * -deviation),
                                    round(self.hg.WIDTH * (1 + deviation))),
                   random.randrange(round(self.hg.HEIGHT * -deviation),
                                    round(self.hg.HEIGHT * (1 + deviation))))
        
            if not self.hg.SCREENRECT.collidepoint(new):
                spawnSpots.append(new)
                
        return spawnSpots
                
    def addEnemy(self, enemy):
        self.enemies.append(enemy)
        
    def killEnemy(self, enemy):
        """Do not confuse with delEnemy. This will split the enemies"""
        
        if isinstance(enemy, int):
            enemy = self.enemies[enemy]
        
        if enemy.generation < self.maxGenerations:
            self.spawnEnemies(2, enemy.generation, enemy.pos, True)
        
        self.hg.hud.sm.changeScore(self.baseScore / enemy.generation)
        self.delEnemy(enemy)
    
    def delEnemy(self, enemy):
        self.enemies.remove(enemy)
        del(enemy)

    def spawnEnemies(self, num = 1, baseGeneration = 0, pos = None, variation = False, phi = 20):
        if pos is None:
            pos = random.choice(self.spawnSpots)
        
        for i in range(num):
            if variation:
                self.addEnemy(Enemy(self.hg, random.gauss(pos[0], phi), random.gauss(pos[1], phi), baseGeneration + 1))
            
            else:
                self.addEnemy(Enemy(self.hg, pos[0], pos[1], baseGeneration + 1))
            
    def update(self):
        for enemy in self.enemies:
            enemy.update()
            
        self.timeToSpawn -= self.hg.deltaTime
            
        if self.timeToSpawn <= 0 and random.randrange(ceil(self.spawnRate / (self.hg.timeElapsed / self.damper))) == 0:
            self.spawnEnemies()
            self.timeToSpawn = self.baseTimeToSpawn
            
    def draw(self):
        for enemy in self.enemies:
            enemy.draw()
            
class Cursor():
    def __init__(self, hg, colour = BRIGHT_RED, radius = 4):
        #pygame.mouse.set_visible(False)
        self.hg = hg
        self.radius = radius
        
        self.colour = colour
        
    def draw(self):
        pos = (i - self.radius for i in pygame.mouse.get_pos())
        
        pygame.draw.circle(self.hg.screen, self.colour,
                           pygame.mouse.get_pos(), self.radius)

class HordeGame(game.Game):
    def __init__(self):
        game.Game.__init__(self, 0, 0, fillcolour = (255, 255, 255), fullscreen = True)

        self.em = EnemyManager(self)
        self.bm = BulletManager(self)
        self.hud = HUD(self)
        self.player = Player(self, self.bm)
        
        self.cursor = Cursor(self)
        
        self.timeElapsed = 0

    def update(self):
        
        self.timeElapsed += self.deltaTime
        
        self.player.update()
        self.bm.update()
        self.em.update()
        self.hud.update()
        
        print(self.clock.get_fps())
    
    def render(self):
        self.bm.draw()
        self.player.draw()
        self.em.draw()
        self.hud.draw()
        self.cursor.draw()

    def handleEvent(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.display.iconify()
            
        self.player.handleEvent(event)

def main():
    hg = HordeGame()
    hg.run()

if __name__ == "__main__":
    main()
    