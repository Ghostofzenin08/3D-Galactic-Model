import math
import os
import random
import sys

import pygame


try:
    import pygame.gfxdraw as gfxdraw
    HAVE_GFXDRAW = True
except ImportError:
    HAVE_GFXDRAW = False



WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
TARGET_FPS = 60

STAR_COUNT = 5500

BULGE_RATIO = 0.10
DISK_RATIO = 0.28


BULGE_RADIUS = 65
NUM_ARMS = 2                 
ARM_PITCH_DEG = 14            
ARM_WIDTH = 24                
GALAXY_RADIUS = 460            
DISK_SCALE_LENGTH = 150         
DISK_THICKNESS = 18


FOV = 560
CAMERA_DISTANCE = 1000
AUTO_ROTATE_SPEED = 0.04


BG_TOP_COLOR = (6, 8, 20)
BG_BOTTOM_COLOR = (0, 0, 2)
BACKGROUND_STAR_COUNT = 350

def clamp(value, lo, hi):
    return max(lo, min(hi, value))



def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    t = clamp(t, 0.0, 1.0)
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))



def temperature_to_color(temperature):
    """Black-body-ish mapping from a temperature (K) to an RGB color."""
    t = temperature / 100.0

    if t <= 66:
        r = 255
    else:
        r = 329.698727446 * ((t - 60) ** -0.1332047592)
    r = clamp(r, 0, 255)

    if t <= 66:
        g = 99.4708025861 * math.log(max(t, 1)) - 161.1195681661
    else:
        g = 288.1221695283 * ((t - 60) ** -0.0755148492)
    g = clamp(g, 0, 255)

    if t >= 66:
        b = 255
    elif t <= 19:
        b = 0
    else:
        b = 138.5177312231 * math.log(max(t - 10, 1)) - 305.0447927307
    b = clamp(b, 0, 255)

    return int(r), int(g), int(b)


def sample_exponential_radius(scale_length, max_radius):
    
    cutoff = 1.0 - math.exp(-max_radius / scale_length)
    u = random.random() * cutoff
    r = -scale_length * math.log(1.0 - u)
    return min(r, max_radius)



class Star:
    __slots__ = (
        "x", "y", "z", "radius", "brightness", "base_brightness",
        "temperature", "color", "twinkle_offset", "orbit_radius",
        "orbit_angle", "orbit_speed", "glow",
    )

    def __init__(self, x, y, z, radius, brightness, temperature, glow):
        self.x = x
        self.y = y
        self.z = z

        self.orbit_radius = math.hypot(x, z)
        self.orbit_angle = math.atan2(z, x)

        self.orbit_speed = 0.35 / (0.6 + self.orbit_radius / 120.0)

        self.radius = radius
        self.brightness = brightness
        self.base_brightness = brightness
        self.temperature = temperature
        self.color = temperature_to_color(temperature)
        self.twinkle_offset = random.uniform(0, math.tau)
        self.glow = glow

    def advance_orbit(self, delta_time):
        self.orbit_angle += self.orbit_speed * delta_time
        self.x = math.cos(self.orbit_angle) * self.orbit_radius
        self.z = math.sin(self.orbit_angle) * self.orbit_radius

    def update_twinkle(self, elapsed_time):
        twinkle = 0.85 + 0.15 * math.sin(elapsed_time * 2.0 + self.twinkle_offset)
        self.brightness = clamp(self.base_brightness * twinkle, 0.0, 1.0)



