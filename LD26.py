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
                               
class Entity():
    def __init__(self, md,  x, y, colour, size, speed, sigma = None):
        self.md = md
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
        pygame.draw.rect(self.md.screen, self.colour, self.rect)
        
    def move(self):
        self.pos[0] += self.direction[0] * self.speed * self.md.deltaTime
        self.pos[1] += self.direction[1] * self.speed * self.md.deltaTime
        
        self.rect = pygame.Rect(self.pos, self.size)
        
    def update(self):
        self.move()
        
class Player(Entity):
    def __init__(self, md, bm, colour = (200, 0, 0), size = (32, 32),
                speed = 180, maxHealth = 100):
        
        x = (md.WIDTH - size[0]) / 2
        y = (md.HEIGHT - size[1]) / 2
        
        Entity.__init__(self, md, x, y, colour, size, speed)
        
        self.maxHealth = maxHealth
        self.health = self.maxHealth
        
        self.midpoint = pygame.math.Vector2(self.pos[0] + self.size[0] / 2,
                                            self.pos[1] + self.size[1] / 2)
       
        self.bm = bm
        
    def damage(self, amount):
        self.health -= amount
        
    def update(self):
        self.move()
        
        self.midpoint = pygame.math.Vector2(self.pos[0] + self.size[0] / 2,
                                            self.pos[1] + self.size[1] / 2)
        
        for enemy in self.md.em.enemies:
            if self.rect.colliderect(enemy.rect) and hasattr(enemy, "damageRate"):
                self.damage(enemy.damageRate * self.md.deltaTime)                    
        
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
        try:
            bulletDirection = (pygame.math.Vector2(pygame.mouse.get_pos()) - self.midpoint).normalize()
        
            self.bm.addBullet(Bullet(self.md, self.midpoint, bulletDirection))
            
        except ValueError:
            pass #Tried to normalize vector of (0, 0)
                 #as the player clicked on the midpoint
        
    def die(self):
        self.md.gameOver()
        
class HealthBar():
    def __init__(self, md, pos, size):
        self.md = md
        self.pos = pos
        
        self.redBarRect = pygame.Rect(pos, size)
        self.greenBarRect = self.redBarRect.copy()
        
        self.surface = pygame.Surface(size).convert()
        self.surface.set_alpha(128)
        
    def draw(self):
        pygame.draw.rect(self.surface, RED, self.redBarRect)
        pygame.draw.rect(self.surface, GREEN, self.greenBarRect)
        
        self.md.screen.blit(self.surface, self.pos)
        
    def update(self, health = None):
        """Health as a fraction of total"""
        
        if health is None:
            health = self.md.player.health / self.md.player.maxHealth

        self.greenBarRect.size = (self.redBarRect.size[0] * health, self.greenBarRect.size[1])
        #the green bar rect is inflated by the red bar rect length,
        #multiplied by the reciprocal of health multiplied be negative one.
        
class ScoreManager():        
    def __init__(self, md, pos, font, colour = BLACK):
        self.md = md
        
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
        self.md.screen.blit(self.scoreImg, self.pos)

class HUD():
    def __init__(self, md):
        self.md = md
        self.font = pygame.font.SysFont("Verdana, Lucida Console, Arial", 96)
        self.smallFont = pygame.font.SysFont("Verdana, Lucida Console, Arial", 48)
        
        healthBarRect = ((0, 0), (self.md.WIDTH * (3 / 4), self.md.HEIGHT / 8))
        scorePos = (self.md.WIDTH * (3 / 4), 0)
        
        self.healthBar = HealthBar(self.md, healthBarRect[0], healthBarRect[1])
        self.sm = ScoreManager(self.md, scorePos, self.font)
        
    def update(self):
        self.healthBar.update()
        self.sm.update()
        
    def draw(self):
        self.healthBar.draw()
        self.sm.draw()
        
class Bullet(Entity):
    def __init__(self, md, pos, direction, side = "player", colour = (117, 117, 117),
                size = (8, 8), speed = 300, damage = 6):
        Entity.__init__(self, md, pos[0], pos[1], colour, size, speed)
        
        self.direction = direction
        self.damage = damage
        self.side = side
        
    def draw(self):
        pygame.draw.ellipse(self.md.screen, self.colour, self.rect)
        
