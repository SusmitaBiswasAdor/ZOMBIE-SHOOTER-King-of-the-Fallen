from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import sys
import time

# ====== Global Variables ======
GRID_LENGTH = 2000
player_pos = [0.0, 0.0, 0.0]
respawn_point = [0, 0, 0]
player_angle = 0.0
player_life = 5
score = 0
fovY = 120
first_person = False
current_weapon = 0
weapons = ['pistol', 'rifle', 'knife']
ammo = {'pistol': 30, 'rifle': 30, 'knife': float('inf')}
day_time = 0.0
lava_time = 0.0
game_state = "MENU"
difficulty = "EASY"

camera_pos = [0, 800, 800]
BULLET_SPEED = 20.0
ENEMY_SPEED = 0.8
PLAYER_SPEED = 12.0
GUN_ROTATION_SPEED = 5.0
KNIFE_RANGE = 80
PLAYER_RADIUS = 35  
PLAYER_HEIGHT = 180  

invincibility_pickups = []
player_invincible = False
invincibility_timer = 0

bullets = []
enemies = []
walls = []
lava = []
grass_patches = []
ammo_pickups = []

# ====== Final Boss Variables ======
final_boss_active = False
final_boss = None
boss_level = 1
boss_transition_timer = 0
laser_target = None
boss_score_threshhold = 30 # 

# Boss animation variables
boss_attack_cooldown = 0
boss_attack_state = None
boss_attack_duration = 0
boss_animation_time = 0

start_time = time.time()

# ====== Core Functions ======
def distance3D(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)

def angle_to_vec(a):
    r = math.radians(a)
    return (-math.sin(r), math.cos(r))

# ====== Game World Configuration ======
WALL_DEFS = [
    # Regular walls
    (-700, -700, 0, 1400, 80, 200),
    (800, -700, 0, 1400, 80, 200),
    (-700, 800, 0, 1400, 80, 200),
    (800, 800, 0, 1400, 80, 200),
    (-1200, 0, 0, 500, 80, 200),
    (900, 0, 0, 500, 80, 200),
    (0, -1200, 0, 80, 500, 200),
    (0, 900, 0, 80, 500, 200),
    (-400, -400, 0, 80, 600, 200),
    (400, -400, 0, 80, 600, 200),
    (0, 0, 250, 600, 600, 40),
    
    (1200, 1200, 0, 100, 100, 50, True),    # Far NE quadrant
    (-1200, -1200, 0, 100, 100, 50, True),  # Far SW quadrant
    (700, -900, 0, 100, 100, 50, True)      # South corridor
]

DIFFICULTY_SETTINGS = {
    "EASY": {"enemies": 3, "enemy_speed": 0.6, "boss_health": 100, "boss_attack_rate": 1.0},
    "MEDIUM": {"enemies": 5, "enemy_speed": 0.8, "boss_health": 150, "boss_attack_rate": 2.0},
    "HARD": {"enemies": 7, "enemy_speed": 1.0, "boss_health": 200, "boss_attack_rate": 3.0}
}

def reset_game():
    global game_state, player_pos, player_angle,invincibility_pickups, player_life, score, ammo, day_time, lava_time, ENEMY_SPEED
    global final_boss_active, final_boss, boss_level, boss_attack_cooldown, boss_attack_state, boss_attack_duration, boss_animation_time,boss_transition_timer,boss_score_threshhold
    start_time = time.time()
    player_pos = list(respawn_point)
    player_angle = 0.0
    player_life = 5
    score = 0
    ammo = {'pistol': 30, 'rifle': 30, 'knife': float('inf')}
    day_time = 0.0
    lava_time = 0.0
    bullets.clear()
    enemies.clear()
    walls.clear()
    lava.clear()
    grass_patches.clear()
    ammo_pickups.clear()
    invincibility_pickups = []

    final_boss_active = False
    final_boss = None
    boss_level = 1
    boss_transition_timer = 0
    laser_target = None
    boss_score_threshhold = 30

    # Boss animation variables
    boss_attack_cooldown = 0
    boss_attack_state = None
    boss_attack_duration = 0
    boss_animation_time = 0


    for wall in WALL_DEFS:
        if len(wall) == 7 and wall[6]:
            lava.append(wall)
        else:
            walls.append(wall[:6])

    walls.extend([
        (-GRID_LENGTH, -GRID_LENGTH, 0, 2*GRID_LENGTH, 150, 300),
        (-GRID_LENGTH, GRID_LENGTH-150, 0, 2*GRID_LENGTH, 150, 300),
        (-GRID_LENGTH, -GRID_LENGTH, 0, 150, 2*GRID_LENGTH, 300),
        (GRID_LENGTH-150, -GRID_LENGTH, 0, 150, 2*GRID_LENGTH, 300)
    ])

    for _ in range(100):
        grass_patches.append((
            random.uniform(-GRID_LENGTH, GRID_LENGTH),
            random.uniform(-GRID_LENGTH, GRID_LENGTH),
            random.uniform(1.5, 4.0)
        ))

     # difficulty settings
    enemy_count = DIFFICULTY_SETTINGS[difficulty]["enemies"]
    
    #invincibility pickup list
    for _ in range(5):
        while True:
            x = random.uniform(-1800, 1800)
            y = random.uniform(-1800, 1800)
            if not is_colliding([x, y, 0]):
                invincibility_pickups.append([x, y, 0])  
                break
    
    # Spawn enemies
    for _ in range(enemy_count):
        while True:
            pos = [random.uniform(-1850, 1850), random.uniform(-1850, 1850), 0]
            if not is_colliding(pos, is_enemy=True):
                enemies.append({
                    'pos': pos,
                    'osc': random.uniform(0, 2*math.pi),
                    'walk_cycle': 0
                })
                break
        
    #ammo pickup list
    for _ in range(15):
        while True:
            pos = [random.uniform(-1800, 1800), random.uniform(-1800, 1800), 0]
            if not is_colliding(pos):
                ammo_pickups.append({
                    'pos': pos,
                    'type': random.choice(['pistol', 'rifle']),
                    'amount': random.randint(5, 15)
                })
                break
   
    glutPostRedisplay()


