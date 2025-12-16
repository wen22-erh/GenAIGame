import pygame
from sys import exit
import random
import math
import threading
from ai_brain import ask_ollama
from settings import * 
from ai_brain import get_battle_review
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Dragon Slayer")
clock = pygame.time.Clock()

font = pygame.font.SysFont("microsoftjhenghei", 20, bold=True)
banner_font = pygame.font.SysFont("microsoftjhenghei", 32, bold=True)
title_font = pygame.font.Font("font/PublicPixel.ttf", 40)
menu_font = pygame.font.SysFont("microsoftjhenghei", 40, bold=True) 
pixel_font_large = pygame.font.Font("font/PublicPixel.ttf", 60)
background = pygame.image.load("assets/ground.png").convert()

# 取得地圖大小 (邊界限制用)
BG_WIDTH = background.get_width()
BG_HEIGHT = background.get_height()

class GameState:
    MENU='MENU'
    PLAYING='PLAYING'
    GAMEOVER='GAMEOVER'
current_state=GameState.MENU
# 遊戲狀態變數
game_active = True
current_time = 0
level_over_time = 0
ready_to_spawn = True # 是否準備生成下一波
is_in_countdown = False
countdown_start_time = 0
countdown_duration = 3000  
game_review_text=""
is_generating_review=False
# --- 類別定義 ---

#AI 戰後評估
def fetch_review_text(memmory_list, player_won):
    global game_review_text, is_generating_review
    
    review= get_battle_review(memmory_list, player_won)
    game_review_text=review
    is_generating_review=False
