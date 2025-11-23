import pygame
from sys import exit
import random
import math
import threading
from ai_brain import ask_ollama # 引入剛剛寫的模組
from settings import * # --- 初始化 ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simple Shooter")
clock = pygame.time.Clock()


# 字體設定：改用微軟正黑體 (Microsoft JhengHei)
try:
    # 方法 A: 直接指定系統字體名稱 (最推薦)
    font = pygame.font.SysFont("microsoftjhenghei", 20, bold=True)
except:
    # 如果失敗，才用預設字體 (但預設字體無法顯示中文)
    print("載入中文字體失敗，使用預設字體")
    font = pygame.font.Font(None, 20)
    
title_font = pygame.font.Font("font/PublicPixel.ttf", 40)

background = pygame.image.load("assets/ground.png").convert()

# 取得地圖大小 (邊界限制用)
BG_WIDTH = background.get_width()
BG_HEIGHT = background.get_height()

# 遊戲狀態變數
game_active = True
current_time = 0
level_over_time = 0
ready_to_spawn = True # 是否準備生成下一波

# --- 類別定義 ---

class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
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
        mouse_coords = pygame.mouse.get_pos()
        x_change = (mouse_coords[0] - WIDTH // 2)
        y_change = (mouse_coords[1] - HEIGHT // 2)
        self.angle = math.degrees(math.atan2(y_change, x_change))
        self.image = pygame.transform.rotate(self.base_player_image, -self.angle)
        self.rect = self.image.get_rect(center=self.hitbox_rect.center)

    def user_input(self):
        self.velocity_x = 0
        self.velocity_y = 0
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: self.velocity_y = -self.speed
        if keys[pygame.K_s]: self.velocity_y = self.speed
        if keys[pygame.K_a]: self.velocity_x = -self.speed
        if keys[pygame.K_d]: self.velocity_x = self.speed
        
        if self.velocity_x != 0 and self.velocity_y != 0:
            self.velocity_x /= math.sqrt(2)
            self.velocity_y /= math.sqrt(2)
            
        if pygame.mouse.get_pressed()[0] or keys[pygame.K_SPACE]:
            self.shoot = True
            self.is_shooting()
        else:
            self.shoot = False

    def is_shooting(self):

        if self.shoot_cooldown==0:
            self.shoot_cooldown= SHOOT_COOLDOWN
            spawn_bullet_pos=self.pos+self.gun_barrel_offset.rotate(self.angle)
            self.bullet=Bullet(spawn_bullet_pos[0],spawn_bullet_pos[1],self.angle)
            camera.add(self.bullet)
            all_sprites_group.add(self.bullet)
            bullet_group.add(self.bullet)

    def get_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0

    def move(self):
        self.pos += pygame.math.Vector2(self.velocity_x, self.velocity_y)
        # 邊界檢查
        if self.pos.x < 0: self.pos.x = 0
        if self.pos.x > BG_WIDTH: self.pos.x = BG_WIDTH
        if self.pos.y < 0: self.pos.y = 0
        if self.pos.y > BG_HEIGHT: self.pos.y = BG_HEIGHT
        
        self.hitbox_rect.center = self.pos
        self.rect.center = self.hitbox_rect.center

    def update(self):
        self.user_input()
        self.move()
        self.player_rotation()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
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

class Fireball(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos):
        super().__init__()
        self.fireball_frames = []
        self.explosion_frames = []
        
        filenames = [
            "assets/fireball02.png",
            "assets/fireball03.png",
            "assets/fireball6.png",
            "assets/fireball7.png"
        ]
        explosion_filenames = [
            "assets/explode1.png",
            "assets/explode2.png",
            "assets/explode3.png"
        ]
        
        self.pos = pygame.math.Vector2(start_pos)
        direction = (pygame.math.Vector2(target_pos) - self.pos)
        if direction.length() > 0:
            direction = direction.normalize()
        else:
            direction = pygame.math.Vector2(1, 0)
            
        self.velocity = direction * FIREBALL_SPEED
        self.spawn_time = pygame.time.get_ticks()
        
        angle = math.degrees(math.atan2(direction.y, direction.x))
        
        # Load explosion frames
        for name in explosion_filenames:
            img = pygame.image.load(name).convert_alpha()
            img = pygame.transform.rotozoom(img, 0, 0.5)
            self.explosion_frames.append(img)


        # Load fireball frames
        for name in filenames: 
            img = pygame.image.load(name).convert_alpha()
            img = pygame.transform.rotozoom(img, 0, 0.5)
            img = pygame.transform.rotate(img, -angle)
            self.fireball_frames.append(img)

        if not self.fireball_frames:
            surf = pygame.Surface((20, 20))
            surf.fill((255, 100, 0))
            self.fireball_frames.append(surf)
            
        self.frames = self.fireball_frames
        self.frame_index = 0
        self.animation_speed = 0.2
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=start_pos)
        self.exploded = False
    def explode(self):
        if not self.exploded:
            self.exploded = True
            self.frames = self.explosion_frames
            self.frame_index = 0
            self.animation_speed = 0.2

    def animate(self):
        self.frame_index += self.animation_speed
        if self.exploded:
            if self.frame_index >= len(self.frames):
                self.kill()
            else:
                self.image = self.frames[int(self.frame_index)]
                self.rect = self.image.get_rect(center=self.rect.center)
        else:
            if self.frame_index >= len(self.frames):
                self.frame_index = 0
            self.image = self.frames[int(self.frame_index)]
            self.rect = self.image.get_rect(center=self.rect.center)

    def update(self):
        self.animate()
            
        if not self.exploded:
            self.pos += self.velocity
            self.rect.center = self.pos
            
        if pygame.time.get_ticks() - self.spawn_time > FIREBALL_LIFETIME:
            self.kill()

class Track_Fireball(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos):
        super().__init__()
        self.fireball_frames = []
        self.explosion_frames = []
        
        filenames = [
            "assets/fireball02.png",
            "assets/fireball03.png",
            "assets/fireball6.png",
            "assets/fireball7.png"
        ]
        explosion_filenames = [
            "assets/explode1.png",
            "assets/explode2.png",
            "assets/explode3.png"
        ]
        
        self.pos = pygame.math.Vector2(start_pos)
        
        # Load explosion frames
        for name in explosion_filenames:
            img = pygame.image.load(name).convert_alpha()
            img = pygame.transform.rotozoom(img, 0, 0.5)
            self.explosion_frames.append(img)

        # Load fireball frames
        target_vec = pygame.math.Vector2(target_pos)
        direction = (target_vec - self.pos)
        if direction.length() > 0:
            direction = direction.normalize()
        else:
            direction = pygame.math.Vector2(1, 0)
        
        angle = math.degrees(math.atan2(direction.y, direction.x))

        for name in filenames: 
            img = pygame.image.load(name).convert_alpha()
            img = pygame.transform.rotozoom(img, 0, 0.5)
            img = pygame.transform.rotate(img, -angle) 
            self.fireball_frames.append(img)

        if not self.fireball_frames:
            surf = pygame.Surface((20, 20))
            surf.fill((255, 100, 0))
            self.fireball_frames.append(surf)
            
        self.frames = self.fireball_frames
        self.frame_index = 0
        self.animation_speed = 0.2
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=start_pos)
        
        self.velocity = direction * FIREBALL_SPEED
        self.spawn_time = pygame.time.get_ticks()
        self.exploded = False

    def explode(self):
        if not self.exploded:
            self.exploded = True
            self.frames = self.explosion_frames
            self.frame_index = 0
            self.animation_speed = 0.2

    def animate(self):
        self.frame_index += self.animation_speed
        if self.exploded:
            if self.frame_index >= len(self.frames):
                self.kill()
            else:
                self.image = self.frames[int(self.frame_index)]
                self.rect = self.image.get_rect(center=self.rect.center)
        else:
            if self.frame_index >= len(self.frames):
                self.frame_index = 0
            self.image = self.frames[int(self.frame_index)]
            self.rect = self.image.get_rect(center=self.rect.center)

    def update(self):
        self.animate()
        
        if not self.exploded:
            # Tracking Logic
            player_pos = pygame.math.Vector2(player.hitbox_rect.center)
            direction = (player_pos - self.pos)
            if direction.length() > 0:
                direction = direction.normalize()
            
            self.velocity = direction * FIREBALL_SPEED
            
            self.pos += self.velocity
            self.rect.center = self.pos
            
            if pygame.time.get_ticks() - self.spawn_time > FIREBALL_LIFETIME:
                self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, name, position):
        super().__init__(enemy_group, all_sprites_group)
        self.name = name
        info = monster_data[self.name]
        
            # 這裡固定讀取 assets/enemy.png，如果你有不同圖可以改
        self.image = pygame.image.load("assets/enemy.png").convert_alpha()
        self.image = pygame.transform.rotozoom(self.image, 0, info["image_scale"])
        self.current_strategy = "CHASE" # 預設策略
        self.speech_text = "..."        # 敵人說的話
        self.is_thinking = False        # 是否正在等待 LLM 回應
        self.last_think_time = 0        # 上次思考的時間
        self.think_cooldown = 2000      # 每 2 秒思考一次 (毫秒)
        self.should_attack = False
        self.rect = self.image.get_rect(center=position)
        self.pos = pygame.math.Vector2(position)
        self.vel = pygame.math.Vector2()
        self.image = info["image"]
        self.health = info["health"]
        self.max_health = info["health"]
        self.speed = info['speed']
        self.notice_radius = info["notice_radius"]
        self.attack_damage = info["attack_damage"]
        # AI 相關
        self.speech_text = "我是不朽的！"
        self.is_thinking = False
        self.last_think_time = 0
        self.think_cooldown = 3000 # Boss 講話慢一點
        
        self.last_attack_time = 0
        
        camera.add(self)
    def think(self, player_pos, player_hp):
            # 計算距離
        dist = self.pos.distance_to(player_pos)
            
            # 呼叫 Ollama (這會花 1~2 秒，但因為在線程裡所以不會卡畫面)
        result = ask_ollama(self.health, player_hp, dist)
        if direction.length() > 0:
            direction = direction.normalize()
            
            self.velocity = direction * FIREBALL_SPEED
            
            self.pos += self.velocity
        self.rect = self.image.get_rect(center=position)
        self.pos = pygame.math.Vector2(position)
        self.vel = pygame.math.Vector2()
        self.image = info["image"]
        self.health = info["health"]
        self.max_health = info["health"]
        self.speed = info['speed']
        self.notice_radius = info["notice_radius"]
        self.attack_damage = info["attack_damage"]
        # AI 相關
        self.speech_text = "我是不朽的！"
        self.is_thinking = False
        self.last_think_time = 0
        self.think_cooldown = 3000 # Boss 講話慢一點
        
        self.last_attack_time = 0
        
        camera.add(self)
    def think(self, player_pos, player_hp):
            # 計算距離
        dist = self.pos.distance_to(player_pos)
            
            # 呼叫 Ollama (這會花 1~2 秒，但因為在線程裡所以不會卡畫面)
        result = ask_ollama(self.health, player_hp, dist)
        self.speech_text = result.get("message", "...")
        self.should_attack = result.get("should_attack", False)
        self.current_strategy = result.get("strategy", "CHASE")
        # Debug 用：可以在終端機印出來確認有沒有收到
        print(f"AI 回應: {self.speech_text}, 策略: {self.current_strategy}")
        self.is_thinking = False # 思考結束
    def execute_strategy(self):
        player_vec = pygame.math.Vector2(player.hitbox_rect.center)
        my_vec = self.pos
        dist = (player_vec - my_vec).magnitude()
            
        self.velocity = pygame.math.Vector2(0, 0) # 預設不動

            # 根據 LLM 決定的策略來移動 (小腦)
        if self.current_strategy == "CHASE":
            if dist > 0:
                self.direction = (player_vec - my_vec).normalize()
                self.velocity = self.direction * self.speed
                    
        elif self.current_strategy == "FLEE":
            if dist > 0:
                    # 往反方向跑 (負號)
                self.direction = (player_vec - my_vec).normalize()
                self.velocity = self.direction * -self.speed * 1.2 # 逃跑通常快一點
                    
            elif self.current_strategy == "IDLE":
                self.velocity = pygame.math.Vector2(0, 0)

            # 更新位置
            self.pos += self.velocity
            self.rect.center = self.pos
    def hunt_player(self):
        player_vec = pygame.math.Vector2(player.hitbox_rect.center)
        my_vec = self.pos
        dist = (player_vec - my_vec).magnitude()

        if dist > 0:
            direction = (player_vec - my_vec).normalize()
        else:
            direction = pygame.math.Vector2()
            
        self.vel = direction * self.speed
        self.pos += self.vel
        self.rect.center = self.pos

    def check_collisions(self):
        # 撞到玩家
        if self.rect.colliderect(player.hitbox_rect):
            player.get_damage(1)
        
        # 被子彈打到
        if pygame.sprite.spritecollide(self, bullet_group, True):
            self.health -= 20
            if self.health <= 0:
                self.kill()

    def draw_health(self, surface, offset):
        if self.health > self.max_health: col = GREEN
        elif self.health > self.max_health: col = YELLOW
        else: col = RED
        
        bar_width=200
        current_bar_width=int(bar_width*(self.health/self.max_health))
        draw_x=self.rect.centerx - offset.x - bar_width // 2
        draw_y=self.rect.top - offset.y - 10
        pygame.draw.rect(surface, BLACK,(draw_x, draw_y, bar_width, 10))
        pygame.draw.rect(surface,col,(draw_x,draw_y,current_bar_width,10))
        # 畫在敵人頭上
        draw_pos = self.rect.topleft - offset
       
        # --- 新增：畫出 LLM 的對話 ---
        text_surf = font.render(self.speech_text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(self.rect.centerx - offset.x, self.rect.top - offset.y - 20))
        surface.blit(text_surf, text_rect)

    def update(self):
        # 1. AI 思考觸發器
        current_time = pygame.time.get_ticks()
        if not self.is_thinking and (current_time - self.last_think_time > self.think_cooldown):
            self.is_thinking = True
            self.last_think_time = current_time
            
            # 啟動執行緒 (Thread)
            # 注意：傳入需要的數據 (玩家位置, 玩家血量)
            t = threading.Thread(target=self.think, args=(player.rect.center, player.health))
            t.daemon = True # 設定為守護執行緒，遊戲關閉時它會自動關閉
            t.start()

        self.attack_behavior()
        self.check_collisions()

    # boss 行為
    def attack_behavior(self):
        if self.name == "boss":
            current_time = pygame.time.get_ticks()
            if current_time - self.last_attack_time > BOSS_ATTACK_COOLDOWN and self.should_attack:
                self.last_attack_time = current_time
                
                # Check AI strategy for fireball type
                if self.current_strategy == "DOUBLE FIRE BALL":
                    fireball = Track_Fireball(self.rect.center, player.hitbox_rect.center)
                else:
                    fireball = Fireball(self.rect.center, player.hitbox_rect.center)
                    
                camera.add(fireball)
                enemy_bullet_group.add(fireball)

