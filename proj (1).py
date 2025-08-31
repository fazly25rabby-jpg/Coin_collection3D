from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import sys, math, random, time


# ---------------------- Utility ----------------------
class Vec3:
    __slots__ = ("x", "y", "z")
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x, self.y, self.z = float(x), float(y), float(z)
    def __add__(self, o): return Vec3(self.x + o.x, self.y + o.y, self.z + o.z)
    def __sub__(self, o): return Vec3(self.x - o.x, self.y - o.y, self.z - o.z)
    def __mul__(self, s): return Vec3(self.x * s, self.y * s, self.z * s)
    def dot(self, o): return self.x*o.x + self.y*o.y + self.z*o.z
    def length(self): return math.sqrt(self.dot(self))
    def normalized(self):
        l = self.length()
        return Vec3(self.x / l, self.y / l, self.z / l) if l > 1e-6 else Vec3()


def forward_from_yaw(yaw_deg: float) -> Vec3:
    r = math.radians(yaw_deg)
    # +Z is forward to screen; we want forward along -Z by default
    return Vec3(math.sin(r), 0.0, -math.cos(r))


def sphere_hit(a_pos: Vec3, a_r: float, b_pos: Vec3, b_r: float) -> bool:
    d = a_pos - b_pos
    return d.x*d.x + d.y*d.y + d.z*d.z <= (a_r + b_r) ** 2


# ---------------------- Config ----------------------
ARENA_HALF = 60.0      # half-size of playable square area on X/Z
WALL_H = 6.0           # wall height
FOV = 60.0
ASPECT = 1200/800
NEAR, FAR = 0.1, 600.0

PLAYER_SPEED = 25.0
PLAYER_RADIUS = 1.0
PLAYER_EYE = 1.4

BULLET_SPEED = 65.0
BULLET_TTL = 2.5
BULLET_RADIUS = 0.25

ENEMY_BASE_SPEED = (8.0, 12.0)
ENEMY_RADIUS = 1.4
ENEMY_DETECT = 22.0
ENEMY_TOUCH_DMG = 15

COIN_RADIUS = 1.0
COIN_PULL_SPEED = 10.0
MAGNET_RANGE = 12.0

# ---------------------- Entities ----------------------
class Bullet:
    __slots__ = ("pos", "dir", "speed", "radius", "ttl", "alive")
    def __init__(self, pos: Vec3, direction: Vec3):
        self.pos = Vec3(pos.x, pos.y, pos.z)
        self.dir = direction.normalized()
        self.speed = BULLET_SPEED
        self.radius = BULLET_RADIUS
        self.ttl = BULLET_TTL
        self.alive = True


class Coin:
    __slots__ = ("pos", "radius", "taken")
    def __init__(self, pos: Vec3):
        self.pos = pos
        self.radius = COIN_RADIUS
        self.taken = False


class Enemy:
    __slots__ = ("pos", "speed", "radius", "vel", "patrol_timer", "alive")
    def __init__(self, pos: Vec3):
        self.pos = pos
        self.speed = random.uniform(*ENEMY_BASE_SPEED)
        self.radius = ENEMY_RADIUS
        self.vel = Vec3()
        self.patrol_timer = 0.0
        self.alive = True


class Player:
    __slots__ = ("pos", "yaw", "speed", "radius", "health", "lives", "cheat")
    def __init__(self):
        self.pos = Vec3(0.0, 1.2, 0.0)
        self.yaw = 0.0
        self.speed = PLAYER_SPEED
        self.radius = PLAYER_RADIUS
        self.health = 100
        self.lives = 3
        self.cheat = False


# ---------------------- Game State ----------------------
player = Player()
bullets: list[Bullet] = []
coins: list[Coin] = []
enemies: list[Enemy] = []

score = 0
level_num = 1
paused = False
magnet_active = False
keys: set[bytes] = set()

last_time = time.time()
cam_nudge = Vec3(0.0, 0.0, 0.0)  # small camera nudge from arrow keys


# ---------------------- Spawning ----------------------
def random_inside_pos(margin: float = 5.0) -> Vec3:
    return Vec3(
        random.uniform(-ARENA_HALF + margin, ARENA_HALF - margin),
        0.0,
        random.uniform(-ARENA_HALF + margin, ARENA_HALF - margin),
    )


