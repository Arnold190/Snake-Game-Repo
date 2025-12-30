import pygame
import sys
import random
import math
from enum import Enum

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
FPS = 60

# Colors
BACKGROUND = (15, 56, 15)  # Dark green
GRID_COLOR = (30, 80, 30)  # Medium green
SNAKE_COLOR = (0, 200, 50)  # Bright green
SNAKE_HEAD_COLOR = (0, 255, 100)  # Lighter green
FOOD_COLOR = (255, 50, 50)  # Red
OBSTACLE_COLOR = (100, 100, 150)  # Blue-gray
TEXT_COLOR = (255, 255, 200)  # Light yellow
HIGHLIGHT_COLOR = (255, 255, 100)  # Bright yellow
MENU_BG = (10, 40, 10, 200)  # Semi-transparent dark green
BUTTON_COLOR = (50, 150, 50)  # Green
BUTTON_HOVER = (80, 200, 80)  # Light green

# Game states


class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3
    INSTRUCTIONS = 4

# Direction enum


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

# ============================================
# MODULE 1: Snake Class
# ============================================


class Snake:
    def __init__(self):
        self.reset()
        self.grow_pending = 0
        self.move_timer = 0
        self.move_delay = 150  # Milliseconds between moves
        self.speed_increase_threshold = 5  # Increase speed every 5 foods

    def reset(self):
        # Start in the middle of the grid
        start_x = GRID_WIDTH // 2
        start_y = GRID_HEIGHT // 2
        self.body = [(start_x, start_y), (start_x-1, start_y),
                     (start_x-2, start_y)]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.grow_pending = 0
        self.move_timer = 0
        self.move_delay = 150
        self.score = 0
        self.foods_eaten = 0

    def update(self, dt):
        # Update movement timer
        self.move_timer += dt

        # Only move if enough time has passed
        if self.move_timer >= self.move_delay:
            self.move_timer = 0
            self.direction = self.next_direction

            # Get the head position
            head_x, head_y = self.body[0]

            # Calculate new head position based on direction
            dx, dy = self.direction.value
            new_head = ((head_x + dx) % GRID_WIDTH,
                        (head_y + dy) % GRID_HEIGHT)

            # Add new head to the body
            self.body.insert(0, new_head)

            # Remove tail if not growing
            if self.grow_pending > 0:
                self.grow_pending -= 1
            else:
                self.body.pop()

    def change_direction(self, new_direction):
        # Prevent 180-degree turns
        if (new_direction == Direction.UP and self.direction != Direction.DOWN) or \
           (new_direction == Direction.DOWN and self.direction != Direction.UP) or \
           (new_direction == Direction.LEFT and self.direction != Direction.RIGHT) or \
           (new_direction == Direction.RIGHT and self.direction != Direction.LEFT):
            self.next_direction = new_direction

    def grow(self, amount=1):
        self.grow_pending += amount
        self.foods_eaten += 1

        # Increase speed every few foods
        if self.foods_eaten % self.speed_increase_threshold == 0 and self.move_delay > 50:
            self.move_delay -= 10

    def check_self_collision(self):
        # Check if head collides with any body segment
        head = self.body[0]
        return head in self.body[1:]

    def get_head_position(self):
        return self.body[0]

    def get_body(self):
        return self.body

    def get_length(self):
        return len(self.body)

# ============================================
# MODULE 2: Food and Obstacles
# ============================================