class FloatingText(pygame.sprite.Sprite):
    def __init__(self, pos, text, color=(255, 255, 255)):
        super().__init__(camera) # 加入 camera 群組，這樣才會被畫出來
        self.font = pygame.font.SysFont("impact", 30) # 用粗一點的字體
        self.image = self.font.render(text, True, color)
        self.rect = self.image.get_rect(center=pos)
        self.vel_y = -3 # 往上飄的速度
        self.timer = 0
        self.lifetime = 40 # 存在 40 幀 (約 0.6 秒)

    def update(self):
        self.rect.y += self.vel_y
        self.timer += 1
        if self.timer >= self.lifetime:
            self.kill() # 時間到就消失
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
        FloatingText(self.rect.midtop, f"-{amount}", (255, 50, 50)) 
        camera.add_shake(5) # 被打到時稍微震動
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
            camera.add_shake(15)

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
        self.heal_frames = []
        #記憶
        self.memory= []
        self.last_player_hp=100
        self.last_strategy="None"
        heal_filenames = [
            "assets/cry_dragon.png",
            "assets/cry_dragon2.png",
            "assets/cry_dragon3.png",
            "assets/cry_dragon4.png",
            "assets/cry_dragon5.png",
        ]
        self.is_attacking = False       # 是否正在播放攻擊動畫
        self.attack_frame_index = 0     # 動畫播放進度
        self.attack_frames = []         # 存放攻擊圖片的 list
        
        blow_filenames = [
            "assets/blowr1.png",
            "assets/blowr2.png",
            "assets/blowr3.png",
            "assets/blowr4.png",
            "assets/blowf5.png",
        ]
        
        
        for name in blow_filenames:
            img = pygame.image.load(name).convert_alpha()
            img = pygame.transform.rotozoom(img, 0, info["image_scale"])
            self.attack_frames.append(img)
             

        for name in heal_filenames:
            img = pygame.image.load(name).convert_alpha()
            img = pygame.transform.rotozoom(img, 0, info["image_scale"]) 
            self.heal_frames.append(img)
        self.heal_frame_index = 0
        self.image = pygame.image.load("assets/enemy.png").convert_alpha()
        self.image = pygame.transform.rotozoom(self.image, 0, info["image_scale"])
        self.current_strategy = "CHASE" # 預設策略
        self.speech_text = "..."        # 敵人說的話
        self.is_thinking = False        # 是否正在等待 LLM 回應
        self.last_think_time = 0        # 上次思考的時間
        self.think_cooldown = 2000      # 每 2 秒思考一次 (毫秒)
        self.should_attack = False
        self.attack_count=0
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
        self.speech_text = "我是小火龍！"
        self.is_thinking = False
        self.last_think_time = 0
        self.think_cooldown = 3000 # Boss 講話慢一點
        
        self.last_attack_time = 0
        
        camera.add(self)
    # test.py -> Enemy 類別內

    def play_attack_anim(self):
        # 播放速度 (數字越小越慢)
        self.attack_frame_index += 0.1
        
        if self.attack_frame_index >= len(self.attack_frames):
            # 動畫播完了！
            self.is_attacking = False 
            self.attack_frame_index = 0
            # ★ 關鍵：播完後，要確保圖片變回原本的樣子，不然會卡在最後一張
            original_img = monster_data[self.name]["image"]
            self.image = pygame.transform.rotozoom(original_img, 0, monster_data[self.name]["image_scale"])
        else:
            # 還在播，換下一張圖
            self.image = self.attack_frames[int(self.attack_frame_index)]
            # 重新校正中心點 (因為噴火圖可能比原本大)
            self.rect = self.image.get_rect(center=self.rect.center)
    def heal(self):
        self.velocity=pygame.math.Vector2()
        
        if self.health<self.max_health:
            self.health+=HEALING_AMOUNT
            if self.health>self.max_health:
                self.health=self.max_health
        if len(self.heal_frames) > 0:
            self.heal_frame_index += 0.1
            if self.heal_frame_index >= len(self.heal_frames):
                self.heal_frame_index = 0
            self.image = self.heal_frames[int(self.heal_frame_index)]
            self.rect = self.image.get_rect(center=self.rect.center)
        draw_pos = self.rect.center - camera.offset
        
    def think(self, player_pos, player_hp):
            # 計算距離
        dist = self.pos.distance_to(player_pos)
        if self.last_strategy is not None:
            # 計算傷害
            damage_dealt = self.last_player_hp - player_hp
            
            # 生成紀錄文字
            if damage_dealt > 0:
                result_msg = f"造成 {damage_dealt} 點傷害 (有效)"
            else:
                result_msg = "被玩家躲開了 (無效)"
            
            log = f"上回合策略: {self.last_strategy} (距離 {int(dist)}) -> 結果: {result_msg}"
            
            # 存入記憶庫
            self.memory.append(log)
            
            # 保持記憶庫只有最新 3 筆
            if len(self.memory) > 3:
                self.memory.pop(0) 
        self.last_player_hp = player_hp   
            # 呼叫 Ollama (這會花 1~2 秒，但因為在線程裡所以不會卡畫面)
        json_response = ask_ollama(self.health, player_hp, dist,self.attack_count,self.memory)
        self.speech_text = json_response.get("message", "...")
        self.should_attack = json_response.get("should_attack", False)
        self.current_strategy = json_response.get("strategy", "IDLE")
        self.last_strategy = self.current_strategy
        
        # Debug 顯示 (可在終端機看到 AI 在想什麼)
        print(f"[{self.name}] 記憶: {self.memory}")
        print(f"[{self.name}] 決策: {self.current_strategy}")
        self.is_thinking = False # 思考結束
    def execute_strategy(self):
        player_vec = pygame.math.Vector2(player.hitbox_rect.center)
        my_vec = self.pos
        dist = (player_vec - my_vec).magnitude()
            
        self.velocity = pygame.math.Vector2(0, 0) # 預設不動
        original_img = monster_data[self.name]["image"]
        current_scale = monster_data[self.name]["image_scale"]
            # 根據 LLM 決定的策略來移動 (小腦)
        if self.current_strategy=="HEAL":
            self.heal()
        elif self.is_attacking:
            self.play_attack_anim()
        else:
            self.image = pygame.transform.rotozoom(original_img, 0, current_scale)
            if self.current_strategy == "CHASE":
                if dist > 0:
                    self.direction = (player_vec - my_vec).normalize()
                self.velocity = self.direction * self.speed
            elif self.current_strategy == "FLEE":
                if dist > 0:
                    self.direction = (player_vec - my_vec).normalize()
                    self.velocity = self.direction * -self.speed * 1.2 
            elif self.current_strategy == "IDLE":
                self.velocity = pygame.math.Vector2(0, 0)
            elif self.current_strategy == "ULTIMATE":
                self.velocity = pygame.math.Vector2(0, 0)

        self.pos += self.velocity
        self.rect.center = self.pos
        self.rect = self.image.get_rect(center=self.pos) # 確保 hitbox 跟隨
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
            self.health -= PLAYER_DAMAGE
            FloatingText(self.rect.midtop, "-100", (255, 255, 255))
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
       
        # # --- 新增：畫出 LLM 的對話 ---
        # text_surf = font.render(self.speech_text, True, (255, 255, 255))
        # text_rect = text_surf.get_rect(center=(self.rect.centerx - offset.x, self.rect.top - offset.y - 20))
        # surface.blit(text_surf, text_rect)

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
        self.execute_strategy()
        self.attack_behavior()
        self.check_collisions()

    # boss 行為
    def attack_behavior(self):
        if self.name == "boss":
            current_time = pygame.time.get_ticks()
            if current_time - self.last_attack_time > BOSS_ATTACK_COOLDOWN and self.should_attack:
                self.last_attack_time = current_time
                if self.current_strategy=="HEAL":
                    return
                self.is_attacking = True 
                self.last_attack_time = current_time
                # Check AI strategy for fireball type
                if self.current_strategy == "TRACKING FIRE BALL":
                    fireball = Track_Fireball(self.rect.center, player.hitbox_rect.center)
                    camera.add(fireball)
                    enemy_bullet_group.add(fireball)
                elif self.current_strategy == "ULTIMATE":
                    # 1. 取得 Boss 中心
                    boss_center = pygame.math.Vector2(self.rect.center)
                    # 2. 建立基準向量 (向右)
                    base_vec = pygame.math.Vector2(1, 0) 
                    self.attack_count += 1
                    # 3. 跑迴圈 0 ~ 360 度
                    for angle in range(0, 360, 20):
                        # 旋轉向量
                        rotated_vec = base_vec.rotate(angle)
                        # 算出目標點 (往外延伸 500 像素)
                        fake_target = boss_center + rotated_vec * 500
                        
                        # 生成火球
                        fireball = Fireball(self.rect.center, fake_target)
                        camera.add(fireball)
                        enemy_bullet_group.add(fireball)
                else:
                    fireball = Fireball(self.rect.center, player.hitbox_rect.center)
                    camera.add(fireball)
                    enemy_bullet_group.add(fireball)


