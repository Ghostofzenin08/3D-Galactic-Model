
import math
import os
import random
import sys

import pygame


WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
TARGET_FPS = 60

STAR_COUNT = 6000
NUM_ARMS = 4                 
ARM_SPREAD = 0.45             
GALAXY_RADIUS = 420          
DISK_THICKNESS = 26           
BULGE_RATIO = 0.12            
BULGE_RADIUS = 60

CAMERA_DISTANCE = 900         
FOV = 500                      
AUTO_ROTATE_SPEED = 0.05        

BACKGROUND_COLOR = (2, 2, 8)


def temperature_to_color(temperature):
   
    t = temperature / 100.0

    # Red
    if t <= 66:
        r = 255
    else:
        r = 329.698727446 * ((t - 60) ** -0.1332047592)
    r = max(0, min(255, r))

    # Green
    if t <= 66:
        g = 99.4708025861 * math.log(max(t, 1)) - 161.1195681661
    else:
        g = 288.1221695283 * ((t - 60) ** -0.0755148492)
    g = max(0, min(255, g))

    # Blue
    if t >= 66:
        b = 255
    elif t <= 19:
        b = 0
    else:
        b = 138.5177312231 * math.log(max(t - 10, 1)) - 305.0447927307
    b = max(0, min(255, b))

    return int(r), int(g), int(b)


def clamp(value, lo, hi):
    return max(lo, min(hi, value))



class Star:
    __slots__ = (
        "x", "y", "z", "base_x", "base_y", "base_z",
        "velocity_y", "mass", "radius", "brightness", "base_brightness",
        "temperature", "color", "age", "twinkle_offset", "orbit_radius",
        "orbit_angle", "orbit_speed",
    )

    def __init__(self, x, y, z, mass, radius, brightness, temperature, age):
        
        self.x = x
        self.y = y
        self.z = z

       
        self.orbit_radius = math.hypot(x, z)
        self.orbit_angle = math.atan2(z, x)
        # Stars further out orbit slower 
        self.orbit_speed = 0.35 / (0.6 + self.orbit_radius / 120.0)

        self.mass = mass
        self.radius = radius
        self.brightness = brightness
        self.base_brightness = brightness
        self.temperature = temperature
        self.color = temperature_to_color(temperature)
        self.age = age
        self.twinkle_offset = random.uniform(0, math.tau)

    def update(self, delta_time, elapsed_time, paused):
        if not paused:
            self.orbit_angle += self.orbit_speed * delta_time
            self.x = math.cos(self.orbit_angle) * self.orbit_radius
            self.z = math.sin(self.orbit_angle) * self.orbit_radius

        
        twinkle = 0.85 + 0.15 * math.sin(elapsed_time * 2.0 + self.twinkle_offset)
        self.brightness = clamp(self.base_brightness * twinkle, 0.0, 1.0)

    def draw(self, surface, screen_pos, projected_radius, extra_brightness=1.0):
        b = clamp(self.brightness * extra_brightness, 0.0, 1.0)
        display_color = tuple(int(v * b) for v in self.color)
        r = max(1, int(projected_radius))
        try:
            pygame.draw.circle(surface, display_color, screen_pos, r)
        except TypeError:
            pass



