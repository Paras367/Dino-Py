#!/usr/bin/env python3
"""
DINO RUN - Chrome Dino, Python (pygame) edition.

Folder structure :
    dino_game.py
    Assets/Dino/   DinoStart, DinoRun1/2, DinoJump, DinoDuck1/2, (DinoDead optional)
    Assets/Cactus/ SmallCactus1/2/3, LargeCactus1/2/3
    Assets/Bird/   Bird1/2
    Assets/Other/  Cloud, Track



Controls
    SPACE / UP / W   jump (hold = high jump, tap = short hop)
    DOWN / S         duck 
    P / ESC          pause
    M                mute
    F / F11          fullscreen

MADE WITH <3 BY PARAS367
Copyright (c) 2026 PARAS367. All rights reserved.
"""


# Quick note: This code is a Python implementation of the Chrome Dino game using the Pygame library. It includes classes for the game elements such as the dinosaur, obstacles, ground, clouds, and the main game loop. The game features jumping, ducking, scoring, and night mode transitions. The assets are loaded from an "Assets" directory, and sound effects are generated programmatically.
# License: This code is provided as-is for educational purposes. You may modify and distribute it, but please give credit to the original author (PARAS367) if you use it in your projects.
# If you have any questions or need further assistance, feel free to reach out to the author.


import array
import asyncio
import math
import os
import random
import sys

import pygame


SCREEN_W, SCREEN_H = 1100, 600
FPS = 60

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "Assets")
HI_FILE = os.path.join(BASE_DIR, "highscore.txt")

TRACK_Y = 380       
DINO_FOOT = 404      
CACTUS_FOOT = 399   

START_SPEED = 420.0 
MAX_SPEED = 1050.0
ACCEL = 6.0         
SCORE_RATE = 0.025  

GRAVITY = 2900.0
JUMP_V = 950.0
CUT_V = 560.0       
FAST_FALL = 3.2

INK = (83, 83, 83)
NIGHT_INK = (190, 190, 190)
DAY_BG = (255, 255, 255)
NIGHT_BG = (24, 24, 28)

JUMP_KEYS = (pygame.K_SPACE, pygame.K_UP, pygame.K_w)
DUCK_KEYS = (pygame.K_DOWN, pygame.K_s)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(lerp(x, y, t)) for x, y in zip(c1, c2))


def load_hi():
    try:
        with open(HI_FILE, "r") as f:
            return max(0, int(f.read().strip() or 0))
    except (OSError, ValueError):
        return 0


def save_hi(value):
    try:
        with open(HI_FILE, "w") as f:
            f.write(str(int(value)))
    except OSError:
        pass


def make_font(size, bold=True):
    try:
        return pygame.font.SysFont("couriernew,courier,consolas,dejavusansmono,monospace", size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size + 6)


def make_night(surf, tint):
    s = surf.copy()
    s.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
    s.fill((tint[0], tint[1], tint[2], 255), special_flags=pygame.BLEND_RGBA_MULT)
    return s


