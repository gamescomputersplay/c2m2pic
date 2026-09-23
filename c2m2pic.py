''' Render a C2M file as a PNG image.
'''

import os
import struct
from enum import Enum
from dataclasses import dataclass
from PIL import Image, ImageDraw

class RenderType(Enum):
    ''' Processing options for tiles 
    '''
    SINGLE = 1
    LOWER_LAYER = 2
    DIRECTIONAL = 3
    GREEN_TOGGLE_WALL = 4
    THIN_WALLS_OR_CANOPY = 5

@dataclass(frozen=True)
class TileInfo:
    ''' Class to store tile information
    '''
    code: int
    sprite_x: int
    sprite_y: int
    render: RenderType

class TileType(Enum):
    ''' List of all tile types
    '''
    FLOOR = TileInfo(0x01, 0, 2, RenderType.SINGLE)
    WALL = TileInfo(0x02, 1, 2, RenderType.SINGLE)
    ICE = TileInfo(0x03, 10, 1, RenderType.SINGLE)
    ICE_CORNER_SW = TileInfo(0x04, 12, 1, RenderType.SINGLE)
    ICE_CORNER_NW = TileInfo(0x05, 14, 1, RenderType.SINGLE)
    ICE_CORNER_NE = TileInfo(0x06, 13, 1, RenderType.SINGLE)
    ICE_CORNER_SE = TileInfo(0x07, 11, 1, RenderType.SINGLE)
    WATER = TileInfo(0x08, 13, 24, RenderType.SINGLE)
    FIRE = TileInfo(0x09, 13, 29, RenderType.SINGLE)

    FORCE_FLOOR_N = TileInfo(0x0A, 0, 19, RenderType.SINGLE)
    FORCE_FLOOR_E = TileInfo(0x0B, 2, 19, RenderType.SINGLE)
    FORCE_FLOOR_S = TileInfo(0x0C, 1, 19, RenderType.SINGLE)
    FORCE_FLOOR_W = TileInfo(0x0D, 3, 19, RenderType.SINGLE)
    GREEN_TOGGLE_WALL = TileInfo(0x0E, 8, 9, RenderType.GREEN_TOGGLE_WALL)
    GREEN_TOGGLE_FLOOR = TileInfo(0x0F, 0, 9, RenderType.SINGLE)

    BLUE_TELEPORT = TileInfo(0x11, 4, 10, RenderType.SINGLE)
    EXIT = TileInfo(0x14, 6, 2, RenderType.SINGLE)
    CHIP_THE_HERO = TileInfo(0x16, 0, 22, RenderType.DIRECTIONAL)
    BLOCK = TileInfo(0x17, 8, 1, RenderType.DIRECTIONAL)
    SHIP = TileInfo(0x19, 8, 8, RenderType.DIRECTIONAL)
    THIN_WALL_S = TileInfo(0x1B, 1, 10, RenderType.LOWER_LAYER)
    GRAVEL = TileInfo(0x1E, 9, 10, RenderType.SINGLE)
    GREEN_BUTTON = TileInfo(0x1F, 9, 6, RenderType.SINGLE)

    BLUE_BUTTON = TileInfo(0x20, 8, 6, RenderType.SINGLE)
    BLUE_TANK = TileInfo(0x21, 0, 8, RenderType.DIRECTIONAL)
    RED_DOOR = TileInfo(0x22, 0, 1, RenderType.SINGLE)
    BLUE_DOOR = TileInfo(0x23, 1, 1, RenderType.SINGLE)
    YELLOW_DOOR = TileInfo(0x24, 2, 1, RenderType.SINGLE)
    GREEN_DOOR = TileInfo(0x25, 3, 1, RenderType.SINGLE)

    RED_KEY = TileInfo(0x26, 4, 1, RenderType.LOWER_LAYER)
    BLUE_KEY = TileInfo(0x27, 5, 1, RenderType.LOWER_LAYER)
    YELLOW_KEY = TileInfo(0x28, 6, 1, RenderType.LOWER_LAYER)
    GREEN_KEY = TileInfo(0x29, 7, 1, RenderType.LOWER_LAYER)

    IC_CHIP = TileInfo(0x2A, 11, 3, RenderType.LOWER_LAYER)
    EXTRA_IC_CHIP = TileInfo(0x2B, 11, 3, RenderType.LOWER_LAYER)
    CHIP_SOCKET = TileInfo(0x2C, 4, 2, RenderType.SINGLE)
    POPUP_WALL = TileInfo(0x2D, 8, 10, RenderType.SINGLE)
    APPEARING_WALL = TileInfo(0x2E, 11, 31, RenderType.SINGLE)
    INVISIBLE_WALL = TileInfo(0x2F, 9, 31, RenderType.SINGLE)

    SOLID_BLUE_WALL = TileInfo(0x30, 0, 10, RenderType.SINGLE)
    FAKE_BLUE_WALL = TileInfo(0x31, 10, 31, RenderType.SINGLE)
    DIRT = TileInfo(0x32, 4, 31, RenderType.SINGLE)
    ANT = TileInfo(0x33, 0, 7, RenderType.DIRECTIONAL)
    BALL = TileInfo(0x35, 10, 10, RenderType.DIRECTIONAL)
    ANGRY_TEETH = TileInfo(0x37, 0, 11, RenderType.DIRECTIONAL)
    FIREBALL = TileInfo(0x38, 15, 9, RenderType.DIRECTIONAL)

    RED_BUTTON = TileInfo(0x39, 10, 6, RenderType.SINGLE)
    BROWN_BUTTON = TileInfo(0x3A, 11, 6, RenderType.SINGLE)
    SKATES = TileInfo(0x3B, 2, 6, RenderType.LOWER_LAYER)
    SUCTION_BOOTS = TileInfo(0x3C, 3, 6, RenderType.LOWER_LAYER)
    FIRE_BOOTS = TileInfo(0x3D, 1, 6, RenderType.LOWER_LAYER)
    FLIPPERS = TileInfo(0x3E, 0, 6, RenderType.LOWER_LAYER)
    TOOL_THIEF = TileInfo(0x3F, 3, 2, RenderType.SINGLE)

    CHERRY_BOMB = TileInfo(0x40, 5, 4, RenderType.LOWER_LAYER)
    TRAP = TileInfo(0x42, 9, 9, RenderType.SINGLE)
    CLONE_MACHINE = TileInfo(0x43, 15, 1, RenderType.SINGLE)
    CLUE = TileInfo(0x45, 5, 2, RenderType.SINGLE)

    THIN_WALLS_OR_CANOPY = TileInfo(0x6d, 14, 3, RenderType.THIN_WALLS_OR_CANOPY)

