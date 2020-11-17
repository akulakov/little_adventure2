#!/usr/bin/env python3
"""
"""
import fov
from bearlibterminal import terminal as blt
import os
import sys
from copy import copy, deepcopy
from time import sleep
from random import random, choice, randrange
from collections import defaultdict
from textwrap import wrap
import string
import shelve

oprint = print

__version__ = (0,1,1)

rock = '█'
blank = ' '
HEIGHT = 16
WIDTH = 79
GROUND = HEIGHT-2   # ground level
LOAD_BOARD = 999
MAIN_Y = 0          # starting row of game boards
SLP = 0.01
SEQ_TYPES = (list, tuple)
MAX_HEALTH = 50
DBG = 0
SIZE = 24           # tile size
debug_log = open('debug', 'w')
triggered_events = []
done_events = set()
boards = []
objects = {}
timers = []
map_to_loc = {}

class ObjectsByAttr:
    def __getattr__(self, attr):
        return objects.get(getattr(ID, attr))
obj_by_attr = ObjectsByAttr()


class OldBlocks:
    door = '🚪'
    steps_r = '▞'
    steps_l = '▚'
    ladder = '☰'
    cupboard = '⌸'
    water = '⏖'
    elephant = '🐘'
    rabbit = '🐰'
    soldier = '⍾'
    tree1 = '🌲'
    tree2 = '🌳'
    tulip = '🌷'
    rock2 = '▧'
    platform2 = '▭'

class Blocks:
    circle3 = '\u25cc'
    tele_pod = '\u2054'
    rock = '\u2588'
    lever = '\u26dd'
    shelves = '\u25a4'
    ladder = '\u26c3'
    platform2 = '\u23af'
    platform_top = '\u23ba'
    # rock2 = '\u2337'
    rock2 = '\u16c9'    # supports under houses

    platform = '▁'
    bell = '\u26c4'
    grill = '\u25a4'
    rubbish = '\u26c1'
    truck_l = '\u26c5'
    truck_r = '\u26c6'
    car_l = '\u26c5'
    car_r = '\u26c6'

    locker = '\u25eb'
    grn_heart = '\u2665'
    coin = '\u25c9'
    key = '\u26bf'
    door = '\u26bd'
    block1 = '\u2587'
    steps_r = '\u2692'
    steps_l = '\u2693'
    chair = '\u2694'
    fountain = '\u2696'
    stool = '\u2698'
    underline = '_'
    cupboard = '\u269a'
    sunflower = '\u269c'
    magic_ball = '\u25cd'
    cursor = '\u25cd'       # for the editor
    crate1 = '\u25e7'
    crate2 = '\u25e8'
    crate3 = '\u25e9'
    crate4 = '\u25ea'
    smoke_pipe = '\u2551'
    fireplace = '\u269e'
    water = '\u224b'
    elephant_l = '\u26c8'
    elephant_r = '\u26c9'
    rabbit_l = '\u26ca'
    rabbit_r = '\u26cb'
    wine = '\u26a0'
    dock_boards = '\u2242'
    ticket_seller = '\u26a1'
    ferry_l = '\u26cd'
    ferry_r = '\u26ce'
    ferry_ticket = 't'
    soldier_l = '\u0015'
    soldier_r = '\u0014'
    bars = '\u0738'
    tree1 = '\u2689'
    tree2 = '\u268a'
    books = [
        '\u26ac',
        '\u26ad',
        '\u26ae',
        '\u26af',
        '\u26b0',
        ]

    guardrail_l = '╔'
    guardrail_r = '╕'
    guardrail_m = '╤'
    tulip = '\u26b3'
    flowers = [
        '\u0088',
        '\u0089',
        '\u008a',
        '\u008b',
        '\u008c',
    ]
    monkey = '\u26d0'
    antitank = '\u2042'

    #---------------
    rock3 = '\u2593'
    angled1 = '\u26e0'
    angled2 = '\u26e1'
    picture = '\u26b4'
    bottle = '\u26b9'
    box1 = '\u25a4'
    cactus = '\u268b'

    statue = '\u16a5'
    sharp_rock = '\u073a'
    runes = '\u073c'
    cow_l = '\u0017'
    cow_r = '\u0018'
    hair_dryer = 'D'
    proto_pack = 'P'

    flag = '\u26a3'
    horn = '\u26de'
    medallion = '\u232c'
    seal = '\u25d9'
    special_stone = '\u16a5'
    flute = '\u26a5'
    snowman = '\u2603'

    snowflake = '\u26a6'
    dynofly_l = '\u001a'
    dynofly_r = '\u001b'
    safe = '\u26a8'
    saber = '\u26a9'
    pod = '\u26ba'
    computer = '\u26bc'
    zoe = '\u26ff'
    funfrock = '\u26d3'

    player_f = '\u26d5'
    player_l = '\u26d6'
    player_r = '\u26d7'
    player_b = '\u26d8'

    window = '\u2503'

    cornice_l = '\u26e3'
    cornice_r = '\u26e4'

    crates = (crate1, crate2, crate3, crate4)

old_blocks_to_new = {}
new_blocks_to_old = {}
for k,v in OldBlocks.__dict__.items():
    nv = None
    if isinstance(v, str):
        nv = getattr(Blocks, k, None)
    if nv:
        old_blocks_to_new[v] = nv
        new_blocks_to_old[nv] = v

class Stance:
    normal = 1
    fight = 2
    sneaky = 3
STANCES = {v:k for k,v in Stance.__dict__.items()}

class Type:
    platform_top = 2
    ladder = 3
    fountain = 4
    chair = 5
    door_top_block = 6
    container = 7
    door1 = 8
    crate = 9
    door2 = 10
    water = 11
    event_trigger = 12
    blocking = 13
    door3 = 14
    deadly = 15
    pressure_sensor = 16
    computer = 17
    pod = 18

BLOCKING = [rock, Type.door1, Type.door2, Type.door3, Blocks.block1, Blocks.steps_r, Blocks.steps_l, Type.platform_top,
            Type.door_top_block, Type.blocking, Type.pressure_sensor]

class ID:
    platform1 = 1
    grill1 = 2
    alarm1 = 3
    grill2 = 5
    rubbish1 = 6
    truck1 = 7
    locker = 8
    coin = 9
    grn_heart = 10
    key1 = 11
    door1 = 12
    platform_top1 = 13
    jar_syrup = 14
    shelves = 15
    magic_ball = 16
    crate1 = 17
    door2 = 18
    grill3 = 19
    wine = 20
    key2 = 21
    door3 = 22
    key3 = 23
    grill4 = 24
    ticket_seller1 = 25
    ferry = 26
    ferry_ticket = 27
    grill5 = 28
    grill6 = 29
    bars1 = 30
    red_card = 31
    grill7 = 32
    sink = 33
    grill8 = 34
    drawing = 35
    car = 36
    empty_bottle = 37
    car2 = 38
    fuel = 39
    sailboat = 40
    lever1 = 41
    lever2 = 42
    statue = 43
    platform3 = 44
    lever3 = 45
    lever4 = 46
    lever5 = 47
    platform4 = 48
    platform5 = 49
    platform6 = 50
    book_of_bu = 51
    runes = 52
    hair_dryer = 53
    proto_pack = 54
    museum_alarm = 55
    museum_door = 56
    pirate_flag = 57
    golden_key = 58
    treasure_chest = 59
    gawley_horn = 60
    sendell_medallion = 61
    gold_door = 62
    seal_sendell = 63
    blue_card = 64
    grill9 = 65
    seal_sendell2 = 66
    marked_stone = 67
    eclipse_stone = 68
    magic_flute = 69
    blue_door = 70
    red_door = 71
    clear_water_lake = 72
    bottle_clear_water = 73
    guitar = 74
    stone1 = 75
    safe = 76
    safe_key = 77
    saber = 78
    architect_pass = 79
    tele_pod = 80
    computer = 81
    stone2 = 82
    stone3 = 83

    guard1 = 100
    technician1 = 101
    player = 102
    soldier1 = 103
    robobunny1 = 104
    shopkeeper1 = 105
    max_ = 106
    anthony = 107
    julien = 108
    soldier2 = 109
    guard2 = 110
    wally = 111
    chamonix = 112
    agen = 113
    agen2 = 114
    clermont_ferrand = 115
    brenne = 116
    trier = 117
    morvan = 118
    morvan2 = 119
    montbard = 120
    astronomer = 121
    groboclone1 = 122
    locksmith = 123
    maurice = 124
    clermont_ferrand2 = 125
    clermont_ferrand3 = 126
    aubigny = 127
    olivet = 128
    olivet2 = 129
    julien2 = 130
    wally = 131
    wally2 = 132
    wally3 = 133
    aubigny2 = 134
    buzancais = 135
    ruffec = 136
    baldino = 137
    fenioux = 138
    salesman = 139
    baldino2 = 140
    baldino3 = 141
    alarm_tech = 142
    elf = 143
    sever = 144
    dynofly = 145
    tartas = 146
    candanchu = 147
    graus = 148
    painter = 149
    soldier3 = 150
    soldier4 = 151
    soldier5 = 152
    zoe = 153
    funfrock = 154
    funfrock2 = 155
    fenioux2 = 156
    olivet3 = 157
    julien3 = 158
    clone1 = 159
    tartas2 = 160

    max1 = 200
    max2 = 201
    trick_guard = 202
    talk_to_brenne = 203
    water_supply = 204
    mstone2_exit = 205
    zoe_taken = 206
    zoe_taken2 = 207
    safe_note = 208
    lake_ice_breaking = 209

    legend1 = 400
    fall = 401  # move that falls through to the map below