def random_perimeter_pos() -> Vec3:
    # Choose a side: 0: +X edge, 1: -X, 2: +Z, 3: -Z
    side = random.randint(0, 3)
    if side == 0:
        return Vec3(ARENA_HALF - 1.0, 0.0, random.uniform(-ARENA_HALF + 2.0, ARENA_HALF - 2.0))
    if side == 1:
        return Vec3(-ARENA_HALF + 1.0, 0.0, random.uniform(-ARENA_HALF + 2.0, ARENA_HALF - 2.0))
    if side == 2:
        return Vec3(random.uniform(-ARENA_HALF + 2.0, ARENA_HALF - 2.0), 0.0, ARENA_HALF - 1.0)
    return Vec3(random.uniform(-ARENA_HALF + 2.0, ARENA_HALF - 2.0), 0.0, -ARENA_HALF + 1.0)


def spawn_coins(n: int):
    for _ in range(n):
        coins.append(Coin(random_inside_pos(margin=6.0)))


def spawn_enemies(n: int):
    for _ in range(n):
        enemies.append(Enemy(random_perimeter_pos()))


def reset_level(lvl: int):
    global bullets, coins, enemies
    bullets, coins, enemies = [], [], []
    player.pos, player.health = Vec3(0.0, 1.2, 0.0), 100
    coin_count = min(10 + lvl * 2, 50)
    enemy_count = min(3 + lvl * 2, 40)
    spawn_coins(coin_count)
    spawn_enemies(enemy_count)


def reset_game():
    global score, level_num, paused, magnet_active
    score = 0
    level_num = 1
    paused = False
    magnet_active = False
    player.lives = 3
    player.cheat = False
    player.yaw = 0.0
    reset_level(level_num)


# ---------------------- Rendering ----------------------

def draw_ground_and_walls():
    # Ground
    glColor3f(0.20, 0.50, 0.20)
    glBegin(GL_QUADS)
    glVertex3f(-ARENA_HALF, 0.0, -ARENA_HALF)
    glVertex3f( ARENA_HALF, 0.0, -ARENA_HALF)
    glVertex3f( ARENA_HALF, 0.0,  ARENA_HALF)
    glVertex3f(-ARENA_HALF, 0.0,  ARENA_HALF)
    glEnd()

    # Walls around the arena (low cubes forming borders)
    glColor3f(0.35, 0.35, 0.38)
    glPushMatrix()
    glTranslatef(0.0, WALL_H * 0.5, -ARENA_HALF)
    glScalef(ARENA_HALF * 2.0, WALL_H, 1.0)
    glutSolidCube(1.0)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0.0, WALL_H * 0.5, ARENA_HALF)
    glScalef(ARENA_HALF * 2.0, WALL_H, 1.0)
    glutSolidCube(1.0)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-ARENA_HALF, WALL_H * 0.5, 0.0)
    glScalef(1.0, WALL_H, ARENA_HALF * 2.0)
    glutSolidCube(1.0)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(ARENA_HALF, WALL_H * 0.5, 0.0)
    glScalef(1.0, WALL_H, ARENA_HALF * 2.0)
    glutSolidCube(1.0)
    glPopMatrix()

def draw_player():
    glPushMatrix()
    glTranslatef(player.pos.x, player.pos.y, player.pos.z)
    glRotatef(player.yaw, 0, 1, 0)  # rotate entire player

    # ---------------- Body ----------------
    glPushMatrix()
    glColor3f(0.0, 0.0, 0.5)  # deep blue body
    glScalef(1.0, 1.5, 0.5)
    glutSolidCube(2.0)
    glPopMatrix()

    # ---------------- Head ----------------
    glPushMatrix()
    glTranslatef(0.0, 2.0, 0.0)
    glColor3f(0.0, 0.0, 0.0)  # black head
    glutSolidSphere(0.6, 20, 20)
    glPopMatrix()

    # ---------------- Hands (behind body) ----------------
    glColor3f(0.82, 0.7, 0.55)  # light brown
    # Left hand
    glPushMatrix()
    glTranslatef(-0.5, 0.5, -0.9)  # behind the body
    glRotatef(-30, 1, 0, 0)
    glScalef(0.4, 1.2, 0.4)
    glutSolidCone(0.4, 1.2, 12, 12)
    glPopMatrix()
    # Right hand
    glPushMatrix()
    glTranslatef(0.5, 0.5, -0.9)  # behind the body
    glRotatef(-30, 1, 0, 0)
    glScalef(0.4, 1.2, 0.4)
    glutSolidCone(0.4, 1.2, 12, 12)
    glPopMatrix()

    # ---------------- Legs ----------------
    glColor3f(0.82, 0.7, 0.55)
    glPushMatrix()
    glTranslatef(-0.5, -1.0, 0.0)
    glScalef(0.4, 1.5, 0.4)
    glutSolidCube(1.0)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.5, -1.0, 0.0)
    glScalef(0.4, 1.5, 0.4)
    glutSolidCube(1.0)
    glPopMatrix()

    # ---------------- Pistol (between hands) ----------------
    glPushMatrix()
    glTranslatef(0.0, 0.5, -1.2)  # behind, between hands
    glColor3f(0.0, 0.0, 0.0)      # black pistol
    glRotatef(-30, 1, 0, 0)
    glScalef(0.3, 0.8, 0.3)
    glutSolidCone(0.3, 1.0, 12, 12)
    glPopMatrix()

    glPopMatrix()  # end player