DIRECTIONAL_SPRITES = {
    TileType.CHIP_THE_HERO:
        [(0, 22), (8,22), (0,23), (8,23)],
    TileType.ANGRY_TEETH:
        [(0, 11), (4, 11), (1, 11), (7, 11)],
    TileType.BLUE_TANK:
        [(0, 8), (2, 8), (4, 8), (6, 8)],
    TileType.SHIP:
        [(8, 8), (10, 8), (12, 8), (14, 8)],
    TileType.FIREBALL:
        [(15, 9), (15, 9), (15, 9), (15, 9)],
    TileType.BALL:
        [(10, 10), (10, 10), (10, 10), (10, 10)],
    TileType.ANT:
        [(0, 7), (4, 7), (8, 7), (12, 7)],
    TileType.BLOCK:
        [(8, 1), (8, 1), (8, 1), (8, 1)],
    }


def get_sections(c2m_file):
    '''
    Break c2m file into sections (unpack if needed), return as dict
    '''
    sections = {}

    with open(c2m_file, "rb") as f:

        while True:
            # Section header:
            #   4 bytes = section code
            #   4 bytes = data length
            header = f.read(8)

            if len(header) != 8:
                raise ValueError("Unexpected end of file while reading section header")

            section_code, data_length = struct.unpack("<4sI", header)

            # Convert bytes to string and remove padding spaces
            section_code = section_code.decode("ascii").rstrip()

            # Read section data
            data = f.read(data_length)

            if len(data) != data_length:
                raise ValueError(
                    f"Unexpected end of file in section {section_code!r}: "
                    f"expected {data_length} bytes, got {len(data)}"
                )

            sections[section_code] = data

            # END section terminates the file
            if section_code == "END":
                break

    return sections