items_by_id = {v:k for k,v in ID.__dict__.items()}
descr_by_id = copy(items_by_id)
descr_by_id.update(
    {
     14: 'a jar of syrup',
     10: 'a green heart',
     11: 'a simple key',
     ID.jar_syrup: 'a jar of raspberry syrup',
    }
)

conversations = {
    ID.robobunny1: ['...'],
}

def mkcell():
    return [blank]

def mkrow():
    return [mkcell() for _ in range(WIDTH)]


class Loc:
    def __init__(self, x, y):
        self.y, self.x = y, x

    def __iter__(self):
        yield self.x
        yield self.y

    def __getitem__(self, i):
        return (self.x, self.y)[i]

    def __repr__(self):
        return str((self.x, self.y))

    def __eq__(self, l):
        if isinstance(l, Loc):
            return (self.x, self.y) == (l.x, l.y)

    def mod(self, y=0, x=0):
        new = copy(self)
        new.y += y
        new.x += x
        return new

    def mod_r(self):
        return self.mod(0, 1)

    def mod_l(self):
        return self.mod(0, -1)

    def mod_d(self):
        return self.mod(1, 0)

    def mod_u(self):
        return self.mod(-1, 0)

def map_to_board(_map):
    l = map_to_loc[_map]
    return boards[l.y][l.x]


class Board:
    def __init__(self, loc, _map):
        self.B = [mkrow() for _ in range(HEIGHT)]
        self.guards = []
        self.soldiers = []
        self.labels = []
        self.doors = []
        self.spawn_locations = {}
        self.trigger_locations = {}
        self.misc = []
        self.seen = set()   # seen locations
        self.loc = loc
        self._map = str(_map)
        self.state = 0
        map_to_loc[str(_map)] = loc

    def __repr__(self):
        return f'<B: {self._map}>'

    def __getitem__(self, loc):
        o = self.B[loc.y][loc.x][-1]
        if isinstance(o,int): o = objects[o]
        return o

    def __iter__(self):
        for y, row in enumerate(self.B):
            for x, cell in enumerate(row):
                yield Loc(x,y), cell

    def board_1(self):
        containers, crates, doors, specials = self.load_map(self._map)
        containers[3].add1(ID.key1)
        Item(self, Blocks.platform, 'mobile platform', specials[1], id=ID.platform1)
        g = Guard(self, specials[1], id=ID.guard1)
        self.guards = [g]
        Item(self, Blocks.grill, 'grill', specials[2], id=ID.grill1)
        p = Player(self, specials[3], id=ID.player)
        BlockingItem(self, rock, '', specials[4], id=ID.stone3, color=gray_col())
        return p

    # -----------------------------------------------------------------------------------------------
    def line(self, a, b):
        for x in range(a.x,b.x+1):
            yield Loc(x,a.y)

    def color_line(self, a, b, col):
        l=[]
        for loc in self.line(a,b):
            l.append((loc,col))
        return l

    def load_map(self, map_num, for_editor=0):
        _map = open(f'maps/{map_num}.map').readlines()
        self.crates = crates = []
        self.containers = containers = []
        self.doors = doors = []
        self.specials = specials = defaultdict(list)

        for y in range(HEIGHT):
            for x in range(79):
                char = _map[y][x]
                loc = Loc(x,y)
                if char != blank:
                    if char==rock:
                        BlockingItem(self, Blocks.rock, '', loc, color=gray_col())

                    elif char in (Blocks.cornice_l, Blocks.cornice_r):
                        BlockingItem(self, char, 'cornice', loc, color=gray_col())

                    if char=='W':
                        Item(self, Blocks.window, '', loc, color='blue')   # window

                    elif char=='D':
                        d = Item(self, Blocks.door, 'steel door', loc, type=Type.door2)
                        doors.append(d)

                    elif char in Blocks.flowers:
                        col = rand_color((60,200), (60,200), (60,200))
                        Item(self, char, 'flower', loc, color=col)

                    elif char=='g':
                        Item(self, Blocks.grn_heart, 'grn_heart', loc, id=ID.grn_heart)

                    elif char==Blocks.locker or char=='o':
                        l = Locker(self, loc)
                        containers.append(l)

                    elif char=='C':
                        c = Item(self, choice(Blocks.crates), 'crate', loc)
                        crates.append(c)

                    elif char=='s':
                        Item(self, Blocks.sunflower, 'sunflower', loc)

                    elif char==Blocks.sharp_rock:
                        Item(self, Blocks.sharp_rock, 'sharp_rock', loc, type=Type.deadly)

                    elif char == Blocks.snowman:
                        Item(self, Blocks.snowman, 'snowman', loc)
                    elif char == Blocks.snowflake:
                        Item(self, Blocks.snowflake, 'snowflake', loc)

                    elif char==Blocks.rock3:
                        BlockingItem(self, Blocks.rock3, 'rock', loc)

                    elif char==Blocks.block1:
                        Item(self, Blocks.block1, 'block', loc, type=Type.door_top_block)

                    elif char==Blocks.smoke_pipe:
                        Item(self, Blocks.smoke_pipe, 'smoke pipe', loc, type=Type.ladder)

                    elif char==Blocks.cactus:
                        col = rand_color(33, (60,255), (10,140))
                        Item(self, Blocks.cactus, 'cactus', loc, color=col)

                    elif char==Blocks.fireplace:
                        Item(self, Blocks.fireplace, 'fireplace', loc)

                    elif char==Blocks.stool:
                        Item(self, Blocks.stool, 'bar stool', loc)

                    elif char=='t':
                        Item(self, Blocks.tulip, 'tulip', loc)

                    elif char==Blocks.fountain:
                        Item(self, Blocks.fountain, 'water fountain basin', loc)

                    elif char==Blocks.dock_boards:
                        BlockingItem(self, Blocks.dock_boards, 'dock boards', loc)

                    elif char==Blocks.grill:
                        Item(self, Blocks.grill, 'barred window', loc)

                    elif char==Blocks.rubbish:
                        Item(self, Blocks.rubbish, 'pile of rubbish', loc, id=ID.rubbish1)

                    elif char == Blocks.books[0]:
                        Item(self, choice(Blocks.books), 'book', loc)

                    elif char == Blocks.books[1]:
                        Item(self, Blocks.books[1], 'book', loc)

                    elif char==Blocks.shelves:
                        s = Item(self, Blocks.shelves, 'shelves', loc, type=Type.container)
                        containers.append(s)

                    elif char==Blocks.ferry_l:
                        Item(self, 'ferry', 'ferry', loc, id=ID.ferry)

                    elif char=='/':
                        BlockingItem(self, Blocks.angled1, '', loc)

                    elif char=='\\':
                        BlockingItem(self, Blocks.angled2, '', loc)

                    # -----------------------------------------------------------------------------------------------
                    elif char == OldBlocks.tree1:
                        col = rand_color(33, (60,255), (10,140))
                        Item(self, Blocks.tree1, 'tree', loc, color=col)

                    elif char == OldBlocks.tree2:
                        col = rand_color(33, (60,255), (10,140))
                        Item(self, Blocks.tree2, 'tree', loc, color=col)

                    elif char==OldBlocks.ladder:
                        Item(self, Blocks.ladder, 'ladder', loc, type=Type.ladder, color=gray_col())

                    elif char==OldBlocks.door or char=='d':
                        d = Item(self, Blocks.door, 'door', loc, type=Type.door1)
                        doors.append(d)

                    elif char==OldBlocks.rock2:
                        Item(self, Blocks.rock2, '', loc)

                    elif char==OldBlocks.steps_l:
                        BlockingItem(self, Blocks.steps_l, '', loc, color=gray_col())

                    elif char==OldBlocks.steps_r:
                        BlockingItem(self, Blocks.steps_r, '', loc, color=gray_col())

                    elif char==OldBlocks.platform2:
                        BlockingItem(self, Blocks.platform2, '', loc)

                    elif char==OldBlocks.elephant:
                        g = Grobo(self, loc)
                        specials[Blocks.elephant_l].append(g)

                    elif char==OldBlocks.water:
                        Item(self, Blocks.water, 'water', loc, type=Type.water)

                    elif char==OldBlocks.soldier:
                        s = Soldier(self, loc)
                        self.soldiers.append(s)

                    elif char==OldBlocks.cupboard or char=='c':
                        c = Cupboard(self, loc)
                        containers.append(c)

                    elif char in '0123456789':
                        specials[int(char)] = loc
                        if for_editor:
                            self.put(char, loc)
        return containers, crates, doors, specials


    def locs_rectangle(self, a, b):
        for y in range(a.y, b.y+1):
            for x in range(a.x, b.x+1):
                yield Loc(x,y)

    def get_all(self, loc):
        return [n for n in self.B[loc.y][loc.x] if n!=blank]

    def get_all_obj_and_player(self, loc):
        return [objects.get(n) or n for n in self.B[loc.y][loc.x] if not isinstance(n, str)]

    def get_all_obj(self, loc):
        return [objects.get(n) or n for n in self.B[loc.y][loc.x] if not isinstance(n, str) and n!=ID.player]

    def get_top_obj(self, loc):
        return last(self.get_all_obj(loc))

    def get_ids(self, loc):
        if isinstance(loc, Loc):
            loc = [loc]
        lst = []
        for l in loc:
            lst.extend(self.get_all(l))
        lst = [getattr(x, 'id', None) or x for x in lst]
        return lst

    def get_types(self, loc):
        return types(self.get_all(loc))

    def found_type_at(self, type, loc):
        def get_obj(x):
            return objects.get(x) or x
        return any(get_obj(x).type==type for x in self.get_all_obj(loc))

    def draw(self):
        blt.clear()
        blt.color("white")
        visible = set()
        def visit(x,y):
            visible.add((x,y))
        def is_blocked(x,y):
            return self.is_blocked(Loc(x,y))

        x,y = obj_by_attr.player.loc

        fov.field_of_view(x, y, WIDTH, HEIGHT, 5, visit, is_blocked)

        for y, row in enumerate(self.B):
            for x, cell in enumerate(row):
                is_seen = (x,y) in self.seen
                is_visible_now = (x,y) in visible
                if is_seen or is_visible_now:
                    # tricky bug: if an 'invisible' item put somewhere, then a being moves on top of it, it's drawn, but
                    # when it's moved out, the invisible item is drawn, but being an empty string, it doesn't draw over the
                    # being's char, so the 'image' of the being remains there, even after being moved away.
                    cell = [c for c in cell if getattr(c,'char',None)!='']
                    a = last(cell)
                    if isinstance(a, int):
                        a = objects[a]
                    if getattr(a, 'type', None)==Type.water:
                        a = f'[color=blue]{a}[/color]'
                    col = getattr(a, 'color', None)
                    if (is_seen and not isinstance(a, Being)) or is_visible_now:
                        if col:
                            a = f'[color={col}]{a}[/color]'
                        Windows.win.addstr(y, x, str(a))
                    self.seen.add((x,y))
        for y,x,txt in self.labels:
            Windows.win.addstr(y,x,txt)
        self.display_status()
        Misc.status = []
        Windows.win2.addstr(0,74, str(self._map))
        Windows.win2.addstr(0,0, Misc.stats)
        Windows.refresh()

    def display_status(self):
        for n, l in enumerate(Misc.status):
            Windows.win2.addstr(n+1, 0, l)

    def put(self, obj, loc=None):
        """
        If loc is not given, try to use obj's own location attr.
        If loc IS given, update obj's own location attr if possible.
        """
        loc = loc or obj.loc
        if not isinstance(obj, (int, str)):
            obj.board_map = self._map
            obj.loc = loc
        try:
            self.B[loc.y][loc.x].append(getattr(obj, 'id', None) or obj)
        except Exception as e:
            sys.stdout.write(str(loc))
            raise

    def remove(self, obj, loc=None):
        """
        If loc is not given, use obj's own location attr.
        """
        loc = loc or obj.loc
        cell = self.B[loc.y][loc.x]
        cell.remove(obj if obj in cell else obj.id)

    def is_blocked(self, loc):
        for x in self.get_all(loc):
            if isinstance(x, int):
                x = objects[x]
            if x in BLOCKING or getattr(x, 'type', None) in BLOCKING:
                return True
        return False

    def is_being(self, loc):
        for x in self.get_all(loc):
            if getattr(x, 'is_being', 0):
                return x
        return False

    def avail(self, loc):
        return not self.is_blocked(loc)

    def display(self, txt):
        w = max(len(l) for l in txt) + 1
        X,Y = 5, 2
        for y, ln in enumerate(txt):
            blt.clear_area(X, Y+y+1, w+3, 1)
            Windows.win.addstr(Y+y+1, X, ' ' + ln)
        Windows.refresh()
        blt.read()