def generate_galaxy(star_count):
    stars = []
    bulge_count = int(star_count * BULGE_RATIO)
    arm_count = star_count - bulge_count

    
    for _ in range(bulge_count):
        r = (random.random() ** 0.5) * BULGE_RADIUS
        theta = random.uniform(0, math.tau)
        phi = random.uniform(0, math.pi)
        x = r * math.sin(phi) * math.cos(theta)
        z = r * math.sin(phi) * math.sin(theta)
        y = r * math.cos(phi) * 0.5

        temperature = random.uniform(4500, 12000)
        radius = random.uniform(1.0, 2.2)
        brightness = random.uniform(0.7, 1.0)
        age = random.uniform(5.0, 12.0)
        mass = random.uniform(0.8, 3.0)
        stars.append(Star(x, y, z, mass, radius, brightness, temperature, age))

    
    for _ in range(arm_count):
        arm_index = random.randrange(NUM_ARMS)
        arm_offset = (math.tau / NUM_ARMS) * arm_index

        
        r = (random.random() ** 0.6) * GALAXY_RADIUS
        
        spiral_angle = math.log(1 + r) * 2.2 + arm_offset

        
        scatter = ARM_SPREAD * (0.3 + r / GALAXY_RADIUS)
        angle = spiral_angle + random.gauss(0, scatter)
        radius_jitter = r + random.gauss(0, r * 0.08 + 5)
        radius_jitter = max(5.0, radius_jitter)

        x = math.cos(angle) * radius_jitter
        z = math.sin(angle) * radius_jitter

        thickness = DISK_THICKNESS * (1.0 - r / (GALAXY_RADIUS * 1.4))
        y = random.gauss(0, max(2.0, thickness) / 3.0)

        temperature = random.uniform(2800, 22000)
        radius = random.uniform(0.6, 2.0)
        brightness = random.uniform(0.4, 1.0)
        age = random.uniform(0.1, 10.0)
        mass = random.uniform(0.3, 5.0)
        stars.append(Star(x, y, z, mass, radius, brightness, temperature, age))

    return stars



class Camera:
    def __init__(self):
        self.reset()

    def reset(self):
        self.yaw = 0.6      
        self.pitch = 0.35   
        self.zoom = 1.0

    def rotate(self, dx, dy):
        self.yaw += dx
        self.pitch = clamp(self.pitch + dy, -1.4, 1.4)

    def adjust_zoom(self, amount):
        self.zoom = clamp(self.zoom * amount, 0.25, 4.0)

    def project(self, x, y, z, center_x, center_y):
        # Rotate around Y axis (yaw)
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

    stars = generate_galaxy(STAR_COUNT)
    camera = Camera()

    center_x, center_y = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2

    running = True
    paused = False
    dragging = False
    last_mouse = (0, 0)
    elapsed_time = 0.0

    
    core_glow = pygame.Surface((240, 240), pygame.SRCALPHA)
    for radius in range(120, 0, -2):
        alpha = int(70 * (1 - radius / 120) ** 2)
        pygame.draw.circle(core_glow, (140, 170, 255, alpha), (120, 120), radius)

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

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    dragging = True
                    last_mouse = event.pos
                elif event.button == 4:  # wheel up
                    camera.adjust_zoom(1.1)
                elif event.button == 5:  # wheel down
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
            star.update(delta_time, elapsed_time, paused)

        screen.fill(BACKGROUND_COLOR)

        
        glow_x, glow_y, glow_scale, _ = camera.project(0, 0, 0, center_x, center_y)
        glow_size = int(240 * glow_scale / (FOV / CAMERA_DISTANCE))
        glow_size = clamp(glow_size, 20, 900)
        scaled_glow = pygame.transform.smoothscale(core_glow, (glow_size, glow_size))
        screen.blit(scaled_glow, (glow_x - glow_size / 2, glow_y - glow_size / 2),
                    special_flags=pygame.BLEND_ADD)

       
        projected = []
        for star in stars:
            sx, sy, scale, depth = camera.project(
                star.x, star.y, star.z, center_x, center_y
            )
            if -50 <= sx <= WINDOW_WIDTH + 50 and -50 <= sy <= WINDOW_HEIGHT + 50:
                projected.append((depth, star, (sx, sy), scale))

        projected.sort(key=lambda item: item[0], reverse=True)

        for depth, star, screen_pos, scale in projected:
            projected_radius = star.radius * scale
           
            depth_fade = clamp(1.4 - depth / (CAMERA_DISTANCE * 2.2), 0.25, 1.0)
            star.draw(screen, screen_pos, projected_radius, extra_brightness=depth_fade)

       
        fps = clock.get_fps()
        hud_lines = [
            f"FPS: {fps:.0f}",
            f"Stars: {len(stars)}",
            f"{'PAUSED' if paused else 'Rotating'}  (SPACE to toggle, R to reset)",
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
