# 🧟 ZOMBIE SHOOTER: King of the Fallen

A 3D OpenGL-based action survival game where you fight off waves of zombies and confront the ultimate evil: the **Final Boss - The Witch of the Fallen**. Gather weapons, collect ammo, survive lava traps, and unleash your fury with pistol, rifle, and knife.

---

## 🎮 How to Play

### 🔥 Objective

* Survive waves of zombies.
* Collect ammo and invincibility shields.
* Defeat the **Final Boss** after reaching a score of **30**.
* Don’t die. You only have **5 lives**!

---

## 🕹️ Controls

### 🧍 Player Movement

| Key   | Action        |
| ----- | ------------- |
| **W** | Move Forward  |
| **S** | Move Backward |
| **A** | Rotate Left   |
| **D** | Rotate Right  |

### 🔫 Weapon & Combat

| Key / Mouse                    | Action                                            |
| ------------------------------ | ------------------------------------------------- |
| **Spacebar** or **Left Click** | Fire (pistol or rifle) / Slash (knife)            |
| **1**                          | Switch to Pistol                                  |
| **2**                          | Switch to Rifle                                   |
| **3**                          | Switch to Knife                                   |
| **R**                          | Reload Ammo (Refills pistol and rifle to 30 each) |
| **Right Click**                | Toggle First-Person View                          |

### 🎥 Camera Controls (Third-Person Only)

| Key                  | Action               |
| -------------------- | -------------------- |
| **Arrow Up/Down**    | Zoom In/Out          |
| **Arrow Left/Right** | Rotate Around Player |

### 🧩 Menu & Game State

| Key   | Action                                          |
| ----- | ----------------------------------------------- |
| **K** | Start Game from Main Menu                       |
| **7** | Cycle Difficulty (EASY → MEDIUM → HARD)         |
| **H** | Pause / Resume                                  |
| **P** | Return to Menu from Pause                       |
| **R** | Return to Menu from Game Over or Victory screen |

---

## 🧱 Game Elements

### Weapons

* **Pistol:** Medium damage, 30 bullets.
* **Rifle:** High damage, 30 bullets.
* **Knife:** Infinite melee damage.

### Power-Ups

* **Ammo Pickup:** Yellow or pink spheres replenish pistol/rifle ammo.
* **Invincibility Shield:** Blue cylinders give temporary invulnerability.

### Hazards

* **Lava Pools:** Instantly damage and respawn player.
* **Zombies:** Hurt you on contact.
* **Final Boss Laser:** Deadly beam attack in Final Boss mode.

---

## 👹 Final Boss: Witch of the Fallen

* Unleashed when your **score reaches 30+**.
* Casts **laser beam attacks** and **teleports** (in higher difficulties).
* Defeat her to **win** the game.

---

## 🧩 Game States

* **MENU:** Navigate game settings.
* **PLAYING:** Main gameplay mode.
* **PAUSED:** Freeze the game (H to resume).
* **FINAL\_BOSS:** Intense boss arena battle.
* **GAME\_OVER:** Player has no lives left.
* **WIN:** Final Boss defeated.

---

## 🧠 Difficulty Settings

| Difficulty | Zombies | Enemy Speed | Boss HP | Boss Attack Rate       |
| ---------- | ------- | ----------- | ------- | ---------------------- |
| EASY       | 3       | 0.6         | 100     | Slow                   |
| MEDIUM     | 5       | 0.8         | 150     | Moderate               |
| HARD       | 7       | 1.0         | 200     | Fast, Teleporting Boss |

---

## 🛠️ Requirements

* Python 3.x
* PyOpenGL
* GLUT (e.g., FreeGLUT)

Install via pip:

```bash
pip install PyOpenGL PyOpenGL_accelerate
```

---

## 🧑‍💻 Run the Game

```bash
python "ZOMBIE SHOOTER_King of the Fallen.py"
```