def unpack_section(packed):
    '''
    Unpacking for PACK and PRPL sections
    '''
    # First 2 bytes = expected uncompressed size
    expected_size = int.from_bytes(packed[:2], "little")

    pos = 2
    unpacked = bytearray()

    while len(unpacked) < expected_size:
        control = packed[pos]
        pos += 1

        if control < 0x80:
            # Data block
            count = control

            unpacked.extend(packed[pos:pos + count])
            pos += count

        else:
            # Back-reference block
            count = control - 0x80
            offset = packed[pos]
            pos += 1

            for _ in range(count):
                unpacked.append(unpacked[-offset])

    if len(unpacked) != expected_size:
        raise ValueError(
            f"Unpacked size mismatch: expected {expected_size}, "
            f"got {len(unpacked)}"
        )

    return bytes(unpacked)


def decode_tile(data, pos, tile_by_code):
    '''
    Decode next tile in the MAP data.
    Returns either:
    - TileType
    - (TileType, TileType)
    - (TileType, direction, TileType)
    '''
    code = data[pos]
    pos += 1

    tile_type = tile_by_code.get(code)

    if tile_type is None:
        print(f"Warning: Unknown tile code {code:#04x} at position {pos - 1}")
        return None, pos

    if tile_type.value.render == RenderType.LOWER_LAYER:
        lower_level, pos = decode_tile(data, pos, tile_by_code)
        return (tile_type, lower_level), pos

    # Exception to how to display toggle-able wall
    if tile_type.value.render == RenderType.GREEN_TOGGLE_WALL:
        return (TileType.GREEN_TOGGLE_WALL, TileType.GREEN_TOGGLE_FLOOR), pos

    if tile_type.value.render == RenderType.DIRECTIONAL or \
       tile_type.value.render == RenderType.THIN_WALLS_OR_CANOPY:
        direction = data[pos]
        pos += 1
        lower_level, pos = decode_tile(data, pos, tile_by_code)
        return (tile_type, direction, lower_level), pos

    return tile_type, pos

def decode_tiles(map_data):
    '''
    Decode all tiles from a MAP section, return a dict:
    {(x,y): [TileType,],... } 
    For the TileType list see decode_tile function 
    '''
    width, length = map_data[:2]
    # image = Image.new("RGB", (width * 32, length * 32))

    tile_by_code = {
        tile_type.value.code: tile_type
        for tile_type in TileType
    }

    tiles = {}
    pos = 2

    for y in range(length):
        for x in range(width):
            tile, pos = decode_tile(map_data, pos, tile_by_code)

            if tile is not None:
                tiles[(x, y)] = [tile]
            else:
                tiles[(x, y)] = []

    return tiles