def gray_col():
    c = hex(randrange(120,150))[2:]
    return '#ff%s%s%s' % (c,c,c)

def rand_color(r, g, b):
    r = (r,r+1) if isinstance(r,int) else r
    g = (g,g+1) if isinstance(g,int) else g
    b = (b,b+1) if isinstance(b,int) else b
    return '#ff%s%s%s' % (
        hex(randrange(*r))[2:],
        hex(randrange(*g))[2:],
        hex(randrange(*b))[2:],
    )

def chk_oob(loc, y=0, x=0):
    return 0 <= loc.y+y <= HEIGHT-1 and 0 <= loc.x+x <= 78

def chk_b_oob(loc, y=0, x=0):
    h = len(boards)
    w = len(boards[1])
    newx, newy = loc.x+x, loc.y+y
    return 0 <= newy <= h-1 and 0 <= newx <= w-1 and boards[newy][newx]

def ids(lst):
    return [x.id for x in lst if not isinstance(x, str)]

def types(lst):
    return [x.type for x in lst if not isinstance(x, str)]


class BeingItemMixin:
    is_player = 0
    state = 0
    color = None

    def __str__(self):
        c=self.char
        if isinstance(c, str) and len(c)>1:
            if '_' not in c:
                c += '_l'
                self.char = c
            c = getattr(Blocks, c)
        if isinstance(c, int):
            c = '[U+{}]'.format(hex(c)[2:])
        return c

    def tele(self, loc):
        self.B.remove(self)
        self.put(loc)

    def put(self, loc):
        self.loc = loc
        B=self.B
        B.put(self)
        if self.is_player and ID.platform1 in B.get_ids(loc) and loc==B.specials[5].mod_r():
            Event(B).animate_arc(obj_by_attr.platform1, B.specials[1], carry_item=self, height=3, sleep_time=0.01)

    def has(self, id):
        return self.inv.get(id)

    def remove1(self, id):
        self.inv[id] -= 1

    def add1(self, id, n=1):
        self.inv[id] += n

    def move_to_board(self, _map, specials_ind=None, loc=None):
        to_B = map_to_board(_map)
        if specials_ind is not None:
            loc = to_B.specials[specials_ind]
        if self.id in self.B.get_all(self.loc):
            self.B.remove(self)
        self.loc = loc
        to_B.put(self)
        self.board_map = to_B._map
        for c in to_B.containers:
            if not any(c.inv.values()):
                if random()>0.6: c.add1(ID.coin)
                if random()>0.6: c.add1(ID.grn_heart)
        return to_B

    @property
    def B(self):
        return map_to_board(self.board_map)


class Item(BeingItemMixin):
    board_map = None

    def __init__(self, B, char, name, loc=None, put=True, id=None, type=None, color=None):
        self.char, self.name, self.loc, self.id, self.type, self.color = char, name, loc, id, type, color

        if B:
            self.board_map = B._map

        self.inv = defaultdict(int)
        if id:
            objects[id] = self
        if B and put:
            B.put(self)

    def __repr__(self):
        return f'<I: {self.char}>'

    def move(self, dir, n=1, fly=False):
        m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0))[dir]
        for _ in range(n):
            new = self.loc.mod(*m)
            self.B.remove(self)
            self.loc = new
            self.B.put(self)