class Camera(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.offset = pygame.math.Vector2()
        self.floor_rect = background.get_rect(topleft=(0,0))

    def custom_draw(self):
        target_x= player.rect.centerx - WIDTH // 2
        target_y= player.rect.centery - HEIGHT // 2
        if target_x<0:
            target_x=0
        if target_x>BG_WIDTH - WIDTH:
            target_x=BG_WIDTH - WIDTH
        if target_y<0:
            target_y=0
        if target_y>BG_HEIGHT - HEIGHT:
            target_y=BG_HEIGHT - HEIGHT
        
        self.offset.x = target_x
        self.offset.y = target_y

        # 畫背景
        floor_offset = self.floor_rect.topleft - self.offset
        screen.blit(background, floor_offset)

        # 畫所有 Sprite
        for sprite in self.sprites():
            offset_pos = sprite.rect.topleft - self.offset
            screen.blit(sprite.image, offset_pos)
            
            # 畫敵人血條
            if isinstance(sprite, Enemy):
                sprite.draw_health(screen, self.offset)
            if isinstance(sprite, Enemy):
                sprite.draw_health(screen, self.offset)
                
                # --- 新增：畫出 LLM 的對話 ---
                text_surf = font.render(sprite.speech_text, True, (255, 255, 255))
                text_rect = text_surf.get_rect(center=(sprite.rect.centerx - self.offset.x, sprite.rect.top - self.offset.y - 20))
                screen.blit(text_surf, text_rect)

class UI():
    def display(self):
        # 血條
        pygame.draw.rect(screen, BLACK, (10, 10, 200, 20))
        pygame.draw.rect(screen, RED, (10, 10, player.health * 2, 20))
        pygame.draw.rect(screen, WHITE, (10, 10, 200, 20), 2)
        
        # 文字資訊
        wave_text = font.render(f"Wave: {game_stats['current_wave']}", True, WHITE)
        enemy_text = font.render(f"Killed: {game_stats['enemies_killed_or_removed']}", True, WHITE)
        screen.blit(wave_text, (WIDTH - 150, 10))
        screen.blit(enemy_text, (WIDTH - 200, 40))

        # 倒數計時顯示
        if not ready_to_spawn and current_time - level_over_time < game_stats["wave_cooldown"]:
            time_left = int((game_stats["wave_cooldown"] - (current_time - level_over_time)) / 1000)
            count_text = title_font.render(f"Next Wave: {time_left}", True, RED)
            screen.blit(count_text, (WIDTH//2 - 150, 100))

# --- 初始化群組 ---
all_sprites_group = pygame.sprite.Group() 
bullet_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
enemy_bullet_group = pygame.sprite.Group()

camera = Camera()
ui = UI()

player = Player((WIDTH//2, HEIGHT//2))
camera.add(player)

# --- 遊戲邏輯函式 ---
def spawn_wave():
    wave_idx = game_stats["current_wave"] - 1
    # 避免超過陣列長度
    if wave_idx >= len(game_stats["number_of_enemies"]):
        wave_idx = len(game_stats["number_of_enemies"]) - 1
        
    count = game_stats["number_of_enemies"][wave_idx]
    
    for _ in range(count):
        spawn_pos = (random.randint(0, BG_WIDTH), random.randint(0, BG_HEIGHT))
        type = random.choice(["necromancer", "nightborne"])
        Enemy(type, spawn_pos) # Enemy 會自己加入 camera

def reset_game():
    global game_active, ready_to_spawn, level_over_time
    game_active = True
    game_won=False
    player.health = 100
    # game_stats["current_wave"] = 1
    # game_stats["enemies_killed_or_removed"] = 0
    
    enemy_group.empty()
    enemy_bullet_group.empty()
    camera.empty()
    camera.add(player)
    boss_pos=(BG_WIDTH//2,BG_HEIGHT//2)
    Enemy("boss",boss_pos)
    # ready_to_spawn = True
    # level_over_time = pygame.time.get_ticks()

reset_game()
while True:
    current_time = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if not game_active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                reset_game()

    if game_active:
        if len(enemy_group) == 0:
            game_active = False
            game_active=True
            if ready_to_spawn:
                level_over_time = current_time 
                ready_to_spawn = False 
        
        camera.update()
        
        camera.custom_draw()
        ui.display()
        
        # Check fireball collisions
        collided_fireballs = pygame.sprite.spritecollide(player, enemy_bullet_group, False)
        for fireball in collided_fireballs:
            if not fireball.exploded:
                fireball.explode()
                player.get_damage(10)

        if player.health <= 0:
            game_active = False
            game_won=False
    else:
        screen.fill((0, 0, 0))
        if game_won:
            txt = title_font.render("YOU WIN!", True, GREEN)
            hint = font.render("Press P to Restart", True, WHITE)
            screen.blit(txt, (WIDTH//2 - 100, HEIGHT//2 - 50))
            screen.blit(hint, (WIDTH//2 - 120, HEIGHT//2 + 20))
        else:
            txt = title_font.render("GAME OVER", True, RED)
        hint = font.render("Press P to Restart", True, WHITE)
        screen.blit(txt, (WIDTH//2 - 150, HEIGHT//2 - 50))
        screen.blit(hint, (WIDTH//2 - 120, HEIGHT//2 + 20))

    pygame.display.update()
    clock.tick(FPS)