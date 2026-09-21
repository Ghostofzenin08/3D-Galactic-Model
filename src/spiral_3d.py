import math
import os
import random
import sys

import pygame


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

        self.orbit_spped = 0.35 / (0.6 + self.orbit_radius / 120.0)

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




def main():
    pygame.init()
    try:
        screen =  pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    except pygame.error:
        if "SDL_VIDEODRIVER" not in os.environ:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.quit()
            pygame.init()
            screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        else:
            raise
        pygame.display.set_caption("Galactic_Model")
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 24)
    
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running  = False
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()