class BlockingItem(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = Type.blocking

class TriggerEventLocation(Item):
    """Location that triggers an event."""
    def __init__(self, B, loc, evt, id=None):
        super().__init__(B, '', '', loc, id=id, type=Type.event_trigger)
        self.evt = evt

class Locker(Item):
    def __init__(self, B, loc):
        super().__init__(B, Blocks.locker, 'locker', loc, id=ID.locker, type=Type.container)
        if random()>.6:
            self.add1(ID.coin)
        elif random()>.6:
            self.add1(ID.grn_heart)

class Cupboard(Item):
    def __init__(self, B, loc):
        super().__init__(B, Blocks.cupboard, 'cupboard', loc, type=Type.container)
        # ugly: this doesn't work in the map editor because `objects` dict doesn't have these items
        try:
            if random()>.5:
                self.add1(ID.coin)
            elif random()>.7:
                self.add1(ID.grn_heart)
        except: pass

class Being(BeingItemMixin):
    stance = Stance.normal
    health = None
    is_being = 1
    is_player = 0
    hostile = 0
    type = None
    char = None

    def __init__(self, B, loc=None, put=True, id=None, name=None, state=0, hostile=False, health=None, char='?', color=None):
        self.id, self.loc, self.name, self.state, self.hostile, self.color  = id, loc, name, state, hostile, color
        if B:
            self.board_map = B._map

        self.health = self.health or health or 5
        self.char = self.char or char
        self.inv = defaultdict(int)
        self.kashes = 0
        if DBG:
            self.kashes = 54
        if id:
            objects[id] = self
        if put:
            B.put(self)

    @property
    def _name(self):
        return self.name or self.__class__.__name__

    @property
    def fight_stance(self):
        return self.stance==Stance.fight

    @property
    def sneaky_stance(self):
        return self.stance==Stance.sneaky

    def talk(self, being, dialog=None, yesno=False, resp=False):
        if isinstance(dialog, int):
            dialog = conversations.get(dialog)
        being = objects.get(being) or being
        loc = being.loc
        if isinstance(dialog, str):
            dialog = [dialog]
        dialog = dialog or conversations[being.id]
        x = min(loc.x, 60)
        multichoice = 0

        for m, txt in enumerate(dialog):
            lst = []
            if isinstance(txt, (list,tuple)):
                multichoice = len(txt)
                for n, t in enumerate(txt):
                    lst.append(f'{n+1}) {t}')
                txt = '\n'.join(lst)
            x = min(40, x)
            w = 78 - x
            if yesno:
                txt += ' [[Y/N]]'
            lines = (len(txt) // w) + 4
            txt_lines = wrap(txt, w)
            txt = '\n'.join(txt_lines)
            offset_y = lines if loc.y<8 else -lines

            y = max(0, loc.y+offset_y)
            W = max(len(l) for l in txt_lines)
            blt.clear_area(x+1, y+1, W, len(txt_lines))
            Windows.win.addstr(y+1,x+1, txt)
            Windows.refresh()

            if yesno:
                # TODO in some one-time dialogs, may need to detect 'no' explicitly
                k = parsekey(blt.read())
                return k in tuple('yY')

            elif multichoice:
                for _ in range(2):
                    k = parsekey(blt.read())
                    try:
                        k=int(k)
                    except ValueError:
                        k = 0
                    if k in range(1, multichoice+1):
                        return k

            if resp and m==len(dialog)-1:
                i=''
                Windows.win2.addstr(1,0, '> ')
                Windows.refresh()
                for _ in range(10):
                    k = parsekey(blt.read())
                    if k==' ': break
                    i+=k
                    Windows.win2.addstr(1,0, '> '+i)
                    Windows.refresh()
                return i

            Windows.refresh()
            k=None
            while k!=' ':
                k = parsekey(blt.read())
            # prompt()
            self.B.draw()

    def handle_directional_turn(self, dir, loc):
        """Turn char based on which way it's facing."""
        if hasattr(Blocks, self.char) and self.char[-2:] in ('_r','_l','_f','_b'):
            to_r = to_l = False
            if loc:
                to_r = loc.x>self.loc.x
                to_l = loc.x<self.loc.x
            if dir and dir =='l' or to_r:
                self.char = self.char[:-2]+'_r'
            elif dir and dir =='h' or to_l:
                self.char = self.char[:-2]+'_l'

    def _move(self, dir, fly=False):
        m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0))[dir]
        if chk_oob(self.loc, *m):
            return True, self.loc.mod(*m)
        else:
            if self.is_player and chk_b_oob(self.B.loc, *m):
                return LOAD_BOARD, self.B.loc.mod(*m)
        return 0, 0

    def move(self, dir, fly=False):
        B = self.B
        rv = self._move(dir, fly)
        if rv and (rv[0] == LOAD_BOARD):
            return rv
        new = rv[1]
        if new and isinstance(B[new], Being):
            being = B[new]
            if self.fight_stance or self.hostile:
                self.attack(being)
            else:
                self.switch_places()    # TODO support direction
            return True, True

        # TODO This is a little messy, doors are by type and keys are by ID
        if new and B.found_type_at(Type.door1, new) and self.has(ID.key1):
            d = B[new]
            B.remove(B[new])    # TODO will not work if something is on top of door
            self.remove1(ID.key1)
            status('You open the door with your key')
            return None, None

        if new and B.is_blocked(new):
            if dir not in 'hlHL':
                new = None
            else:
                new = new.mod(-1,0)
                if B.is_blocked(new):
                    new = None
                    if self.fight_stance:
                        status('BANG')

        if new:
            B.remove(self)
            self.handle_directional_turn(dir, new)
            if not fly:
                new = self.fall(new)
            if new[0] == LOAD_BOARD or new[0] is None:
                return new
            self.loc = new

            if self.is_player:
                self.handle_player_move(new)

            # this needs to be after previous block because the block looks at `top_obj` which would always be the being
            # instead of an event trigger item
            self.put(new)
            Windows.refresh()
            return True, True
        return None, None

    def handle_player_move(self, new):
        B=self.B
        pick_up = [ID.key1, ID.key2, ID.key3, ID.coin]
        top_obj = B.get_top_obj(new)
        items = B.get_all_obj(new)
        if top_obj:
            if isinstance(top_obj, int):
                top_obj = objects[top_obj.id]
            if top_obj.type == Type.event_trigger:
                triggered_events.append(top_obj.evt)

        for x in reversed(items):
            if x.id == ID.coin:
                self.kashes += 1
                B.remove(x, new)
            elif x.id == ID.grn_heart:
                self.health = min(MAX_HEALTH, self.health+1)
                B.remove(x)
            elif x.id in pick_up:
                self.inv[x.id] += 1
                B.remove(x, new)

        names = [o.name for o in B.get_all_obj(new) if o.name]

        plural = len(names)>1
        names = ', '.join(names)
        if names:
            a = ':' if plural else ' a'
            status(f'You see{a} {names}')

    def fall(self, new):
        fly = False
        B=self.B
        if B.found_type_at(Type.ladder, new):
            if self.is_player:
                self.char = 'player_b'
        else:
            new2 = new
            while 1:
                # TODO: these may overdraw non-blocking items; it's an ugly hack but creates a nice fall animation
                # for now
                Windows.win.addstr(self.loc.y, self.loc.x, ' ')
                Windows.win.addstr(new2.y, new2.x, ' ')
                new2 = new2.mod(1,0)
                if chk_oob(new2) is False:
                    self.loc = new
                    return LOAD_BOARD, ID.fall

                if getattr(B[new2], 'type', None) == Type.water:
                    triggered_events.append(DieEvent)
                    status('You fall into the water and drown...')
                    return None, None

                if B.found_type_at(Type.deadly, new2):
                    triggered_events.append(DieEvent)
                    status('You fall down onto sharp rocks and die of sustained wounds...')
                    return None, None

                if chk_oob(new2) and B.avail(new2) and not B.found_type_at(Type.ladder, new2):
                    # ugly hack for the fall animation
                    Windows.win.addstr(new2.y, new2.x, str(self))
                    sleep(0.05)
                    Windows.refresh()
                    new = new2
                else:
                    break
        return new

    def attack(self, obj):
        if abs(self.loc.x - obj.loc.x) <= 1 and \
           abs(self.loc.y - obj.loc.y) <= 1:
                self.hit(obj)
        else:
            # TODO handle vertical, ladders etc; real pathfinding
            if self.loc.x < obj.loc.x:
                self.move('l')
            else:
                self.move('h')

    def hit(self, obj):
        B=self.B
        if obj.health:
            obj.health -= 1
            status(f'{self} hits {obj} for 1pt')
            if obj.is_being and not obj.is_player:
                obj.hostile = 1

            # KILL
            if obj.health <=0:
                B.remove(obj)
                if random()>0.6:
                    Item(B, Blocks.coin, 'coin', obj.loc, id=ID.coin)
                elif random()>0.6:
                    Item(B, Blocks.grn_heart, 'heart', obj.loc, id=ID.grn_heart)

                for id, qty in obj.inv.items():
                    # TODO note item will not have a `loc` (ok for now)
                    # it.loc = obj.loc
                    B.put(id, obj.loc)

    def switch_places(self):
        B = self.B
        r,l = self.loc.mod_r(), self.loc.mod_l()
        ro = lo = None
        if chk_oob(r): ro = B[r]
        if chk_oob(l): lo = B[l]

        if isinstance(ro, Being):
            B.remove(ro)
            B.remove(self)
            loc = self.loc
            self.put(r)
            ro.put(loc)
            status(f'{self} moved past {ro._name}')
        elif isinstance(lo, Being):
            B.remove(lo)
            B.remove(self)
            loc = self.loc
            self.put(l)
            lo.put(loc)
            status(f'{self} moved past {lo._name}')

    def loot(self, B, cont):
        items = {k:v for k,v in cont.inv.items() if v}
        lst = []
        for x in items:
            if x==ID.grn_heart:
                self.health = min(MAX_HEALTH, self.health+1)
            if x==ID.golden_key:
                status('You have found the Golden Key that the runes at cave under your home spoke of!')
            if x==ID.coin:
                self.kashes+=1
            else:
                self.inv[x] += cont.inv[x]
            cont.inv[x] = 0
            # pdb(objects, x)
            lst.append(str(objects[x]))
        status('You found {}'.format(', '.join(lst)))
        if not items:
            status(f'{cont.name} is empty')

    def action(self):
        B=self.B
        cont = last( [x for x in B.get_all_obj(self.loc) if x.type==Type.container] )
        ids = B.get_all_obj(self.loc)
        self.char = 'player_f'

        r,l = self.loc.mod_r(), self.loc.mod_l()
        rd, ld = r.mod_d(), l.mod_d()
        locs = [self.loc]
        obj = obj_by_attr

        if chk_oob(r): locs.append(r)
        if chk_oob(l): locs.append(l)
        if chk_oob(rd): locs.append(rd)
        if chk_oob(ld): locs.append(ld)

        def is_near(id):
            return getattr(ID, id) in B.get_ids(locs)

        if cont:
            self.loot(B, cont)

        elif is_near('red_door') and self.has(ID.red_card):
            B.remove(obj.red_door)

        elif is_near('blue_door') and self.has(ID.blue_card):
            B.remove(obj.blue_door)

        elif is_near('sailboat'):
            self.use_sailboat()
        else:
            loc = self.loc.mod(1,0)
            x = B[loc] # TODO won't work if something is in the platform tile
            if x and getattr(x, 'id', None)==ID.platform_top1:
                PlatformEvent2(B).go()

    def talk_to_julien(self):
        obj = obj_by_attr
        have_bb = self.has('book_of_bu')
        self.talk(obj.julien, (ID.julien if not have_bb else ID.julien2))
        if have_bb:
            obj.aubigny.state = 1
        y = self.talk(obj.julien, ID.julien3, yesno=1)
        if y:
            if self.kashes>=10:
                self.add1(ID.ferry_ticket, 5)
                self.kashes -= 10

    def use_car(self):
        # if 1:     # for testing
        B=self.B
        obj = obj_by_attr
        if obj.maurice and obj.maurice.state == 1:
            if B._map == 'top3':
                choices = ['Water Tower', 'Port Beluga']
            elif B._map == 'wtower':
                choices = ['Old town', 'Port Beluga']
            elif B._map == 'beluga':
                choices = ['Old town', 'Water Tower']
        else:
            if B._map == 'top3': choices = ['Water Tower']
            elif B._map == 'wtower': choices = ['Old town']
        ch = self.talk(ID.car, ['Where would you like to go?', choices])
        if ch:
            ch = choices[ch-1]
            desc_to_map = {'Water Tower': 'wtower', 'Port Beluga': 'beluga', 'Old town': 'top3'}
            ch = desc_to_map[ch]
            if self.has(ID.fuel):
                triggered_events.append((TravelByCarEvent, dict(dest=ch)))
                self.remove1(ID.fuel)
            else:
                status("It looks like you don't have any petrol!")

    def talk_to_olivet(self):
        obj = obj_by_attr
        self.talk(obj.olivet, ID.olivet2 if self.has(ID.book_of_bu) else ID.olivet)
        if self.has(ID.magic_flute):
            y = self.talk(obj.olivet, ID.olivet3, yesno=1)
            if y:
                self.inv[ID.magic_flute] = 0
                Item(None, 'g', 'guitar', id=ID.guitar)
                self.inv[ID.guitar] = 1
        elif self.has(ID.guitar):
            y = self.talk(obj.olivet, "Would you like to return the guitar and get your flute back?", yesno=1)
            if y:
                self.inv[ID.magic_flute] = 1
                self.inv[ID.guitar] = 0

    def use_sailboat(self):
        dests = [('White Leaf Desert', 'desert1'), ('Port Beluga', 'beluga')]
        if obj_by_attr.sailboat.state==1:
            dests.append(('Proxima Island', 'proxima1'))
            dests.append(('Himalayi Mountains', 'himalaya1'))
        dests = [(n,m) for n,m in dests if m!=self.B._map]
        lnames = [n for n,m in dests]
        y = self.talk(self, f'Would you like to use the sailboat for 10 kashes?', yesno=1)
        if y:
            if self.kashes>=10:
                self.kashes-=10
                ch = self.talk(self, [f'Where would you like to go?', lnames])
                if ch:
                    dest = dests[ch-1]
                    triggered_events.append((TravelBySailboat, dict(dest=dest[1], dests=dests)))
            else:
                status("Looks like you don't have enough kashes!")

    def use(self):
        if not self.inv:
            return
        B=self.B
        ascii_letters = string.ascii_letters
        x = 10
        y = 2

        lst = []
        for n, (id,qty) in enumerate(self.inv.items()):
            item = objects[id]
            lst.append(f' {ascii_letters[n]}) {item.name:4} - {qty} ')
        w = max(len(l) for l in lst)
        blt.clear_area(x, y, w+2, len(lst))
        for n, l in enumerate(lst):
            Windows.win.addstr(y+n, x, l)
        Windows.refresh()

        ch = parsekey(blt.read())
        item_id = None
        if ch and ch in ascii_letters:
            try:
                item_id = list(self.inv.keys())[string.ascii_letters.index(ch)]
            except IndexError:
                return
        if not item_id: return
        locs = [self.loc]
        if chk_oob(self.loc, x=1):
            # need this for Brundle island only, for the sendell seal in the wall
            locs.append(self.loc.mod_r())
        def is_near(id):
            return getattr(ID, id) in B.get_ids(locs)
        obj = obj_by_attr
        seal2 = obj.seal_sendell2

        if item_id == ID.magic_flute and is_near('clear_water_lake'):
            self.talk(self, ID.lake_ice_breaking)
            for loc in B.line(B.specials[1], B.specials[2]):
                if B[loc] == rock:
                    B.remove(rock, loc)
                Item(B, Blocks.water, '', loc, type=Type.water)
            self.inv[ID.empty_bottle] = 0
            Item(None, Blocks.bottle, 'Bottle of clear water', id=ID.bottle_clear_water)
            self.inv[ID.bottle_clear_water] = 1

        elif item_id == ID.gawley_horn and is_near('stone2'):
            self.B.remove(obj.stone2)

        elif item_id == ID.gawley_horn and is_near('seal_sendell'):
            triggered_events.append(GoToElfMapEvent)

        elif item_id == ID.gawley_horn and is_near('seal_sendell2') and seal2.state==0:
            status('You see a passage opening up in the seal stone.')
            obj.seal_sendell2.state = 1

        elif item_id == ID.proto_pack:
            pp = obj.proto_pack
            pp.state = not pp.state
            status('Proto-pack is ' + ('on' if pp.state else 'off'))

        elif is_near('water_supply') and item_id == ID.jar_syrup:
            status('You add raspberry syrup to the water supply')
            self.inv[item_id] -=1
            self.inv[ID.empty_bottle] += 1
            # a little hacky, would be better to add a water supply obj and update its state
            obj.clermont_ferrand.state = 2
        else:
            status('Nothing happens')
        Windows.refresh()

    def get_top_item(self):
        x = self.B[self.loc]
        return None if x==blank else x

    @property
    def alive(self):
        return self.health>0

    @property
    def dead(self):
        return not self.alive

