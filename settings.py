import pygame
import os
WIDTH=1280
HEIGHT=720
FPS=60
TILESIZE = 32
# colours
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)
YELLOW = (255,255,0)
BLACK = (0,0,0)
WHITE = (255,255,255)
#player setting
PLAYER_START_X=400
PLAYER_START_Y=500
PLAYER_SIZE=0.3
PLAYER_SPEED=8
PLAYER_DAMAGE=50
##bullet settings
SHOOT_COOLDOWN=15
BULLET_SCALE=0.05
BULLET_SPEED=100
BULLET_LIFETIME=500
GUN_OFFSET_X=50
GUN_OFFSET_Y=50
#enemy settings
ENEMY_SPEED=3
# boss settings
FIREBALL_COUNT=2
FIREBALL_SPEED = 6
FIREBALL_LIFETIME = 3000
BOSS_ATTACK_COOLDOWN = 2000

def extract_number(filename):
    return int(filename.split(".")[0])

def import_folder(path):
    surface_list = []

    for root, dirs, img_files in os.walk(path): 
        sorted_file_names = sorted(img_files, key=extract_number)  

    for img_name in sorted_file_names:
        full_path = path + '/' + img_name
        image_surf = pygame.image.load(full_path).convert_alpha()
        surface_list.append(image_surf)

    return surface_list
game_stats = {
    "enemies_killed_or_removed": 0, "necromancer_death_count": 0, "nightborne_death_count": 0, "coins": 0, "health_potion_heal": 20, "current_wave": 1, "number_of_enemies": [5, 6,7], "wave_cooldown": 6000, "num_health_potions": 3
}
monster_data = {
    "necromancer": {"health": 100,"attack_damage": 20, "speed": 2, "hunting_speed": [4,4,7,7,7], "image": pygame.image.load("assets/enemy.png"), "image_scale": 1, "hitbox_rect": pygame.Rect(0,0,75,100), "animation_speed": 0.2, "roam_animation_speed": 0.05, "death_animation_speed": 0.12, "notice_radius": 500},
    "nightborne": {"health": 100,"attack_damage": 40, "speed": 4, "hunting_speed": [4,4,6,6,6], "image": pygame.image.load("assets/enemy2.png"), "image_scale": 1, "hitbox_rect": pygame.Rect(0,0,75,90), "animation_speed": 0.1, "roam_animation_speed": 0.12, "death_animation_speed": 0.2, "notice_radius": 400},
    "boss": {
        "health": 2000,       # 血量超厚
        "attack_damage": 50,  # 攻擊力高
        "image": pygame.image.load("assets/image.png"),
        "speed": 0,           # [重點] 速度為 0，不會動
        "image_scale": 1.5,   # 體型變大
        "notice_radius": 9999,# 全圖嘲諷範圍
        "hitbox_rect": pygame.Rect(0, 0, 100, 100)
    }
}