# ====== Collision System ======()
def is_colliding(pos,is_enemy=False):
    px, py, pz = pos

    if is_enemy:
        radius = 25  
        height = 100 
    else:
        radius = PLAYER_RADIUS
        height = PLAYER_HEIGHT

    # player's collision bounds
    player_min = (px - radius, py - radius, 0)
    player_max = (px + radius, py + radius, height)

    if game_state == "FINAL_BOSS":
        arena_size = 1500 
        if (px - radius < -arena_size or px + radius > arena_size or
            py - radius < -arena_size or py + radius > arena_size):
            return True
    else:
    #boundary check
        if (abs(px) > GRID_LENGTH - PLAYER_RADIUS or 
            abs(py) > GRID_LENGTH - PLAYER_RADIUS):
            return True
        
    if game_state == "FINAL_BOSS":
        return False
    
    # AABB collision check
    for wall in walls:
        if len(wall) == 7:  # lava 
            wx, wy, wz, ww, wh, wd, _ = wall
        else:
            wx, wy, wz, ww, wh, wd = wall[:6]
                
        wall_min = (wx, wy, wz)
        wall_max = (wx + ww, wy + wh, wz + wd)

     #Checking collision in all axes
        collision = (
                player_min[0] < wall_max[0] and
                player_max[0] > wall_min[0] and
                player_min[1] < wall_max[1] and
                player_max[1] > wall_min[1] and
                player_min[2] < wall_max[2] and
                player_max[2] > wall_min[2]
            )
        if collision:
                return True
    return False