class Quest:
    pass

def first(x):
    return x[0] if x else None
def last(x):
    return x[-1] if x else None

def pdb(*arg):
    pass
    # curses.nocbreak()
    # Windows.win.keypad(0)
    # curses.echo()
    # curses.endwin()
    import pdb; pdb.set_trace()

class Event:
    done = False
    def __init__(self, B, **kwargs):
        self.B = map_to_board(B._map)
        self.player = objects[ID.player]
        self.kwargs = kwargs

    def animate_arc(self, item, to_loc, height=1, carry_item=None, sleep_time=SLP*4):
        for _ in range(height):
            self.animate(item, 'k', n=height, carry_item=carry_item, sleep_time=sleep_time)
        a,b = item.loc, to_loc
        dir = 'h' if a.x>b.x else 'l'
        self.animate(item, dir, n=abs(a.x-b.x), carry_item=carry_item, sleep_time=sleep_time)
        for _ in range(height):
            self.animate(item, 'j', n=height, carry_item=carry_item, sleep_time=sleep_time)

    def animate(self, items, dir, B=None, n=999, carry_item=None, sleep_time=SLP*4):
        if not isinstance(items, SEQ_TYPES):
            items = [items]
        B = B or self.B
        for _ in range(n):
            for item in items:
                item.move(dir)
                if carry_item:
                    carry_item.move(dir, fly=1)
                B.draw()
                sleep(sleep_time)
                if item.loc.x==0:
                    B.remove(item)
                    if carry_item:
                        B.remove(carry_item)
                    return

