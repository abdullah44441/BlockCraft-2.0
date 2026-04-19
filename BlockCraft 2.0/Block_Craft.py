from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from perlin_noise import PerlinNoise as noise
import random
import math

app = Ursina()

# ---------------- WINDOW ----------------
window.exit_button.enabled = False
window.fps_counter.enabled = True
window.collider_counter.enabled = False
window.entity_counter.enabled = False
window.title = "Block Craft 1.0"

# ---------------- WORLD ----------------
CHUNK_SIZE = 10
CHUNK_HEIGHT = 6
render_distance = 1

pnoise = noise(octaves=1, seed=random.randint(0, 100))

# ---------------- CHUNKS ----------------
chunks = {}
chunk_loading = set()
chunk_queue = []

# ---------------- TEXTURES ----------------
grass_block = load_texture('Grass.png')
dirt_block = load_texture('dirt.jpg')
stone_block = load_texture('stone.jpg')
wood_block = load_texture('wood.jpg')
Bedrock_block = load_texture('bedrock.png')

Placable_blocks = wood_block


# ---------------- CHUNK GENERATION ----------------
def generate_chunk(cx, cz):

    if (cx, cz) in chunks:
        return

    chunk_blocks = {}

    for z in range(CHUNK_SIZE):
        for x in range(CHUNK_SIZE):

            world_x = cx * CHUNK_SIZE + x
            world_z = cz * CHUNK_SIZE + z

            height = math.floor((pnoise([world_x/30, world_z/30]) + 1) * (CHUNK_HEIGHT / 2)) + 1

            for y in range(height):

                # 🌍 layer system
                if y == 0:
                    texture = Bedrock_block
                elif y < 0.3 * height:
                    texture = stone_block
                elif y < height - 1:
                    texture = dirt_block
                else:
                    texture = grass_block

                block = Entity(
                    model='cube',
                    position=(world_x, y, world_z),
                    texture=texture,
                    collider='box',
                )

                # 🛑 mark bedrock as unbreakable
                if y == 0:
                    block.unbreakable = True

                chunk_blocks[(world_x, y, world_z)] = block

    chunks[(cx, cz)] = chunk_blocks
    chunk_loading.discard((cx, cz))


# ---------------- CHUNK SYSTEM ----------------
def update_chunks():

    pcx = int(player.x // CHUNK_SIZE)
    pcz = int(player.z // CHUNK_SIZE)

    for x in range(pcx - render_distance, pcx + render_distance + 1):
        for z in range(pcz - render_distance, pcz + render_distance + 1):

            if (x, z) not in chunks and (x, z) not in chunk_loading:
                chunk_loading.add((x, z))
                chunk_queue.append((x, z))

    if chunk_queue:
        cx, cz = chunk_queue.pop(0)
        generate_chunk(cx, cz)

    for (cx, cz) in list(chunks.keys()):
        if abs(cx - pcx) > render_distance or abs(cz - pcz) > render_distance:
            for b in chunks[(cx, cz)].values():
                destroy(b)
            del chunks[(cx, cz)]


# ---------------- UPDATE ----------------
def update():
    global Placable_blocks

    if held_keys['escape']:
        application.quit()

    # sprint
    player.speed = 8 if held_keys['shift'] else 5

    # crouch
    if held_keys['control']:
        player.height = 1
        player.camera_pivot.y = lerp(player.camera_pivot.y, 0.5, time.dt * 10)
    else:
        player.height = 2
        player.camera_pivot.y = lerp(player.camera_pivot.y, 2, time.dt * 10)

    # safety fall reset
    if player.y < -10:
        player.y = 10

    # block select
    if held_keys['1']:
        Placable_blocks = stone_block
    if held_keys['2']:
        Placable_blocks = dirt_block
    if held_keys['3']:
        Placable_blocks = grass_block
    if held_keys['4']:
        Placable_blocks = wood_block

    update_chunks()


# ---------------- INPUT ----------------
def input(key):

    # PLACE BLOCK
    if key == 'right mouse up':
        hit = raycast(camera.world_position, camera.forward, distance=5)

        if hit.hit:
            pos = hit.entity.position + hit.normal

            if distance(pos, player.position) > 1.5:
                Entity(
                    model='cube',
                    position=pos,
                    texture=Placable_blocks,
                    collider='box',
                )

    # BREAK BLOCK
    if key == 'left mouse up':
        hit = raycast(camera.world_position, camera.forward, distance=5)

        if hit.hit:

            # 🛑 prevent bedrock breaking
            if hasattr(hit.entity, "unbreakable") and hit.entity.unbreakable:
                return

            destroy(hit.entity)


# ---------------- PLAYER ----------------
player = FirstPersonController()
player.y = 10

player.gravity = 1.5
player.jump_height = 2.2
player.speed = 5

Sky()

app.run()