def distance2D(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

# ====== Game Logic ======
def update():
    global game_state, player_life, score, day_time, lava_time, slash_anim, player_invincible, invincibility_timer, invincibility_pickups,final_boss_active,boss_score_threshhold,final_boss_active,final_boss,score
    
    if game_state != "PLAYING" and game_state != "FINAL_BOSS":
        return

    if game_state == "PLAYING" and score >=boss_score_threshhold :
        trigger_final_boss()
        

    # Time progression
    day_time += 0.0015
    lava_time += 0.1
    
    if game_state == "FINAL_BOSS" and final_boss_active and final_boss:
        update_final_boss()

    # Lava damage check
    for l in lava: 
        lx, ly, lz, lw, lh, ld, _ = l
        if (lx <= player_pos[0] <= lx + lw and
            ly <= player_pos[1] <= ly + lh and
            lz <= player_pos[2] <= lz + ld):
            player_life -= 1
            if player_life > 0:
                player_pos[:] = respawn_point
            else:
                game_state = "GAME_OVER"
            break  

    # Checking shield pickup collisions
    for pickup in invincibility_pickups[:]:
        if distance3D(player_pos, pickup) < 50:
            player_invincible = True
            invincibility_timer = 1000  
            invincibility_pickups.remove(pickup)
    
    #invincibility timer
    if player_invincible:
        invincibility_timer -= 1
        if invincibility_timer <= 0:
            player_invincible = False

    # Ammo pickups
    global ammo_pickups
    new_pickups = []
    for pickup in ammo_pickups:
        if distance3D(player_pos, pickup['pos']) < 30:
            ammo[pickup['type']] += pickup['amount']
        else:
            new_pickups.append(pickup)
    ammo_pickups = new_pickups
    
    # Bullet position update
    new_bullets = []
    for bullet in bullets:
        bullet['pos'][0] += bullet['dir'][0] * BULLET_SPEED
        bullet['pos'][1] += bullet['dir'][1] * BULLET_SPEED
        
        hit = False
        for enemy in enemies:
            if distance3D(bullet['pos'], enemy['pos']) < 35:
                score += 15
                hit = True
                enemy['pos'] = [random.uniform(-1850, 1850), random.uniform(-1850, 1850), 0]
                break
       
        #boss damage check
        if not hit and game_state == "FINAL_BOSS" and final_boss_active:
            if distance3D(bullet['pos'], final_boss['pos']) < final_boss['size']:
                damage = 5  
                if weapons[current_weapon] == 'rifle':
                    damage = 15  # Rifle does more damage
                elif weapons[current_weapon] == 'pistol':
                    damage = 10  # Pistol does medium damage

                score += damage * 2  
                hit = True
                final_boss['hp'] -= damage
        

        if not hit and not is_colliding(bullet['pos']):
            new_bullets.append(bullet)
    bullets[:] = new_bullets
    
    # Enemy 
    for enemy in enemies:
        if not player_invincible: 
            dx = player_pos[0] - enemy['pos'][0]
            dy = player_pos[1] - enemy['pos'][1]
            dist = math.hypot(dx, dy) or 1
            
            nx = dx/dist * ENEMY_SPEED
            ny = dy/dist * ENEMY_SPEED
            
            new_pos = [enemy['pos'][0] + nx, enemy['pos'][1] + ny, 0]
        
            if not is_colliding(new_pos, is_enemy=True):
                enemy['pos'][0] = new_pos[0]
                enemy['pos'][1] = new_pos[1]
        
        enemy['osc'] += 0.12
        enemy['walk_cycle'] += 0.1

        if weapons[current_weapon] == 'knife':
            dx, dy = angle_to_vec(player_angle)
            knife_offset = 75  
            knife_x = player_pos[0] + dx * knife_offset
            knife_y = player_pos[1] + dy * knife_offset
            
            # Checking collisions with all enemies
            for enemy in enemies[:]: 
                if distance2D((knife_x, knife_y), enemy['pos']) < 40:
                    score += 10
                    enemies.remove(enemy)
                    while True:
                        new_pos = [random.uniform(-1850, 1850), random.uniform(-1850, 1850), 0]
                        if not is_colliding(new_pos, is_enemy=True):
                            enemies.append({
                                'pos': new_pos,
                                'osc': random.uniform(0, 2*math.pi),
                                'walk_cycle': 0
                            })
                            break
                    break 

        #player enemy collision
        if not player_invincible and distance3D(enemy['pos'], player_pos) < 35:
            player_life -= 1
            if player_life > 0:
                player_pos[:] = respawn_point
            else:
                game_state = "GAME_OVER"
            enemy['pos'] = [random.uniform(-1850, 1850), random.uniform(-1850, 1850), 0]
    
    glutPostRedisplay()

def fire():
    if weapons[current_weapon] != 'knife' and ammo[weapons[current_weapon]] <= 0:
        return
    
    dx, dy = angle_to_vec(player_angle)
    bullets.append({
        'pos': [player_pos[0] + dx*40, player_pos[1] + dy*40, 0],
        'dir': [dx, dy, 0]
    })
    if weapons[current_weapon] != 'knife':
        ammo[weapons[current_weapon]] -= 1

def knife_attack():
    global score
    for enemy in enemies[:]:
        if distance3D(player_pos, enemy['pos']) < KNIFE_RANGE:
            score += 5
            enemies.remove(enemy)
            enemies.append({
                'pos': [random.uniform(-1850, 1850), random.uniform(-1850, 1850), 0],
                'osc': random.uniform(0, 2*math.pi),
                'walk_cycle': 0
            })

########### Final Boss Functions ======

def trigger_final_boss():
    """Trigger the final boss encounter."""
    global game_state, final_boss_active, boss_transition_timer, boss_camera_transition,boss_score_threshhold

    if not final_boss_active and (score >= boss_score_threshhold or game_state == "PLAYING"):
        print("Triggering final boss...")
        spawn_final_boss(boss_level)
        final_boss_active = True
        boss_transition_timer = 60  
        boss_camera_transition = 0.0
        game_state = "FINAL_BOSS"
        print(f"Game state: {game_state}, Final boss active: {final_boss_active}")

############################################
def keyboardListener(key, x, y):
    global player_angle, current_weapon, game_state, difficulty, ENEMY_SPEED
    key = key.decode().lower()
    
    if game_state == "MENU":
        if key == 'k':
            ENEMY_SPEED = DIFFICULTY_SETTINGS[difficulty]["enemy_speed"]
            game_state = "PLAYING"
            reset_game()
        elif key == '7':
            # Cycle through difficulties
            difficulties = list(DIFFICULTY_SETTINGS.keys())
            current_index = difficulties.index(difficulty)
            difficulty = difficulties[(current_index + 1) % len(difficulties)]
            glutPostRedisplay()
        return
    
    if game_state == "GAME_OVER" or game_state == "WIN":
        if key == 'r':
            game_state = "MENU"
            glutPostRedisplay()
        return
    
    if game_state == "PAUSED" :
        if key == 'h':
            game_state = "PLAYING"
            glutPostRedisplay() 
        elif key == 'p':
            game_state = "MENU"
            glutPostRedisplay() 
        return
    
    if key == 'h':
        game_state = "PAUSED"
        glutPostRedisplay()
        return
    
    if game_state not in ["PLAYING", "FINAL_BOSS"]:
        return
    
    if key == 'f': 
       trigger_final_boss()

    if key == 'w' or key == 's':
        dx, dy = angle_to_vec(player_angle)
        move_speed = PLAYER_SPEED * (-1 if key == 's' else 1)

        new_x = player_pos[0] + dx * move_speed
        new_y = player_pos[1] + dy * move_speed

        if not is_colliding((new_x, new_y, 0)):
            # first-person cam position check
            if first_person:
                cam_offset = 50  # Match camera forward offset
                cam_x = new_x + dx * cam_offset
                cam_y = new_y + dy * cam_offset
                if not is_colliding((cam_x, cam_y, 100)):
                    player_pos[0] = new_x
                    player_pos[1] = new_y
            else:
                player_pos[0] = new_x
                player_pos[1] = new_y
    elif key == 'a':
        player_angle += GUN_ROTATION_SPEED
    elif key == 'd':
        player_angle -= GUN_ROTATION_SPEED

    elif key == 'r':
        ammo['pistol'] = 30
        ammo['rifle'] = 30
    elif key == ' ':
        fire()
    elif key == '1':
        current_weapon = 0
    elif key == '2':
        current_weapon = 1
    elif key == '3':
        current_weapon = 2

def specialKeyListener(key, x, y):
    global camera_pos
    cam_x, cam_y, cam_z = camera_pos  
    radius = math.hypot(cam_x, cam_y)
    angle = math.atan2(cam_y, cam_x) 
    
    if key == GLUT_KEY_UP:
        cam_z += 15
    elif key == GLUT_KEY_DOWN:
        cam_z -= 15
    elif key == GLUT_KEY_LEFT:
        angle -= math.radians(3)  
    elif key == GLUT_KEY_RIGHT:
        angle += math.radians(3)  

    new_cam_x = radius * math.cos(angle)
    new_cam_y = radius * math.sin(angle)
    
    camera_pos = (new_cam_x, new_cam_y, cam_z)
    glutPostRedisplay()

def mouseListener(button, state, x, y):
    global game_state, first_person
    if game_state == "MENU":
        if state == GLUT_DOWN:
            if 350 <= x <= 650:
                if 500 <= y <= 550:
                    glutDestroyWindow(glutGetWindow())
    elif button == GLUT_LEFT_BUTTON:
        if state == GLUT_DOWN:
            if weapons[current_weapon] == 'knife':
                knife_attack()
            else:
                fire()
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person = not first_person


# ====== Graphics System ======
def draw_sky():
    r = 0.3 + 0.2 * math.sin(day_time)
    g = 0.5 + 0.3 * math.sin(day_time)
    b = 0.7 + 0.2 * math.cos(day_time)
    glClearColor(r, g, b, 1.0)

def draw_ground():
    # glColor3f(1.0, 0.5, 0.0)
    glColor3f(0.1, 0.4, 0.1)  # Dark green
    glBegin(GL_QUADS)
    glVertex3f(-50, -50, 1)
    glVertex3f(50, -50, 1)
    glVertex3f(50, 50, 1)
    glVertex3f(-50, 50, 1)
    glEnd()

    glColor3f(0.12, 0.45, 0.15)
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glEnd()

    for x, y, h in grass_patches:
        glPushMatrix()
        glTranslatef(x, y, 0)
        glColor3f(0.1, 0.35, 0.1)
        gluCylinder(gluNewQuadric(), h*2.5, 0, h*5, 10, 2)
        glPopMatrix()

    glColor3f(0.2, 0.2, 0.2)
    road_width = 350
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -road_width/2, 1)
    glVertex3f(GRID_LENGTH, -road_width/2, 1)
    glVertex3f(GRID_LENGTH, road_width/2, 1)
    glVertex3f(-GRID_LENGTH, road_width/2, 1)
    glVertex3f(-road_width/2, -GRID_LENGTH, 1)
    glVertex3f(road_width/2, -GRID_LENGTH, 1)
    glVertex3f(road_width/2, GRID_LENGTH, 1)
    glVertex3f(-road_width/2, GRID_LENGTH, 1)
    glEnd()

def draw_walls():
    wall_colors = [
        (0.55, 0.27, 0.07),  
        (0.65, 0.16, 0.16),  
        (0.62, 0.45, 0.03), 
        (0.82, 0.41, 0.12)   
    
    ]
    for i, wall in enumerate(walls):
        wx, wy, wz, ww, wh, wd = wall
        shading_factor = (wx + wy) / (2 * GRID_LENGTH)  
        shading_factor = max(0.5, min(1.0, 0.8 + shading_factor * 0.2))
        base_color = wall_colors[i % len(wall_colors)]
        shaded_color = (
            base_color[0] * shading_factor,
            base_color[1] * shading_factor,
            base_color[2] * shading_factor
        )
        glColor3f(*shaded_color)
        glPushMatrix()
        glTranslatef(wx + ww/2, wy + wh/2, wz + wd/2)
        glScalef(ww, wh, wd)
        glutSolidCube(1.0)
        glPopMatrix()