def make_mask(surf):
    w, h = surf.get_size()
    m = pygame.mask.from_surface(surf, 127)
    if m.count() == w * h:
        ix, iy = max(2, w // 10), max(2, h // 10)
        m = pygame.mask.Mask((w, h))
        m.draw(pygame.mask.Mask((w - 2 * ix, h - 2 * iy), fill=True), (ix, iy))
    return m


class Sprite:

    def __init__(self, surf, tint=NIGHT_INK):
        self.day = surf
        self.night = make_night(surf, tint)
        self.mask = make_mask(surf)
        self.w, self.h = surf.get_size()

    def get(self, night):
        return self.night if night else self.day



def _surf(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def fb_dino(kind="run", step=0):
    c = INK
    if kind == "duck":
        s = _surf(118, 60)
        pygame.draw.rect(s, c, (0, 14, 84, 32), border_radius=8)
        pygame.draw.rect(s, c, (70, 0, 46, 32), border_radius=6)
        s.fill((0, 0, 0, 0), (96, 8, 8, 8))
        for lx, down in ((20, step == 0), (50, step == 1)):
            ln = 14 if down else 8
            pygame.draw.rect(s, c, (lx, 44, 10, ln))
        return s
    s = _surf(88, 94)
    pygame.draw.rect(s, c, (40, 0, 48, 38), border_radius=8)
    pygame.draw.rect(s, c, (8, 34, 56, 44), border_radius=10)
    pygame.draw.rect(s, c, (36, 30, 28, 22))
    pygame.draw.polygon(s, c, [(12, 42), (0, 28), (0, 58)])
    pygame.draw.rect(s, c, (60, 58, 14, 6))
    s.fill((0, 0, 0, 0), (70, 10, 8, 8))
    if kind == "run":
        left, right = (18, 10) if step == 0 else (10, 18)
    else:
        left = right = 18
    pygame.draw.rect(s, c, (20, 76, 10, left))
    pygame.draw.rect(s, c, (42, 76, 10, right))
    return s


def fb_cactus(n, unit_w, h):
    s = _surf(unit_w * n, h)
    tw = max(8, unit_w // 3)
    arm_y = int(h * 0.35)
    for i in range(n):
        ox = i * unit_w
        tx = ox + (unit_w - tw) // 2
        pygame.draw.rect(s, INK, (tx, 0, tw, h), border_radius=tw // 2)
        # left arm
        pygame.draw.rect(s, INK, (ox + 2, arm_y, tx - (ox + 2) + 2, 8))
        pygame.draw.rect(s, INK, (ox + 2, arm_y - 18, 8, 26), border_radius=4)
        # right arm
        rx = tx + tw - 2
        pygame.draw.rect(s, INK, (rx, arm_y + 14, ox + unit_w - 2 - rx, 8))
        pygame.draw.rect(s, INK, (ox + unit_w - 10, arm_y - 4, 8, 26), border_radius=4)
    return s


def fb_bird(flap):
    s = _surf(92, 68)
    pygame.draw.ellipse(s, INK, (14, 28, 56, 24))
    pygame.draw.ellipse(s, INK, (4, 26, 26, 22))
    pygame.draw.polygon(s, INK, [(0, 36), (12, 31), (12, 41)])
    pygame.draw.polygon(s, INK, [(66, 36), (90, 30), (90, 46)])
    if flap == 0:
        pygame.draw.polygon(s, INK, [(30, 32), (58, 32), (50, 2)])
    else:
        pygame.draw.polygon(s, INK, [(30, 48), (58, 48), (50, 66)])
    s.fill((0, 0, 0, 0), (14, 32, 5, 5))
    return s


def fb_cloud():
    s = _surf(92, 27)
    col = (190, 190, 190)
    pygame.draw.ellipse(s, col, (0, 10, 40, 17))
    pygame.draw.ellipse(s, col, (22, 0, 46, 27))
    pygame.draw.ellipse(s, col, (52, 8, 40, 19))
    return s


def fb_track():
    s = _surf(2400, 34)
    pygame.draw.rect(s, INK, (0, 20, 2400, 2))
    rnd = random.Random(7)
    for _ in range(150):
        x = rnd.randrange(2400)
        y = rnd.randrange(26, 33)
        pygame.draw.rect(s, INK, (x, y, rnd.choice((2, 3, 4, 6, 8)), 2))
    return s


class Assets:
    def __init__(self):
        self.missing = []
        L = self._load
        self.start = Sprite(L(("Dino", "DinoStart.png"), lambda: fb_dino("stand")))
        self.run = [Sprite(L(("Dino", "DinoRun%d.png" % (i + 1)), lambda i=i: fb_dino("run", i))) for i in range(2)]
        self.jump = Sprite(L(("Dino", "DinoJump.png"), lambda: fb_dino("stand")))
        self.duck = [Sprite(L(("Dino", "DinoDuck%d.png" % (i + 1)), lambda i=i: fb_dino("duck", i))) for i in range(2)]
        self.dead = Sprite(L(("Dino", "DinoDead.png"), lambda: self.jump.day, quiet=True))
        self.small = [Sprite(L(("Cactus", "SmallCactus%d.png" % (i + 1)), lambda i=i: fb_cactus(i + 1, 34, 70)))
                      for i in range(3)]
        self.large = [Sprite(L(("Cactus", "LargeCactus%d.png" % (i + 1)), lambda i=i: fb_cactus(i + 1, 50, 100)))
                      for i in range(3)]
        self.bird = [Sprite(L(("Bird", "Bird%d.png" % (i + 1)), lambda i=i: fb_bird(i))) for i in range(2)]
        self.cloud = Sprite(L(("Other", "Cloud.png"), fb_cloud), tint=(80, 80, 88))
        self.track = Sprite(L(("Other", "Track.png"), fb_track), tint=(150, 150, 150))
        if self.missing:
            print("[Dino Run] %d asset nahi mile, built-in sprites use ho rahe hain." % len(self.missing))

    def _load(self, parts, fallback, quiet=False):
        path = os.path.join(ASSET_DIR, *parts)
        try:
            return pygame.image.load(path).convert_alpha()
        except (pygame.error, OSError):
            if not quiet:
                self.missing.append("/".join(parts))
            return fallback().convert_alpha()


class SoundBank:
    def __init__(self):
        self.enabled = False
        self.muted = False
        self.fx = {}
        try:
            pygame.mixer.quit()
            pygame.mixer.init(44100, -16, 1, 512)
            init = pygame.mixer.get_init()
            if not init or init[1] != -16:
                return
            self.fx["jump"] = self._tone([(420, 780, 0.13)])
            self.fx["die"] = self._tone([(400, 300, 0.12), (0, 0, 0.04), (260, 120, 0.30)])
            self.fx["milestone"] = self._tone([(880, 880, 0.08), (0, 0, 0.04), (1320, 1320, 0.12)])
            self.enabled = True
        except Exception:
            self.enabled = False

    @staticmethod
    def _tone(notes, vol=0.16):
        freq, _, ch = pygame.mixer.get_init()
        buf = array.array("h")
        for f0, f1, dur in notes:
            n = int(freq * dur)
            phase = 0.0
            fade = max(1, int(freq * 0.01))
            for i in range(n):
                f = f0 + (f1 - f0) * i / max(1, n - 1)
                phase += f / freq
                v = 0 if f <= 0 else (1 if (phase % 1.0) < 0.5 else -1)
                env = min(1.0, (n - i) / fade)
                sample = int(v * vol * 32767 * env)
                for _ in range(ch):
                    buf.append(sample)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def play(self, name):
        if self.enabled and not self.muted and name in self.fx:
            try:
                self.fx[name].play()
            except pygame.error:
                pass


class Dino:
    X = 80

    def __init__(self, assets):
        self.a = assets
        self.reset()

    def reset(self):
        self.h = 0.0         
        self.vy = 0.0
        self.on_ground = True
        self.ducking = False
        self.jump_held = False
        self.buffer = 0.0      
        self.anim = 0.0
        self.dead = False
        self.just_jumped = False

    def request_jump(self):
        self.jump_held = True
        self.buffer = 0.12

    def release_jump(self):
        self.jump_held = False

    def update(self, dt, duck_held, speed):
        self.just_jumped = False
        self.anim += dt * (1.0 + (speed - START_SPEED) / 1400.0)

        if self.on_ground and self.buffer > 0:
            self.vy = JUMP_V
            self.on_ground = False
            self.buffer = 0.0
            self.just_jumped = True
        self.buffer = max(0.0, self.buffer - dt)

        if not self.on_ground:
            if not self.jump_held and self.vy > CUT_V:
                self.vy = CUT_V                    
            g = GRAVITY * (FAST_FALL if duck_held else 1.0)
            self.vy -= g * dt
            self.h += self.vy * dt
            if self.h <= 0:
                self.h = 0.0
                self.vy = 0.0
                self.on_ground = True

        self.ducking = self.on_ground and duck_held

    def sprite(self):
        if self.dead:
            return self.a.dead
        if not self.on_ground:
            return self.a.jump
        i = int(self.anim / 0.09) % 2
        return self.a.duck[i] if self.ducking else self.a.run[i]

    def rect(self):
        s = self.sprite()
        return pygame.Rect(self.X, int(DINO_FOOT - self.h - s.h), s.w, s.h)

    def draw(self, scr, night, idle=False):
        if idle:
            s = self.a.start
            scr.blit(s.get(night), (self.X, DINO_FOOT - s.h))
        else:
            r = self.rect()
            scr.blit(self.sprite().get(night), r.topleft)


class Obstacle:
    def __init__(self, frames, foot):
        self.frames = frames
        self.foot = foot
        self.x = float(SCREEN_W + 10)
        self.t = 0.0
        self.w = frames[0].w

    def sprite(self):
        if len(self.frames) == 1:
            return self.frames[0]
        return self.frames[int(self.t / 0.14) % len(self.frames)]

    def rect(self):
        s = self.sprite()
        return pygame.Rect(int(self.x), int(self.foot - s.h), s.w, s.h)

    def update(self, dt, speed):
        self.x -= speed * dt
        self.t += dt

    def offscreen(self):
        return self.x + self.w < -10

    def draw(self, scr, night):
        r = self.rect()
        scr.blit(self.sprite().get(night), r.topleft)


def collides(dino, ob):
    dr, orr = dino.rect(), ob.rect()
    if not dr.colliderect(orr):
        return False
    offset = (orr.x - dr.x, orr.y - dr.y)
    return dino.sprite().mask.overlap(ob.sprite().mask, offset) is not None


class Ground:
    def __init__(self, sprite):
        self.s = sprite
        self.x = 0.0

    def update(self, dt, speed):
        self.x = (self.x + speed * dt) % self.s.w

    def draw(self, scr, night):
        img = self.s.get(night)
        x = -int(self.x)
        while x < SCREEN_W:
            scr.blit(img, (x, TRACK_Y))
            x += self.s.w


class Cloud:
    def __init__(self, sprite, x=None):
        self.s = sprite
        self.x = float(x if x is not None else SCREEN_W + random.randint(40, 400))
        self.y = random.randint(40, 170)

    def update(self, dt, speed):
        self.x -= (28 + speed * 0.12) * dt
        if self.x < -self.s.w:
            self.x = SCREEN_W + random.randint(60, 500)
            self.y = random.randint(40, 170)

    def draw(self, scr, night):
        scr.blit(self.s.get(night), (int(self.x), self.y))


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Dino Run - Chrome Dino in Python")
        try:
            self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.SCALED | pygame.RESIZABLE)
        except (pygame.error, AttributeError):
            self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.assets = Assets()
        self.sound = SoundBank()

        self.font_big = make_font(56)
        self.font = make_font(30)
        self.font_hud = make_font(28)
        self.font_small = make_font(20)

        self.hi = load_hi()
        self.ground = Ground(self.assets.track)
        self.dino = Dino(self.assets)
        self.clouds = [Cloud(self.assets.cloud, x) for x in (180, 560, 920)]
        self.stars = [(random.randint(0, SCREEN_W), random.randint(20, 270), random.random() * 6.28)
                      for _ in range(40)]

        self.t_total = 0.0
        self.state = "menu"         
        self.dead_timer = 0.0
        self.new_record = False
        self.reset_run()

    def reset_run(self):
        self.dino.reset()
        self.obstacles = []
        self.speed = START_SPEED
        self.score = 0.0
        self.run_time = 0.0
        self.next_gap = 0.0
        self.night_t = 0.0
        self.flash = 0.0
        self.flash_value = 0
        self.last_ms = 0
        self.history = []
        self.new_record = False

    def start_game(self, jump=False):
        self.reset_run()
        self.state = "play"
        if jump:
            self.dino.request_jump()

    def die(self):
        self.state = "dead"
        self.dino.dead = True
        self.dead_timer = 0.0
        self.sound.play("die")
        final = int(self.score)
        if final > self.hi:
            self.hi = final
            self.new_record = True
            save_hi(self.hi)

  
    def toggle_fullscreen(self):
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error:
            pass

    def quit(self):
        # In the browser, stop the game loop instead of exiting Python.
        self.running = False

    def handle_event(self, e):
        if e.type == pygame.QUIT:
            self.quit()

        if hasattr(pygame, "WINDOWFOCUSLOST") and e.type == pygame.WINDOWFOCUSLOST and self.state == "play":
            self.state = "pause"

        if e.type == pygame.KEYUP and e.key in JUMP_KEYS:
            self.dino.release_jump()
        if e.type == pygame.MOUSEBUTTONUP:
            self.dino.release_jump()

        pressed_jump = (e.type == pygame.KEYDOWN and e.key in JUMP_KEYS) or e.type == pygame.MOUSEBUTTONDOWN

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_m:
                self.sound.muted = not self.sound.muted
                return
            if e.key in (pygame.K_f, pygame.K_F11):
                self.toggle_fullscreen()
                return

        if self.state == "menu":
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.quit()
            if e.type == pygame.MOUSEBUTTONDOWN or (e.type == pygame.KEYDOWN and e.key != pygame.K_p):
                self.start_game(jump=pressed_jump)

        elif self.state == "play":
            if pressed_jump:
                self.dino.request_jump()
            elif e.type == pygame.KEYDOWN and e.key in (pygame.K_p, pygame.K_ESCAPE):
                self.state = "pause"

        elif self.state == "pause":
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_p, pygame.K_ESCAPE):
                self.state = "play"
            elif pressed_jump:
                self.state = "play"

        elif self.state == "dead":
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.quit()
            restart = pressed_jump or (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_r))
            if restart and self.dead_timer >= 0.45:
                self.start_game()

    # --------------------------------------------------------------- spawn
    def make_obstacle(self):
        a, s = self.assets, self.score
        kinds, weights = ["small", "large"], [50, 40]
        if s >= 250:
            kinds.append("bird")
            weights.append(25)

        if len(self.history) >= 2 and self.history[-1] == self.history[-2]:
            bad = self.history[-1]
            pairs = [(k, w) for k, w in zip(kinds, weights) if k != bad]
            kinds, weights = [p[0] for p in pairs], [p[1] for p in pairs]
        kind = random.choices(kinds, weights)[0]
        self.history.append(kind)
        self.history = self.history[-4:]

        if kind == "small":
            top = 0 if s < 100 else (1 if s < 300 else 2)
            ob = Obstacle([a.small[random.randint(0, top)]], CACTUS_FOOT)
        elif kind == "large":
            top = 0 if s < 200 else (1 if s < 700 else 2)
            ob = Obstacle([a.large[random.randint(0, top)]], CACTUS_FOOT)
        else:
            stand_h, duck_h = a.run[0].h, a.duck[0].h
            offset = random.choices([6, duck_h + 6, stand_h + 10], [35, 40, 25])[0]

            ob = Obstacle(a.bird, DINO_FOOT - offset)
        self.next_gap = ob.w * 0.6 + self.speed * random.uniform(0.78, 1.5)
        return ob

    def maybe_spawn(self):
        if self.run_time < 0.9:
            return
        if self.obstacles:
            last = self.obstacles[-1]
            if (SCREEN_W + 10) - (last.x + last.w) < self.next_gap:
                return
        self.obstacles.append(self.make_obstacle())


    def update(self, dt):
        self.t_total += dt

        if self.state == "menu":
            for c in self.clouds:
                c.update(dt, 0)
            return
        if self.state == "dead":
            self.dead_timer += dt
            return
        if self.state == "pause":
            return

        keys = pygame.key.get_pressed()
        duck = bool(keys[DUCK_KEYS[0]] or keys[DUCK_KEYS[1]])

        self.run_time += dt
        self.speed = min(MAX_SPEED, self.speed + ACCEL * dt)
        self.score += self.speed * dt * SCORE_RATE

        ms = int(self.score) // 100
        if ms > self.last_ms:
            self.last_ms = ms
            self.flash = 0.9
            self.flash_value = ms * 100
            self.sound.play("milestone")
        self.flash = max(0.0, self.flash - dt)


        phase = self.score % 1000
        target = 1.0 if 700 <= phase < 900 else 0.0
        step = dt / 1.2
        self.night_t += max(-step, min(step, target - self.night_t))

        self.dino.update(dt, duck, self.speed)
        if self.dino.just_jumped:
            self.sound.play("jump")

        self.ground.update(dt, self.speed)
        for c in self.clouds:
            c.update(dt, self.speed)

        self.maybe_spawn()
        for o in self.obstacles:
            o.update(dt, self.speed)
        self.obstacles = [o for o in self.obstacles if not o.offscreen()]

        for o in self.obstacles:
            if collides(self.dino, o):
                self.die()
                break

  
    def text(self, font, msg, color, **pos):
        surf = font.render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(**pos))
        return surf

    def draw_sky(self, bg):
        if self.night_t < 0.05:
            return
        for x, y, p in self.stars:
            b = 0.5 + 0.5 * math.sin(self.t_total * 2.2 + p)
            col = lerp_color(bg, (220, 220, 220), self.night_t * (0.35 + 0.65 * b))
            self.screen.fill(col, (x, y, 2, 2))
        cx, cy = SCREEN_W - 210, 95
        pygame.draw.circle(self.screen, lerp_color(bg, (225, 225, 225), self.night_t), (cx, cy), 24)
        pygame.draw.circle(self.screen, bg, (cx + 11, cy - 5), 21)

    def draw_hud(self, ink, bg):
        right = SCREEN_W - 30
        score_w = self.font_hud.size("00000")[0]
        if self.state != "menu":
            value = int(self.score)
            visible = True
            if self.flash > 0:
                value = self.flash_value
                visible = int(self.flash / 0.14) % 2 == 0
            if visible:
                self.text(self.font_hud, "%05d" % value, ink, topright=(right, 24))
        if self.hi > 0:
            self.text(self.font_hud, "HI %05d" % self.hi, lerp_color(ink, bg, 0.4),
                      topright=(right - score_w - 26, 24))
        if self.sound.muted:
            self.text(self.font_small, "MUTE", lerp_color(ink, bg, 0.4), topleft=(30, 28))

    def draw_restart_icon(self, color, cx, cy, r=24):
        rect = pygame.Rect(cx - r, cy - r, 2 * r, 2 * r)
        theta = 6.0
        pygame.draw.arc(self.screen, color, rect, 0.9, theta, 5)
        px, py = cx + r * math.cos(theta), cy - r * math.sin(theta)
        tx, ty = -math.sin(theta), -math.cos(theta)    # tangent
        nx, ny = math.cos(theta), -math.sin(theta)     # outward normal
        pygame.draw.polygon(self.screen, color, [
            (px + tx * 13, py + ty * 13),
            (px + nx * 9, py + ny * 9),
            (px - nx * 9, py - ny * 9),
        ])

    def draw(self):
        night = self.night_t > 0.5
        bg = lerp_color(DAY_BG, NIGHT_BG, self.night_t)
        ink = lerp_color(INK, NIGHT_INK, self.night_t)
        faded = lerp_color(ink, bg, 0.35)
        scr = self.screen
        cx = SCREEN_W // 2

        scr.fill(bg)
        self.draw_sky(bg)
        for c in self.clouds:
            c.draw(scr, night)
        self.ground.draw(scr, night)
        for o in self.obstacles:
            o.draw(scr, night)
        self.dino.draw(scr, night, idle=(self.state == "menu"))
        self.draw_hud(ink, bg)

        if self.state == "menu":
            self.text(self.font_big, "DINO RUN", ink, center=(cx, 130))
            self.text(self.font_small, "Chrome Dino | Python Edition", faded, center=(cx, 176))
            self.text(self.font, "Press any key to Start", ink, center=(cx, 240))
            self.text(self.font_small, "Ok, Lets Start!", faded, center=(cx, 274))
            self.text(self.font_small,
                      "SPACE/UP jump   DOWN duck   P pause   M mute   F fullscreen",
                      faded, center=(cx, SCREEN_H - 40))

        elif self.state == "pause":
            self.text(self.font_big, "PAUSED", ink, center=(cx, 190))
            self.text(self.font_small, "P ya ESC dabao, wapas khelo", faded, center=(cx, 240))

        elif self.state == "dead":
            if self.new_record:
                self.text(self.font_small, "** NEW RECORD! **", ink, center=(cx, 130))
            self.text(self.font_big, "GAME OVER", ink, center=(cx, 180))
            self.draw_restart_icon(ink, cx, 250)
            self.text(self.font_small, "Score %d   |   Best %d" % (int(self.score), self.hi),
                      faded, center=(cx, 300))
            if self.dead_timer >= 0.45:
                self.text(self.font_small, "Play Again? Press SPACE", ink, center=(cx, 330))

  
    async def run(self):
        # Pygbag requires the loop to yield so the browser can process frames/input.
        self.running = True
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.quit()
                    break
                self.handle_event(e)
                if not self.running:
                    break

            if not self.running:
                break

            self.update(dt)
            self.draw()
            pygame.display.flip()
            await asyncio.sleep(0)


async def main():
    game = Game()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())



#Dino Run - Chrome Dino, Python (pygame) edition.
#BY - PARAS367


#__EOF__