def draw_enemy(e: Enemy):
    glPushMatrix()
    glTranslatef(e.pos.x, e.pos.y, e.pos.z)
    
    # Enemy body (sphere)
    glColor3f(0.9, 0.2, 0.2)
    glutSolidSphere(1.0, 20, 20)  # radius 1.0, 20 slices, 20 stacks
    
    # Enemy head (small black cube on top)
    glPushMatrix()
    glTranslatef(0.0, 1.2, 0.0)  # position above body (radius + half cube height)
    glColor3f(0.0, 0.0, 0.0)
    glutSolidCube(0.6)           # small head cube
    glPopMatrix()
    
    glPopMatrix()



def draw_coin(c: Coin):
    glPushMatrix()
    glTranslatef(c.pos.x, c.pos.y + 0.5, c.pos.z)
    glColor3f(1.0, 0.84, 0.0)
    glutSolidTorus(0.2, 0.8, 16, 24)
    glPopMatrix()


def draw_bullet(b: Bullet):
    glPushMatrix()
    glTranslatef(b.pos.x, b.pos.y, b.pos.z)
    glColor3f(0.95, 0.95, 0.95)
    glutSolidSphere(b.radius, 12, 12)
    glPopMatrix()


def draw_text_hud():
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, 100, 0, 100)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity(); glDisable(GL_DEPTH_TEST)

    def write(x, y, s):
        glRasterPos2f(x, y)
        for ch in s:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    glColor3f(1, 1, 1)
    write(2, 96, f"Score: {score}   Level: {level_num}")
    write(2, 90, f"Health: {player.health}   Lives: {player.lives}{'  [CHEAT]' if player.cheat else ''}")
    write(2, 84, f"Magnet: {'ON' if magnet_active else 'OFF'}")
    if paused:
        write(44, 50, "PAUSED")

    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_MODELVIEW); glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix()


# ---------------------- Update ----------------------

def clamp_to_arena(p: Vec3, r: float) -> Vec3:
    return Vec3(
        max(-ARENA_HALF + r, min(ARENA_HALF - r, p.x)),
        p.y,
        max(-ARENA_HALF + r, min(ARENA_HALF - r, p.z)),
    )


def update():
    global last_time, level_num, score
    now = time.time()
    dt = max(0.0, min(0.05, now - last_time))  # clamp dt for stability
    last_time = now

    if paused:
        glutPostRedisplay()
        return

    # Player movement (WASD relative to yaw)
    move_z = 0.0
    move_x = 0.0
    if b'w' in keys: move_z -= 1.0
    if b's' in keys: move_z += 1.0
    if b'a' in keys: move_x -= 1.0
    if b'd' in keys: move_x += 1.0

    fwd = forward_from_yaw(player.yaw)
    right = Vec3(fwd.z, 0.0, -fwd.x)
    vel = fwd * move_z + right * move_x
    if vel.length() > 0.0:
        player.pos = player.pos + vel.normalized() * player.speed * dt
        player.pos = clamp_to_arena(player.pos, player.radius)

    # Bullets
    for b in bullets:
        if b.alive:
            b.pos = b.pos + b.dir * (b.speed * dt)
            b.ttl -= dt
            if b.ttl <= 0.0:
                b.alive = False
            # Remove bullets that hit walls
            if abs(b.pos.x) > ARENA_HALF - 0.5 or abs(b.pos.z) > ARENA_HALF - 0.5:
                b.alive = False
    # Bullet vs enemy
    for b in bullets:
        if not b.alive: continue
        for e in enemies:
            if e.alive and sphere_hit(b.pos, b.radius, e.pos, e.radius):
                e.alive = False
                b.alive = False
                score += 20
    bullets[:] = [b for b in bullets if b.alive]

    # Enemies
    for e in enemies:
        if not e.alive: continue
        # Simple seek if close, else wander
        to_player = player.pos - e.pos
        d = to_player.length()
        if d < ENEMY_DETECT:
            dirv = to_player.normalized()
            e.vel = dirv * e.speed
        else:
            e.patrol_timer -= dt
            if e.patrol_timer <= 0.0:
                rnd = Vec3(random.uniform(-1, 1), 0.0, random.uniform(-1, 1)).normalized()
                e.vel = rnd * e.speed * 0.6
                e.patrol_timer = random.uniform(1.0, 2.5)
        e.pos = e.pos + e.vel * dt
        # Bounce off walls
        if e.pos.x > ARENA_HALF - e.radius: e.pos.x = ARENA_HALF - e.radius; e.vel.x *= -1
        if e.pos.x < -ARENA_HALF + e.radius: e.pos.x = -ARENA_HALF + e.radius; e.vel.x *= -1
        if e.pos.z > ARENA_HALF - e.radius: e.pos.z = ARENA_HALF - e.radius; e.vel.z *= -1
        if e.pos.z < -ARENA_HALF + e.radius: e.pos.z = -ARENA_HALF + e.radius; e.vel.z *= -1
        # Contact damage
        if sphere_hit(e.pos, e.radius, player.pos, player.radius):
            if not player.cheat:
                player.health -= ENEMY_TOUCH_DMG
                # small knockback
                kb = (player.pos - e.pos).normalized()
                player.pos = clamp_to_arena(player.pos + kb * 0.6, player.radius)
                if player.health <= 0:
                    player.lives -= 1
                    player.health = 100
                    player.pos = Vec3(0.0, 1.2, 0.0)
                    if player.lives < 0:
                        reset_game()

    # Coins
    all_taken = True
    for c in coins:
        if c.taken:
            continue
        all_taken = False
        # Pickup
        if sphere_hit(player.pos, player.radius, c.pos, c.radius):
            c.taken = True
            score += 10
        # Magnet attraction
        elif magnet_active:
            to_player = player.pos - c.pos
            d = to_player.length()
            if d < MAGNET_RANGE and d > 1e-4:
                pull = to_player * (1.0 / d)
                c.pos = c.pos + pull * (COIN_PULL_SPEED * dt)

    # Level complete
    if all_taken:
        level_num += 1
        reset_level(level_num)

    glutPostRedisplay()