class Food:
    def __init__(self):
        self.position = (0, 0)
        self.spawn_time = 0
        self.sparkle_timer = 0
        self.spawn()

    def spawn(self, snake_body=None, obstacles=None):
        # Generate random position
        if snake_body is None:
            snake_body = []
        if obstacles is None:
            obstacles = []

        # Keep trying until we find a valid position
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            self.position = (x, y)

            # Check if position is not on snake or obstacles
            if (self.position not in snake_body) and (self.position not in obstacles):
                self.spawn_time = pygame.time.get_ticks()
                break

    def update(self, dt):
        # Update sparkle animation
        self.sparkle_timer += dt

    def get_position(self):
        return self.position

    def draw(self, screen):
        x, y = self.position
        pixel_x = x * GRID_SIZE
        pixel_y = y * GRID_SIZE

        # Draw the food with sparkle effect
        food_rect = pygame.Rect(pixel_x, pixel_y, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(screen, FOOD_COLOR, food_rect)
        pygame.draw.rect(screen, (255, 200, 200), food_rect, 1)

        # Draw sparkle effect
        sparkle_value = int((math.sin(self.sparkle_timer * 0.01) + 1) * 127)
        sparkle_color = (255, min(255, 150 + sparkle_value),
                         min(255, 150 + sparkle_value))

        # Draw small sparkle dots
        sparkle_positions = [
            (pixel_x + GRID_SIZE//4, pixel_y + GRID_SIZE//4),
            (pixel_x + 3*GRID_SIZE//4, pixel_y + GRID_SIZE//4),
            (pixel_x + GRID_SIZE//4, pixel_y + 3*GRID_SIZE//4),
            (pixel_x + 3*GRID_SIZE//4, pixel_y + 3*GRID_SIZE//4),
        ]

        for pos in sparkle_positions:
            pygame.draw.circle(screen, sparkle_color, pos, 2)


class Obstacle:
    def __init__(self, level=1):
        self.positions = []
        self.generate_obstacles(level)

    def generate_obstacles(self, level):
        self.positions = []

        # Generate more obstacles as level increases
        num_obstacles = min(level * 2, 10)

        for _ in range(num_obstacles):
            while True:
                x = random.randint(2, GRID_WIDTH - 3)
                y = random.randint(2, GRID_HEIGHT - 3)
                obstacle = (x, y)

                # Make sure obstacle is not too close to center
                if abs(x - GRID_WIDTH//2) > 5 or abs(y - GRID_HEIGHT//2) > 5:
                    self.positions.append(obstacle)
                    break

    def get_positions(self):
        return self.positions

# ============================================
# MODULE 3: Game Class (Main Controller)
# ============================================


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Magical Garden Snake")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)
        self.state = GameState.MENU
        self.snake = Snake()
        self.food = Food()
        self.obstacle = Obstacle(1)
        self.level = 1
        self.high_score = 0
        self.game_over_timer = 0
        self.game_over_delay = 2000  # 2 seconds

        # Load sounds
        self.load_sounds()

        # Menu buttons
        self.menu_buttons = [
            {"text": "Play", "rect": pygame.Rect(
                0, 0, 200, 50), "action": GameState.PLAYING},
            {"text": "Instructions", "rect": pygame.Rect(
                0, 0, 200, 50), "action": GameState.INSTRUCTIONS},
            {"text": "Quit", "rect": pygame.Rect(
                0, 0, 200, 50), "action": "quit"}
        ]

        # Position menu buttons
        button_y = SCREEN_HEIGHT // 2 - 100
        for button in self.menu_buttons:
            button["rect"].center = (SCREEN_WIDTH // 2, button_y)
            button_y += 70

        # Game over button
        self.restart_button = {"text": "Play Again",
                               "rect": pygame.Rect(0, 0, 200, 50)}
        self.restart_button["rect"].center = (
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)

        # Back button for instructions
        self.back_button = {"text": "Back to Menu",
                            "rect": pygame.Rect(0, 0, 200, 50)}
        self.back_button["rect"].center = (
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)

    def load_sounds(self):
        # Create simple sound effects
        self.eat_sound = pygame.mixer.Sound(
            buffer=bytes([128] * 1000))  # Placeholder
        self.collision_sound = pygame.mixer.Sound(
            buffer=bytes([200] * 500))  # Placeholder

    def reset_game(self):
        self.snake.reset()
        self.food.spawn(self.snake.get_body(), self.obstacle.get_positions())
        self.level = 1
        self.obstacle.generate_obstacles(self.level)
        self.game_over_timer = 0

    def check_collisions(self):
        # Check food collision
        if self.snake.get_head_position() == self.food.get_position():
            # Increase score and grow snake
            points = 10 * self.level
            self.snake.score += points
            self.snake.grow()

            # Play sound
            self.eat_sound.play()

            # Spawn new food
            self.food.spawn(self.snake.get_body(),
                            self.obstacle.get_positions())

            # Level up every 5 foods
            if self.snake.foods_eaten % 5 == 0:
                self.level += 1
                self.obstacle.generate_obstacles(self.level)

            # Update high score
            if self.snake.score > self.high_score:
                self.high_score = self.snake.score

        # Check obstacle collision
        if self.snake.get_head_position() in self.obstacle.get_positions():
            return True

        # Check self collision
        if self.snake.check_self_collision():
            return True

        return False

    def draw_grid(self):
        # Draw background
        self.screen.fill(BACKGROUND)

        # Draw grid lines
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR,
                             (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR,
                             (0, y), (SCREEN_WIDTH, y), 1)

    def draw_snake(self):
        # Draw each segment of the snake
        for i, (x, y) in enumerate(self.snake.get_body()):
            pixel_x = x * GRID_SIZE
            pixel_y = y * GRID_SIZE
            segment_rect = pygame.Rect(pixel_x, pixel_y, GRID_SIZE, GRID_SIZE)

            # Head is a different color
            if i == 0:
                pygame.draw.rect(self.screen, SNAKE_HEAD_COLOR, segment_rect)
                pygame.draw.rect(self.screen, (0, 255, 150), segment_rect, 2)

                # Draw eyes
                eye_size = GRID_SIZE // 5
                dx, dy = self.snake.direction.value

                # Left eye
                left_eye_x = pixel_x + GRID_SIZE//4
                left_eye_y = pixel_y + GRID_SIZE//4

                # Right eye
                right_eye_x = pixel_x + 3*GRID_SIZE//4
                right_eye_y = pixel_y + GRID_SIZE//4

                # Adjust eye position based on direction
                if dx == 1:  # Right
                    left_eye_x = pixel_x + 3*GRID_SIZE//4
                    right_eye_x = pixel_x + 3*GRID_SIZE//4
                    left_eye_y = pixel_y + GRID_SIZE//4
                    right_eye_y = pixel_y + 3*GRID_SIZE//4
                elif dx == -1:  # Left
                    left_eye_x = pixel_x + GRID_SIZE//4
                    right_eye_x = pixel_x + GRID_SIZE//4
                    left_eye_y = pixel_y + GRID_SIZE//4
                    right_eye_y = pixel_y + 3*GRID_SIZE//4
                elif dy == 1:  # Down
                    left_eye_x = pixel_x + GRID_SIZE//4
                    right_eye_x = pixel_x + 3*GRID_SIZE//4
                    left_eye_y = pixel_y + 3*GRID_SIZE//4
                    right_eye_y = pixel_y + 3*GRID_SIZE//4
                elif dy == -1:  # Up
                    left_eye_x = pixel_x + GRID_SIZE//4
                    right_eye_x = pixel_x + 3*GRID_SIZE//4
                    left_eye_y = pixel_y + GRID_SIZE//4
                    right_eye_y = pixel_y + GRID_SIZE//4

                pygame.draw.circle(self.screen, (0, 0, 0),
                                   (left_eye_x, left_eye_y), eye_size)
                pygame.draw.circle(self.screen, (0, 0, 0),
                                   (right_eye_x, right_eye_y), eye_size)
            else:
                # Body segments
                color_factor = max(100, 255 - i * 5)
                segment_color = (0, min(255, color_factor), 50)
                pygame.draw.rect(self.screen, segment_color, segment_rect)
                pygame.draw.rect(self.screen, (0, min(
                    255, color_factor + 50), 100), segment_rect, 1)

    def draw_obstacles(self):
        for x, y in self.obstacle.get_positions():
            pixel_x = x * GRID_SIZE
            pixel_y = y * GRID_SIZE
            obstacle_rect = pygame.Rect(pixel_x, pixel_y, GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(self.screen, OBSTACLE_COLOR, obstacle_rect)
            pygame.draw.rect(self.screen, (150, 150, 200), obstacle_rect, 2)

    def draw_hud(self):
        # Draw score
        score_text = self.font.render(
            f"Score: {self.snake.score}", True, TEXT_COLOR)
        self.screen.blit(score_text, (10, 10))

        # Draw high score
        high_score_text = self.font.render(
            f"High Score: {self.high_score}", True, TEXT_COLOR)
        self.screen.blit(high_score_text, (SCREEN_WIDTH -
                         high_score_text.get_width() - 10, 10))

        # Draw level
        level_text = self.font.render(f"Level: {self.level}", True, TEXT_COLOR)
        self.screen.blit(level_text, (SCREEN_WIDTH // 2 -
                         level_text.get_width() // 2, 10))

        # Draw snake length
        length_text = self.small_font.render(
            f"Length: {self.snake.get_length()}", True, TEXT_COLOR)
        self.screen.blit(length_text, (10, 50))

        # Draw speed indicator
        speed = max(1, 10 - (self.snake.move_delay - 50) // 10)
        speed_text = self.small_font.render(
            f"Speed: {speed}/10", True, TEXT_COLOR)
        self.screen.blit(speed_text, (10, 80))

    def draw_menu(self):
        # Draw semi-transparent overlay
        overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(MENU_BG)
        self.screen.blit(overlay, (0, 0))

        # Draw title
        title = self.font.render("Magical Garden Snake", True, HIGHLIGHT_COLOR)
        title_shadow = self.font.render(
            "Magical Garden Snake", True, (0, 0, 0))
        self.screen.blit(title_shadow, (SCREEN_WIDTH//2 -
                         title.get_width()//2 + 3, 103))
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))

        # Draw subtitle
        subtitle = self.small_font.render(
            "Collect enchanted fruits in the magical garden", True, TEXT_COLOR)
        self.screen.blit(subtitle, (SCREEN_WIDTH//2 -
                         subtitle.get_width()//2, 150))

        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        for button in self.menu_buttons:
            # Check if mouse is hovering over button
            is_hover = button["rect"].collidepoint(mouse_pos)
            color = BUTTON_HOVER if is_hover else BUTTON_COLOR

            # Draw button
            pygame.draw.rect(self.screen, color,
                             button["rect"], border_radius=10)
            pygame.draw.rect(self.screen, HIGHLIGHT_COLOR,
                             button["rect"], 3, border_radius=10)

            # Draw button text
            text = self.font.render(button["text"], True, TEXT_COLOR)
            text_rect = text.get_rect(center=button["rect"].center)
            self.screen.blit(text, text_rect)

    def draw_instructions(self):
        # Draw semi-transparent overlay
        overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(MENU_BG)
        self.screen.blit(overlay, (0, 0))

        # Draw title
        title = self.font.render("Instructions", True, HIGHLIGHT_COLOR)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))

        # Draw instructions
        instructions = [
            "Control the snake using arrow keys",
            "Eat the red fruits to grow and earn points",
            "Avoid colliding with yourself or the blue obstacles",
            "",
            "Game Features:",
            "- Snake speeds up as you eat more fruits",
            "- New obstacles appear each level",
            "- Earn 10 points per fruit, multiplied by level",
            "- Reach level 5 to win the game!",
            "",
            "Good luck in the magical garden!"
        ]

        # Draw each line
        y_pos = 120
        for line in instructions:
            text = self.small_font.render(line, True, TEXT_COLOR)
            self.screen.blit(
                text, (SCREEN_WIDTH//2 - text.get_width()//2, y_pos))
            y_pos += 40

        # Draw back button
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.back_button["rect"].collidepoint(mouse_pos)
        color = BUTTON_HOVER if is_hover else BUTTON_COLOR

        pygame.draw.rect(self.screen, color,
                         self.back_button["rect"], border_radius=10)
        pygame.draw.rect(self.screen, HIGHLIGHT_COLOR,
                         self.back_button["rect"], 3, border_radius=10)

        text = self.font.render(self.back_button["text"], True, TEXT_COLOR)
        text_rect = text.get_rect(center=self.back_button["rect"].center)
        self.screen.blit(text, text_rect)

    def draw_game_over(self):
        # Draw semi-transparent overlay
        overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Draw game over text
        game_over_text = self.font.render("Game Over", True, (255, 50, 50))
        self.screen.blit(game_over_text, (SCREEN_WIDTH//2 -
                         game_over_text.get_width()//2, 150))

        # Draw final score
        score_text = self.font.render(
            f"Final Score: {self.snake.score}", True, TEXT_COLOR)
        self.screen.blit(score_text, (SCREEN_WIDTH//2 -
                         score_text.get_width()//2, 200))

        # Draw high score
        high_score_text = self.font.render(
            f"High Score: {self.high_score}", True, TEXT_COLOR)
        self.screen.blit(high_score_text, (SCREEN_WIDTH//2 -
                         high_score_text.get_width()//2, 240))

        # Check if player won (reached level 5)
        if self.level >= 5:
            win_text = self.font.render(
                "You Mastered the Magical Garden!", True, HIGHLIGHT_COLOR)
            self.screen.blit(win_text, (SCREEN_WIDTH//2 -
                             win_text.get_width()//2, 290))

        # Draw restart button
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.restart_button["rect"].collidepoint(mouse_pos)
        color = BUTTON_HOVER if is_hover else BUTTON_COLOR

        pygame.draw.rect(self.screen, color,
                         self.restart_button["rect"], border_radius=10)
        pygame.draw.rect(self.screen, HIGHLIGHT_COLOR,
                         self.restart_button["rect"], 3, border_radius=10)

        text = self.font.render(self.restart_button["text"], True, TEXT_COLOR)
        text_rect = text.get_rect(center=self.restart_button["rect"].center)
        self.screen.blit(text, text_rect)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if self.state == GameState.PLAYING:
                    if event.key == pygame.K_UP:
                        self.snake.change_direction(Direction.UP)
                    elif event.key == pygame.K_DOWN:
                        self.snake.change_direction(Direction.DOWN)
                    elif event.key == pygame.K_LEFT:
                        self.snake.change_direction(Direction.LEFT)
                    elif event.key == pygame.K_RIGHT:
                        self.snake.change_direction(Direction.RIGHT)
                    elif event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU

                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        self.reset_game()
                        self.state = GameState.PLAYING

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                if self.state == GameState.MENU:
                    for button in self.menu_buttons:
                        if button["rect"].collidepoint(mouse_pos):
                            if button["action"] == "quit":
                                return False
                            else:
                                self.state = button["action"]
                                if self.state == GameState.PLAYING:
                                    self.reset_game()

                elif self.state == GameState.GAME_OVER:
                    if self.restart_button["rect"].collidepoint(mouse_pos):
                        self.reset_game()
                        self.state = GameState.PLAYING

                elif self.state == GameState.INSTRUCTIONS:
                    if self.back_button["rect"].collidepoint(mouse_pos):
                        self.state = GameState.MENU

        return True

    def run(self):
        running = True
        last_time = pygame.time.get_ticks()

        while running:
            # Calculate delta time
            current_time = pygame.time.get_ticks()
            dt = current_time - last_time
            last_time = current_time

            # Handle events
            running = self.handle_events()

            # Update game state
            if self.state == GameState.PLAYING:
                # Update snake
                self.snake.update(dt)

                # Update food animation
                self.food.update(dt)

                # Check collisions
                if self.check_collisions():
                    self.collision_sound.play()
                    self.game_over_timer = pygame.time.get_ticks()
                    self.state = GameState.GAME_OVER

                # Check for win condition (level 5)
                if self.level >= 5:
                    self.game_over_timer = pygame.time.get_ticks()
                    self.state = GameState.GAME_OVER

            # Draw everything
            self.draw_grid()

            if self.state == GameState.PLAYING:
                self.draw_obstacles()
                self.draw_snake()
                self.food.draw(self.screen)
                self.draw_hud()
            elif self.state == GameState.MENU:
                self.draw_menu()
            elif self.state == GameState.GAME_OVER:
                self.draw_obstacles()
                self.draw_snake()
                self.food.draw(self.screen)
                self.draw_hud()
                self.draw_game_over()
            elif self.state == GameState.INSTRUCTIONS:
                self.draw_instructions()

            # Update display
            pygame.display.flip()

            # Control frame rate
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ============================================
# Main entry point
# ============================================
if __name__ == "__main__":
    game = Game()
    game.run()
