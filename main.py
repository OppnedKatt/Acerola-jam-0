import json
import os
import sys
from array import array
from math import ceil, copysign, cos, floor, radians, sin, sqrt
from random import randint, seed
from time import time

import glcontext
import moderngl
import pygame

import asset_handler
from entity import Entity
from player import Player
from spitwar import Fireball
from world import World

os.chdir(os.path.dirname(__file__))

pygame.init()
pygame.display.set_icon(asset_handler.get_texture('tech', 'big_sword.png'))

seed(1)

clock = pygame.time.Clock()
fps = 60

# screen = pygame.display.set_mode((1280, 720), pygame.OPENGL | pygame.DOUBLEBUF)
# screen = pygame.display.set_mode((960, 540), pygame.OPENGL | pygame.DOUBLEBUF)
screen = pygame.display.set_mode((0, 0), pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN)
display = pygame.Surface(screen.get_size())
display.fill((70, 50, 180))

ctx = moderngl.create_context()

def surf_to_texture(surf: pygame.Surface):
    tex = ctx.texture(surf.get_size(), 4)
    tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
    tex.swizzle = 'BGRA'
    tex.write(surf.get_view('1'))
    return tex

def redraw_texture(tex: moderngl.Context.texture, surf: pygame.Surface):
    tex.write(surf.get_view('1'))

quad_buffer = ctx.buffer(data=array('f', [
    -1.0, 1.0, 0.0, 0.0,
    1.0, 1.0, 1.0, 0.0,
    -1.0, -1.0, 0.0, 1.0,
    1.0, -1.0, 1.0, 1.0
]))
with open('vert_shader.glsl', 'r') as f:
    vert_shader = f.read()
with open('frag_shader.glsl', 'r') as f:
    frag_shader = f.read()
program = ctx.program(vertex_shader=vert_shader, fragment_shader=frag_shader)
render_object = ctx.vertex_array(program, [(quad_buffer, '2f 2f', 'vert', 'texcoord')])
program['awake'] = True
program['vertRat'] = screen.get_height() / screen.get_width()
program['screenSize'] = screen.get_size()

display_tex = surf_to_texture(display)
display_tex.use(0)
program['tex'] = 0

field_tex = surf_to_texture(asset_handler.get_texture('tech', 'field.png'))
field_tex.use(1)
program['field'] = 1

stars1_tex = surf_to_texture(asset_handler.get_texture('tech', 'stars1.png'))
stars1_tex.use(2)
program['stars1'] = 2

stars2_tex = surf_to_texture(asset_handler.get_texture('tech', 'stars2.png'))
stars2_tex.use(3)
program['stars2'] = 3

noise = asset_handler.get_texture('tech', 'noise1.png')
noise_surf = pygame.Surface(noise.get_size())
noise_surf.blit(noise, (0, 0))
noise_tex = surf_to_texture(noise_surf)
noise_tex.use(4)
program['noise'] = 4

world = World('map')
Entity.default_world = world
player = Player()
player.health = 5
Entity.player = player
player.colour = (150, 30, 170)
dream_player = Player()
dream_player.health = 5
dream_player.dreamer = True
Entity.other_world_player = dream_player
dream_player.colour = (210, 180, 10)
awake = True
world.player = player
world.dream_player = dream_player
PIXELS_IN_TILE = 16
PIXELS_IN_CHUNK = world.CHUNK_SIZE * PIXELS_IN_TILE
offset = [-9.5, -10]
offset_vel = [0, 0]
OFFSET_ACCEL = 18
OFFSET_DEACCEL = 16
EDGE_CLOSNESS = 0.8

r = 16
view_circle = set()
for y in range(-r, r + 1):
    for x in range(-r, r + 1):
        if (player.pos[0] - x)**2 + (player.pos[1] - y)**2 <= r**2:
            world.seen_blocks.add((x, y))
            view_circle.add((x, y))
for y in range(-r, r + 1):  #NOTE: Just included the blocks above to the view_circle to make sure everything is filled
    for x in range(-r, r + 1):
        if abs(sqrt((player.pos[0] - x)**2 + (player.pos[1] - y)**2) - r) < 1:
            view_circle.add((x, y))