def status(msg):
    Misc.status.append(msg)
    Windows.win2.addstr(2,0,msg)

class PortalEvent(Event):
    once = False
    def go(self):
        _map = self.kwargs.get('map')
        spawn_specials_ind = self.kwargs.get('spawn_specials_ind')
        return self.player.move_to_board(_map, spawn_specials_ind)

class OneTimePortalEvent(PortalEvent):
    once = True

class MovePlatform3Event(Event):
    once=False
    def go(self):
        B = self.B
        p = obj_by_attr.platform3
        a,b = B.specials[4], B.specials[5]
        i = B[p.loc.mod_u()]
        if i==p or i is blank: i=None
        self.animate_arc(p, to_loc=(a if p.loc==b else b), carry_item=i)

class TravelByFerry(Event):
    once=False
    def go(self):
        dest = self.kwargs.get('dest')
        player = objects[ID.player]
        B = map_to_board('sea1')
        ferry = obj_by_attr.ferry
        B.put(ferry, Loc(78,GROUND+1))
        self.animate(ferry, 'h', B=B)
        status('The ferry took you to ' + ('Principal Island' if dest=='8' else 'Citadel Island'))
        if dest == '8':
            ferry.move_to_board(dest, 0)
            return player.move_to_board('8', 9)
        elif dest == '7':
            ferry.move_to_board(dest, 8)
            return player.move_to_board('7', 9)

class EndGameEvent(Event):
    pass

class PlatformEvent2(Event):
    once=True
    def go(self):
        pl = self.player
        dir = 'k' if pl.loc.y==GROUND else 'j'
        self.animate(obj_by_attr.platform_top1, dir, carry_item=pl, n=4)

class DieEvent(Event):
    """Die or get arrested and sent back to jail."""
    once=False
    def go(self):
        print ("in DieEvent go()")
        return Saves().load('start')

def rev_dir(dir):
    return dict(h='l',l='h',j='k',k='j')[dir]

class Timer:
    def __init__(self, turns, evt):
        self.turns, self.evt = turns, evt

class Player(Being):
    char = 'player'
    health = 10
    is_player = 1
    stance = Stance.sneaky
    name = 'Player'

class Guard(Being):
    char = '\u001d'
    health = 3

class Soldier(Being):
    health = 10
    char = 'soldier'

class Technician(Being):
    char = '\u001e'

class RoboBunny(Being):
    char = 'rabbit'

class Clone(Being):
    char = 'elephant'

class ShopKeeper(Being):
    char = Blocks.monkey

class Grobo(Being):
    char = 'elephant'


class Win1:
    @staticmethod
    def addstr(y, x, text, color=None):
        if color:
            text = f'[color={color}]{text}[/color]'
        if isinstance(text, str):
            blt.puts(x, y, text)
        else:
            blt.put(x, y, text)

class Win2:
    @staticmethod
    def addstr(y,x, text):
        blt.puts(x, y+16, text)

class Windows:
    win = Win1
    win2 = Win2

    @staticmethod
    def refresh():
        blt.refresh()


class Misc:
    status = []
    stats = ''

class Saves:
    saves = {}
    loaded = 0

    def load(self, name=None):
        for n in range(1,999):
            fn = f'saves/{n}.data'
            if not os.path.exists(fn+'.db'):
                n-=1
                fn = f'saves/{n}.data'
                break

        if name:
            fn = f'saves/{name}.data'
        if not os.path.exists(fn+'.db'):
            return

        sh = shelve.open(fn, protocol=1)
        self.saves = sh['saves']
        s = self.saves[name or n]
        boards[:] = s['boards']
        global objects, done_events

        done_events = s.get('done_events') or set()
        objects = s['objects']
        player = objects[ID.player]
        loc = player.loc
        bl = s['cur_brd']
        B = boards[bl.y][bl.x]
        return player, B

    def save(self, cur_brd, name=None):
        if not name:
            for n in range(1,999):
                fn = f'saves/{n}.data'
                name = str(n)
                if not os.path.exists(fn+'.db'):
                    break
        fn = f'saves/{name}.data'
        sh = shelve.open(fn, protocol=1)
        s = {}
        s['boards'] = boards
        s['cur_brd'] = cur_brd
        s['objects'] = objects
        s['done_events'] = done_events
        player = obj_by_attr.player
        bl = cur_brd
        B = boards[bl.y][bl.x]
        sh['saves'] = {name: s}
        sh.close()
        return B.get_all(player.loc), name

def dist(a,b):
    return max(abs(a.loc.x - b.loc.x),
               abs(a.loc.y - b.loc.y))

def main(load_game):
    blt.open()
    blt.set(f"window: resizeable=true, size=80x25, cellsize=auto, title='Little Adventure'; font: FreeMono.ttf, size={SIZE}")
    blt.color("white")
    blt.composition(True)

    blt.clear()
    blt.color("white")

    if not os.path.exists('saves'):
        os.mkdir('saves')
    Misc.is_game = 1
    win = Windows.win
    win2 = Windows.win2

    # generatable items
    coin = Item(None, Blocks.coin, 'coin', id=ID.coin)
    grn_heart = Item(None, Blocks.grn_heart, 'heart', id=ID.grn_heart)
    key1 = Item(None, Blocks.key, 'key', id=ID.key1)
    key2 = Item(None, Blocks.key, 'key', id=ID.key2)
    fuel = Item(None, Blocks.box1, 'fuel', id=ID.fuel)
    ft = Item(None, Blocks.ferry_ticket, 'ferry ticket', id=ID.ferry_ticket)

    objects[ID.ferry_ticket] = ft
    objects[ID.fuel] = fuel
    objects[ID.coin] = coin
    objects[ID.grn_heart] = grn_heart
    objects[ID.key1] = key1
    objects[ID.key2] = key2

    B = b1 = Board(Loc(0,MAIN_Y), 1)

    player = b1.board_1()
    if DBG:
        player.health = 100

    boards[:] = (
         [b1,None,None,None, None,None,None,None, None,None, None, None],
    )
    B.draw()

    win2.addstr(0, 0, '-'*80)
    Windows.refresh()

    Misc.last_cmd = None
    Misc.wait_count = 0
    Misc.last_dir = 'l'

    if load_game:
        player, B = Saves().load(load_game)
        B.draw()

    Item(None, Blocks.key,'gk',id=ID.golden_key)
    Item(None, Blocks.key,'special key', id=ID.key3)
    Item(None, Blocks.bottle,'empty bottle', id=ID.empty_bottle)
    Item(None, Blocks.flute,'magic flute', id=ID.magic_flute)
    Item(None, 'c','blue card', id=ID.blue_card)
    Item(None, Blocks.bottle, 'jar of raspberry syrup', id=ID.jar_syrup)
    Item(None, Blocks.wine, 'half bottle of wine', id=ID.wine)
    Item(None, Blocks.bottle, 'Bottle of clear water', id=ID.bottle_clear_water)

    f = obj_by_attr.ferry
    player.add1(ID.key1)

    Saves().save(B.loc, 'start')

    while 1:
        rv = handle_ui(B, player)
        if not rv: break
        if rv==1: continue
        B, player = rv
    blt.set('U+E100: none; U+E200: none; U+E300: none; zodiac font: none')
    blt.composition(False)
    blt.close()