def draw_lava():
    current_time = (time.time() - start_time)  / 0.5
    for l in lava:
        lx, ly, lz, lw, lh, ld, _ = l
        glPushMatrix()
        glTranslatef(lx + lw/2, ly + lh/2, lz + math.sin(current_time*0.002)*5)
        glScalef(lw, lh, ld + math.sin(current_time*0.003)*3)
        lava_color = (0.9, 0.3, 0.0)
        glColor3f(*lava_color)
        glutSolidCube(1.0)
        glPopMatrix()

def draw_zombie(pos, osc):
    glPushMatrix()
    glTranslatef(*pos)
    glRotatef(math.degrees(osc)*15, 0, 0, 1)
    
    glColor3f(0.15, 0.35, 0.1)
    glPushMatrix()
    glTranslatef(0, 0, 50)
    glScalef(25, 25, 50)
    glutSolidCube(1.0)
    glPopMatrix()
    
    glColor3f(0.75, 0.55, 0.4)
    glPushMatrix()
    glTranslatef(0, 0, 90)
    glutSolidSphere(18, 20, 20)
    
    glColor3f(1, 1, 1)
    glPushMatrix()
    glTranslatef(-8, 12, 8)
    glutSolidSphere(4, 10, 10)
    glTranslatef(16, 0, 0)
    glutSolidSphere(4, 10, 10)
    glPopMatrix()
    
    glColor3f(0.5, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(0, 10, -8)
    glScalef(10, 1.5, 4)
    glutSolidCube(1.0)
    glPopMatrix()
    glPopMatrix()
    
    arm_length = 50
    for side in [-1, 1]:
        glPushMatrix()
        glTranslatef(side*35, 0, 50)
        glRotatef(math.sin(osc)*40, 1, 0, 0)
        glColor3f(0.75, 0.55, 0.4)
        gluCylinder(gluNewQuadric(), 7, 7, arm_length, 12, 12)
        glPopMatrix()
    
    leg_length = 60
    for side in [-1, 1]:
        glPushMatrix()
        glTranslatef(side*15, 0, 0)
        glRotatef(math.sin(osc+math.pi/2)*25, 1, 0, 0)
        glColor3f(0.15, 0.25, 0.1)
        gluCylinder(gluNewQuadric(), 10, 7, leg_length, 12, 12)
        glPopMatrix()
    
    glPopMatrix()

def draw_gun():
    if weapons[current_weapon] == 'rifle':
        glColor3f(0.25, 0.25, 0.25)
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 4, 3, 60, 20, 20)
        glTranslatef(0, 0, 60)
        glutSolidSphere(4, 15, 15)
        glPopMatrix()
    elif weapons[current_weapon] == 'pistol':
        glColor3f(0.0, 0.0, 0.5)
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 3, 2, 40, 15, 15)
        glTranslatef(0, 0, 40)
        glutSolidSphere(2.5, 12, 12)
        glPopMatrix()
    else:
        arm_length = 75  
        glPushMatrix()
        glRotatef(-80, 1, 0, 0) 
        glTranslatef(-10, -10, 0) 
        glTranslatef(0, 0, arm_length)  
        glPushMatrix()

        # Sword blade
        glColor3f(0.7, 0.7, 0.7) 
        glScalef(1.2, 1.2, 60)     
        glutSolidCube(1.0)
        
        glColor3f(0.3, 0.2, 0.1)  
        glScalef(1, 1, 0.1)       
        glTranslatef(0, 0, -5)   
        glutSolidCube(3.0)
        glPopMatrix()
        glPopMatrix()

def draw_player():
    glPushMatrix()
    glTranslatef(*player_pos)
    glRotatef(player_angle, 0, 0, 1)
    glScalef(0.7, 0.7, 0.7)

    glColor3f(0.0, 0.0, 0.0)  
    glPushMatrix()
    glTranslatef(0, 0, 70) 
    glScalef(25, 25, 40)     
    glutSolidCube(1.0)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 110) 
    
    glColor3f(0.9, 0.75, 0.6)
    glutSolidSphere(20, 20, 20)
    
    glPushMatrix()
    glRotatef(180, 0, 0, 1)  
    glColor3f(0.0, 0.0, 0.0)

    glPushMatrix()
    glTranslatef(0, 0, 15)
    glScalef(1.2, 1.2, 0.6)
    glutSolidSphere(22, 20, 20)
    
    glColor3f(0.15, 0.15, 0.15)
    glTranslatef(0, 0, -10)
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 22, 22, 5, 20, 2)
    glPopMatrix()
    
    glPopMatrix() 
    glPopMatrix() 

    glColor3f(1.0, 0.8, 0.6)
    for side in [-1, 1]:
        glPushMatrix()
        glTranslatef(side*15, 0, 85)
        glRotatef(-90, 1, 0, 0)  
        gluCylinder(gluNewQuadric(), 6, 3, 50, 10, 10)
        glPopMatrix()

 
    if weapons[current_weapon] != 'knife':
        glPushMatrix()
        glTranslatef(0, 0, 85)  
        glTranslatef(0, 10, 0) 
        glRotatef(0, 1, 0, 0)
        draw_gun()  
        glPopMatrix()
    else:
        glPushMatrix()
        glTranslatef(30, 0, 85)
        glRotatef(-45, 0, 1, 0)
        draw_gun()
        glPopMatrix()
    
    glColor3f(0, 0.25, 0.5)
    for side in [-1, 1]:
        glPushMatrix()
        glTranslatef(side*15, 0, 0)
        gluCylinder(gluNewQuadric(), 9, 7, 50, 12, 12)
        glPopMatrix()
    
    glPopMatrix()

def draw_protection_sphere():
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2] + 90) 
    
    glColor3f(0.3, 0.5, 1.0) 
    for i in range(8):
        glPushMatrix()
        glRotatef(45 * i, 0, 1, 0)  
        gluCylinder(gluNewQuadric(), 75, 75, 1, 32, 1)  
        glPopMatrix()
    
    for i in range(4):
        glPushMatrix()
        glRotatef(45 * i, 1, 0, 0)  
        gluCylinder(gluNewQuadric(), 75, 75, 1, 32, 1)
        glPopMatrix()
    glPopMatrix()

