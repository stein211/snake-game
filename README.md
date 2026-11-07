# Snake

A polished, well-structured Snake game in Python + pygame.

## Run (with uv)

```bash
uv sync                 # creates .venv and installs pygame + pytest from uv.lock
uv run main.py          # start the game
uv run pytest           # run the test suite
```

Plain pip also works: `pip install -r requirements.txt && python main.py`.

**Controls:** Arrows / WASD to move · P or Esc to pause · Enter / click to select · R to retry on the results screen.

## Features

- Smooth movement: the snake is interpolated between logic ticks, so it glides at any FPS
- Gradient snake with eyes, soft shadow and highlight; glowing apples; spinning golden star bonus (+5) with a countdown ring
- Particles, floating "+1" text, screen shake on crash, level-up banner
- Two modes: **Classic** (walls kill) and **No Walls** (wrap-around)
- Speed increases every level; buffered input so fast turns are never lost
- High scores saved per mode to `~/.snake_game/highscores.json` (override with `SNAKE_DATA_DIR`)

## Architecture

```
snake/
├── core/            # Pure game model: no pygame, fully unit-tested
│   ├── geometry.py  #   Point, Direction
│   ├── snake.py     #   Snake: body, buffered turns, growth
│   ├── food.py      #   Food, FoodKind, Spawner protocol + RandomSpawner
│   └── world.py     #   World: rules, tick(), emits GameEvent list
├── ui/              # Presentation (pygame)
│   ├── drawing.py   #   fonts, AA shapes, glow, blur, panels
│   ├── board.py     #   BoardRenderer: board, food, interpolated snake
│   ├── hud.py       #   score / best / level cards
│   ├── widgets.py   #   ButtonMenu (keyboard + mouse)
│   └── effects.py   #   particles, floating text, screen shake
├── scenes/          # One class per screen, common Scene interface
│   ├── menu.py · play.py · game_over.py
├── config.py        # Settings + Theme (frozen dataclasses)
├── persistence.py   # HighScoreStore
└── app.py           # Window, main loop, scene navigation
```

Design principles:

- **Model / view separation.** `core` knows nothing about pygame, so the rules can be tested in isolation.
- **Events, not callbacks.** `World.tick()` returns `GameEvent`s; the play scene turns them into particles, shake, and text. The rules never reference the UI.
- **Dependency injection.** The food `Spawner` is a protocol, and tests inject a scripted one for deterministic results.
- **Fixed timestep.** Logic runs at a level-dependent tick rate, separate from the render frame rate.
- **Acyclic scene graph.** Scenes never import each other. They call `app.start_game()`, `app.show_menu()`, etc.
- **Theming in one place.** Every color lives in `Theme`, so you can reskin the game without touching rendering code.