world.seen_blocks.update((player.pos[0] + x, player.pos[1] + y) for x, y in view_circle)

sword_swinging = False
swinging_start = time()
swing_length = 0.2
other_way = False
swing_window = (0.7, 2.5)
hit_entities = []
original_sword_surf = asset_handler.get_texture('tech', 'sword.png')

def set_zoom(tiles: int | float):
    if tiles < 8:
        return
    global tiles_horizontally
    tiles_horizontally = tiles
    global grid_size
    grid_size = screen.get_width() / tiles_horizontally

    global top_left_chunk
    top_left_chunk = (floor(offset[0] / world.CHUNK_SIZE) - world.chunk_padding, floor(offset[1] / world.CHUNK_SIZE) - world.chunk_padding)
    global convert_chunk_pos
    convert_chunk_pos = lambda pos: tuple(map(int, pos.split('.')))
    global world_canvas
    world_canvas = pygame.Surface((
        (ceil(tiles_horizontally / world.CHUNK_SIZE) + 2*world.chunk_padding) * PIXELS_IN_CHUNK,
        (ceil((tiles_horizontally / world.CHUNK_SIZE) * (screen.get_height() / screen.get_width())) + 2*world.chunk_padding) * PIXELS_IN_CHUNK
    ))
    # world_canvas.fill((240, 230, 230))  #DEBUG
    global draw_section
    draw_section = pygame.Surface((
        ceil(tiles_horizontally) * PIXELS_IN_TILE + 2,
        ceil(tiles_horizontally * screen.get_height() / screen.get_width()) * PIXELS_IN_TILE + 2
    ))
    # world_canvas.fill((230, 220, 220))  #DEBUG
    world_canvas.fill((0, 0, 0))
    for chunk in world.loaded_chunks.keys():
        draw_chunk(chunk)
    global health_edge
    health_edge = grid_size * 2 / PIXELS_IN_TILE
    
    global sword_surf
    sword_surf = pygame.transform.scale(original_sword_surf, (
        floor(1.5 * grid_size), floor(1.5 * grid_size)
    ))
set_zoom(20)

def draw_chunk(chunk: tuple[int, int]):
    chunk_head = (
        (chunk[0] - top_left_chunk[0])*PIXELS_IN_CHUNK,
        (top_left_chunk[1] - chunk[1] + 2*world.chunk_padding)*PIXELS_IN_CHUNK
    )
    """ print(top_left_chunk[1] - chunk[1], top_left_chunk[1], chunk[1])
    print(chunk_head) """
    # pygame.draw.rect(  #DEBUG
    #     world_canvas, (randint(100, 255), randint(100, 255), randint(100, 255)),
    #     pygame.Rect(*chunk_head, PIXELS_IN_CHUNK, PIXELS_IN_CHUNK)
    # )
    # if chunk == (0, 0):
    #     """ print(chunk_head)
    #     print(chunk[0] - top_left_chunk[0], top_left_chunk[1] - chunk[1] + 2*world.chunk_padding)
    #     print(chunk, top_left_chunk) """
    #     pygame.draw.rect(  #DEBUG
    #         world_canvas, (250, 0, 0),
    #         pygame.Rect(*chunk_head, PIXELS_IN_CHUNK, PIXELS_IN_CHUNK)
    #     )
    chunk_data = world.get_chunk(chunk)
    layers = sorted(chunk_data['layers'].keys())
    for layer in layers:
        layer_data = chunk_data['layers'][layer]
        if layer_data['type'] == 'single':
            for block_pos, block_data in layer_data['data'].items():
                block_pos = convert_chunk_pos(block_pos)
                block_head = (
                    (block_pos[0] - chunk[0]*world.CHUNK_SIZE)*PIXELS_IN_TILE + chunk_head[0],
                    (15 - block_pos[1] + chunk[1]*world.CHUNK_SIZE)*PIXELS_IN_TILE + chunk_head[1]
                )
                world_canvas.blit(asset_handler.get_block_texture(json.dumps(block_data)), block_head)

        elif layer_data['type'] == 'uniform':
            block_texture = asset_handler.get_block_texture(json.dumps(tuple(layer_data['data'].values())[0]))
            for y in range(16):
                for x in range(16):
                    block_head = (
                        x*PIXELS_IN_TILE + chunk_head[0],
                        y*PIXELS_IN_TILE + chunk_head[1]
                    )
                    world_canvas.blit(block_texture, block_head)
    
    if awake:
        return
    for cy, y in zip(
        range(chunk_head[1], chunk_head[1] + PIXELS_IN_CHUNK, PIXELS_IN_TILE),
        range(
            chunk[1] * world.CHUNK_SIZE,
            (chunk[1] - 1) * world.CHUNK_SIZE,
            -1
        )
    ):
        for cx, x in zip(
            range(chunk_head[0], chunk_head[0] + PIXELS_IN_CHUNK, PIXELS_IN_TILE),
            range(
                chunk[0] * world.CHUNK_SIZE,
                (chunk[0] + 1) * world.CHUNK_SIZE
            )
        ):
            if (x, y+world.CHUNK_SIZE-1) in world.seen_blocks:
                continue
            pygame.draw.rect(
                world_canvas, (255, 0, 0),
                pygame.Rect(cx, cy, PIXELS_IN_TILE, PIXELS_IN_TILE)
            )