########################FINAL BOSS DRAWING###########################
def draw_final_boss():
    if final_boss_active and final_boss:
        if boss_attack_state == 'laser_beam' and laser_target:
            #laser beam effect
            glPushMatrix()
            glBegin(GL_LINES)
            glColor3f(1.0, 0.0, 0.0) 
            glVertex3f(final_boss['pos'][0], final_boss['pos'][1], final_boss['pos'][2] + final_boss['size'])
            glVertex3f(laser_target[0], laser_target[1], laser_target[2])
            glEnd()
            glPopMatrix()
            
        glPushMatrix()
        glTranslatef(final_boss['pos'][0], final_boss['pos'][1], final_boss['pos'][2])

        # ===== Head =====
        glPushMatrix()
        glTranslatef(0, 0, final_boss['size'] * 1.5) 
        glColor3f(0.95, 0.75, 0.6)  
        gluSphere(gluNewQuadric(), final_boss['size'] / 2, 30, 30)
        glPopMatrix()

        # ===== Witch Hat =====
        # Hat brim
        glPushMatrix()
        glTranslatef(0, 0, final_boss['size'] * 1.9) 
        glColor3f(0.1, 0.1, 0.1)  
        gluCylinder(gluNewQuadric(), 0, final_boss['size'] * 1.1, 1, 30, 1) 

        # Hat cone
        glPushMatrix()
        glTranslatef(0, 0, final_boss['size'] * 0.05)  
        glColor3f(0.1, 0.1, 0.1)  
        gluCylinder(gluNewQuadric(), final_boss['size'] * 0.6, 0, final_boss['size'] * 1.2, 30, 30)
        glPopMatrix()  
        
        # Hat band
        glColor3f(0.5, 0.0, 0.5)  
        gluCylinder(gluNewQuadric(), final_boss['size'] * 0.61, final_boss['size'] * 0.61, final_boss['size'] * 0.1, 30, 5)
        glPopMatrix()

        # ===== Hair =====
        glPushMatrix()
        glTranslatef(0, 0, final_boss['size'] * 1.5)
        glColor3f(0.1, 0.1, 0.1)  
        
        for i in range(20):
            glPushMatrix()
            glRotatef(i * 18, 0, 0, 1)  
            glRotatef(random.uniform(30, 60), 1, 0, 0)  
            glTranslatef(0, final_boss['size'] * 0.6, 0)
            gluCylinder(gluNewQuadric(), final_boss['size'] / 20, final_boss['size'] / 40, final_boss['size'] * 0.8, 8, 2)
            glPopMatrix()
        glPopMatrix()

        # ===== Body =====
        glPushMatrix()
        glTranslatef(0, 0, final_boss['size'] * 0.5) 
        glColor3f(0.2, 0.0, 0.3)  
        gluCylinder(gluNewQuadric(), final_boss['size'], final_boss['size'] * 0.8, final_boss['size'], 30, 30)
        
        glTranslatef(0, 0, 0)
        glColor3f(0.1, 0.0, 0.2) 
        gluCylinder(gluNewQuadric(), final_boss['size'] * 0.8, final_boss['size'] * 1.3, final_boss['size'] * 0.5, 30, 30)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0, 0, final_boss['size'] * 1.2)
        glColor3f(0.95, 0.75, 0.6)  
        gluCylinder(gluNewQuadric(), final_boss['size'] / 4, final_boss['size'] / 3, final_boss['size'] * 0.3, 20, 5)
        glPopMatrix()

        # ===== Arms =====
        arm_length = final_boss['size'] * 0.8
        for side in [-1, 1]:  
            glPushMatrix()
            glTranslatef(side * final_boss['size'] * 0.7, 0, final_boss['size'] * 1.2) 
            glRotatef(side * 30, 1, 0, 0) 
            glRotatef(side * 20, 0, 1, 0)  
            
            # Upper arm
            glColor3f(0.2, 0.0, 0.3) 
            gluCylinder(gluNewQuadric(), final_boss['size'] / 6, final_boss['size'] / 7, arm_length, 15, 5)
            
            # Elbow joint
            glTranslatef(0, 0, arm_length)

            gluSphere(gluNewQuadric(), final_boss['size'] / 7, 15, 15)
            # Forearm - bent at elbow
            glRotatef(side * 30, 0, 1, 0)
            glRotatef(40, 1, 0, 0)
            glColor3f(0.2, 0.0, 0.3) 
            gluCylinder(gluNewQuadric(), final_boss['size'] / 7, final_boss['size'] / 8, arm_length, 15, 5)
            
            # Bony hands
            glTranslatef(0, 0, arm_length)
            glColor3f(0.8, 0.7, 0.6)  

            gluSphere(gluNewQuadric(), final_boss['size'] / 8, 10, 10)
            # Fingers (as claws)
            for f in range(5):
                glPushMatrix()
                glRotatef(f * 30 - 90, 0, 0, 1)  
                glTranslatef(0, final_boss['size'] / 10, 0)
                glRotatef(20, 1, 0, 0) 
                
                # Finger segment
                glColor3f(0.8, 0.7, 0.6)
                gluCylinder(gluNewQuadric(), final_boss['size'] / 20, final_boss['size'] / 25, final_boss['size'] / 6, 8, 2)
                
                # Sharp nail
                glTranslatef(0, 0, final_boss['size'] / 6)
                glColor3f(0.3, 0.0, 0.0)  
                gluCylinder(gluNewQuadric(), final_boss['size'] / 40, 0, final_boss['size'] / 10, 10, 6)
                glPopMatrix()
            glPopMatrix()
        
        for side in [-1, 1]:  
            glPushMatrix()
            glTranslatef(side * final_boss['size'], 0, final_boss['size'] * 1.2)
            glColor4f(0.5, 0.0, 0.5, 0.5)  
           
            gluSphere(gluNewQuadric(), final_boss['size'] / 5 + (math.sin(time.time() - start_time) / 0.75) * 5, 15, 15)
            time_offset = (time.time() - start_time)  / 0.25
            for i in range(8):
                angle = i * 45 + time_offset
                distance = final_boss['size'] / 4 + math.sin(time_offset + i) * 5
                
                glPushMatrix()
                glRotatef(angle, 0, 0, 1)
                glTranslatef(distance, 0, 0)
                glColor3f(1.0, 0.0, 1.0) 
                
                gluSphere(gluNewQuadric(), final_boss['size'] / 30, 8, 8)
                glPopMatrix()
            glPopMatrix()

        # ===== Legs =====
        leg_length = final_boss['size']
        for side in [-1, 1]:  
            glPushMatrix()
            glTranslatef(side * final_boss['size'] * 0.5, 0, 0)  
            glColor3f(0.1, 0.0, 0.2) 
            gluCylinder(gluNewQuadric(), final_boss['size'] / 4, final_boss['size'] / 4, leg_length, 20, 20)
            
            # Feet
            glTranslatef(0, 0, 0)  
            glColor3f(0.0, 0.0, 0.0) 
            gluSphere(gluNewQuadric(), final_boss['size'] / 4, 15, 15)
            # Pointed shoes
            glTranslatef(0, final_boss['size'] / 4, 0)
            glRotatef(-90, 1, 0, 0)
            glPopMatrix()

       #  ===== Broomstick =====
        glPushMatrix()
        glTranslatef(final_boss['size'] * 0.8, -final_boss['size'] * 0.5, final_boss['size'] * 0.5)
        glRotatef(45, 0, 1, 0)  # Angle the broom
        glRotatef(30, 1, 0, 0)
        
        # Stick
        glColor3f(0.4, 0.2, 0.1)  # Dark brown stick
        gluCylinder(gluNewQuadric(), final_boss['size'] / 20, final_boss['size'] / 20, final_boss['size'] * 2, 12, 2)
        
        # Bristles
        glTranslatef(0, 0, final_boss['size'] * 2)
        glColor3f(0.6, 0.4, 0.0)  # Golden bristles
        gluCylinder(gluNewQuadric(), final_boss['size'] / 8, 0, final_boss['size'] / 2, 15, 5)


        # Magical glow on broomstick
        glColor3f(0.8, 0.0, 1.0)  # Neon purple
        gluSphere(gluNewQuadric(), final_boss['size'] / 6 + math.sin(time.time() - start_time/ 0.5) * 10, 15, 15)
        glPopMatrix()


        # ===== Magical Aura =====
        glPushMatrix()
        glColor4f(0.5, 0.0, 0.5, 0.2) 
        draw_demon_aura(final_boss['size'] * 2.5 + math.sin((time.time() - start_time) / 0.8) * 10, 20, 20)
        glPopMatrix()

        # ===== Floating Magical Orbs =====
        time_factor = (time.time() - start_time)  / 0.5
        for i in range(3):
            glPushMatrix()
            angle = time_factor * 45 + i * 120
            orb_x = math.sin(angle * 0.0174533) * final_boss['size'] * 1.5
            orb_y = math.cos(angle * 0.0174533) * final_boss['size'] * 1.5
            orb_z = final_boss['size'] * 1.0 + math.sin(time_factor * 2 + i) * final_boss['size'] * 0.2
            
            glTranslatef(orb_x, orb_y, orb_z)
            
            # Orb
            glColor3f(0.8, 0.0, 0.8)  # Purple orb
            gluSphere(gluNewQuadric(), final_boss['size'] / 10, 15, 15)

            
            # Glow
            glColor4f(0.8, 0.0, 0.8, 0.3)  # Purple glow
            # glutSolidSphere(final_boss['size'] / 8 + math.sin(time_factor * 5 + i) * 5, 10, 10)
            gluSphere(gluNewQuadric(), final_boss['size'] / 8 + math.sin(time_factor * 5 + i) * 5, 10, 10)
            glPopMatrix()

        glPopMatrix()

