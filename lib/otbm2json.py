import json
import os
import traceback

from collections import defaultdict
from functools import partial
from pathlib import Path


class Otbm2Json:
    """
    OTBM to Json parser.
    """
    IDENTIFIER = 4    # Number of bytes
    MAP_VERSION = 4
    MAP_WIDTH = 2
    MAP_HEIGHT = 2
    ITEMS_MAJOR_VERSION = 4
    ITEMS_MINOR_VERSION = 4

    def __init__(self):
        self._otbm_file_path = None    # Input file
        self._json_file_path = None    # Output file
        self._json_data = defaultdict(list)
        self._node_list = list()

        # Json keys counter
        self._tile_area_cnt = 0
        self._tile_cnt = 0
        self._item_cnt = 0
        self._town_cnt = 0
        self._house_tile_cnt = 0
        self._waypoints_cnt = 0
        self._waypoint_cnt = 0
        self._description_cnt = 0

    @property
    def otbm_file_path(self):
        return self._otbm_file_path

    @otbm_file_path.setter
    def otbm_file_path(self, value):
        new_path = Path(value)
        assert new_path.is_file(), "File not found!"
        assert new_path.suffix == ".otbm", "Wrong file format!"
        self._otbm_file_path = new_path

    @property
    def json_file_path(self):
        return self._json_file_path

    @json_file_path.setter
    def json_file_path(self, value):
        new_path = Path(value)
        assert new_path.is_file(), "File not found!"
        assert new_path.suffix == ".json", "Wrong file format!"
        self._json_file_path = new_path

    def _merge_nodes(self, a_node, b_node):
        """
        Merge second node into the first one (dict).
        Taken from https://stackoverflow.com/questions/7204805/how-to-merge-dictionaries-of-dictionaries
        """
        try:
            for k, v in a_node.items():
                if k in b_node:
                    b_node[k] = self._merge_nodes(v, b_node[k])
            a_node.update(b_node)
        except:
            pass
        return a_node

    def _add_data(self, node_list, data):
        """
        Add data to nested json dict.

        Example:
            Input:
                node_list = ["MAP", "TILE_AREA", "TILE"]
                data = "0xda12"
            Output:
                res = {"Map":
                          "TILE_AREA":
                              "TILE": "0xda12"}

        """
        if len(node_list) > 0:
            return {node_list[0] : self._add_data(node_list[1:], data)}
        else:
            return data

    def _get_identifier(self, iterator):
        """
        Iterate over identifier bytes and add them to json data.
        """
        identifier = bytes()
        for _ in range(self.IDENTIFIER):
            identifier += next(iterator)
        self._json_data['identifier'] = int.from_bytes(identifier, "little")

    def _get_otbm_header(self, iterator):
        """"
        Iterate over header bytes and add them to json data.
        """
        map_version = bytes()
        map_width = bytes()
        map_height = bytes()
        items_major_version = bytes()
        items_minor_version = bytes()

        next(iterator)  # Skip first 0xFE node (0xFE00)
        next(iterator)  # Skip first 0x00 node (0xFE00)

        for _ in range(self.MAP_VERSION):
            map_version += next(iterator)
        self._json_data['map_version'] = int.from_bytes(map_version, "little")

        for _ in range(self.MAP_WIDTH):
            map_width += next(iterator)
        self._json_data['map_width'] = int.from_bytes(map_width, "little")

        for _ in range(self.MAP_WIDTH):
            map_height += next(iterator)
        self._json_data['map_height'] = int.from_bytes(map_height, "little")

        for _ in range(self.ITEMS_MAJOR_VERSION):
            items_major_version += next(iterator)
        self._json_data['items_major_version'] = int.from_bytes(
                                                  items_major_version,
                                                  "little"
                                                )

        for _ in range(self.ITEMS_MINOR_VERSION):
            items_minor_version += next(iterator)
        self._json_data['items_minor_version'] = int.from_bytes(
                                                  items_minor_version,
                                                  "little"
                                                )

    def _get_node_properties(self, node_list, byte_data):
        """
        Add properties to node.
        """
        description = b'\x01'       # N bytes
        ext_file = b'\x02'          # Apparently not used
        tile_flags = b'\x03'        # 4 bytes
        action_id = b'\x04'         # 2 bytes
        unique_id = b'\x05'         # 2 bytes
        text = b'\x06'              # N bytes
        teleport_dest = b'\x08'     # 2, 2, 1 bytes (x, y, z)
        identifier = b'\x09'        # 2 bytes
        depot_id = b'\x0a'          # 2 bytes
        ext_spawn_file = b'\x0b'    # N bytes
        ext_house_file = b'\x0d'    # N bytes
        housedoorid = b'\x0e'       # 1 byte
        count = b'\x0f'             # 1 byte
        rune_charges = b'\x16'      # 2 bytes

        if not byte_data:
            return

        node = None
        property_type = byte_data[:1]
        if property_type == description:
            self._description_cnt += 1
            node_list.append(f'DESCRIPTION_{self._description_cnt}')
            lenght = int.from_bytes(byte_data[1:3], "little")
            node = self._add_data(node_list, str(byte_data[3:lenght+3].decode('ascii')))
            self._merge_nodes(self._json_data, node)
            # Get Spawn and House files
            node_list.pop()
            self._get_node_properties(node_list, byte_data[lenght+3:])
        elif property_type == ext_file:
            node_list.append('EXT_FILE')
            lenght = int.from_bytes(byte_data[1:3], "little")
            node = self._add_data(node_list, str(byte_data[3:lenght+3].decode('ascii')))
            self._merge_nodes(self._json_data, node)
        elif property_type == tile_flags:
            flag = int.from_bytes(byte_data[1:2], "little")
            protection_zone = int((flag & int.from_bytes(b'\x01\x00\x00\x00', "little")) / 1)
            no_pvp = int((flag & int.from_bytes(b'\x04\x00\x00\x00', "little")) / 4)
            no_logout = int((flag & int.from_bytes(b'\x08\x00\x00\x00', "little")) / 8)
            pvp_zone = int((flag & int.from_bytes(b'\x10\x00\x00\x00', "little")) / 10)
            node_list.append('PROTECTION_ZONE')
            node = self._add_data(node_list, protection_zone)
            self._merge_nodes(self._json_data, node)
            node_list.pop()
            node_list.append('NO_PVP')
            node = self._add_data(node_list, no_pvp)
            self._merge_nodes(self._json_data, node)
            node_list.pop()
            node_list.append('NO_LOGOUT')
            node = self._add_data(node_list, no_logout)
            self._merge_nodes(self._json_data, node)
            node_list.pop()
            node_list.append('PVP_ZONE')
            node = self._add_data(node_list, pvp_zone)
            self._merge_nodes(self._json_data, node)
        elif property_type == action_id:
            node_list.pop()
            node_list.append('ACTION_ID')
            node = self._add_data(node_list, int.from_bytes(byte_data[1:3], "little"))
            self._merge_nodes(self._json_data, node)
            self._get_node_properties(node_list, byte_data[3:])
        elif property_type == unique_id:
            node_list.pop()
            node_list.append('UNIQUE_ID')
            node = self._add_data(node_list, int.from_bytes(byte_data[1:3], "little"))
            self._merge_nodes(self._json_data, node)
            self._get_node_properties(node_list, byte_data[3:])
        elif property_type == text:
            node_list.pop()
            node_list.append('TEXT')
            lenght = int.from_bytes(byte_data[1:3], "little")
            node = self._add_data(node_list, str(byte_data[3:lenght+3].decode('ascii')))
            self._merge_nodes(self._json_data, node)
        elif property_type == teleport_dest:
            node_list.append('DESTINATION_X')
            node = self._add_data(node_list, int.from_bytes(byte_data[1:3],"little"))
            self._merge_nodes(self._json_data, node)
            node_list.pop()
            node_list.append('DESTINATION_Y')
            node = self._add_data(node_list, int.from_bytes(byte_data[3:5],"little"))
            self._merge_nodes(self._json_data, node)
            node_list.pop()
            node_list.append('DESTINATION_Z')
            node = self._add_data(node_list, int.from_bytes(
                                                      byte_data[5:6],
                                                      "little"
                                                    ))
            self._merge_nodes(self._json_data, node)
        elif property_type == identifier:
            node_list.append('IDENTIFIER')
            node = self._add_data(node_list, int.from_bytes(byte_data[1:], "little"))
            self._merge_nodes(self._json_data, node)
        elif property_type == depot_id:
            node_list.append('DEPOT_ID')
            node = self._add_data(node_list, int.from_bytes(byte_data[1:3],"little"))
            self._merge_nodes(self._json_data, node)
        elif property_type == ext_spawn_file:
            node_list.append('SPAWN_FILE')
            lenght = int.from_bytes(byte_data[1:3], "little")
            node = self._add_data(node_list, str(byte_data[3:lenght+3].decode('ascii')))
            self._merge_nodes(self._json_data, node)
            # Get house file
            node_list.pop()
            self._get_node_properties(node_list, byte_data[lenght+3:])
        elif property_type == ext_house_file:
            node_list.append('HOUSE_FILE')
            lenght = int.from_bytes(byte_data[1:3], "little")
            node = self._add_data(node_list, str(byte_data[3:lenght+3].decode('ascii')))
            self._merge_nodes(self._json_data, node)
        elif property_type == housedoorid:
            node_list.append('HOUSE_DOOR_ID')
            node = self._add_data(node_list, int.from_bytes(byte_data[1:2], "little"))
            self._merge_nodes(self._json_data, node)
        elif property_type == count:
            node_list.append('COUNT')
            node = self._add_data(node_list, int.from_bytes(byte_data[1:2], "little"))
            self._merge_nodes(self._json_data, node)
        elif property_type == rune_charges:
            node_list.pop()
            node_list.append('RUNE_CHARGES')
            node = self._add_data(node_list, int.from_bytes(byte_data[1:3], "little"))
            self._merge_nodes(self._json_data, node)


    def _get_node_data(self, byte_data):
        """
        Add data to node. TODO: Change method's name
        """
        if self._node_list:
            # Remove node number
            if len(self._node_list) > 1:
                node_type = "_".join(self._node_list[-1].split("_")[:-1])
            else:
                node_type = "MAP"
            tmp_node_list = self._node_list.copy()
            try:
                if node_type == "MAP":
                    self._get_node_properties(tmp_node_list, byte_data)
                elif node_type == "TILE_AREA":
                    tmp_node_list.append('X')
                    node = self._add_data(tmp_node_list, int.from_bytes(
                                                              byte_data[:2],
                                                              "little"
                                                            ))
                    self._merge_nodes(self._json_data, node)
                    tmp_node_list.pop()
                    tmp_node_list.append('Y')
                    node = self._add_data(tmp_node_list, int.from_bytes(
                                                              byte_data[2:4],
                                                              "little"
                                                            ))
                    self._merge_nodes(self._json_data, node)
                    tmp_node_list.pop()
                    tmp_node_list.append('Z')
                    node = self._add_data(tmp_node_list, int.from_bytes(
                                                              byte_data[4:],
                                                              "little"
                                                            ))
                    self._merge_nodes(self._json_data, node)
                    self._get_node_properties(tmp_node_list, byte_data[4:])
                elif node_type == "TILE":
                    # Position is relative to parent area node's
                    tmp_node_list = self._node_list.copy()
                    tmp_node_list.append('X')
                    node = self._add_data(tmp_node_list, int.from_bytes(
                                                              byte_data[:1],
                                                              "little"
                                                            ))
                    self._merge_nodes(self._json_data, node)
                    tmp_node_list.pop()
                    
                    tmp_node_list.append('Y')
                    node = self._add_data(tmp_node_list, int.from_bytes(
                                                              byte_data[1:2],
                                                              "little"
                                                            ))
                    self._merge_nodes(self._json_data, node)
                    tmp_node_list.pop()
                    self._get_node_properties(tmp_node_list, byte_data[2:])
                elif node_type == "ITEM":
                    tmp_node_list.append('IDENTIFIER')
                    node = self._add_data(tmp_node_list, int.from_bytes(
                                                              byte_data[:2],
                                                              "little"
                                                            ))
                    self._merge_nodes(self._json_data, node)
                    tmp_node_list.pop()
                    self._get_node_properties(tmp_node_list, byte_data[2:])

                elif node_type == "TOWNS":
                    pass    # Nothing to do here
                elif node_type == "TOWN":
                    tmp_node_list.append('ID')
                    node = self._add_data(tmp_node_list, int.from_bytes(byte_data[:2], "little"))
                    self._merge_nodes(self._json_data, node)
                    tmp_node_list.pop()
                    tmp_node_list.append('NAME')
                    lenght = int.from_bytes(byte_data[4:6], "little")
                    node = self._add_data(tmp_node_list, str(byte_data[6:6+lenght].decode('ascii')))
                    self._merge_nodes(self._json_data, node)
                    tmp_node_list.pop()
                    tmp_node_list.append('X')
                    node = self._add_data(tmp_node_list, int.from_bytes(byte_data[6+lenght:6+lenght+2], "little"))
                    self._merge_nodes(self._json_data, node)
                    tmp_node_list.pop()
                    tmp_node_list.append('Y')
                    node = self._add_data(tmp_node_list, int.from_bytes(byte_data[6+lenght+2:6+lenght+4], "little"))
                    self._merge_nodes(self._json_data, node)
                    tmp_node_list.pop()
                    tmp_node_list.append('Z')
                    node = self._add_data(tmp_node_list, int.from_bytes(byte_data[6+lenght+4:6+lenght+5], "little"))
                    self._merge_nodes(self._json_data, node)
                elif node_type == "HOUSE_TILE":
                    tmp_node_list.append('X')
                    node = self._add_data(tmp_node_list, int.from_bytes(byte_data[:1], "little"))
                    self._merge_nodes(self._json_data, node)
                    tmp_node_list.pop()
                    tmp_node_list.append('Y')
                    node = self._add_data(tmp_node_list, int.from_bytes(byte_data[1:2], "little"))
                    self._merge_nodes(self._json_data, node)
                    tmp_node_list.pop()
                    tmp_node_list.append('HOUSE_ID')
                    node = self._add_data(tmp_node_list, int.from_bytes(byte_data[2:6], "little"))
                    self._merge_nodes(self._json_data, node)
                    tmp_node_list.pop()
                    self._get_node_properties(tmp_node_list, byte_data[6:])
                elif node_type == "WAYPOINTS":
                    pass    # Nothing to do here
                elif node_type == "WAYPOINT":
                    tmp_node_list.append('NAME')
                    lenght = int.from_bytes(byte_data[:2], "little")
                    node = self._add_data(tmp_node_list, str(byte_data[2:2+lenght].decode('ascii')))
                    self._merge_nodes(self._json_data, node)
                    tmp_node_list.pop()
                    tmp_node_list.append('X')
                    node = self._add_data(tmp_node_list, int.from_bytes(byte_data[2+lenght:2+lenght+2], "little"))
                    self._merge_nodes(self._json_data, node)
                    tmp_node_list.pop()
                    tmp_node_list.append('Y')
                    node = self._add_data(tmp_node_list, int.from_bytes(byte_data[2+lenght+2:2+lenght+4], "little"))
                    self._merge_nodes(self._json_data, node)
                    tmp_node_list.pop()
                    tmp_node_list.append('Z')
                    node = self._add_data(tmp_node_list, int.from_bytes(byte_data[2+lenght+4:2+lenght+5], "little"))
                    self._merge_nodes(self._json_data, node)
                del tmp_node_list
            except Exception as e:
                print(traceback.format_exc())
        else:
            pass


    def _get_next_node(self, iterator):
        """
        Iterate over bytes until next node (0xFE) and get its type (+1 byte).
        """
        node_init = b'\xfe'
        node_end = b'\xff'
        map_data = b'\x02'
        tile_area = b'\x04'
        tile = b'\x05'
        item = b'\x06'
        towns = b'\x0c'
        town = b'\x0d'
        house_tile = b'\x0e'
        waypoints = b'\x0f'
        waypoint = b'\x10'

        try:
            byte_data = bytes()
            while True:
                byte = next(iterator)
                if byte == node_init:
                    if byte_data:
                        self._get_node_data(byte_data)
                    if self._node_list:
                        byte_data = bytes()
                    node_type = next(iterator)
                    if node_type == map_data: 
                        self._node_list.append('MAP')
                    elif node_type == tile_area:
                        self._tile_area_cnt += 1
                        self._node_list.append(f'TILE_AREA_{self._tile_area_cnt}')
                    elif node_type == tile:
                        self._tile_cnt += 1
                        self._node_list.append(f'TILE_{self._tile_cnt}')
                        self._item_cnt = 0
                    elif node_type == item:
                        self._item_cnt += 1
                        self._node_list.append(f'ITEM_{self._item_cnt}')
                    elif node_type == towns:
                        self._node_list.append('TOWNS')
                    elif node_type == town:
                        self._town_cnt += 1
                        self._node_list.append(f'TOWN_{self._town_cnt}')
                    elif node_type == house_tile:
                        self._house_tile_cnt += 1
                        self._node_list.append(f'HOUSE_TILE_{self._house_tile_cnt}')
                        self._item_cnt = 0
                    elif node_type == waypoints:
                        self._waypoints_cnt += 1
                        self._node_list.append(f'WAYPOINTS_{self._waypoints_cnt}')
                    elif node_type == waypoint:
                        self._waypoint_cnt += 1
                        self._node_list.append(f'WAYPOINT_{self._waypoint_cnt}')
                    else:
                        pass  # TODO: Process byte (?)
                elif byte == node_end:
                    if self._node_list:
                        if byte_data != b'':
                            node = self._add_data(list(self._node_list), str(byte_data))
                            self._get_node_data(byte_data)
                            byte_data = bytes()
                        else:
                            node = self._add_data(list(self._node_list), {})
                        key = list(node.keys())[0]
                        self._merge_nodes(self._json_data, node)
                        self._node_list.pop()   # Pop current node
                else:
                    if byte != b'':
                        byte_data += byte
                    if byte == b'\xfd':
                        next(iterator)    # Skip next byte
        except StopIteration:
            return


    def process_file(self):
        with open(self.otbm_file_path, 'rb') as file:
            data_iterator = iter(partial(file.read1, 1), bytes())
            self._get_identifier(data_iterator)
            self._get_otbm_header(data_iterator)
            self._get_next_node(data_iterator)


    def generate_json(self):
        """
        Create output json file with otbm data.
        """
        os.makedirs(os.path.dirname(self._json_file_path), exist_ok=True)
        with open(self._json_file_path, 'w+', encoding='utf-8') as f:
            json.dump(self._json_data, f, ensure_ascii=False, indent=4)