empty_heart = asset_handler.get_texture('tech', 'empty_heart.png')
filled_heart = asset_handler.get_texture('tech', 'filled_heart.png')
def draw_hearts():
    hor = 2 * screen.get_width() // 7
    heart_hor = max(32, ((hor // 8) // 8) * 8)
    hearts_per_row = hor // heart_hor
    rows = ceil(Entity.player.max_health / hearts_per_row)
    empty_heart_scaled = pygame.transform.scale(empty_heart, (heart_hor, heart_hor))
    filled_heart_scaled = pygame.transform.scale(filled_heart, (heart_hor, heart_hor))
    global hearts
    hearts = pygame.Surface((hor, heart_hor*rows)).convert_alpha()
    hearts.fill((0, 0, 0, 0))
    for heart in range(Entity.player.max_health):
        x = heart % hearts_per_row
        y = heart // hearts_per_row
        hearts.blit(
            filled_heart_scaled if heart < Entity.player.health else empty_heart_scaled,
            (x*heart_hor, y*heart_hor)
        )
player.heart_drawer = draw_hearts
dream_player.heart_drawer = draw_hearts
draw_hearts()

last_change = time()
def go_to_dream(*_):
    global in_death_scene
    global awake
    if not awake:
        return
    awake = False
    program['awake'] = awake
    Entity.awake = False
    Entity.player, Entity.other_world_player = Entity.other_world_player, Entity.player
    Entity.entities, Entity.other_world_entities = Entity.dream_entities, Entity.normal_entities
    if not in_death_scene:
        dream_player.pos = player.pos
        dream_player.health = player.health
    else:
        global offset
        global offset_vel
        offset = [-9.5, -10]
        offset_vel = [0, 0]
        global no_control
        no_control = False
    global last_change
    diff = time() - last_change
    for entity in Entity.entities:
        entity.real_last_move += diff
        entity.last_move = entity.real_last_move
    world_canvas.fill((0, 0, 0))
    for chunk in world.loaded_chunks.keys():
        draw_chunk(chunk)
    last_change = time()
    in_death_scene = False
Player.go_to_dream = go_to_dream

def return_from_dream(*_):
    if dream_player.pos != player.pos:
        return
    global awake
    if awake:
        return
    player.health = dream_player.health
    Entity.awake = True
    awake = True
    program['awake'] = awake
    Entity.player, Entity.other_world_player = Entity.other_world_player, Entity.player
    Entity.entities, Entity.other_world_entities = Entity.normal_entities, Entity.dream_entities
    global last_change
    diff = time() - last_change
    for entity in Entity.entities:
        entity.real_last_move += diff
        entity.last_move = entity.real_last_move
    world_canvas.fill((0, 0, 0))
    for chunk in world.loaded_chunks.keys():
        draw_chunk(chunk)
    last_change = time()
    global no_control
    if hit_meet_scene and no_control:
        no_control = False
        global finished_start
        finished_start = True
Player.return_from_dream = return_from_dream

finished_start = False
no_control = False
hit_force_death = False
critical_death_elevation = 33
in_death_scene = False
death_scene_start = -1
hit_meet_scene = False
critical_meet_elevation = 30
meet_scene_start = -1
change_prompt = asset_handler.get_texture('tech', 'change_prompt.png')
change_prompt_width = screen.get_width() / 4
change_prompt = pygame.transform.scale(change_prompt, (
    change_prompt_width, change_prompt_width * change_prompt.get_height() / change_prompt.get_width()
))
hit_end = False
quit_prompt = asset_handler.get_texture('tech', 'quit_prompt.png')
quit_prompt_width = screen.get_width() / 4
quit_prompt = pygame.transform.scale(quit_prompt, (
    quit_prompt_width, quit_prompt_width * quit_prompt.get_height() / quit_prompt.get_width()
))

ease_in_out = lambda x: 2*x*x if x < 0.5 else (1 - (-2*x + 2)**2 / 2)

def restart(*_):
    start = time()
    display.fill((255, 0, 0))
    global prev_time
    dt = -prev_time + (prev_time := time())
    global t
    t += dt
    program['t'] = t
    redraw_texture(display_tex, display)
    render_object.render(mode=moderngl.TRIANGLE_STRIP)
    
    global offset
    offset = [-9.5, -10]
    global offset_vel
    offset_vel = [0, 0]

    global hit_entities
    hit_entities = []

    global world
    world = World('map')
    Entity.default_world = world
    global player
    player = Player()
    player.health = 5
    Entity.player = player
    player.colour = (150, 30, 170)
    global dream_player
    dream_player = Player()
    dream_player.health = 5
    dream_player.dreamer = True
    Entity.other_world_player = dream_player
    dream_player.colour = (210, 180, 10)
    global awake
    awake = True
    program['awake'] = awake
    world.player = player
    world.dream_player = dream_player
    player.heart_drawer = draw_hearts
    dream_player.heart_drawer = draw_hearts
    global walks
    walks = False
    draw_hearts()
    
    Entity.entities = []
    Entity.normal_entities = Entity.entities
    Entity.other_world_entities = []
    Entity.dream_entities = Entity.other_world_entities
    Entity.awake = True
    Entity.spawned_entities = []
    
    while time() - start < 6:
        dt = -prev_time + (prev_time := time())
        t += dt
        program['t'] = t
        redraw_texture(display_tex, display)
        render_object.render(mode=moderngl.TRIANGLE_STRIP)
        pygame.display.flip()
        clock.tick(fps)

walks = False
t = 0
prev_time = time()
while True:
    dt = -prev_time + (prev_time := time())
    
    if sword_swinging and time() - swinging_start > swing_length:
        sword_swinging = False
    
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if awake and event.key in (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d):
                world.seen_blocks.update((player.pos[0] + x, player.pos[1] + y) for x, y in view_circle)
            if not no_control:
                if event.key == pygame.K_w:
                    (player if awake else dream_player).move((0, 1, 0))
                    walks = True
                elif event.key == pygame.K_s:
                    (player if awake else dream_player).move((0, -1, 0))
                    walks = True
                elif event.key == pygame.K_a:
                    (player if awake else dream_player).move((-1, 0, 0))
                    walks = True
                elif event.key == pygame.K_d:
                    (player if awake else dream_player).move((1, 0, 0))
                    walks = True
            
            if event.key == pygame.K_SPACE and hit_force_death and not in_death_scene:
                go_to_dream() if awake else return_from_dream()
                draw_hearts()

            elif event.key == pygame.K_MINUS:
                set_zoom(tiles_horizontally + 0.5)
            elif event.key == pygame.K_PLUS:
                set_zoom(tiles_horizontally - 0.5)
            
            elif event.key == pygame.K_ESCAPE:
                print('fps:', clock.get_fps())
                pygame.quit()
                sys.exit(0)
        
        elif event.type == pygame.KEYUP:
            if walks:
                walks = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == pygame.BUTTON_LEFT:
                in_switch_window = swing_window[0] < (time() - swinging_start) / swing_length < swing_window[1]
                if in_switch_window and not other_way:
                    sword_swinging = True
                    swinging_start = time()
                    other_way = True
                    hit_entities = []
                    continue
                elif not in_switch_window and sword_swinging:
                    continue
                sword_swinging = True
                swinging_start = time()
                other_way = False
                hit_entities = []

        elif event.type == pygame.QUIT:
            print('fps:', clock.get_fps())
            pygame.quit()
            sys.exit(0)

    if not no_control:
        just_moved = True
        if pygame.key.get_pressed()[pygame.K_w] and time() - Entity.player.real_last_move >= Entity.player.move_speed:
            Entity.player.move((0, 1, 0))
        elif pygame.key.get_pressed()[pygame.K_a] and time() - Entity.player.real_last_move >= Entity.player.move_speed:
            Entity.player.move((-1, 0, 0))
        elif pygame.key.get_pressed()[pygame.K_s] and time() - Entity.player.real_last_move >= Entity.player.move_speed:
            Entity.player.move((0, -1, 0))
        elif pygame.key.get_pressed()[pygame.K_d] and time() - Entity.player.real_last_move >= Entity.player.move_speed:
            Entity.player.move((1, 0, 0))
        else:
            just_moved = False
        if just_moved:
            world.seen_blocks.update((player.pos[0] + x, player.pos[1] + y) for x, y in view_circle)

    if not hit_force_death or in_death_scene:
        offset[1] = min(offset[1], 22)
    if not hit_force_death and player.pos[1] >= critical_death_elevation:
        hit_force_death = True
        in_death_scene = True
        no_control = True
        death_scene_start = time()
        Entity.entities.append(Fireball(world=world, pos=[player.pos[0], 41, 1], dir=(0, -1, 0)))
        Entity.entities[-1].insta_kill = True
        Entity.entities[-1].life = 30
        Entity.entities[-1].real_last_move += 1.5
    if in_death_scene and time() - death_scene_start > 10:  #NOTE: Failsafe
        player.damage(player.health)
    # if in_death_scene and tiles_horizontally != 10:  #NOTE: Too laggy?
    #     set_zoom(20 - 10*min(1, max(0, (time() - death_scene_start) / 2)))
    if hit_force_death and not in_death_scene and not hit_meet_scene and dream_player.pos[1] >= critical_meet_elevation:
        hit_meet_scene = True
        no_control = True
        meet_scene_start = time()
    if not finished_start and hit_meet_scene and player.pos != dream_player.pos and time() - meet_scene_start > 0.8:
        dx = player.pos[0] - dream_player.pos[0]
        dy = player.pos[1] - dream_player.pos[1]
        dst = (
            min(1, max(-1, dx)) if abs(dx) >= abs(dy) else 0,
            min(1, max(-1, dy)) if abs(dy) > abs(dx) else 0,
            0
        )
        if dream_player.illegal_pos(dream_player.if_moved(dst)):
            dream_player.pos = player.pos  #NOTE: Failsafe - Will happen if both players are to the right in the meet scene
        else:
            dream_player.move(dst)
        meet_scene_start = time()
    if not hit_end and Entity.player.pos[0] <= -184:
        hit_end = True
        hit_end_time = time()

    target_pos = player.pos if awake else dream_player.pos
    hor_overflow = max(0, abs(offset[0] + tiles_horizontally/2 - target_pos[0]) / (tiles_horizontally/2) - 1 + EDGE_CLOSNESS)
    ver_overflow = max(0, abs(offset[1] + world.CHUNK_SIZE - 0.5 - tiles_horizontally/2 * (screen.get_height() / screen.get_width()) - target_pos[1]) / (tiles_horizontally/2 * (screen.get_height() / screen.get_width())) - 1 + EDGE_CLOSNESS)
    hor_sign = copysign(1, offset[0] + tiles_horizontally/2 - target_pos[0]) * -1
    ver_sign = copysign(1, offset[1] + world.CHUNK_SIZE - 0.5 - tiles_horizontally/2 * (screen.get_height() / screen.get_width()) - target_pos[1]) * -1
    if hor_overflow:
        offset_vel[0] += hor_overflow * OFFSET_ACCEL * dt * hor_sign
    elif offset_vel[0]:
        offset_vel[0] -= dt * OFFSET_DEACCEL * hor_sign
        offset_vel[0] = max(0, offset_vel[0])
    if ver_overflow:
        offset_vel[1] += ver_overflow * OFFSET_ACCEL * dt * ver_sign
    elif offset_vel[1]:
        offset_vel[1] -= dt * OFFSET_DEACCEL * ver_sign
        offset_vel[1] = max(0, offset_vel[1])
    
    offset[0] += offset_vel[0] * dt
    offset[1] += offset_vel[1] * dt

    Entity.propagate_movement(awake)

    if top_left_chunk != (floor(offset[0] / world.CHUNK_SIZE) - world.chunk_padding, floor(offset[1] / world.CHUNK_SIZE) - world.chunk_padding):
        top_left_chunk = (floor(offset[0] / world.CHUNK_SIZE) - world.chunk_padding, floor(offset[1] / world.CHUNK_SIZE) - world.chunk_padding)
        # world_canvas.fill((30, 30, 30))
        world_canvas.fill((0, 0, 0))
        for chunk in world.loaded_chunks.keys():
            draw_chunk(chunk)
    
    display.fill((70, 50, 180))
    
    chunks_to_draw = world.handle_revolving_chunks(offset, tiles_horizontally, screen.get_size())
    for chunk in chunks_to_draw:
        draw_chunk(chunk)

    dest = (
        (top_left_chunk[0] * world.CHUNK_SIZE - offset[0]) * PIXELS_IN_TILE,
        ((-top_left_chunk[1] - 2*world.chunk_padding) * world.CHUNK_SIZE + offset[1]) * PIXELS_IN_TILE,
    )
    draw_section.blit(world_canvas, dest)
    draw_size = (
        ceil(draw_section.get_width() * screen.get_width() / (tiles_horizontally * PIXELS_IN_TILE)),
        ceil(draw_section.get_height() * screen.get_width() / (tiles_horizontally * PIXELS_IN_TILE))
    )
    display.blit(pygame.transform.scale(
        draw_section, draw_size
    ), (
        -(offset[0] * PIXELS_IN_TILE % 1) * (screen.get_width() / (tiles_horizontally * PIXELS_IN_TILE)) - 1,
        (offset[1] * PIXELS_IN_TILE % 1 - 1) * (screen.get_width() / (tiles_horizontally * PIXELS_IN_TILE))
    ))
    # display.blit(pygame.transform.scale(world_canvas, screen.get_size()), (0, 0))  #DEBUG
    
    entities_to_draw: list[Entity] = [*(entity for entity in Entity.entities if awake or tuple(entity.pos[:2]) in world.seen_blocks), player]
    if not awake:
        entities_to_draw.append(dream_player)
    for entity in entities_to_draw:
        # entity_pos = entity.pos if time() > entity.last_move + entity.step_time else entity.inter_offset
        entity_pos = entity.pos if not entity.walking else entity.inter_offset
        """ pygame.draw.rect(
            display, entity.colour,
            pygame.Rect(
                (entity_pos[0] - offset[0]) * grid_size,
                (offset[1] - entity_pos[1] + world.CHUNK_SIZE - 1) * grid_size,
                grid_size,
                grid_size
            )
        ) """
        display.blit(
            pygame.transform.scale(
                entity.get_tex(),
                (grid_size, grid_size)
            ),
            (
                (entity_pos[0] - offset[0]) * grid_size,
                (offset[1] - entity_pos[1] + world.CHUNK_SIZE - 1) * grid_size
            )
        )
        if entity.walking:
            entity.walking = False
        
        if entity.health is not None and not isinstance(entity, Player) and entity.health != entity.max_health:
            pygame.draw.rect(
                display, (80, 0, 0),
                pygame.Rect(
                    (entity_pos[0] - offset[0]) * grid_size + health_edge,
                    (offset[1] - entity_pos[1] + world.CHUNK_SIZE) * grid_size + health_edge,
                    grid_size - 2*health_edge,
                    health_edge
                )
            )
            pygame.draw.rect(
                display, (200, 0, 0),
                pygame.Rect(
                    (entity_pos[0] - offset[0]) * grid_size + health_edge,
                    (offset[1] - entity_pos[1] + world.CHUNK_SIZE) * grid_size + health_edge,
                    (grid_size - 2*health_edge) * (entity.health / entity.max_health),
                    health_edge
                )
            )
    
    """ awake_pos = player.pos if not player.walking else player.inter_offset
    pygame.draw.rect(
        display, (255, 0, 0),
        pygame.Rect(
            (awake_pos[0] - offset[0]) * grid_size,
            (offset[1] - awake_pos[1] + world.CHUNK_SIZE - 1) * grid_size,
            grid_size,
            grid_size
        )
    )
    if player.walking:
        player.walking = False

    if not awake:
        dream_pos = dream_player.pos if not dream_player.walking else dream_player.inter_offset
        pygame.draw.rect(
            display, (210, 180, 10),
            pygame.Rect(
                (dream_pos[0] - offset[0]) * grid_size,
                (offset[1] - dream_pos[1] + world.CHUNK_SIZE - 1) * grid_size,
                grid_size,
                grid_size
            )
        )
        if dream_player.walking:
            dream_player.walking = False """
    
    display.blit(hearts, (16, 16))
    
    player_pos = (
        (Entity.player.pos[0] - offset[0] + 0.5) * grid_size,
        (offset[1] - Entity.player.pos[1] - 0.5 + world.CHUNK_SIZE) * grid_size
    )
    player_to_mouse = (
        pygame.mouse.get_pos()[0] - player_pos[0],
        pygame.mouse.get_pos()[1] - player_pos[1]
    )
    direction = pygame.math.Vector2(player_to_mouse)
    if direction.length() == 0:
        direction = pygame.math.Vector2(-0.5, -0.5)
    direction.normalize_ip()
    sword_angle = pygame.math.Vector2(-0.5, -0.5).angle_to(direction)
    if sword_swinging:
        sword_angle += 110 * -(((time() - swinging_start) / swing_length)**2 - 0.5) * (-1 if other_way else 1)
    elif (time() - swinging_start) / swing_length < swing_window[1]:
        sword_angle += 55 * (1 if other_way else -1)
    
    if sword_swinging:
        x = cos(radians(sword_angle - 135)) + direction[0] / 2
        x = -1 if x <= -0.5 else (1 if 0.5 <= x else 0)
        x += Entity.player.pos[0]
        y = sin(radians(sword_angle - 135)) + direction[1] / 2
        y = -1 if y <= -0.5 else (1 if 0.5 <= y else 0)
        y = Entity.player.pos[1] - y
        colliding_entities = [entity for entity in Entity.entities if tuple(entity.pos) == (x, y, Entity.player.pos[2]) and entity not in hit_entities and (awake or tuple(entity.pos[:2]) in world.seen_blocks)]
        for entity in colliding_entities:
            entity.damage(1)
            hit_entities.append(entity)

        """ pygame.draw.rect(
            display,
            (10, 6, 40),
            pygame.Rect(
                x*grid_size + player_pos[0] - grid_size/2,
                y*grid_size + player_pos[1] - grid_size/2,
                grid_size, grid_size
            )
        ) """
    
    rotated_sword = pygame.transform.rotate(sword_surf, -sword_angle)
    display.blit(rotated_sword, [
        a + b - rotated_sword.get_width() // 2 for a, b in zip(direction * grid_size * 0.45, player_pos)
    ])
    
    if not finished_start and hit_meet_scene and player.pos == dream_player.pos:
        display.blit(
            change_prompt,
            (0, display.get_height() - change_prompt.get_height() * min(1, max(0, ease_in_out(min(1, max(0, (time() - meet_scene_start) / 0.8))))))
        )
    if hit_end:
        display.blit(
            quit_prompt,
            (0, display.get_height() - quit_prompt.get_height() * min(1, max(0, ease_in_out(min(1, max(0, (time() - hit_end_time) / 0.8))))))
        )
    
    if dream_player.health <= 0:
        restart()
    
    t += dt
    program['t'] = t
    
    redraw_texture(display_tex, display)
    render_object.render(mode=moderngl.TRIANGLE_STRIP)

    pygame.display.flip()
    
    clock.tick(fps)