def draw_demon_aura(radius, slices, stacks):
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        z0 = radius * math.sin(lat0)
        zr0 = radius * math.cos(lat0)

        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        z1 = radius * math.sin(lat1)
        zr1 = radius * math.cos(lat1)

        for j in range(slices):
            lng0 = 2 * math.pi * float(j) / slices
            x0 = math.cos(lng0)
            y0 = math.sin(lng0)

            lng1 = 2 * math.pi * float((j + 1) % slices) / slices
            x1 = math.cos(lng1)
            y1 = math.sin(lng1)

            glBegin(GL_LINES)
            glVertex3f(x0 * zr0, y0 * zr0, z0)
            glVertex3f(x1 * zr0, y1 * zr0, z0)

            glVertex3f(x0 * zr0, y0 * zr0, z0)
            glVertex3f(x0 * zr1, y0 * zr1, z1)
            glEnd()

def draw_boss_arena():
    arena_size = 1500
    wall_thickness = 150
    wall_height = 300


    wall_color = (0.1, 0.0, 0.15)
 
    floor_color = (0.2, 0.2, 0.3)  
    accent_color = (0.5, 0.0, 0.7)
    
    # Draw floor
    glColor3f(*floor_color)
    glPushMatrix()
    glTranslatef(0, 0, -10)
    glScalef(2 * arena_size, 2 * arena_size, 20)
    glutSolidCube(1)
    glPopMatrix()
    
    # Draw walls
    glColor3f(*wall_color)

    # Bottom wall
    glPushMatrix()
    glTranslatef(0, -arena_size, wall_height / 2)
    glScalef(2 * arena_size, wall_thickness, wall_height)
    glutSolidCube(1)
    glPopMatrix()

    # Top wall
    glPushMatrix()
    glTranslatef(0, arena_size - wall_thickness, wall_height / 2)
    glScalef(2 * arena_size, wall_thickness, wall_height)
    glutSolidCube(1)
    glPopMatrix()

    # Left wall
    glPushMatrix()
    glTranslatef(-arena_size, 0, wall_height / 2)
    glScalef(wall_thickness, 2 * arena_size, wall_height)
    glutSolidCube(1)
    glPopMatrix()

    # Right wall
    glPushMatrix()
    glTranslatef(arena_size - wall_thickness, 0, wall_height / 2)
    glScalef(wall_thickness, 2 * arena_size, wall_height)
    glutSolidCube(1)
    glPopMatrix()
    
   
    draw_lava()
    draw_pillars(arena_size, accent_color)