class BulletManager():
    def __init__(self, md):
        self.bullets = []
        self.md = md
        
    def addBullet(self, bullet):
        self.bullets.append(bullet)
        
    def delBullet(self, bullet):
        self.bullets.remove(bullet)
        del(bullet)
        
    def update(self):
        for bullet in self.bullets:
            bullet.update()
            
            if not bullet.rect.colliderect(self.md.SCREENRECT):
                self.delBullet(bullet)
            
            elif bullet.side == "player":
                collidedEnemy = bullet.rect.collidelist([enemy.rect for enemy in self.md.em.enemies])
                
                if collidedEnemy != -1:
                    self.md.em.damageEnemy(collidedEnemy, bullet)
                    self.delBullet(bullet)
                    
            elif bullet.side == "enemy":
                if bullet.rect.colliderect(self.md.player.rect):
                    self.md.player.damage(bullet.damage / 2)
                    self.delBullet(bullet)
            
    def draw(self):
        for bullet in self.bullets:
            bullet.draw()

class Enemy(Entity):
    def __init__(self, md, em, type, scoreValue,  x, y, maxHealth, colour, size, speed):
        self.maxHealth = maxHealth
        self.health = self.maxHealth
        self.em = em
        self.type = type
        self.scoreValue = scoreValue
        
        self.fireChance = 0
        
        self.baseTimeUntilFire = .5
        self.timeUntilFire = self.baseTimeUntilFire
        
        Entity.__init__(self, md, x, y, colour, size, speed, sigma = 10)
        
    def calcDirection(self):
        return (self.md.player.pos - self.pos).normalize()
    
    def specificUpdate(self):
        pass
    
    def update(self):        
        self.direction = self.calcDirection()
        self.move()
        
        if self.fireChance:
            self.timeUntilFire -= self.md.deltaTime
            
            if self.timeUntilFire <= 0 and random.randrange(self.fireChance) == 0:
                self.fire()
                self.timeUntilFire = self.baseTimeUntilFire
        
        if self.health <= 0:
            self.die()
            
        self.specificUpdate()
            
    def fire(self, misaim = 10):
        #The game will error if you line up the two midpoints
        
        midpoint = pygame.math.Vector2(self.pos[0] + self.size[0] / 2,
                                       self.pos[1] + self.size[1] / 2)
        
        shotPoint = pygame.math.Vector2([random.gauss(i, misaim) for i in self.md.player.midpoint])
        
        bulletDirection = (shotPoint - midpoint).normalize()
        
        self.md.bm.addBullet(Bullet(self.md, midpoint, bulletDirection, "enemy", colour = BLACK))
        
            
    def damage(self, amount):
        self.health -= amount
        
    def die(self):
        self.em.delEnemy(self)
        self.md.hud.sm.changeScore(self.scoreValue)

        
class Slime(Enemy):
    def __init__(self, md, em,  x, y, generation, size = (32, 32),
                 maxGenerations = 3, damageRate = 4):
        self.generation = generation
        self.maxGenerations = maxGenerations
        
        self.damageRate = damageRate / self.generation ** 2
        
        size = (size[0] / self.generation, size[1] / self.generation)
        
        Enemy.__init__(self, md, em, "slime", 30 / self.generation, x, y,
                       1, (153, 253, 56), size, 150)
        
    def die(self):
        if self.generation < self.maxGenerations:
            self.em.spawnSlimes(2, self.generation, self.pos, True)
        
        self.md.hud.sm.changeScore(self.scoreValue)
        self.em.delEnemy(self)
        
class Gunman(Enemy):
    def __init__(self, md, em, x, y, fireChance = 80):
        Enemy.__init__(self, md, em, "gunman", 200, x, y, 30, (101, 67, 33), (28, 28), 80)
        
        self.campPoint = pygame.math.Vector2(random.randrange(md.WIDTH),
                                             random.randrange(md.HEIGHT))
        
        self.fireChance = fireChance
        
    def calcDirection(self):
        return (self.campPoint - self.pos).normalize()
    
class Zombie(Enemy):
    def __init__(self, md, em, x, y, damageRate = 10):
        Enemy.__init__(self, md, em, "zombie", 50, x, y, 10, (165, 165, 2), (24, 24), 200)
        
        self.damageRate = damageRate
        
    def draw(self):
        pygame.draw.ellipse(self.md.screen, self.colour, self.rect)
        
class Tank(Enemy):
    def __init__(self, md, em, x, y, fireChance = 100):
        if x < 0 or x > md.WIDTH:
            size = (48, 32)
        else:
            size = (32, 48)
        
        Enemy.__init__(self, md, em, "tank", 500, x, y, 100, (224, 223, 219), size, 50)
        
        if x < 0:
            self.direction[0] = 1
        elif x > self.md.WIDTH:
            self.direction[0] = -1
        elif y < 0:
            self.direction[1] = 1
        else:
            self.direction[1] = -1
            
        print(x, y)
            
        self.fireChance = fireChance
        
    def calcDirection(self):
        return self.direction
        
    def specificUpdate(self):
        if not self.rect.colliderect(self.md.SCREENRECT):
            self.em.delEnemy(self)
        
