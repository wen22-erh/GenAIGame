import pygame

from sys import exit

import threading

import time

import random

import math

from settings import *

# --- 設定 ---

pygame.init()



# create window

screen=pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("Shooter Game")



clock=pygame.time.Clock()

# fonts
font = pygame.font.Font("font/PublicPixel.ttf", 20)
small_font = pygame.font.Font("font/PublicPixel.ttf", 15)
title_font = pygame.font.Font("font/PublicPixel.ttf", 60)
score_font = pygame.font.Font("font/PublicPixel.ttf", 50)
# 1. 取得地圖邊界 (確保怪物不會生在牆壁外)
map_width = WIDTH
map_height = HEIGHT


spawn_x = random.randint(0, map_width)

spawn_y = random.randint(0, map_height)

#loadimages

background=pygame.image.load("assets/ground.png").convert()

game_active = True

beat_game = False

current_time = 0

level_over_time = 0

ready_to_spawn = False

display_countdown_time = False

first_level = True



def hitbox_collide(sprite1, sprite2):

    return sprite1.base_zombie_rect.colliderect(sprite2.rect)

class Player(pygame.sprite.Sprite):

    def __init__(self,pos):
        super().__init__()
        self.pos=pygame.math.Vector2(PLAYER_START_X,PLAYER_START_Y)
        self.pos = pos
        self.image=pygame.transform.rotozoom(pygame.image.load("assets/player1.png").convert_alpha(),0,PLAYER_SIZE)
        self.base_player_image=self.image
        self.hitbox_rect=self.base_player_image.get_rect(center=self.pos)
        self.rect=self.hitbox_rect.copy()
        self.base_player_rect = self.base_player_image.get_rect(center = pos)
        self.speed=PLAYER_SPEED
        self.shoot=False
        self.shoot_cooldown=0
        self.health = 100
        self.gun_barrel_offset=pygame.math.Vector2(GUN_OFFSET_X,GUN_OFFSET_Y)

    def player_rotation(self):

        self.mouse_coords=pygame.mouse.get_pos()

        self.x_change_mouse_player=(self.mouse_coords[0]-WIDTH//2)

        self.y_change_mouse_player=(self.mouse_coords[1]-HEIGHT//2)

        self.angle=math.degrees(math.atan2(self.y_change_mouse_player,self.x_change_mouse_player))

        self.image=pygame.transform.rotate(self.base_player_image,-self.angle)

        self.rect=self.image.get_rect(center=self.hitbox_rect.center)

       

    def user_input(self):

        self.velocity_x=0

        self.velocity_y=0

        keys=pygame.key.get_pressed()

        if keys[pygame.K_w]:

            self.velocity_y=-self.speed

        if keys[pygame.K_s]:

            self.velocity_y=self.speed

        if keys[pygame.K_a]:

            self.velocity_x=-self.speed

        if keys[pygame.K_d]:

            self.velocity_x=self.speed

        if self.velocity_x!=0 and self.velocity_y!=0:

            self.velocity_x/=math.sqrt(2)

            self.velocity_y/=math.sqrt(2)

        if pygame.mouse.get_pressed()==(1,0,0)or keys[pygame.K_SPACE]:

            self.shoot=True

            self.is_shooting()

        else:

            self.shoot=False

           

    def get_damage(self, amount):

        if ui.current_health > 0:

            ui.current_health -= amount

            self.health -= amount

        if ui.current_health <= 0: # dead

            ui.current_health = 0

            self.health = 0

           

    def is_shooting(self):

        if self.shoot_cooldown==0:
            self.shoot_cooldown= SHOOT_COOLDOWN
            spawn_bullet_pos=self.pos+self.gun_barrel_offset.rotate(self.angle)
            self.bullet=Bullet(spawn_bullet_pos[0],spawn_bullet_pos[1],self.angle)
            camera.add(self.bullet)
            all_sprites_group.add(self.bullet)
            bullet_group.add(self.bullet)

   

    def increase_health(self, amount):

        if ui.current_health < ui.maximum_health:

            ui.current_health += amount

            self.health += amount

        if ui.current_health >= ui.maximum_health:

            ui.current_health = ui.maximum_health

            self.health = ui.maximum_health

    def move(self):

        self.pos+=pygame.math.Vector2(self.velocity_x,self.velocity_y)

        self.hitbox_rect.center=self.pos

        self.rect.center=self.hitbox_rect.center

        #物理碰撞修正

    def check_collision(self, direction):

        for sprite in obstacles_group:

            if sprite.rect.colliderect(self.base_player_rect):

                if direction == "horizontal":

                    if self.velocity_x > 0:

                        self.base_player_rect.right = sprite.rect.left

                    if self.velocity_x < 0:

                        self.base_player_rect.left = sprite.rect.right

               

                if direction == "vertical":

                    if self.velocity_y < 0:

                        self.base_player_rect.top = sprite.rect.bottom

                    if self.velocity_y > 0:

                        self.base_player_rect.bottom = sprite.rect.top  

    def update(self):
        self.user_input()
        self.player_rotation()
        self.move()

        if self.shoot_cooldown>0:

            self.shoot_cooldown-=1

class UI():

    def __init__(self):

        self.current_health = 100

        self.maximum_health = 100

        self.health_bar_length = 100

        self.health_ratio = self.maximum_health / self.health_bar_length

        self.current_colour = None



    def display_health_bar(self):

        pygame.draw.rect(screen, BLACK, (10, 15, self.health_bar_length * 3, 20)) # black



        if self.current_health >= 75:

            pygame.draw.rect(screen, GREEN, (10, 15, self.current_health * 3, 20)) # green    

            self.current_colour = GREEN

        elif self.current_health >= 25:

            pygame.draw.rect(screen, YELLOW, (10, 15, self.current_health * 3, 20)) # yellow

            self.current_colour = YELLOW

        elif self.current_health >= 0:

            pygame.draw.rect(screen, RED, (10, 15, self.current_health * 3, 20)) # red

            self.current_colour = RED



        pygame.draw.rect(screen, WHITE, (10, 15, self.health_bar_length * 3, 20), 4) # white border



    def display_health_text(self):

        health_surface = font.render(f"{player.health} / {self.maximum_health}", False, self.current_colour)

        health_rect = health_surface.get_rect(center = (410, 25))

        screen.blit(health_surface, health_rect)



    def display_wave_text(self):

        wave_surface = font.render(f"Wave: {game_stats['current_wave']}", False, GREEN)

        wave_rect = wave_surface.get_rect(center = (745, 28))

        screen.blit(wave_surface, wave_rect)



    def display_countdown(self, time):

        text_1 = font.render(f"Enemies spawning in {int(time/1000)} seconds!",True, RED)

        screen.blit(text_1, (400, 100))



    def display_enemy_count(self):

        text_1 = font.render(f"Enemies: {game_stats['number_of_enemies'][game_stats['current_wave'] - 1] - game_stats['enemies_killed_or_removed']}",True, GREEN)

        screen.blit(text_1, (855, 18))



    def update(self):

        self.display_health_bar()

        self.display_health_text()

        self.display_wave_text()

        self.display_enemy_count()

ui = UI()

class Bullet(pygame.sprite.Sprite):

        def __init__(self,x,y,angle):

            super().__init__()
            self.image=pygame.image.load("assets/bullet1.png").convert_alpha()
            self.image=pygame.transform.rotozoom(self.image,0,BULLET_SCALE)
            self.rect=self.image.get_rect()
            self.rect.center=(x,y)
            self.x=x
            self.y=y
            self.angle=angle
            self.speed=BULLET_SPEED
            self.x_vel=math.cos(self.angle*(2*math.pi/360))*self.speed
            self.y_vel=math.sin(self.angle*(2*math.pi/360))*self.speed
            self.bullet_lifetime=BULLET_LIFETIME
            self.spawn_time=pygame.time.get_ticks()

           

        def bullet_movement(self):
            self.x+=self.x_vel
            self.y+=self.y_vel
            self.rect.x=int(self.x)
            self.rect.y=int(self.y)
            if pygame.time.get_ticks()-self.spawn_time>=self.bullet_lifetime:
                self.kill()

           

        def update(self):

            self.bullet_movement()

class Enemy(pygame.sprite.Sprite):

        def __init__(self,name,position):

            super().__init__(enemy_group,all_sprites_group)

            self.image=pygame.image.load("assets/enemy.png").convert_alpha()

            self.image=pygame.transform.rotozoom(self.image,0,1)

            self.name = name

            self.direction_index = random.randint(0, 3)

            self.position=pygame.math.Vector2(position)

            self.rect=self.image.get_rect()

            self.steps = random.randint(3, 6) * TILESIZE

            enemy_info = monster_data[self.name]

            self.rect.center=position

            self.direction=pygame.math.Vector2()

            self.velocity=pygame.math.Vector2()

            self.speed=ENEMY_SPEED

            self.hitbox_rect = enemy_info["hitbox_rect"]

            self.base_zombie_rect = self.hitbox_rect.copy()

            self.base_zombie_rect.center = self.rect.center

           



           

            self.health = enemy_info["health"]

            self.roaming_speed = enemy_info["roaming_speed"]

            self.hunting_speed = random.choice(enemy_info["hunting_speed"])

            self.image_scale = enemy_info["image_scale"]

            self.image = enemy_info["image"].convert_alpha()

            self.image = pygame.transform.rotozoom(self.image, 0, self.image_scale)

            # self.animation_speed = enemy_info["animation_speed"]

            # self.roam_animation_speed = enemy_info["roam_animation_speed"]

            # self.death_animation_speed = enemy_info["death_animation_speed"]

            self.notice_radius = enemy_info["notice_radius"]

            self.attack_damage = enemy_info["attack_damage"]

            self.direction_list = [(1,1), (1,-1), (-1,1), (-1,-1)]

            camera.add(self)

        def check_alive(self): # checks if enemy dies

            if self.health <= 0:

                self.alive = False

                if self.name == "necromancer":

                    game_stats["necromancer_death_count"] += 1

                if self.name == "nightborne":

                    game_stats["nightborne_death_count"] += 1

                game_stats["enemies_killed_or_removed"] += 1

        def get_new_direction_and_distance(self):

            self.direction_index = random.randint(0, len(self.direction_list)-1)

           

        def roam(self):

            self.direction.x, self.direction.y = self.direction_list[self.direction_index] # gets a random direction

            self.velocity = self.direction * self.roaming_speed

            self.position += self.velocity

           

            self.base_zombie_rect.centerx = self.position.x

            self.check_collision("horizontal", "roam")



            self.base_zombie_rect.centery = self.position.y

            self.check_collision("vertical", "roam")

           

            self.rect.center = self.base_zombie_rect.center

            self.position = pygame.math.Vector2(self.base_zombie_rect.center)



            self.steps -= 1



            if self.steps == 0:

                self.get_new_direction_and_distance()

        def check_collision(self, direction, move_state):

            self.collide = False

            for sprite in obstacles_group:

                if sprite.rect.colliderect(self.base_zombie_rect):

                    self.collide = True

                    if direction == "horizontal":

                        if self.velocity.x > 0:

                            self.base_zombie_rect.right = sprite.rect.left

                        if self.velocity.x < 0:

                            self.base_zombie_rect.left = sprite.rect.right

                    if direction == "vertical":

                        if self.velocity.y < 0:

                            self.base_zombie_rect.top = sprite.rect.bottom

                        if self.velocity.y > 0:

                            self.base_zombie_rect.bottom = sprite.rect.top

                    if move_state == "roam":

                        self.get_new_direction_and_distance()

        def hunt_player(self):

            if self.velocity.x > 0:

                self.current_movement_sprite = 0

            else:

                self.current_movement_sprite = 1

           

            player_vector = pygame.math.Vector2(player.base_player_rect.center)

            enemy_vector = pygame.math.Vector2(self.base_zombie_rect.center)

            distance = self.get_vector_distance(player_vector, enemy_vector)



            if distance > 0:

                self.direction = (player_vector - enemy_vector).normalize()

            else:

                self.direction = pygame.math.Vector2()



            self.velocity = self.direction * self.hunting_speed

            self.position += self.velocity



            self.base_zombie_rect.centerx = self.position.x

            self.check_collision("horizontal", "hunt")



            self.base_zombie_rect.centery = self.position.y

            self.check_collision("vertical", "hunt")



            self.rect.center = self.base_zombie_rect.center

            self.position = pygame.math.Vector2(self.base_zombie_rect.center)

        def get_vector_distance(self,vector_1,vector_2):

            return (vector_1-vector_2).magnitude()

        def draw_enemy_health(self, x, y):

            if self.health > 60:

                col = GREEN

            elif self.health > 30:

                col = YELLOW

            else:

                col = RED

            width = int(self.base_zombie_rect.width * self.health / 100)

            pygame.draw.rect(screen, col, (x - 40 - camera.offset.x, y - 45 - camera.offset.y, width, 5))

        def animate(self, index, animation_speed, sprite, type):

            index += animation_speed



            if index >= len(sprite): # animation over

                index = 0

                if type == "death":

                    self.kill()

       

            self.image = sprite[int(index)]

            self.image = pygame.transform.rotozoom(self.image, 0, self.image_scale)



            if type == "hunt" or type == "idle" or "death":

                if self.velocity.x < 0:

                    self.image = pygame.transform.flip(self.image, flip_x = 180, flip_y = 0)



            return index

        def check_player_collision(self):          

            if pygame.Rect.colliderect(self.base_zombie_rect, player.base_player_rect): # player and enemy collides

                self.kill()

                player.get_damage(self.attack_damage)

                game_stats["enemies_killed_or_removed"] += 1

                # scream_sound.play()

        def update(self):

       

            self.draw_enemy_health(self.position[0], self.position[1])

       

            if self.alive:

                self.check_alive()

                if self.get_vector_distance(pygame.math.Vector2(player.base_player_rect.center),

                                            pygame.math.Vector2(self.base_zombie_rect.center)) < 100:

                    self.check_player_collision()

                   

                if self.get_vector_distance(pygame.math.Vector2(player.base_player_rect.center),

                                            pygame.math.Vector2(self.base_zombie_rect.center)) < self.notice_radius:    # nightborne 400, necromancer 500

                    self.hunt_player()

                    self.current_index = self.animate(self.current_index, self.animation_speed, self.animations["hunt"], "hunt")

                else:

                    self.roam()

                    if self.get_vector_distance(pygame.math.Vector2(player.base_player_rect.center), pygame.math.Vector2(self.base_zombie_rect.center)) < 700:    

                        self.current_index = self.animate(self.current_index, self.roam_animation_speed, self.animations["roam"], "idle")

            else: # drop coin and play death animation

                if not self.coin_dropped:

                    self.coin_dropped = True

                self.current_index = self.animate(self.current_index, self.death_animation_speed, self.animations["death"], "death")

         

class Camera(pygame.sprite.Group):

        def __init__(self):

            super().__init__()

            self.offset=pygame.math.Vector2()

            self.floor_rect=background.get_rect(topleft=(0,0))

        def custom_draw(self):

            self.offset.x=player.rect.centerx-WIDTH//2

            self.offset.y=player.rect.centery-HEIGHT//2

            floor_offset_pos=self.floor_rect.topleft-self.offset

            screen.blit(background,floor_offset_pos)

            for sprite in obstacles_group:

                screen.blit(sprite.image, sprite.rect.topleft - self.offset)

            for sprite in self.sprites():

                offset_pos=sprite.rect.topleft - self.offset

                screen.blit(sprite.image,offset_pos)

               

all_sprites_group=pygame.sprite.Group()

bullet_group=pygame.sprite.Group()

enemy_group=pygame.sprite.Group()

obstacles_group = pygame.sprite.Group()

items_group = pygame.sprite.Group()





camera=Camera()

player = Player((1000,900))

necromancer = Enemy("necromancer", (spawn_x, spawn_y))

camera.add(player)



all_sprites_group.add(player)

# 增加測試用障礙物類別
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, rect):
        super().__init__()
        self.image = pygame.Surface((rect[2], rect[3]))
        self.image.fill((100, 100, 100))
        self.rect = pygame.Rect(rect)

# 障礙物加入初始化流程，只需建立一個示例
obstacle = Obstacle((600, 400, 120, 60))
obstacles_group.add(obstacle)
all_sprites_group.add(obstacle)

def end_game():

    global game_active

    game_active = False

    for item in items_group:

        item.kill()

    for enemy in enemy_group:

        enemy.kill()

    enemy_group.empty()

    items_group.empty()  

while True:

    current_time = pygame.time.get_ticks()

    if player.health <= 0:

        end_game()

    keys=pygame.key.get_pressed()

    for event in pygame.event.get():

        if event.type==pygame.QUIT:

            pygame.quit()

            exit()

        if not game_active and keys[pygame.K_p]:

            player.health, ui.current_health = 100, 100

            game_active = True

            game_stats["current_wave"] = 1

            start_time = pygame.time.get_ticks()            

           

            game_stats["necromancer_death_count"] = 0

            game_stats["nightborne_death_count"] = 0

            game_stats["enemies_killed_or_removed"] = 0

            game_stats["coins"] = 0

           

    if game_active:

        all_sprites_group.update()

        camera.update()

        camera.custom_draw()

        ui.update()

        # 保證每一幀都畫出敵人血條
        for enemy in enemy_group:
            if hasattr(enemy, "draw_enemy_health"):
                enemy.draw_enemy_health(enemy.position[0], enemy.position[1])

    else:

        end_game()

    # pygame.draw.rect(screen,"red",player.hitbox_rect,2)

    # pygame.draw.rect(screen,"blue",player.rect,2)

    pygame.display.update()

    clock.tick(FPS)