keymap = dict(
    [
    [ blt.TK_SHIFT, 'SHIFT' ],
    [ blt.TK_RETURN, '\n' ],
    [ blt.TK_PERIOD, '.' ],

    [ blt.TK_Q, 'q' ],
    [ blt.TK_W, 'w' ],
    [ blt.TK_E, 'e' ],
    [ blt.TK_R, 'r' ],
    [ blt.TK_T, 't' ],
    [ blt.TK_Y, 'y' ],
    [ blt.TK_U, 'u' ],
    [ blt.TK_I, 'i' ],
    [ blt.TK_O, 'o' ],
    [ blt.TK_P, 'p' ],
    [ blt.TK_A, 'a' ],
    [ blt.TK_S, 's' ],
    [ blt.TK_D, 'd' ],
    [ blt.TK_F, 'f' ],
    [ blt.TK_G, 'g' ],
    [ blt.TK_H, 'h' ],
    [ blt.TK_J, 'j' ],
    [ blt.TK_K, 'k' ],
    [ blt.TK_L, 'l' ],
    [ blt.TK_Z, 'z' ],
    [ blt.TK_X, 'x' ],
    [ blt.TK_C, 'c' ],
    [ blt.TK_V, 'v' ],
    [ blt.TK_B, 'b' ],
    [ blt.TK_N, 'n' ],
    [ blt.TK_M, 'm' ],

    [ blt.TK_1, '1' ],
    [ blt.TK_2, '2' ],
    [ blt.TK_3, '3' ],
    [ blt.TK_4, '4' ],
    [ blt.TK_5, '5' ],
    [ blt.TK_6, '6' ],
    [ blt.TK_7, '7' ],
    [ blt.TK_8, '8' ],
    [ blt.TK_9, '9' ],
    [ blt.TK_0, '0' ],

    [ blt.TK_COMMA, ',' ],
    [ blt.TK_SPACE, ' ' ],
    [ blt.TK_MINUS, '-' ],
    [ blt.TK_SLASH, '/' ],

    [ blt.TK_UP, 'UP' ],
    [ blt.TK_LEFT, 'LEFT' ],
    [ blt.TK_DOWN, 'DOWN' ],
    [ blt.TK_RIGHT, 'RIGHT' ],

    ]
)

def parsekey(k):
    if k==blt.TK_SHIFT:
        return k
    keys = [ blt.TK_UP,
             blt.TK_LEFT,
             blt.TK_DOWN,
             blt.TK_RIGHT,
             blt.TK_RETURN, ]
    if k and blt.check(blt.TK_WCHAR) or k in keys:
        k = keymap.get(k)
        if k and blt.state(blt.TK_SHIFT):
            k = k.upper()
            if k=='-':
                k = '_'
            if k=='/':
                k = '?'
        return k

def handle_ui(B, player):
    win, win2 = Windows.win, Windows.win2
    k = parsekey(blt.read())
    if k==blt.TK_SHIFT:
        return 1 # continue

    def show_stats():
        key = '(key)' if player.has(ID.key1) else ''
        Misc.stats = f'({STANCES[player.stance]}) (H{player.health}) ({player.kashes} Kashes) {key}'
        Windows.win2.addstr(0,0, Misc.stats)
        Windows.refresh()

    # win2.clear()
    win2.addstr(1,0, ' '*78)
    # if k:
        # win2.addstr(2,0,k)
    if not k:
        return 1
    if k in ('Q', blt.TK_CLOSE, blt.TK_ESCAPE):
        return
    elif k=='f':
        player.stance = Stance.fight
        show_stats()
        Windows.refresh()
    elif k=='n':
        player.stance = Stance.normal
        show_stats()
        Windows.refresh()
    elif k == 's':
        player.stance = Stance.sneaky
        show_stats()
        Windows.refresh()
    elif k == '?':
        B.display("""
                  MOVE
                  hjkl - left/down/up/right
                  H and L - run

                  STANCE
                  (n)ormal (f)ighty (s)neaky

                  OTHER

                  SPACE - action
                  .     - wait

                  (u)se item
                  (i)nventory
                  (m)agic ball - (if you have it)

                  (S)ave game
                  l(o)ad game
                  (Q)uit game
                  """.split('\n'))

    elif k in 'hjklHL' or k in 'UP DOWN LEFT RIGHT'.split():
        Misc.last_dir = k
        if k in 'HL':
            k = k.lower()
            for _ in range(5):
                rv = player.move(k)
                if rv[0] == LOAD_BOARD:
                    break
        else:
            k = dict(UP='k',DOWN='j',LEFT='h',RIGHT='l').get(k) or k
            rv = player.move(k)

        if rv[0] == LOAD_BOARD:
            loc = rv[1]
            if loc==ID.fall:
                # a bit ugly, handle fall as explicit 'move' down
                k = 'j'
                loc = B.loc.mod(1,0)
                if not chk_b_oob(loc):
                    status('You fall down and die.....')
                    triggered_events.append(DieEvent)
            x, y = player.loc
            if k=='l': x = 0
            if k=='h': x = 78
            if k=='k': y = 15
            if k=='j': y = 0

            # ugly but....
            p_loc = Loc(x, y)
            if chk_b_oob(loc):
                B = player.move_to_board(boards[loc.y][loc.x]._map, loc=p_loc)
                B.remove(player)
                player.loc = player.fall(player.loc)
                B.put(player)

    elif k == '.':
        if Misc.last_cmd=='.':
            Misc.wait_count += 1
        if Misc.wait_count >= 5 and ID.rubbish1 in B.get_ids(player.loc):
            triggered_events.append(GarbageTruckEvent)
        debug(str(triggered_events))
    elif k == 'o':
        name = prompt()
        rv = Saves().load(name)
        if rv:
            player, B = rv
        else:
            player.talk(player, 'Saved game not found')
    elif k == 'S':
        name = prompt()
        Saves().save(B.loc, name)
        status(f'Saved game as "{name}"')
        Windows.refresh()
    elif k == 'v':
        status(str(player.loc))
    elif k == ' ':
        player.action()

    elif k == '4' and DBG:
        mp = ''
        status('> ')
        Windows.refresh()
        while 1:
            k = parsekey(blt.read())
            if not k: break
            if k == blt.TK_SHIFT:
                continue
            mp += k
            status('> '+mp)
            Windows.refresh()
            if mp in map_to_loc:
                B = player.move_to_board(mp, loc=Loc(40, 5))
                if B._map=='des_und': player.tele(Loc(7,7))
                if B._map=='und1': player.tele(Loc(65,7))
                if B._map=='des_und2': player.tele(Loc(70,7))
            if not any(m.startswith(mp) for m in map_to_loc):
                break

    elif k == '5' and DBG:
        k = parsekey(blt.read())
        k2 = parsekey(blt.read())
        if k and k2:
            try:
                print(B.B[int(k+k2)])
                status(f'printed row {k+k2} to debug')
            except:
                status('try again')

    elif k == 't' and DBG:
        # debug teleport
        mp = ''
        while 1:
            k = parsekey(blt.read())
            if not k: break
            mp+=k
            status(mp)
            Windows.refresh()
            if mp.endswith(' '):
                try:
                    x,y=mp[:-1].split(',')
                    print(Loc(int(x), int(y)))
                    player.tele(Loc(int(x), int(y)))
                except Exception as e:
                    print(e)
                break

    # -----------------------------------------------------------------------------------------------

    elif k == 'u':
        player.use()

    elif k == 'E':
        B.display([str(B.get_all(player.loc)).replace('[','[[').replace(']',']]')])
        # player.talk(player, str(B.get_all(player.loc)))
    elif k == 'm':
        if player.has(ID.magic_ball):
            MagicBallEvent(B).go(player, Misc.last_dir)
    elif k == 'i':
        txt = []
        for id, n in player.inv.items():
            item = objects[id]
            if item and n:
                txt.append(f'{item.name} {n}')
        B.display(txt or ['Inventory is empty'])

    if k != '.':
        Misc.wait_count = 0
    Misc.last_cmd = k

    B.guards = [g for g in B.guards if g.health>0]
    B.soldiers = [g for g in B.soldiers if g.health>0]
    for g in B.guards:
        if g.hostile:
            g.attack(player)
    for s in B.soldiers:
        attack = False
        if s.id == ID.clone1 and dist(s, player) <= 1:
            attack = True
        elif s.id!=ID.clone1 and dist(s, player) <= (1 if player.sneaky_stance else 5):
            attack = True
        if attack:
            s.hostile = 1
            s.attack(player)
        else:
            s.hostile = 0

    if player.health <= 0:
        Windows.win2.addstr(1, 0, f'Hmm.. it looks like you lost the game!')
        player, B = Saves().load('start')

    for evt in triggered_events:
        if evt==EndGameEvent:
            return
        kwargs = {}
        if isinstance(evt, SEQ_TYPES):
            evt, kwargs = evt
        if evt in done_events and evt.once:
            continue
        rv = evt(B, **kwargs).go()
        if isinstance(rv, Board):
            B = rv
        try:
            player, B = rv
        except Exception as e:
            print("e", e)
            pass
        done_events.add(evt)

    triggered_events.clear()
    for t in timers:
        t.turns -= 1
        if not t.turns:
            triggered_events.append(t.evt)
    timers[:] = [t for t in timers if t.turns>0]
    B.draw()
    key = '(key)' if player.has(ID.key1) else ''
    Misc.stats = f'({STANCES[player.stance]}) (H{player.health}) ({player.kashes} Kashes) {key}'
    Windows.refresh()
    return B, player