class EnemyManager():
    def __init__(self, md, spawnRate = 180, damper = 14):
        self.enemies = []
        
        self.md = md
        self.spawnRate = spawnRate
        
        self.tankPoints = 3000    
        
        self.damper = damper #Dampener for the increase of spawn rate over time
        
        self.spawnSpots = self.createSpawnSpots()
        
        self.baseTimeToSpawn = 1
        self.timeToSpawn = self.baseTimeToSpawn
        
    def createSpawnSpots(self, desiredAmount = 16, deviation = 0.2):
        """Should optimise"""
        
        spawnSpots = []
        
        while len(spawnSpots) < desiredAmount:
            new = (random.randrange(round(self.md.WIDTH * -deviation),
                                    round(self.md.WIDTH * (1 + deviation))),
                   random.randrange(round(self.md.HEIGHT * -deviation),
                                    round(self.md.HEIGHT * (1 + deviation))))
        
            if not self.md.SCREENRECT.collidepoint(new):
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
                self.addEnemy(Slime(self.md, self, random.gauss(pos[0], sigma), random.gauss(pos[1], sigma), baseGeneration + 1))
            
            else:
                self.addEnemy(Slime(self.md, self, pos[0], pos[1], baseGeneration + 1))
            
    def spawnEnemies(self, num = 1):
        toSpawn = random.randrange(20)
        pos = random.choice(self.spawnSpots)
        
        if toSpawn in range(13):
            self.spawnSlimes(pos = pos)
            
        elif toSpawn in range(16):
            self.addEnemy(Zombie(self.md, self, pos[0], pos[1]))
        
        elif toSpawn in range(18):
            self.addEnemy(Gunman(self.md, self, pos[0], pos[1]))
            
        elif self.md.hud.sm.score > self.tankPoints:
            self.addEnemy(Tank(self.md, self, pos[0], pos[1]))            
        
    def update(self):
        for enemy in self.enemies:
            enemy.update()
            
        self.timeToSpawn -= self.md.deltaTime
            
        if self.timeToSpawn <= 0 and random.randrange(ceil(self.spawnRate / (self.md.timeElapsed / self.damper))) == 0:
            self.spawnEnemies()
            self.timeToSpawn = self.baseTimeToSpawn
            
    def draw(self):
        for enemy in self.enemies:
            enemy.draw()
            
class Cursor():
    def __init__(self, md, colour = BRIGHT_RED, radius = 4):
        pygame.mouse.set_visible(False)
        self.md = md
        self.radius = radius
        
        self.colour = colour
        
    def draw(self):
        pos = [i + self.radius for i in pygame.mouse.get_pos()]
        
        pygame.draw.circle(self.md.screen, self.colour, pos, self.radius * 2, 1)
        
        pygame.draw.circle(self.md.screen, self.colour,
                           pos, self.radius)

class MinimalDeathmatch(game.Game):
    def __init__(self):
        game.Game.__init__(self, 0, 0, gameName = "Minimal Deathmatch", FRAMERATE = 60, fillcolour = (255, 255, 255), fullscreen = True)

    def setup(self):
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
        
    def gameOver(self):
        self.screen.fill(BLACK)
        
        text = (self.hud.font.render("Game Over", True, RED, BLACK),
                self.hud.font.render("You lasted " + str(int(self.timeElapsed)) + " seconds", True, RED, BLACK),
                self.hud.font.render("You scored " + str(int(self.hud.sm.score)) + " points", True, RED, BLACK),
                self.hud.smallFont.render("Press any key to exit", True, RED, BLACK))
        
        self.screen.blit(text[0], ((self.WIDTH - text[0].get_width()) / 2,
                                   0))
        
        cumulativeHeight = (self.HEIGHT - sum([item.get_height() for item in text])) / 2
        
        for item in text[1:]:
            self.screen.blit(item, ((self.WIDTH - item.get_width()) / 2, cumulativeHeight))
            cumulativeHeight += item.get_height()
            
        pygame.display.update()
        
        while True:
            for event in pygame.event.get():
                if event.type in (pygame.QUIT, pygame.KEYDOWN):
                    self.quit()

def main():
    md = MinimalDeathmatch()
    md.run()

if __name__ == "__main__":
    main()
    