def draw_pillars(arena_size, accent_color):
    pillar_radius = 50
    pillar_height = 500
    num_pillars = 8
    pillar_distance = arena_size * 0.8
    pillar_color = (accent_color[0] * 0.5, accent_color[1] * 0.5, accent_color[2] * 0.5)
    quadric = gluNewQuadric()
    for i in range(num_pillars):
        angle = i * (2 * 3.14159 / num_pillars)
        x = pillar_distance * math.cos(angle)
        y = pillar_distance * math.sin(angle)
        glPushMatrix()
        glTranslatef(x, y, 0)
        
        glColor3f(*pillar_color)
        gluCylinder(quadric, pillar_radius * 1.2, pillar_radius, pillar_height, 16, 4)
        
        glColor3f(*accent_color)
        glPushMatrix()
        glTranslatef(0, 0, pillar_height * 0.8)

       
        ring_segments = 16  
        ring_radius = pillar_radius * 1.1 
        cylinder_thickness = pillar_radius * 0.75 
        
        for i in range(ring_segments):
            angle = (2 * math.pi / ring_segments) * i  
            x = ring_radius * math.cos(angle)  
            y = ring_radius * math.sin(angle) 
        
            glPushMatrix()
            glTranslatef(x, y, 0)  
            glRotatef(math.degrees(angle), 0, 0, 1)  
            gluCylinder(gluNewQuadric(), cylinder_thickness, cylinder_thickness, 1, 8, 1)  # Thin cylinder
            glPopMatrix()
        glPopMatrix()
        
        glColor3f(*accent_color)
        glPushMatrix()
        glTranslatef(0, 0, pillar_height)
        gluCylinder(quadric, pillar_radius * 0.8, 0, pillar_radius * 2, 8, 1)
        glPopMatrix()
        
        glPopMatrix()


# ====== UI System ======
def draw_text(x, y, text):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_menu():
    glClearColor(0.1, 0.0, 0.0, 1.0) 
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glColor3f(1, 1, 1)
  
    draw_text(300, 600, "WELCOME TO ZOMBIE SHOOTER: King of the Fallen")
    draw_text(400, 550, "START GAME (K)")
    draw_text(400, 450,f"DIFFICULTY: {difficulty} (7)")
    draw_text(400, 350, "EXIT GAME (Click)")
    glutSwapBuffers()

def draw_win():
    glClearColor(0.8, 0.6, 0.2, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    draw_text(450, 400, "YOU WON!")
    draw_text(400, 350, "Press r to return to menu")
    glutSwapBuffers()
    
def draw_game_over():
    glClearColor(0, 0, 0, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    draw_text(450, 400, "YOU DIED!")
    draw_text(400, 350, "Press R to return to menu")
    glutSwapBuffers()

def draw_shield_pickup(pos):
    glPushMatrix()
    glTranslatef(pos[0], pos[1], 40) 
    glColor3f(0.1, 0.1, 0.5) 
    gluCylinder(gluNewQuadric(), 25, 20, 5, 12, 2)
    
    glPushMatrix()
    glTranslatef(0, 0, 25)
    glColor3f(0.3, 0.3, 1.0) 
    glBegin(GL_QUADS)
    glVertex3f(-15, 0, 0)
    glVertex3f(0, 15, 0)
    glVertex3f(15, 0, 0)
    glVertex3f(0, -15, 0)
    glEnd()
    glColor3f(0.8, 0.8, 1.0)  
    glutSolidSphere(8, 16, 16)
    
    glPopMatrix()
    glPopMatrix()

def draw_bullets():
    for bullet in bullets:
            glPushMatrix()
            glTranslatef(*bullet['pos'])
            glColor3f(1, 0.5, 0)
            gluSphere(gluNewQuadric(), 4, 12, 12)
            glPopMatrix()

def draw_ammo_pickups():
    for pickup in ammo_pickups:
            glPushMatrix()
            glTranslatef(*pickup['pos'])
            glColor3f(1, 1, 0 if pickup['type'] == 'pistol' else 1)
            gluSphere(gluNewQuadric(), 15, 12, 12)
            glPopMatrix()



# ====== Main Rendering ======
def showScreen():
    if game_state == "MENU":
        draw_menu()
        return
    elif game_state == "GAME_OVER":
        draw_game_over()
        return
    elif game_state == "WIN":
        draw_win()
        return
    else:     
        draw_sky()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        width = glutGet(GLUT_WINDOW_WIDTH)
        height = glutGet(GLUT_WINDOW_HEIGHT)
        glViewport(0, 0, width, height) 
        setupCamera()
        if game_state == "FINAL_BOSS" and boss_transition_timer > 0:
            draw_boss_arena() 
            draw_final_boss()  
        else:
            draw_ground()
            draw_walls()
            draw_lava()
        draw_player()
        
        if player_invincible:
            draw_protection_sphere()

        for enemy in enemies:
            draw_zombie(enemy['pos'], enemy['walk_cycle'])
        
        draw_bullets()
        draw_ammo_pickups()

        for pickup in invincibility_pickups:
             draw_shield_pickup(pickup)

        current_weapon_name = weapons[current_weapon].upper()
        time_of_day = "Day" if math.sin(day_time) > 0 else "Night"
        if game_state == "FINAL_BOSS":
            draw_text(800, 770, "FINAL BOSS ARENA")
            if final_boss:
                draw_text(10, 750, f"FINAL BOSS HP: {final_boss['hp']}/{final_boss['max_hp']}") 
        draw_text(10, 770, 
            f"Life: {player_life}  Score: {score}  " +
            f"Weapon: {current_weapon_name}  " +
            f"Ammo: {ammo[weapons[current_weapon]]}  " +
            f"Time: {time_of_day}")
        
        if game_state == "PAUSED":
            draw_text(400, 400, "PAUSED (H to resume, P to menu)")

        glutSwapBuffers()

# ====== Camera System ======

def setupCamera():
       glMatrixMode(GL_PROJECTION)
       glLoadIdentity()
    
       width, height = glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT)
       aspect_ratio = float(width) / float(height)
       gluPerspective(fovY, aspect_ratio, 0.1, 3000)  
       glMatrixMode(GL_MODELVIEW)
       glLoadIdentity()
    
       if first_person:
              dx, dy = angle_to_vec(player_angle)
              eye_x = player_pos[0] + dx * 20 
              eye_y = player_pos[1] + dy * 20
              eye_z = 85  
              gluLookAt(eye_x, eye_y, eye_z,
                     eye_x + dx * 50, 
                     eye_y + dy * 50,
                     eye_z - 10,  
                     0, 0, 1)
    
       else:
              gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
                     0, 0, 0,
                     0, 0, 1)
              
