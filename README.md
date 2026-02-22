# Undead_Corridor
A fast-paced, procedural 2.5D raycasting FPS inspired by classic DOOM. Built from scratch in Python &amp; Pygame, featuring dynamic AI, scaling difficulty, ultimate abilities, and persistent SQLite leaderboards💀 Undead Corridor

Undead Corridor is a fast-paced, retro-style 2.5D First-Person Shooter inspired by classic DOOM and dark gothic fantasy. Built entirely from scratch using Python and Pygame, the game utilizes complex raycasting mathematics to render a pseudo-3D world out of a 2D grid.

Players must blast their way through 5 levels of procedurally generated dungeons, managing health, armor, and an energy-based ultimate ability while fighting off a roster of demonic enemies and bosses.

✨ Key Features

Custom Raycasting Engine: A fully functional 2.5D rendering pipeline using Pygame and Numpy, complete with textured walls, sprite depth-sorting, and a dynamic minimap.

Procedural Dungeon Generation: No two playthroughs are the same. Maps, enemy spawn locations, and loot drops are procedurally generated every level, with algorithms ensuring safe starting zones and epic, far-corner boss placements.

Dynamic, "Smart" AI: Enemies don't just hit harder on higher difficulties—they think faster. AI reaction times scale with difficulty, alongside specialized enemy behaviors like lunging attacks and AoE ground slams.

Arsenal & Ultimate System: Swap between 4 distinct weapons, and build up an Energy meter via kills to unleash a devastating screen-clearing 'Energy Cannon' blast.

Persistent Level Leaderboards: A fully integrated SQLite database tracks your high scores across all 5 levels, displayed in a polished, mouse-scrollable UI menu.

Adaptive UI: A highly polished, responsive menu system that dynamically scales fonts, buttons, and backgrounds perfectly to any monitor resolution.

🛠️ Tech Stack

Language: Python 3.x

Rendering & Input: Pygame

Math & Optimization: Numpy

Database: SQLite (Built-in)

Build Tool: PyInstaller