def erase_half(image, side):
    ''' Helper in case we need only half of teh sprite
    '''
    draw = ImageDraw.Draw(image)

    if side == "top":
        box = (0, 0, image.width - 1, image.height // 2 - 1)
    elif side == "bottom":
        box = (0, image.height // 2, image.width - 1, image.height - 1)
    elif side == "left":
        box = (0, 0, image.width // 2 - 1, image.height - 1)
    elif side == "right":
        box = (image.width // 2, 0, image.width - 1, image.height - 1)

    draw.rectangle(box, fill=(0, 0, 0, 0))


def render_thin_wall_or_canopy(sprite_sheet, tile):
    ''' Special case: thin tile or canopy
    '''
    bitmask = tile[1]
    underlying_tile = tile[-1]
    sprite = tile_sprite(sprite_sheet, underlying_tile)

    wall_options = {
        1: (1, "bottom"),   # North
        2: (2, "left"),     # East
        4: (1, "top"),      # South
        8: (2, "right"),    # West
    }

    for bit, (sprite_x, erase) in wall_options.items():
        if bitmask & bit:
            wallsprite = sprite_sheet.crop(
                (sprite_x * 32, 10 * 32,
                 sprite_x * 32 + 32, 10 * 32 + 32)
            )

            erase_half(wallsprite, erase)
            sprite.alpha_composite(wallsprite)

    if bitmask & 16:
        # canopy
        pass

    return sprite


def tile_sprite(sprite_sheet, tile_stack):
    '''
    From a TileType tuple, return rendered image of a tile,
    with all elements superimposed
    '''
    # A single tile
    if isinstance(tile_stack, TileType):
        tile_type = tile_stack

        x = tile_type.value.sprite_x * 32
        y = tile_type.value.sprite_y * 32

        sprite = sprite_sheet.crop((x, y, x + 32, y + 32))

        # Erase top section of South Thin Wall
        if tile_type == TileType.THIN_WALL_S:
            draw = ImageDraw.Draw(sprite)
            draw.rectangle((0, 0, sprite.width, sprite.height // 2), fill=(0, 0, 0, 0))

        return sprite

    # Directional tile: (tile_type, direction, lower_level)
    if len(tile_stack) == 3 and tile_stack[0].value.render == RenderType.DIRECTIONAL:

        tile_type, direction, lower_level = tile_stack

        image = tile_sprite(sprite_sheet, lower_level)

        x, y = DIRECTIONAL_SPRITES[tile_type][direction]
        overlay = sprite_sheet.crop(
            (x * 32, y * 32, x * 32 + 32, y * 32 + 32)
        ).convert("RGBA")

        image.alpha_composite(overlay)

        return image

    # Thin wall or canopy: (tile_type, mask, lower_level)
    if len(tile_stack) == 3 and tile_stack[0].value.render == RenderType.THIN_WALLS_OR_CANOPY:
        image = render_thin_wall_or_canopy(sprite_sheet, tile_stack)
        return image

    # Remaining case is a tile with a underlying layer
    # Render from the last tile toward the first
    image = tile_sprite(sprite_sheet, tile_stack[-1])

    for tile_part in reversed(tile_stack[:-1]):
        overlay = tile_sprite(sprite_sheet, tile_part)
        image.alpha_composite(overlay)

    return image


def load_sprite_sheet(filename="./spritesheet.png", transparent_color=(82, 206, 107)):
    '''
    Load sprite sheet, remove transparent color
    '''
    sprite_sheet = Image.open(filename).convert("RGBA")
    pixels = sprite_sheet.load()

    for y in range(sprite_sheet.height):
        for x in range(sprite_sheet.width):
            r, g, b, _ = pixels[x, y]

            if (r, g, b) == transparent_color:
                pixels[x, y] = (r, g, b, 0)

    return sprite_sheet


def render_map(width, length, tiles):
    '''
    Receives decoded tiles dict and returns rendered image
    '''
    # Load the sprite sheet
    sprite_sheet = load_sprite_sheet()

    # Create a new image for the map
    image = Image.new("RGBA", (width * 32, length * 32))

    for (x, y), tile_list in tiles.items():
        for tile in tile_list:
            sprite = tile_sprite(sprite_sheet, tile)
            image.paste(sprite, (x * 32, y * 32))

    return image

def c2m_to_pic(c2m_file, output_file):
    ''' 
    Full processing of a c2m file
    '''

    # Create folder if not exist
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Get sections from C2M file
    sections = get_sections(c2m_file)


    level_title = sections.get("TITL", b"").decode("ascii").replace("\x00", "")
    print(f"Level title: {level_title!r}")

    time_to_beat = struct.unpack("<H", sections["OPTN"][:2])[0]
    print(f"Time to beat: {time_to_beat} seconds")

    if "PACK" in sections:
        sections["MAP"] = unpack_section(sections["PACK"])
        print(f"Unpacked MAP data length: {len(sections['MAP'])} bytes")

    if "PRPL" in sections:
        sections["REPL"] = unpack_section(sections["PRPL"])

    width, length = sections["MAP"][:2]
    print(f"Map dimensions: {width} x {length}")

    # print("Sections found:")
    # for name, data in sections.items():
    #     print(f"  {name!r}: {len(data)} bytes")

    tiles = decode_tiles(sections["MAP"])
    # for (x, y), tile_list in tiles.items():
    #     print(f"Tile at ({x}, {y}): {tile_list}")

    image = render_map(width, length, tiles)
    image.save(output_file)


def main():
    '''
    Example of processing a c2m file
    '''
    c2m_file = "./cc1/001-020/map011.c2m"  # Replace with the actual C2M file path
    output_file = "./cc1_done/map011.png"  # Replace with the desired output PNG file path
    c2m_to_pic(c2m_file, output_file)

if __name__ == "__main__":
    main()