class Camera(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.offset = pygame.math.Vector2()
        self.floor_rect = background.get_rect(topleft=(0,0))
        self.shake_strength = 0
    def add_shake(self, strength):
        self.shake_strength = max(self.shake_strength, strength)
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
        shake_offset_x = 0
        shake_offset_y = 0
        if self.shake_strength > 0:
            shake_offset_x = random.randint(-int(self.shake_strength), int(self.shake_strength))
            shake_offset_y = random.randint(-int(self.shake_strength), int(self.shake_strength))
            self.shake_strength *=0.9  # 漸漸減弱震動效果
            if self.shake_strength < 1: self.shake_strength = 0
        
        self.offset.x = target_x+ shake_offset_x
        self.offset.y = target_y+ shake_offset_y

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
                
                # # --- 新增：畫出 LLM 的對話 ---
                # text_surf = font.render(sprite.speech_text, True, (255, 255, 255))
                # text_rect = text_surf.get_rect(center=(sprite.rect.centerx - self.offset.x, sprite.rect.top - self.offset.y - 20))
                # screen.blit(text_surf, text_rect)

class UI():
    def __init__(self):
        self.font = pygame.font.SysFont("microsoftjhenghei", 20, bold=True)
        self.count_font=pygame.font.Font("font/PublicPixel.ttf", 50)
        self.flame_pic=pygame.image.load("assets/frame.png").convert_alpha()
    def show_countdown(self,time_left):
        secs=int(time_left/1000)+1
        if secs > 0:
            text_surf = self.count_font.render(str(secs), True, (255, 0, 0)) # 金色
        else:
            text_surf = self.count_font.render("GO!", True, (255, 0, 0))   # 紅色 GO!

        rect = text_surf.get_rect(center=(WIDTH//2, HEIGHT//2))
        
        # 做一點陰影效果讓字更清楚
        shadow_surf = self.count_font.render(str(secs) if secs > 0 else "GO!", True, (0,0,0))
        shadow_rect = rect.copy()
        shadow_rect.centerx += 4
        shadow_rect.centery += 4
        
        screen.blit(shadow_surf, shadow_rect)
        screen.blit(text_surf, rect)
        
    def draw_start_menu(self):
        # 1. 畫半透明遮罩 (讓背景變暗)
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180) # 0-255，越低越透明
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # 2. 畫標題
        title = pixel_font_large.render("DRAGON SLAYER", True, (255, 50, 50))
        title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 100))
        
        # 簡單的標題陰影效果
        shadow = pixel_font_large.render("DRAGON SLAYER", True, (100, 0, 0))
        screen.blit(shadow, (title_rect.x + 4, title_rect.y + 4))
        screen.blit(title, title_rect)
        
        # 3. 畫說明
        inst = banner_font.render("WASD: 移動 | 滑鼠左鍵: 射擊", True, WHITE)
        i_rect = inst.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(inst, i_rect)
        
        # 4. 閃爍的開始提示
        if pygame.time.get_ticks() % 1000 < 500:
            start_txt = menu_font.render("按空白鍵 [SPACE] 開始遊戲", True, YELLOW)
            s_rect = start_txt.get_rect(center=(WIDTH//2, HEIGHT//2 + 100))
            screen.blit(start_txt, s_rect)
        
    def display(self):
        # 血條
        pygame.draw.rect(screen, BLACK, (10, 10, 200, 20))
        pygame.draw.rect(screen, RED, (10, 10, player.health * 2, 20))
        pygame.draw.rect(screen, WHITE, (10, 10, 200, 20), 2)
        
        # 倒數計時顯示
        if not ready_to_spawn and current_time - level_over_time < game_stats["wave_cooldown"]:
            time_left = int((game_stats["wave_cooldown"] - (current_time - level_over_time)) / 1000)
            count_text = title_font.render(f"Next Wave: {time_left}", True, RED)
            screen.blit(count_text, (WIDTH//2 - 100, 100))
        if "boss_enemy" in globals() and boss_enemy and boss_enemy.health > 0:
            message=boss_enemy.speech_text
            max_text_width=WIDTH-250
            lines=[]
            current_line=""
            for char in message:
                test_line=current_line+char
                if banner_font.size(test_line)[0]<max_text_width:
                    current_line=test_line
                else:
                    lines.append(current_line)
                    current_line=char
            lines.append(current_line)
            
            max_line_width = 0
            for line in lines:
                w = banner_font.size(line)[0]
                if w > max_line_width:
                    max_line_width = w
            padding_x=200
            padding_y=80
            line_height = banner_font.get_height()
            min_width=600
            BG_WIDTH=max(min_width,max_line_width+padding_x)
            BG_HEIGHT=len(lines)*line_height+padding_y
            bg_rect = pygame.Rect(0, 0, BG_WIDTH, BG_HEIGHT)
            bg_rect.midtop = (WIDTH // 2, 80)
    
            if self.flame_pic:
                scaled_pic=pygame.transform.scale(self.flame_pic,(bg_rect.width,bg_rect.height))
                screen.blit(scaled_pic,bg_rect.topleft)
            else:
                pygame.draw.rect(screen,(0,0,0),bg_rect)
            start_y = bg_rect.centery - (len(lines) * line_height) // 2
            
            for i, line in enumerate(lines):
                text_surf = banner_font.render(line, True, (255, 255, 200))
                text_rect = text_surf.get_rect()
                # 水平置中
                text_rect.centerx = bg_rect.centerx 
                # 垂直排列
                text_rect.top = start_y + i * line_height
                screen.blit(text_surf, text_rect)


        if not ready_to_spawn and current_time - level_over_time < game_stats["wave_cooldown"]:
            time_left = int((game_stats["wave_cooldown"] - (current_time - level_over_time)) / 1000)
            count_text = title_font.render(f"Next Wave: {time_left}", True, RED)
            screen.blit(count_text, (WIDTH//2 - 150, 100))
            

# --- 初始化群組 ---
all_sprites_group = pygame.sprite.Group() 
bullet_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
enemy_bullet_group = pygame.sprite.Group()
boss_enemy = None
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
boss_enemy=None
def reset_game():
    global is_in_countdown, countdown_start_time,game_review_text,is_generating_review
    global game_active, ready_to_spawn, level_over_time,boss_enemy,current_state
    current_state = GameState.PLAYING
    game_active = True
    game_won=False
    player.pos = pygame.math.Vector2(PLAYER_START_X, PLAYER_START_Y)
    player.health = 100
    game_review_text = ""
    is_generating_review = False
    # game_stats["current_wave"] = 1
    # game_stats["enemies_killed_or_removed"] = 0
    
    enemy_group.empty()
    enemy_bullet_group.empty()
    camera.empty()
    camera.add(player)
    boss_pos=(BG_WIDTH//2,BG_HEIGHT//2)
    boss_enemy=Enemy("boss",boss_pos)
    is_in_countdown = True
    countdown_start_time = pygame.time.get_ticks()
    
    boss_enemy.last_think_time = 0 # 確保不會被冷卻時間卡住
    t = threading.Thread(target=boss_enemy.think, args=(player.rect.center, player.health))
    t.daemon = True
    t.start()
    boss_enemy.is_thinking = True # 標記為思考中
    # ready_to_spawn = True
    # level_over_time = pygame.time.get_ticks()

current_state = GameState.MENU
while True:
    current_time = pygame.time.get_ticks()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        # 狀態機: MENU
        if current_state == GameState.MENU:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                reset_game()
        
        # 狀態機: GAMEOVER
        elif current_state == GameState.GAMEOVER:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                reset_game()
        elif current_state == GameState.GAMEOVER:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                reset_game()
    screen.fill((0, 0, 0)) # 清空畫面
     
    if current_state == GameState.MENU:
        camera.custom_draw()
        ui.draw_start_menu()
    elif current_state == GameState.PLAYING:
        camera.custom_draw()
        ui.display()
        # Check fireball collisions
        if is_in_countdown:
            # 計算經過時間
            elapsed = current_time - countdown_start_time
            time_left = countdown_duration - elapsed
            
            # 畫出倒數數字
            ui.show_countdown(time_left)
            
            # 如果時間到了，結束倒數，開始遊戲
            if time_left <= 0:
                is_in_countdown = False
            
        else:
            # --- 倒數結束，遊戲正式邏輯 ---
            
            camera.update() # 這裡面包含了 player.update() 和 enemy.update()
            
            # Check fireball collisions
            collided_fireballs = pygame.sprite.spritecollide(player, enemy_bullet_group, False)
            for fireball in collided_fireballs:
                if not fireball.exploded:
                    fireball.explode()
                    player.get_damage(10)

            if player.health <= 0:
                game_active = False
                current_state = GameState.GAMEOVER
                game_won=False
            elif boss_enemy.health<=0:
                game_won=True
                game_active=False
                current_state = GameState.GAMEOVER
    elif current_state == GameState.GAMEOVER:
        camera.custom_draw() 
        ui.display()
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0,0,0))
        screen.blit(overlay, (0,0))
        if game_won:
            txt = title_font.render("YOU WIN!", True, GREEN)
            hint = font.render("Press P to Restart", True, WHITE)
            screen.blit(txt, (WIDTH//2 - 100, HEIGHT//2 - 50))
            screen.blit(hint, (WIDTH//2 - 100 ,HEIGHT//2 + 20))
            if not is_generating_review and game_review_text=="":
                is_generating_review=True
                t=threading.Thread(target=fetch_review_text,args=(boss_enemy.memory,game_won))
                t.daemon=True
                t.start()
                
            if is_generating_review:
                review_surf=font.render("火龍正在撰寫與你的戰鬥回顧...",True,WHITE)
                # screen.blit(review_surf,(WIDTH//2 - 150, HEIGHT//2 + 80))
            else:
                review_surf=banner_font.render(f"Boss:「{game_review_text}」",True,WHITE)
            
            review_rect=review_surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 120))
            screen.blit(review_surf,review_rect)
            
            # hint = font.render("Press P to Restart", True, WHITE)
            # screen.blit(hint, (WIDTH//2 - 120, HEIGHT//2 + 60))
        else:
            txt = title_font.render("GAME OVER", True, RED)
            hint = font.render("Press P to Restart", True, WHITE)
            screen.blit(txt, (WIDTH//2 - 150, HEIGHT//2 - 50))
            screen.blit(hint, (WIDTH//2 - 150,HEIGHT//2 + 20))

    pygame.display.update()
    clock.tick(FPS)