# lilith_tf2e

`lilith_tf2e` is intended to be a fully-fledged helper tool for interacting with, and recording data from, Team Fortress 2.

In line with the [TF2 Bot Kicker GUI](https://github.com/Bash-09/tf2-bot-kicker-gui) by Bash09, and the plans behind [MegaScatterBomb](https://www.youtube.com/@megascatterbomb)'s MegaAntiCheat and associated helper clients, this is intended to be used by legitimate players to aid with investigation, recording and reporting suspicious players and bots. But this app also aims to be a lot more - it aims to be an effective data collection tool for recording player interactions, stats, scores and games, as well as automatically recording demos.

It will implement a robust data archival system involving compression algorithms (probably python `gzip` library) and an automatic repository upkeep tool to minimise sparse, out of date, and/or unwanted data being collected.

## The design
`lilith_tf2e` intends to be 100% Python, end-to-end. It uses PySimpleGUI for the user interface (because I wanted to learn it, but the other alternative would be to turn this into a `Flask` server and display it via a web-browser or electron app). It will use `SQLite3` for databasing and data archival. It will use pythonic job schedulers and the python package '`schedule`' to run ephemeral/sparse upkeep and maintenance jobs. 

## The timeline

This table will be added to as tasks are planned and as each task evolves.

|                           Task Name                           |    Start Time    |     End Time     |          Stage          |                                    Current Focus                                     |                                                                          Issues                                                                           |                  Result                   |
|:-------------------------------------------------------------:|:----------------:|:----------------:|:-----------------------:|:------------------------------------------------------------------------------------:|:---------------------------------------------------------------------------------------------------------------------------------------------------------:|:-----------------------------------------:|
|                 Bespoke Path Listener/Watcher                 | prior to go-live | prior to go-live |        Complete.        |                                          -                                           |                                             Existing Pythonic packages do not work to solve the task at hand.                                             |              `clwd` package               |
|               Interface with RCON and Steam API               | prior to go-live | prior to go-live | Complete (with issues). |                             Refactor code and packaging                              |                                                                             -                                                                             |               `rc` package                |
|                    Simple GUI App for PoC                     | prior to go-live |    25/05/2023    |        Complete.        |                                          -                                           |                                                                             -                                                                             |         `gui/lobbyviewer.py` app          |
|   Refactor and reform code base for launch platform for MVP   |    25/05/2023    |        -         |      In progress.       |                                          -                                           |                                                                             -                                                                             |                     -                     |
| Implement G15 parser to parse `g15_dumpplayer` command output |    30/06/2023    |    30/06/2023    |        Complete.        |        integrating the parser with existing UI and lobby code to leverage it         | `g15_dumpplayer` returns data via RCON, yay! Downside - the packets are fragmented because the output is massive. Need to implement proper packet de-frag | g15parser package, FragClient rcon client |
|       Interface console listener (l2) for lobby updates       |    25/05/2023    |        -         |      In progress.       | Develop effective startup sequence that avoids desyncs and unnecessary RCON commands |                                                                                                                                                           |                                           |
|  Convert this to a poetry project for dependency management   |        -         |        -         |        Planned.         |                                          -                                           |                                                                             -                                                                             |                     -                     |
|            Minimum viable product for full product            |        -         |        -         |        Planned.         |                                          -                                           |                                                                             -                                                                             |                     -                     |
|                                                               |                  |                  |                         |                                                                                      |                                                                                                                                                           |                                           |

# Current in progress
~~Currently working on the `gui/lobbyviewer.py` simple GUI class, and it is fairly functional given a complete `data/` directory. ~~

We are on to version 0.2.1 of the SimpleLobbyViewer, and already working to refactor it _again_, as we now can integrate
more, higher quality, data from `g15_dumpplayer` to better handle player instances, interleaving and data stagnation.

Example:
![Functioning simple lobby viewer from a random TF2 lobby I was in](docs/pictures/gui.lobbyviewer.png)

**NOTE:**  

You will need to make a `data/` directory to house a `config.yml` and a `.env` file. They can be structured as such:

`config.yml`:
```
tf2:
  dir: "path/to/tf2"
  rcon:
    password: "lilith_is_hot"
```

and

`.env`:
```
STEAM_WEB_API_KEY="YOUR_STEAM_API_KEY_HERE"
```

I also used two photos in the `data/` dir that get loaded by the `gui/lobbyviewer.py`. These were `lilith.png` and `tf2.png`. I have **NOT** included these in the repo because I do not own the TF2 logo (although it would probably be fine if I used it), and because Lilith is my OC and the artwork is commissioned and not MIT licensed.

These images were `2000x2000` and in PNG format. Feel free to replace them with whatever you like.

# Main dependencies
- PySimpleGUI
- steam_converter
- rcon
- steam
- psutil
- schedule
- loguru
- PyYAML

My intention is for this application to be fairly heavy weight, but nicely concurrent with a mix of python multiprocessing and threading.

I had to add the following lines to my `autoexec.cfg` to allow the `gui/lobbyviewer.py` to interface with TF2:
```
ip 0.0.0.0
rcon_password lilith_is_hot
net_start 
```
Note that you don't actually need to specify the rcon_password as such, but rather it can be whatever you want, as long as `data/config.yml` corresponds to this.

# The purpose
This is intended to be a 100% Python full-stack application to interface with Team Fortress 2.
This will be achieved via RCON and monitoring the console.log file, and will take advantage of the Steam Web API, and several other external APIs (such as Bash09's cheater list, and 
megascatterbomb's mcd or anti-cheat (when its released)).

If you want an actually complete and functional program, see Bash's TF2 Bot Kicker GUI (written in Rust! blazingly fast!) --> https://github.com/Bash-09/tf2-bot-kicker-gui
