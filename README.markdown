# Coin Frenzy 3D

## Overview
Coin Frenzy 3D is a first-person shooter game developed using Python and OpenGL (PyOpenGL with GLUT). Players navigate a 3D arena, collecting coins, shooting enemies, and avoiding damage to survive and progress through levels. The game features a simple yet engaging gameplay loop with player movement, shooting mechanics, enemy AI, and coin collection with an optional magnet power-up.

## Features
- **Player Mechanics**: Move using WASD keys, rotate view with Q/E keys, and shoot bullets with the left mouse button.
- **Enemies**: Enemies spawn at the arena's perimeter and pursue the player when within detection range or patrol randomly otherwise.
- **Coins**: Collect coins to increase your score. Activate the magnet (M key) to attract coins within a certain range.
- **Levels**: Progress through levels by collecting all coins. Each level increases the number of coins and enemies.
- **Health and Lives**: Players start with 100 health and 3 lives. Enemies deal contact damage, and lives are depleted when health reaches zero.
- **Cheat Mode**: Toggle invincibility with the C key for testing or casual play.
- **Pause and Reset**: Pause the game with P and reset with R.
- **Camera Nudge**: Use arrow keys to slightly adjust the camera for better viewing.

## Requirements
- Python 3.x
- PyOpenGL
- PyOpenGL_accelerate (optional, for better performance)
- OpenGL-compatible graphics driver
- GLUT (FreeGLUT recommended)

Install dependencies using pip:
```bash
pip install PyOpenGL PyOpenGL_accelerate
```

## How to Run
1. Ensure all dependencies are installed.
2. Save the project code as `proj.py`.
3. Run the script:
   ```bash
   python proj.py
   ```
4. The game window (1200x800) will open, and the game will start immediately.

## Controls
- **WASD**: Move forward, backward, left, or right relative to the player's facing direction.
- **Q/E**: Rotate the player's view left or right.
- **Left Mouse Button**: Shoot a bullet in the facing direction.
- **M**: Toggle magnet to attract coins.
- **C**: Toggle cheat mode (invincibility).
- **P**: Pause/unpause the game.
- **R**: Reset the game to the initial state.
- **Arrow Keys**: Nudge the camera slightly for better visibility.
- **Esc**: Exit the game.

## Game Elements
- **Player**: A humanoid model with a body, head, hands, legs, and a pistol. Starts at the center of the arena with 100 health and 3 lives.
- **Enemies**: Red spherical enemies with a black cube head. They spawn at the arena's edges, deal 15 damage on contact, and can be killed with bullets (20 points each).
- **Coins**: Yellow torus-shaped coins worth 10 points each. Collect all coins to advance to the next level.
- **Bullets**: Small white spheres fired from the player's pistol, traveling straight until they hit an enemy or a wall.
- **Arena**: A square 120x120 unit area with a green floor and grey walls (6 units high). The player and enemies are confined within this area.

## Technical Details
- **Language**: Python with PyOpenGL and GLUT.
- **Graphics**: Uses OpenGL for 3D rendering, including GLUT's built-in shapes (cubes, spheres, cones, torus) for entities.
- **Physics**: Simple sphere-based collision detection for player-enemy, bullet-enemy, and player-coin interactions.
- **Camera**: Third-person perspective positioned behind and above the player, with a 60-degree FOV and slight nudge adjustments via arrow keys.
- **Update Loop**: Frame-rate independent updates using delta time (`dt`) clamped between 0 and 0.05 seconds for stability.
- **Coordinate System**: X/Z plane for movement, Y for height. Forward is along -Z by default.

## Gameplay Tips
- Use the magnet (M) strategically to collect coins faster, but beware of enemies closing in.
- Keep moving to avoid enemy contact, especially in higher levels with more enemies.
- Aim carefully with bullets, as they have a limited lifespan (2.5 seconds) and range.
- Use cheat mode (C) to explore levels without risk or for debugging.
- Adjust the camera with arrow keys to get a better view of the arena.

## Known Limitations
- No sound or advanced lighting effects due to simplicity focus.
- Enemy AI is basic (seek or patrol), which may feel predictable.
- Performance may vary on lower-end systems due to OpenGL rendering.
- No save/load functionality; progress resets on game restart.

## Future Improvements
- Add sound effects and background music.
- Implement more complex enemy AI (e.g., pathfinding or group tactics).
- Introduce power-ups beyond the magnet (e.g., speed boost, health restore).
- Add a main menu and game-over screen for better UX.
- Optimize rendering for better performance on low-end hardware.

## License
This project is for educational purposes and provided as-is. Feel free to modify or extend it for non-commercial use.