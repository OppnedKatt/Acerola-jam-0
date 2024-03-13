import json
import re
from functools import lru_cache
from os import chdir, listdir
from os.path import dirname, exists, join

import pygame

chdir(dirname(__file__))

not_found_surf = pygame.Surface((2, 2))
not_found_surf.fill((244, 86, 151))
pygame.draw.rect(
    not_found_surf, (22, 22, 22),
    pygame.Rect(0, 0, 1, 1)
)
pygame.draw.rect(
    not_found_surf, (22, 22, 22),
    pygame.Rect(1, 1, 1, 1)
)

@lru_cache(128)
def get_texture(*asset_path: str):
    if not exists(join('assets', *asset_path)):
        return not_found_surf.copy()
    return pygame.image.load(join('assets', *asset_path))
    
    """ if asset_path not in loaded_assets.keys():
        loaded_assets[asset_path] = pygame.image.load(asset_path)
    return loaded_assets[asset_path] """

rotation_order = (0, 4, 2, 4)

def rotate_flip(
    surface: pygame.Surface,
    rotation: int,
    flip: bool
) -> pygame.Surface:
    if flip:
        surface = pygame.transform.flip(surface, 1, 0)
    if rotation:
        surface = pygame.transform.rotate(surface, rotation * 45)
    return surface

def get_type(data: dict, neighbours: str, total_rotation: int) -> pygame.Surface:
    return rotate_flip(
        get_texture('types', data['asset_name'], f'{neighbours}.png'),
        total_rotation,
        data.get('flipped', False)
    )

def get_back_front(rules: dict, asset: str) -> pygame.Surface:  #TODO: Finish matching
    if '*' in rules.keys():
        return get_texture('types', asset, f'{rules["*"]}.png')

    return get_texture('tech', 'missing_equal.png')

def merge_surfaces(bottom_surface, *surfaces):
    bottom_surface = bottom_surface.copy()
    for surface in surfaces:
        bottom_surface.blit(surface, (0, 0))
    return bottom_surface

def finalise_type(
    data: dict,
    neighbours: str, 
    total_rotation: int,
    back: pygame.Surface | None,
    front: pygame.Surface | None
) -> pygame.Surface:
    return merge_surfaces(*filter(None.__ne__, (
        back,
        get_type(data, neighbours, total_rotation),
        front
    )))

@lru_cache(128)
def get_block_texture(data: str) -> pygame.Surface:
    data = json.loads(data)  #NOTE: Maybe data should be stored as a string to not require conversion on the other side
    total_rotation = data.get('rotation', 0)
    
    if data['type'] == 'texture':
        texture = get_texture('textures', data['asset_name'])
        if texture is None:
            return get_texture('tech', 'missing_texture.png')
        return rotate_flip(texture, total_rotation, data.get('flipped', False))

    if data['type'] == 'object':
        with open(
            join('assets', 'objects', data['asset_name'], 'properties.json'),
            'r',
            encoding='utf-8'
        ) as f:
            object_data = json.load(f)
        if object_data.get('static', False):
            texture = get_texture('objects', data['asset_name'], object_data['texture'])
            if texture is None:
                return get_texture('tech', 'missing_object.png')
            return rotate_flip(texture, total_rotation, data.get('flipped', False))

        #TODO: Add animation

    if data['type'] == 'type':  #TODO: Add z-layers
        if not exists(join('assets', 'types', data['asset_name'])):
            return get_texture('tech', 'missing_type.png')

        with open(
            join('assets', 'types', data['asset_name'], 'rules.json'),
            'r',
            encoding='utf-8'
        ) as f:
            rules: dict = json.load(f)
        type_textures = [
            path[:-4] for path in listdir(join('assets', 'types', data['asset_name']))
            if path.endswith('.png')
        ]
        neighbours = data['neighbours']
        equals = rules['equals'].items()
        if 'extra' in rules.keys():  #TODO: Check if .get('', False) is faster or not. May vary based on size
            if 'back' in rules['extra'].keys():
                back = rotate_flip(
                    get_back_front(rules['extra']['back'], data['asset_name']),
                    total_rotation,
                    data.get('flipped', False)
                )
            else:
                back = None
            if 'front' in rules['extra'].keys():
                front = rotate_flip(
                    get_back_front(rules['extra']['front'], data['asset_name']),
                    total_rotation,
                    data.get('flipped', False)
                )
            else:
                front = None
        else:
            back = None
            front = None

        for rotation in rotation_order:
            total_rotation += rotation
            neighbours = neighbours[-rotation:] + neighbours[:-rotation]

            # Checks if a direct match exists
            if neighbours in type_textures:
                return finalise_type(data, neighbours, total_rotation, back, front)

            # Checks rules for equals
            for equivalent, equal in equals:
                equivalent = equivalent.replace('x', '[0-1]')
                if re.search(equivalent, neighbours) is None:
                    continue
                neighbours = equal
                return finalise_type(data, equal, total_rotation, back, front)
            else:
                continue
        else:
            return get_texture('tech', 'missing_equal.png')