def spawn_final_boss(level):
    global final_boss, ENEMY_SPEED, boss_attack_cooldown, boss_attack_state, boss_attack_duration
    boss_health = DIFFICULTY_SETTINGS[difficulty]["boss_health"]
    attack_rate = DIFFICULTY_SETTINGS[difficulty]["boss_attack_rate"]
    base_health = boss_health * (1 + (level * 0.5))
    final_boss = {
        'pos': [0, 800, 0],  
        'size': 60 + (level * 30),  
        'hp': 100 + (level * 50),    
        'max_hp': base_health,
        'osc': random.uniform(0, 2 * math.pi),
        'walk_cycle': 0,
        'powers': ['laser_beam'],
        'speed': ENEMY_SPEED + (level * 0.2),
        'attack_rate': attack_rate  
    }
    boss_attack_cooldown = 0  
    boss_attack_state = None
    boss_attack_duration = 0
    print(f"Final boss spawned: HP={final_boss['hp']}, Attack Rate={attack_rate}")

def teleport_boss():
    global final_boss
    if not final_boss:
        return

    while True:
        new_x = random.uniform(-1500, 1500)
        new_y = random.uniform(-1500, 1500)

        if not is_colliding([new_x, new_y, final_boss['pos'][2]]):
            final_boss['pos'][0] = new_x
            final_boss['pos'][1] = new_y
            print(f"Boss teleported to: {final_boss['pos']}")
            break

def is_player_hit_by_laser(player_pos, laser_start, laser_end, beam_radius):
    
    laser_vec = [laser_end[i] - laser_start[i] for i in range(3)]
  
    player_vec = [player_pos[i] - laser_start[i] for i in range(3)]
    
    laser_length_sq = sum([laser_vec[i] ** 2 for i in range(3)])
    if laser_length_sq == 0:
        return False 
    t = sum([player_vec[i] * laser_vec[i] for i in range(3)]) / laser_length_sq
    if t < 0 or t > 1:
        return False  
    closest_point = [laser_start[i] + t * laser_vec[i] for i in range(3)]
    distance_to_laser = distance3D(player_pos, closest_point)
    return distance_to_laser <= beam_radius


def update_final_boss():
    global final_boss, player_pos, player_life, score, game_state, final_boss_active, laser_target,boss_score_threshhold
    global boss_attack_cooldown, boss_attack_state, boss_attack_duration

    if not final_boss_active or not final_boss :
        return

    final_boss['osc'] += 0.05
    z_offset = math.sin(final_boss['osc']) * 5
    final_boss['pos'][2] = z_offset 
    if difficulty == "MEDIUM" and random.random() < 0.005:  # 0.5% chance per frame
        lava.append((
            random.uniform(-1500, 1500),
            random.uniform(-1500, 1500),
            0, 100, 100, 50, True
        ))
        # Teleport boss and spawn lava in hard difficulty
    if difficulty == "HARD":
        if random.random() < 0.01:  # 1% chance per frame
            teleport_boss()
        if random.random() < 0.01:  # 1% chance per frame
            lava.append((
                random.uniform(-1500, 1500),
                random.uniform(-1500, 1500),
                0, 100, 100, 50, True
            ))

    
    if boss_attack_state == 'laser_beam':
        boss_attack_duration -= 1

        # On the first frame of the laser attack, set a random target
        if boss_attack_duration == 59:  # Just before the laser starts
             # Calculate direction vector from boss to player
            dx = player_pos[0] - final_boss['pos'][0]
            dy = player_pos[1] - final_boss['pos'][1]
            dist = math.hypot(dx, dy) or 1

            # Normalize the direction vector
            direction_x = dx / dist
            direction_y = dy / dist

            # Add randomness to the laser target within a cone in front of the player
            random_offset_x = random.uniform(-400, 400)  # Random offset for x-axis
            random_offset_y = random.uniform(-400, 400)  # Random offset for y-axis
            
            laser_target = [
                final_boss['pos'][0] + direction_x * 800 + random_offset_x,
                final_boss['pos'][1] + direction_y * 800 + random_offset_y,
                final_boss['pos'][2]
            ]
            print(f"Boss firing laser at random target: {laser_target}")


        if boss_attack_duration % 5 == 0 and laser_target:
            laser_start = final_boss['pos']
            laser_end = laser_target
            beam_radius = 5  # Adjust the beam radius as needed

            if not player_invincible and is_player_hit_by_laser(player_pos, laser_start, laser_end, beam_radius):
                player_life -= 1
                print(f"Player hit by laser beam! Player position: {player_pos}, Laser start: {laser_start}, Laser end: {laser_end}")
                if player_life <= 0:
                    game_state = "GAME_OVER"
    
        # Reset attack state when finished
        if boss_attack_duration <= 0:
            boss_attack_state = None
            laser_target = None

    else:
        # Boss movement towards the player when not attacking
        dx = player_pos[0] - final_boss['pos'][0]
        dy = player_pos[1] - final_boss['pos'][1]
        dist = math.hypot(dx, dy) or 1

        # Move closer to the player
        nx = dx / dist * final_boss['speed']
        ny = dy / dist * final_boss['speed']

        # Update boss position with boundary checks
        new_x = final_boss['pos'][0] + nx
        new_y = final_boss['pos'][1] + ny

        if abs(new_x) < GRID_LENGTH - 200:
            final_boss['pos'][0] = new_x
        if abs(new_y) < GRID_LENGTH - 200:
            final_boss['pos'][1] = new_y

        # Decide when to shoot laser based on cooldown
        boss_attack_cooldown -= 1
        if boss_attack_cooldown <= 0:
            boss_attack_state = 'laser_beam'
            boss_attack_duration = 60  # Laser beam duration

            # Faster attacks on higher difficulties
            cooldown_base = 120  # Base cooldown in frames
            cooldown_modifier = DIFFICULTY_SETTINGS[difficulty]["boss_attack_rate"]
            boss_attack_cooldown = int(cooldown_base / cooldown_modifier)

            print(f"Boss charging laser beam! Next attack in {boss_attack_cooldown} frames")

    # Check collision with the player
    if not player_invincible and distance3D(player_pos, final_boss['pos']) < final_boss['size']:
        player_life = 0
        print(f"Player hit by boss! Remaining life: {player_life}")

        # Knockback from collision
        dx = player_pos[0] - final_boss['pos'][0]
        dy = player_pos[1] - final_boss['pos'][1]
        dist = math.hypot(dx, dy) or 1

        player_pos[0] += (dx / dist) * 50
        player_pos[1] += (dy / dist) * 50

        if player_life <= 0:
            game_state = "GAME_OVER"

    # Check if boss is defeated
    if final_boss['hp'] <= 0:
        game_state = "WIN"

# ====== Entry Point ======
def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1200, 900)
    glutCreateWindow(b"Ultimate Zombie Shooter")
    glEnable(GL_DEPTH_TEST)
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(update)
    
    glutMainLoop()

if __name__ == "__main__":
    main()