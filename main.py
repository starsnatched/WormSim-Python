import pygame
import math
import random
from brain import Brain

class IKSegment:
    def __init__(self, size):
        self.size = size
        self.angle = 0
        self.pos = {"x": 0, "y": 0}

    def update(self, target_x, target_y):
        dx = target_x - self.pos["x"]
        dy = target_y - self.pos["y"]
        self.angle = math.atan2(dy, dx)
        self.pos["x"] = target_x - math.cos(self.angle) * self.size
        self.pos["y"] = target_y - math.sin(self.angle) * self.size

class IKChain:
    def __init__(self, size, segment_length):
        self.segments = [IKSegment(segment_length) for _ in range(size)]

    def update(self, target):
        self.segments[0].pos["x"] = target["x"]
        self.segments[0].pos["y"] = target["y"]
        for i in range(1, len(self.segments)):
            self.segments[i].update(self.segments[i-1].pos["x"], self.segments[i-1].pos["y"])

class WormSimulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.width, self.height = self.screen.get_size()
        self.clock = pygame.time.Clock()

        self.brain = Brain()
        self.chain = IKChain(10, 10)
        self.target = {"x": self.width // 2, "y": self.height // 2}
        self.food = []

        self.facing_dir = 0
        self.target_dir = 0
        self.speed = 0
        self.target_speed = 0
        self.speed_change_interval = 0

        self.neuron_positions = self.initialize_neuron_positions()
        self.neuron_radius = 5
        self.connection_thickness = 1
        self.neuron_colors = {
            'sensory': (255, 0, 0),    # Red
            'inter': (0, 255, 0),      # Green
            'motor': (0, 0, 255),      # Blue
            'other': (255, 255, 255)   # White
        }

        self.neuron_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.draw_static_neurons()

    def initialize_neuron_positions(self):
        positions = {}
        neurons = list(self.brain.post_synaptic.keys())
        rows = int(math.sqrt(len(neurons)))
        cols = math.ceil(len(neurons) / rows)
        
        neuron_width = self.width / (cols + 1)
        neuron_height = self.height / (rows + 1)
        
        for i, neuron in enumerate(neurons):
            row = i // cols
            col = i % cols
            x = (col + 1) * neuron_width
            y = (row + 1) * neuron_height
            positions[neuron] = (x, y)
        
        return positions
    
    def get_neuron_color(self, neuron):
        if neuron.startswith(('ADF', 'ASE', 'ASG', 'ASH', 'ASI', 'ASJ', 'ASK', 'AWA', 'AWB', 'AWC')):
            return self.neuron_colors['sensory']
        elif neuron.startswith(('DA', 'DB', 'DD', 'VA', 'VB', 'VC', 'VD')):
            return self.neuron_colors['motor']
        elif neuron.startswith(('AIA', 'AIB', 'AIM', 'AIY', 'AIZ', 'DVA', 'PVC', 'RIA', 'RIB', 'RIM')):
            return self.neuron_colors['inter']
        else:
            return self.neuron_colors['other']

    def draw_neurons(self):
        for neuron, pos in self.neuron_positions.items():
            color = self.get_neuron_color(neuron)
            pygame.draw.circle(self.screen, color, pos, self.neuron_radius)
            
            for target, weight in self.brain.weights.get(neuron, {}).items():
                if target in self.neuron_positions:
                    start_pos = pos
                    end_pos = self.neuron_positions[target]
                    
                    intensity = int(min(abs(weight) * 10, 255))
                    connection_color = (intensity, intensity, intensity)
                    
                    pygame.draw.line(self.screen, connection_color, start_pos, end_pos, self.connection_thickness)

    def draw_static_neurons(self):
        self.neuron_surface.fill((0, 0, 0, 0))
        for neuron, pos in self.neuron_positions.items():
            color = self.get_neuron_color(neuron)
            pygame.draw.circle(self.neuron_surface, color, pos, self.neuron_radius)
            
            for target, weight in self.brain.weights.get(neuron, {}).items():
                if target in self.neuron_positions:
                    start_pos = pos
                    end_pos = self.neuron_positions[target]
                    
                    intensity = int(min(abs(weight) * 10, 255))
                    connection_color = (intensity, intensity, intensity, 128)
                    
                    pygame.draw.line(self.neuron_surface, connection_color, start_pos, end_pos, self.connection_thickness)

    def update_neuron_activity(self):
        activity_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for neuron, pos in self.neuron_positions.items():
            activity = self.brain.post_synaptic[neuron][self.brain.this_state]
            if activity > self.brain.fire_threshold:
                glow_radius = self.neuron_radius + 5
                glow_color = (*self.get_neuron_color(neuron)[:3], 128)
                pygame.draw.circle(activity_surface, glow_color, pos, glow_radius)
        return activity_surface
    
    def update_brain(self):
        self.brain.update()
        scaling_factor = 20
        new_dir = (self.brain.accumleft - self.brain.accumright) / scaling_factor
        self.target_dir = self.facing_dir + new_dir * math.pi
        self.target_speed = (abs(self.brain.accumleft) + abs(self.brain.accumright)) / (scaling_factor * 5)
        self.speed_change_interval = (self.target_speed - self.speed) / (scaling_factor * 1.5)

    def update(self):
        self.speed += self.speed_change_interval

        facing_minus_target = self.facing_dir - self.target_dir
        angle_diff = facing_minus_target

        if abs(facing_minus_target) > math.pi:
            if self.facing_dir > self.target_dir:
                angle_diff = -1 * (2 * math.pi - self.facing_dir + self.target_dir)
            else:
                angle_diff = 2 * math.pi - self.target_dir + self.facing_dir

        if angle_diff > 0:
            self.facing_dir -= 0.1
        elif angle_diff < 0:
            self.facing_dir += 0.1

        self.target["x"] += math.cos(self.facing_dir) * self.speed
        self.target["y"] -= math.sin(self.facing_dir) * self.speed

        self.target["x"] = self.target["x"] % self.width
        self.target["y"] = self.target["y"] % self.height

        for food in self.food[:]:
            distance = math.hypot(round(self.target["x"]) - food[0], round(self.target["y"]) - food[1])
            if distance <= 50:
                self.brain.stimulate_food_sense_neurons = True
                if distance <= 20:
                    self.food.remove(food)

        self.chain.update(self.target)

    def draw(self):
        self.screen.fill((0, 0, 0))

        self.screen.blit(self.neuron_surface, (0, 0))

        activity_surface = self.update_neuron_activity()
        self.screen.blit(activity_surface, (0, 0))

        for food in self.food:
            pygame.draw.circle(self.screen, (251, 192, 45), food, 10)

        points = [(int(segment.pos["x"]), int(segment.pos["y"])) for segment in self.chain.segments]
        
        pygame.draw.lines(self.screen, (100, 200, 100), False, points, 20)
        
        for point in points:
            pygame.draw.circle(self.screen, (50, 150, 50), point, 10)

        pygame.draw.circle(self.screen, (0, 255, 0), points[0], 15)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.food.append(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            self.update_brain()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    simulation = WormSimulation()
    simulation.run()