def generate_galaxy(star_count):
    stars = []
    dust_patches = []

    bulge_count = int(star_count * BULGE_RATIO)
    disk_count = int(star_count * DISK_RATIO)
    arm_count = star_count - bulge_count - disk_count

    pitch_k = 1.0 / math.tan(math.radians(ARM_PITCH_DEG))
    arm_offsets = [(math.tau / NUM_ARMS) * i for i in range(NUM_ARMS)]

   
    for _ in range(bulge_count):
        r = (random.random() ** 0.5) * BULGE_RADIUS
        theta = random.uniform(0, math.tau)
        phi = random.uniform(0, math.pi)
        x = r * math.sin(phi) * math.cos(theta)
        z = r * math.sin(phi) * math.sin(theta)
        y = r * math.cos(phi) * 0.45

       
        core_fraction = 1.0 - clamp(r / BULGE_RADIUS, 0.0, 1.0)
        temperature = random.uniform(3800, 5400) + random.uniform(0, 4000) * core_fraction ** 3
        radius = random.uniform(1.0, 2.0) + 0.6 * core_fraction
        brightness = random.uniform(0.75, 1.0)
        glow = core_fraction > 0.45 or random.random() < 0.15
        stars.append(Star(x, y, z, radius, brightness, temperature, glow))

   
    for _ in range(disk_count):
        r = sample_exponential_radius(DISK_SCALE_LENGTH, GALAXY_RADIUS)
        angle = random.uniform(0, math.tau)
        x = math.cos(angle) * r
        z = math.sin(angle) * r

        thickness = DISK_THICKNESS * (1.0 - r / (GALAXY_RADIUS * 1.3))
        y = random.gauss(0, max(1.5, thickness) / 3.0)

        temperature = random.uniform(3200, 5800)
        radius = random.uniform(0.5, 1.1)
        brightness = random.uniform(0.25, 0.55)
        stars.append(Star(x, y, z, radius, brightness, temperature, glow=False))

    # --- Spiral arm stars ---
    for _ in range(arm_count):
        arm_offset = random.choice(arm_offsets)
        r = sample_exponential_radius(GALAXY_RADIUS * 0.55, GALAXY_RADIUS)
        r = max(r, 4.0)

        spiral_angle = arm_offset + pitch_k * math.log(r)

        
        angular_scatter = random.gauss(0, ARM_WIDTH / r)
        angle = spiral_angle + angular_scatter
        arc_dist = abs(angular_scatter) * r

        x = math.cos(angle) * r
        z = math.sin(angle) * r

        thickness = DISK_THICKNESS * (1.0 - r / (GALAXY_RADIUS * 1.3))
        y = random.gauss(0, max(1.5, thickness) / 3.0)


        proximity = clamp(1.0 - arc_dist / (ARM_WIDTH * 1.6), 0.0, 1.0)

       
        cool_temp = random.uniform(3200, 5200)
        hot_temp = random.uniform(8000, 24000)
        temperature = lerp(cool_temp, hot_temp, proximity ** 1.6)

        radius = lerp(0.55, 2.1, proximity ** 1.3) + random.uniform(-0.15, 0.15)
        radius = max(0.4, radius)
        brightness = lerp(0.3, 1.0, proximity ** 1.2) + random.uniform(-0.05, 0.1)
        brightness = clamp(brightness, 0.15, 1.0)

        
        is_cluster = proximity > 0.85 and random.random() < 0.03
        if is_cluster:
            radius += random.uniform(0.8, 1.6)
            brightness = 1.0

        
        glow = is_cluster
        stars.append(Star(x, y, z, radius, brightness, temperature, glow))

        
        if proximity > 0.55 and random.random() < 0.12:
            dust_r = max(4.0, r - random.uniform(6, 22))
            dust_angle = spiral_angle - random.uniform(0.02, 0.10)
            dx = math.cos(dust_angle) * dust_r
            dz = math.sin(dust_angle) * dust_r
            dy = random.gauss(0, thickness / 4.0)
            dust_patches.append({
                "x": dx, "y": dy, "z": dz,
                "orbit_radius": math.hypot(dx, dz),
                "orbit_angle": math.atan2(dz, dx),
                "orbit_speed": 0.35 / (0.6 + math.hypot(dx, dz) / 120.0),
                "size": random.uniform(12, 26),
                "alpha": random.randint(35, 75),
            })

    return stars, dust_patches


class Camera:
    def __init__(self):
        self.reset()

    def reset(self):
        self.yaw = 0.5
        self.pitch = 1.0     # steep angle so the spiral shape reads clearly
        self.zoom = 1.0

    def rotate(self, dx, dy):
        self.yaw += dx
        self.pitch = clamp(self.pitch + dy, -1.45, 1.45)

    def adjust_zoom(self, amount):
        self.zoom = clamp(self.zoom * amount, 0.25, 4.0)

    def project(self, x, y, z, center_x, center_y):
        cos_yaw, sin_yaw = math.cos(self.yaw), math.sin(self.yaw)
        x1 = x * cos_yaw - z * sin_yaw
        z1 = x * sin_yaw + z * cos_yaw

        cos_pitch, sin_pitch = math.cos(self.pitch), math.sin(self.pitch)
        y2 = y * cos_pitch - z1 * sin_pitch
        z2 = y * sin_pitch + z1 * cos_pitch

        distance = CAMERA_DISTANCE / self.zoom
        depth = z2 + distance
        if depth < 1:
            depth = 1

        scale = FOV / depth
        screen_x = center_x + x1 * scale
        screen_y = center_y - y2 * scale
        return screen_x, screen_y, scale, depth



def build_background(width, height):
    surface = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(1, height - 1)
        color = lerp_color(BG_TOP_COLOR, BG_BOTTOM_COLOR, t)
        pygame.draw.line(surface, color, (0, y), (width, y))

    for _ in range(BACKGROUND_STAR_COUNT):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        b = random.uniform(0.2, 0.9)
        shade = int(180 * b)
        color = (shade, shade, clamp(shade + 20, 0, 255))
        r = 1 if random.random() < 0.85 else 2
        pygame.draw.circle(surface, color, (x, y), r)

    return surface



def draw_aa_circle(surface, color, pos, radius):
    x, y = int(pos[0]), int(pos[1])
    radius = max(1, int(radius))
    if HAVE_GFXDRAW:
        try:
            gfxdraw.filled_circle(surface, x, y, radius, color)
            if radius > 1:
                gfxdraw.aacircle(surface, x, y, radius, color)
            return
        except Exception:
            pass
    pygame.draw.circle(surface, color, (x, y), radius)