# ---------------------- GLUT & Input ----------------------

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Camera behind and above player; allow tiny arrow-key nudge
    glMatrixMode(GL_PROJECTION); glLoadIdentity(); gluPerspective(FOV, ASPECT, NEAR, FAR)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()

    cam_fwd = forward_from_yaw(player.yaw)
    cam_pos = Vec3(player.pos.x, 0.0, player.pos.z) - cam_fwd * 55.0 + Vec3(0.0, 35.0, 0.0) + cam_nudge
    gluLookAt(cam_pos.x, cam_pos.y, cam_pos.z,
              player.pos.x, 0.0, player.pos.z,
              0.0, 1.0, 0.0)

    draw_ground_and_walls()
    draw_player()
    for e in enemies:
        if e.alive: draw_enemy(e)
    for c in coins:
        if not c.taken: draw_coin(c)
    for b in bullets:
        draw_bullet(b)

    draw_text_hud()

    glutSwapBuffers()


def keyboard(key, x, y):
    global magnet_active, paused
    keys.add(key)
    if key in (b'q', b'Q'): player.yaw -= 5.0
    elif key in (b'e', b'E'): player.yaw += 5.0
    elif key in (b'm', b'M'): magnet_active = not magnet_active
    elif key in (b'c', b'C'): player.cheat = not player.cheat
    elif key in (b'p', b'P'): paused = not paused
    elif key in (b'r', b'R'): reset_game()
    elif key == b'\x1b': sys.exit(0)


def keyboard_up(key, x, y):
    if key in keys:
        keys.remove(key)


def special_keys(key, x, y):
    # Small camera nudge with arrow keys (inspired by a.py)
    n = 1.0
    if key == GLUT_KEY_UP:    cam_nudge.z -= n
    elif key == GLUT_KEY_DOWN:  cam_nudge.z += n
    elif key == GLUT_KEY_LEFT:  cam_nudge.x -= n
    elif key == GLUT_KEY_RIGHT: cam_nudge.x += n


def mouse(button, state, x, y):
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # Calculate forward direction from player yaw
        dirv = forward_from_yaw(player.yaw).normalized()
        
        # Position at the tip of the pistol (between the hands)
        muzzle = Vec3(player.pos.x, player.pos.y + 0.5, player.pos.z) + dirv * 1.3  # in front of body
        bullets.append(Bullet(muzzle, dirv))



# ---------------------- Main ----------------------

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1200, 800)
    glutCreateWindow(b"CSE423 Final - Coin Frenzy 3D")

    reset_game()

    glEnable(GL_DEPTH_TEST)
    glClearColor(0.05, 0.06, 0.07, 1.0)

    glutDisplayFunc(display)
    glutIdleFunc(update)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(special_keys)
    glutMouseFunc(mouse)

    glutMainLoop()


if __name__ == "__main__":
    main()