def prompt():
    mp = ''
    status('> ')
    Windows.refresh()
    while 1:
        k = parsekey(blt.read())
        if not k: continue
        if k=='\n':
            return mp
        mp += k
        status('> '+mp)
        Windows.refresh()


def debug(*args):
    debug_log.write(str(args) + '\n')
    debug_log.flush()
print=debug

def editor(_map):
    blt.open()
    blt.set("window: resizeable=true, size=80x25, cellsize=auto, title='Little Adventure'; font: FreeMono.ttf, size=24")
    blt.color("white")
    blt.composition(True)

    blt.clear()
    blt.color("white")
    Misc.is_game = 0
    begin_x = 0; begin_y = 0; width = 80
    loc = Loc(40, 8)
    brush = None
    written = 0
    B = Board(Loc(0,0), _map)
    fname = f'maps/{_map}.map'
    if not os.path.exists(fname):
        with open(fname, 'w') as fp:
            for _ in range(HEIGHT):
                fp.write(blank*78 + '\n')
    B.load_map(_map, 1)

    B.draw()

    while 1:
        k = parsekey(blt.read())
        if k == blt.TK_SHIFT:
            continue
        if k=='Q': break
        elif k and k in 'hjklyubnHL':
            n = 1
            if k in 'HL':
                n = 5
            m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0), y=(-1,-1), u=(-1,1), b=(1,-1), n=(1,1), H=(0,-1), L=(0,1))[k]

            for _ in range(n):
                if chk_oob(loc.mod(*m)):
                    loc = loc.mod(*m)
                if brush:
                    B.B[loc.y][loc.x] = [brush]

        elif k == ' ':
            brush = None
        elif k == 'e':
            brush = ' '
            B.B[loc.y][loc.x] = [brush]
        elif k == 'r':
            brush = rock
        elif k == 's':
            B.put(Blocks.steps_r, loc)
            brush = Blocks.steps_r
        elif k == '/':
            B.put(Blocks.angled1, loc)
            brush = Blocks.angled1
        elif k == '\\':
            B.put(Blocks.angled2, loc)
            brush = Blocks.angled2
        elif k == 'S':
            B.put(Blocks.steps_l, loc)
            brush = Blocks.steps_l
        elif k == 'M':
            B.put(Blocks.smoke_pipe, loc)
        elif k == 'd':
            B.put('d', loc)
        elif k and k in '0123456789':
            B.put(k, loc)
        elif k == 'w':
            Item(B, Blocks.water, 'water', loc)
        elif k == 't':
            B.put(Blocks.stool, loc)
        elif k == 'a':
            B.put(Blocks.ladder, loc)
        elif k == 'c':
            B.put(Blocks.cupboard, loc)
        elif k == 'B':
            B.put(Blocks.dock_boards, loc)
        elif k == 'p':
            B.put(Blocks.platform_top, loc)
        elif k == 'g':
            B.put(Blocks.grill, loc)
        elif k == 'F':
            B.put(Blocks.ferry_l, loc)
        elif k == 'A':
            B.put(Blocks.bars, loc)
        elif k == 'R':
            B.put(Blocks.rubbish, loc)

        # NPCs
        elif k == 'G':
            B.put(Blocks.elephant_l, loc)
        elif k == 'O':
            B.put(Blocks.soldier_l, loc)

        elif k == 'T':
            B.put(choice((Blocks.tree1, Blocks.tree2)), loc)
        elif k == 'z':
            B.put(Blocks.guardrail_m, loc)
            brush = Blocks.guardrail_m
        elif k == 'x':
            B.put(Blocks.rock2, loc)
            brush = Blocks.rock2
        elif k == 'X':
            B.put(Blocks.shelves, loc)
        elif k == 'C':
            B.put(Blocks.cactus, loc)
        elif k == 'v':
            B.put(Blocks.snowflake, loc)
        elif k == 'V':
            B.put(Blocks.snowman, loc)
        elif k == 'f':
            B.put(choice(Blocks.flowers), loc)

        elif k == 'o':
            cmds = 'gm gl gr l b ob f C cl cr'.split()
            cmd = ''
            BL=Blocks
            while 1:
                k = parsekey(blt.read())
                if k:
                    cmd += k
                if   cmd == 'gm': B.put(BL.guardrail_m, loc)
                elif cmd == 'gl': B.put(BL.guardrail_l, loc)
                elif cmd == 'gr': B.put(BL.guardrail_r, loc)

                elif cmd == 'cl': B.put(BL.cornice_l, loc)
                elif cmd == 'cr': B.put(BL.cornice_r, loc)

                elif cmd == 'l':  B.put(BL.locker, loc)
                elif cmd == 'b':  B.put(BL.books[0], loc)
                elif cmd == 'ob': B.put(BL.books[0], loc)
                elif cmd == 't':  B.put('t', loc)
                elif cmd == 'f':  B.put(BL.fountain, loc)
                elif cmd == 'a':  B.put(BL.antitank, loc)
                elif cmd == 'p':  B.put(BL.platform2, loc)
                elif cmd == 'C':  B.put('C', loc)   # crate -- note 'C' shortcut adds cactus
                elif cmd == 'w':  B.put('W', loc)   # window

                elif cmd == 'oc':  B.put(BL.car, loc)

                elif cmd == 'm': B.put(BL.monkey, loc)
                elif cmd == 'v': B.put(BL.lever, loc)
                elif cmd == 's': B.put(BL.sharp_rock, loc)
                elif cmd == 'r': B.put(BL.rock3, loc)
                elif cmd == 'd': B.put('d', loc)     # drawing
                elif cmd == 'R': B.put(Blocks.rabbit_l, loc)

                elif any(c.startswith(cmd) for c in cmds):
                    continue
                break

        elif k == 'E':
            Windows.win.addstr(2,2, 'Are you sure you want to clear the map? [Y/N]')
            y = parsekey(blt.read())
            if y=='Y':
                for row in B.B:
                    for cell in row:
                        cell[:] = [blank]
                B.B[-1][-1].append('_')
        elif k == 'f':
            B.put(Blocks.shelves, loc)

        elif k == 'W':
            with open(f'maps/{_map}.map', 'w') as fp:
                for row in B.B:
                    for cell in row:
                        a = cell[-1]
                        print("a", a)
                        a = new_blocks_to_old.get(str(a)) or a
                        if str(a) in Blocks.crates:
                            a = 'C'
                        print("2: a", a)
                        fp.write(str(a))
                    fp.write('\n')
            written=1

        B.draw()
        blt.clear_area(loc.x,loc.y,1,1)
        # Windows.win.addstr(loc.y, loc.x, Blocks.circle3)
        Windows.win.addstr(loc.y, loc.x, Blocks.cursor, 'blue')
        Windows.refresh()
        if brush==blank:
            tool = 'eraser'
        elif brush==rock:
            tool = 'rock'
        elif not brush:
            tool = ''
        else:
            tool = brush
        Windows.win.addstr(1,73, tool)
        Windows.win.addstr(0, 0 if loc.x>40 else 70,
                           str(loc))
        Windows.refresh()
        if written:
            Windows.win.addstr(2,65, 'map written')
            written=0
        # win.move(loc.y, loc.x)
    blt.set("U+E100: none; U+E200: none; U+E300: none; zodiac font: none")
    blt.composition(False)
    blt.close()


if __name__ == "__main__":
    argv = sys.argv[1:]
    load_game = None
    for a in argv:
        if a == '-d':
            DBG = True
        if a and a.startswith('-l'):
            load_game = a[2:]
        if a and a.startswith('-s'):
            SIZE = int(a[2:])
    if first(argv) == 'ed':
        editor(argv[1])
    else:
        main(load_game)
