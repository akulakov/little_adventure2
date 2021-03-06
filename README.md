# Little adventure

Little adventure is a turn based game with graphics / mechanics similar to games like Dwarf Fortress or Nethack.

The game is inspired by the world and story of an old game called Little Big Adventure.

Requirements
---

- Python3.6+  (On Mac OS run `brew install python3`, other platforms see http://www.python.org/downloads/)

- bearlibterminal
    `pip3 install bearlibterminal`

To play, first clone the repo, `git clone git@github.com:akulakov/little_adventure2.git`; then run `python3 adv.py`

## Gameplay hints

 - In the beginning, try to attract the attention of the guard somehow!

 - Some hidden passages are so narrow that you have to sneak through them!

 - Once you get Gawley's horn, remember it can open Seals of Sendell which are sometimes hidden!

# Commands

## Move

    h - move left

    l - move right

    k - move up

    j - move down

    H and L - run

## Modes

    n - normal
    f - fighty
    s - sneaky  (some passages are small so have to be sneaked through)


## Other

    ? - HELP
    space - action
    u - use item
    i - inventory
    . - wait
    m - magic ball (if you have it)


    S - save game
    o - load game
    Q - quit

# Window Size

-s arg can be used to adjust tile size and therefore window size
Default is 24, so to make a smaller window, you can run, e.g.:

    python3 adv.py -s18
