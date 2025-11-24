"""Flappy Bird-like game (Pygame)

Controls:
  Space - flap / jump
  ESC   - quit

Run:
  python "c:/Users/GEN/3D Objects/main.py"
"""

import random
import sys
import os

try:
	import pygame
except Exception:
	print("The game requires pygame. Install with: pip install pygame")
	raise


WIDTH, HEIGHT = 400, 600
FPS = 60

GRAVITY = 0.5
FLAP_STRENGTH = -9
PIPE_GAP = 150
PIPE_WIDTH = 70
PIPE_SPEED = 3
SPAWN_INTERVAL_MS = 1500


def make_pipe(x):
	gap_y = random.randint(80, HEIGHT - 80 - PIPE_GAP)
	top = pygame.Rect(x, 0, PIPE_WIDTH, gap_y)
	bottom = pygame.Rect(x, gap_y + PIPE_GAP, PIPE_WIDTH, HEIGHT - (gap_y + PIPE_GAP))
	return {"x": x, "top": top, "bottom": bottom, "passed": False}


def main():
	pygame.init()
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	pygame.display.set_caption("Flappy - Pygame Demo")
	clock = pygame.time.Clock()

	font = pygame.font.SysFont(None, 48)
	small = pygame.font.SysFont(None, 24)

	# Ensure assets folder and bird image exist; if not, generate a simple sprite
	assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
	os.makedirs(assets_dir, exist_ok=True)
	bird_img_path = os.path.join(assets_dir, 'bird.png')

	bw, bh = 34, 24
	# Initialize display before creating Surfaces to save
	if not os.path.exists(bird_img_path):
		surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
		surf.fill((0, 0, 0, 0))
		# body
		pygame.draw.ellipse(surf, (255, 230, 80), (0, 0, bw, bh))
		# eye
		pygame.draw.circle(surf, (30, 30, 30), (int(bw * 0.65), int(bh * 0.35)), 3)
		# beak (triangle)
		pygame.draw.polygon(surf, (255, 150, 40), [(int(bw*0.9), int(bh*0.45)), (bw+2, int(bh*0.3)), (bw+2, int(bh*0.6))])
		try:
			pygame.image.save(surf, bird_img_path)
		except Exception:
			# If saving fails for any reason, skip saving and use the generated surface directly
			bird_surface = surf
	else:
		bird_surface = None

	# bird rect and vertical speed
	bird = pygame.Rect(80, HEIGHT // 2 - bh // 2, bw, bh)
	vy = 0.0

	# Prepare animated bird frames (wing up/mid/down)
	bird_frames = []
	for i in range(3):
		frame_path = os.path.join(assets_dir, f"bird_{i}.png")
		if not os.path.exists(frame_path):
			# draw a simple bird frame with wing position varying by i
			surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
			surf.fill((0, 0, 0, 0))
			# body
			pygame.draw.ellipse(surf, (255, 230, 80), (0, 0, bw, bh))
			# wing polygon - positions change per frame
			if i == 0:
				wing = [(int(bw*0.2), int(bh*0.5)), (int(bw*0.5), int(bh*0.15)), (int(bw*0.7), int(bh*0.35))]
			elif i == 1:
				wing = [(int(bw*0.2), int(bh*0.55)), (int(bw*0.5), int(bh*0.3)), (int(bw*0.7), int(bh*0.45))]
			else:
				wing = [(int(bw*0.2), int(bh*0.6)), (int(bw*0.5), int(bh*0.45)), (int(bw*0.7), int(bh*0.6))]
			pygame.draw.polygon(surf, (240, 200, 60), wing)
			# eye
			pygame.draw.circle(surf, (30, 30, 30), (int(bw * 0.65), int(bh * 0.35)), 3)
			# beak
			pygame.draw.polygon(surf, (255, 150, 40), [(int(bw*0.9), int(bh*0.45)), (bw+2, int(bh*0.3)), (bw+2, int(bh*0.6))])
			try:
				pygame.image.save(surf, frame_path)
			except Exception:
				# ignore save errors; we'll keep surf in memory
				pass
		# load frame (or use generated surf if saving failed)
		try:
			frame = pygame.image.load(frame_path).convert_alpha()
		except Exception:
			# fallback to an in-memory surface if available
			frame = None
		bird_frames.append(frame)

	# If frames failed to load, create them in-memory
	if all(f is None for f in bird_frames):
		bird_frames = []
		for i in range(3):
			surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
			surf.fill((0,0,0,0))
			pygame.draw.ellipse(surf, (255,230,80), (0,0,bw,bh))
			if i == 0:
				wing = [(int(bw*0.2), int(bh*0.5)), (int(bw*0.5), int(bh*0.15)), (int(bw*0.7), int(bh*0.35))]
			elif i == 1:
				wing = [(int(bw*0.2), int(bh*0.55)), (int(bw*0.5), int(bh*0.3)), (int(bw*0.7), int(bh*0.45))]
			else:
				wing = [(int(bw*0.2), int(bh*0.6)), (int(bw*0.5), int(bh*0.45)), (int(bw*0.7), int(bh*0.6))]
			pygame.draw.polygon(surf, (240,200,60), wing)
			pygame.draw.circle(surf, (30,30,30), (int(bw * 0.65), int(bh * 0.35)), 3)
			pygame.draw.polygon(surf, (255,150,40), [(int(bw*0.9), int(bh*0.45)), (bw+2, int(bh*0.3)), (bw+2, int(bh*0.6))])
			bird_frames.append(surf)

	# animation state
	frame_idx = 0
	frame_timer = 0


	score = 0
	pipes = []
	last_spawn = pygame.time.get_ticks()

	playing = True
	game_over = False

	while True:
		dt = clock.tick(FPS)
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_SPACE:
					if playing and not game_over:
						vy = FLAP_STRENGTH
					elif game_over:
						# restart
						bird.x, bird.y = 80, HEIGHT // 2 - bh // 2
						vy = 0.0
						pipes.clear()
						score = 0
						last_spawn = pygame.time.get_ticks()
						game_over = False
				if event.key == pygame.K_ESCAPE:
					pygame.quit()
					sys.exit()

		if not game_over:
			# physics
			vy += GRAVITY
			bird.y += int(vy)

			# spawn pipes
			now = pygame.time.get_ticks()
			if now - last_spawn > SPAWN_INTERVAL_MS:
				last_spawn = now
				pipes.append(make_pipe(WIDTH))

			# move pipes
			for p in pipes:
				p["x"] -= PIPE_SPEED
				p["top"].x = p["x"]
				p["bottom"].x = p["x"]

				# score when bird passes pipe
				if not p["passed"] and p["x"] + PIPE_WIDTH < bird.x:
					p["passed"] = True
					score += 1

			# remove off-screen
			pipes = [p for p in pipes if p["x"] + PIPE_WIDTH > -50]

			# collisions
			if bird.top <= 0 or bird.bottom >= HEIGHT:
				game_over = True
			for p in pipes:
				if bird.colliderect(p["top"]) or bird.colliderect(p["bottom"]):
					game_over = True

		# draw
		screen.fill((64, 192, 255))

		# ground
		pygame.draw.rect(screen, (80, 200, 120), (0, HEIGHT - 40, WIDTH, 40))

		# pipes
		for p in pipes:
			pygame.draw.rect(screen, (34, 139, 34), p["top"]) 
			pygame.draw.rect(screen, (34, 139, 34), p["bottom"]) 

		# bird (animated frames if available)
		if bird_frames:
			# advance animation timer
			frame_timer += dt
			if frame_timer > 100:
				frame_timer = 0
				frame_idx = (frame_idx + 1) % len(bird_frames)
			frame = bird_frames[frame_idx]
			# rotate slightly based on vertical speed
			angle = max(-30, min(30, -vy * 3))
			if frame:
				img = pygame.transform.rotozoom(frame, angle, bird.width / frame.get_width())
				rect_img = img.get_rect(center=bird.center)
				screen.blit(img, rect_img.topleft)
			else:
				pygame.draw.ellipse(screen, (255, 230, 80), bird)
		else:
			pygame.draw.ellipse(screen, (255, 230, 80), bird)

		# score
		score_surf = font.render(str(score), True, (255, 255, 255))
		screen.blit(score_surf, (WIDTH//2 - score_surf.get_width()//2, 20))

		if game_over:
			over = font.render("Game Over", True, (200, 50, 50))
			screen.blit(over, (WIDTH//2 - over.get_width()//2, HEIGHT//2 - 40))
			hint = small.render("Press Space to restart", True, (255,255,255))
			screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT//2 + 10))

		pygame.display.flip()


if __name__ == "__main__":
	main()




