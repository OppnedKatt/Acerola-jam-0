import json
from math import ceil, floor
from os.path import exists, join

from chicken import Chicken
from diagger import Diagger
from entity import Entity
from frog import Frog
from sheep import Sheep
from spitwar import Spitwar

chunk_pos = tuple[int]

class World:
    player = None
    dream_player = None
    
    def __init__(self, name: str) -> None:
        self.name = name

        world_properties = {}
        if exists(join(name, 'properties.json')):
            with open(join(name, 'properties.json'), 'r', encoding='utf-8') as f:
                world_properties = json.load(f)
        self.CHUNK_SIZE = world_properties.get('chunk_size', 16)
        self.chunk_padding = 2

        self.loaded_chunks = {}
        self.solids = {}
        self.force_loaded_chunks = set()
        self.seen_blocks = set()
        self.seen = set()

    def handle_revolving_chunks(self, offset: list[int | float], tiles_horizontally: int | float, screen_size: tuple[int, int]) -> set[chunk_pos]:  #TODO
        needed_chunks = set(self.force_loaded_chunks)
        visible_chunks = (
            ceil(tiles_horizontally / self.CHUNK_SIZE) + 2*self.chunk_padding,
            ceil((tiles_horizontally / self.CHUNK_SIZE) * (screen_size[1] / screen_size[0])) + 2*self.chunk_padding
        )
        needed_chunks.update(
            (
                floor(offset[0] / self.CHUNK_SIZE) + x - self.chunk_padding,
                floor(offset[1] / self.CHUNK_SIZE) - y + self.chunk_padding
            )
            for x in range(visible_chunks[0])
            for y in range(visible_chunks[1])
        )
        chunks_to_draw = set(needed_chunks).difference(self.loaded_chunks.keys())  #TODO: Move difference to camera when individual chunk-storing has been added

        chunks_to_load = needed_chunks.difference(self.loaded_chunks.keys())
        #print('chunks_to_load', chunks_to_load, len(chunks_to_load))  #DEBUG
        #print('--------------')  #DEBUG
        #print('loaded_chunks before load', len(self.loaded_chunks))  #DEBUG
        self.load_chunks(chunks_to_load)
        #print('loaded_chunks after load', len(self.loaded_chunks))  #DEBUG
        
        #TODO: Load dependent chunks: They have to be stored separately 
        # from other chunks to not chain-load. Maybe store which camera needs the 
        # dependency
        """ needed_chunks.update(chain.from_iterable(
            chunks for chunk in needed_chunks
            if (chunks := getattr(chunk, 'dependent_chunks', None)) is not None
        )) """

        #TODO: Unload dependent chunks not needed

        #TODO: Unload chunks
        chunks_to_unload = set(self.loaded_chunks.keys()).difference(needed_chunks)
        self.unload_chunks(chunks_to_unload)
        #print(chunks_to_unload)  #DEBUG
        #TODO: Protect dependent chunks

        return chunks_to_draw

    def load_chunks(self, chunks: set[chunk_pos], force=False) -> None:  #TODO
        #print('chunks in load chunks', chunks)  #DEBUG
        if force:
            self.force_loaded_chunks.update(chunks)
        
        chunk_path = join('map', 'chunks')
        needed_dependencies = {}
        for chunk in chunks:
            path = join(chunk_path, '.'.join(map(str, chunk)) + '.json')
            if not exists(path):
                self.loaded_chunks[chunk] = {'layers': {}}
                continue
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.loaded_chunks[chunk] = data

                y_range = range(chunk[1]*self.CHUNK_SIZE, (chunk[1]+1)*self.CHUNK_SIZE)
                x_range = range(chunk[0]*self.CHUNK_SIZE, (chunk[0]+1)*self.CHUNK_SIZE)
                for layer_data in data['layers'].values():
                    if layer_data['type'] != 'uniform':
                        continue
                    block_data = layer_data['data']
                    layer_data['data'] = {}
                    for y in y_range:
                        for x in x_range:
                            layer_data['data'][f'{x}.{y}'] = block_data.copy()

                for layer in data['layers'].keys():
                    if not int(layer) in self.solids.keys():
                        self.solids[int(layer)] = []
                for layer, layer_data in data['layers'].items():
                    layer = int(layer)
                    to_remove = []
                    for block_pos, block_data in layer_data['data'].items():
                        pos = tuple(map(int, block_pos.split('.')))
                        if block_data['type'] == 'object':  #NOTE: Shoehorning in entities. The map editor haven't been given entity support yet
                            # loaded = any((entity.origin == [*pos, layer] for entity in Entity.entities))
                            loaded = block_pos in Entity.spawned_entities
                            lol = True
                            if loaded:
                                pass
                            elif block_data['asset_name'] == 'spitwar':
                                Entity.normal_entities.append(Spitwar([*pos, layer], self.player))
                            elif block_data['asset_name'] == 'frog':
                                Entity.normal_entities.append(Frog([*pos, layer], self.player))
                            elif block_data['asset_name'] == 'sheep':
                                Entity.dream_entities.append(Sheep([*pos, layer]))
                            elif block_data['asset_name'] == 'chicken':
                                Entity.normal_entities.append(Chicken([*pos, layer]))
                            elif block_data['asset_name'] == 'diagger':
                                Entity.dream_entities.append(Diagger([*pos, layer], self.dream_player))
                            else:
                                lol = False
                            if lol:
                                to_remove.append(block_pos)
                                Entity.spawned_entities.append(block_pos)
                                continue
                        
                        #TODO: Add check for passable
                        self.solids[layer].append(pos)
                    
                    for pos in to_remove:
                        del layer_data['data'][pos]

                if 'dependencies' in data.keys():
                    needed_dependencies[chunk] = data['dependencies']
                    
                new_layer_dict = {}
                for key, value in data['layers'].items():
                    new_layer_dict[int(key)] = value
                data['layers'] = new_layer_dict

        #TODO: Extract solids

        #TODO: Load dependencies

    def unload_chunks(self, chunks) -> None:
        for chunk in chunks:
            del self.loaded_chunks[chunk]

    def get_chunk(self, chunk: chunk_pos) -> dict:
        return self.loaded_chunks.get(chunk, {'layers': {}})