def main():
    pygame.init()
    try:
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    except pygame.error:
        if "SDL_VIDEODRIVER" not in os.environ:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.quit()
            pygame.init()
            screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        else:
            raise
    pygame.display.set_caption("Galactic Model")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    stars, dust_patches = generate_galaxy(STAR_COUNT)
    camera = Camera()
    background = build_background(WINDOW_WIDTH, WINDOW_HEIGHT)
    glow_layer = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    dust_layer = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)

    center_x, center_y = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2

    running = True
    paused = False
    dragging = False
    glow_enabled = True
    dust_enabled = True
    last_mouse = (0, 0)
    elapsed_time = 0.0

    while running:
        delta_time = clock.tick(TARGET_FPS) / 1000
        elapsed_time += delta_time if not paused else 0.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    camera.reset()
                elif event.key == pygame.K_g:
                    glow_enabled = not glow_enabled
                elif event.key == pygame.K_d:
                    dust_enabled = not dust_enabled

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    dragging = True
                    last_mouse = event.pos
                elif event.button == 4:
                    camera.adjust_zoom(1.1)
                elif event.button == 5:
                    camera.adjust_zoom(0.9)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if dragging:
                    mx, my = event.pos
                    lx, ly = last_mouse
                    camera.rotate((mx - lx) * 0.005, (my - ly) * 0.005)
                    last_mouse = (mx, my)

            elif event.type == pygame.MOUSEWHEEL:
                camera.adjust_zoom(1.0 + event.y * 0.1)

        if not dragging and not paused:
            camera.yaw += AUTO_ROTATE_SPEED * delta_time

        for star in stars:
            if not paused:
                star.advance_orbit(delta_time)
            star.update_twinkle(elapsed_time)
        if not paused:
            for dust in dust_patches:
                dust["orbit_angle"] += dust["orbit_speed"] * delta_time
                dust["x"] = math.cos(dust["orbit_angle"]) * dust["orbit_radius"]
                dust["z"] = math.sin(dust["orbit_angle"]) * dust["orbit_radius"]

        screen.blit(background, (0, 0))

       
        projected = []
        for star in stars:
            sx, sy, scale, depth = camera.project(
                star.x, star.y, star.z, center_x, center_y
            )
            if -50 <= sx <= WINDOW_WIDTH + 50 and -50 <= sy <= WINDOW_HEIGHT + 50:
                projected.append((depth, star, sx, sy, scale))
        projected.sort(key=lambda item: item[0], reverse=True)

      
        if glow_enabled:
            glow_layer.fill((0, 0, 0, 0))
            for depth, star, sx, sy, scale in projected:
                if not star.glow:
                    continue
                depth_fade = clamp(1.4 - depth / (CAMERA_DISTANCE * 2.2), 0.15, 1.0)
                b = star.brightness * depth_fade
                base_r = max(1.0, star.radius * scale)
                for ring, alpha_mult in ((base_r * 3.0, 0.07), (base_r * 1.6, 0.16)):
                    alpha = int(255 * b * alpha_mult)
                    if alpha <= 0:
                        continue
                    color = (*star.color, clamp(alpha, 0, 255))
                    pygame.draw.circle(glow_layer, color, (int(sx), int(sy)), max(1, int(ring)))
            screen.blit(glow_layer, (0, 0), special_flags=pygame.BLEND_ADD)

        
        for depth, star, sx, sy, scale in projected:
            depth_fade = clamp(1.4 - depth / (CAMERA_DISTANCE * 2.2), 0.25, 1.0)
            b = clamp(star.brightness * depth_fade, 0.0, 1.0)
            display_color = tuple(int(v * b) for v in star.color)
            draw_aa_circle(screen, display_color, (sx, sy), star.radius * scale)

        
        if dust_enabled and dust_patches:
            dust_layer.fill((0, 0, 0, 0))
            for dust in dust_patches:
                sx, sy, scale, depth = camera.project(
                    dust["x"], dust["y"], dust["z"], center_x, center_y
                )
                if -60 <= sx <= WINDOW_WIDTH + 60 and -60 <= sy <= WINDOW_HEIGHT + 60:
                    size = max(2, int(dust["size"] * scale))
                    pygame.draw.circle(
                        dust_layer, (35, 16, 12, dust["alpha"]), (int(sx), int(sy)), size
                    )
            screen.blit(dust_layer, (0, 0))

        
        fps = clock.get_fps()
        hud_lines = [
            f"FPS: {fps:.0f}   Stars: {len(stars)}",
            f"{'PAUSED' if paused else 'Rotating'}  (SPACE pause, R reset)",
            f"Glow: {'on' if glow_enabled else 'off'} (G)   Dust: {'on' if dust_enabled else 'off'} (D)",
            "Drag: rotate   Wheel: zoom",
        ]
        for i, line in enumerate(hud_lines):
            text_surface = font.render(line, True, (220, 220, 230))
            screen.blit(text_surface, (15, 15 + i * 22))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()