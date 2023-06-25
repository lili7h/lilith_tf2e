import os

from rc.rcon_client import Client
from steam import Steam
from dotenv import load_dotenv


def test(_steam: Steam):
    with Client('127.0.0.1', 27015, passwd='lilith_is_hot') as client:
        response = client.run('tf_lobby_debug')
    print(response.split("\n"))


# F:\projects\py\lilith_tf2e\library\Scripts\python.exe F:\projects\py\lilith_tf2e\test.py
# ['CTFLobbyShared: ID:00022b29776f570e  24 member(s), 0 pending', '  Member[0] [U:1:1067916592]  team = TF_GC_TEAM_DEFENDERS  type = MATCH_PLAYER', '  Member[1] [U:1:1249816897]  team = TF_GC_TEAM_INVADERS  type = MATCH_PLAYER', '  Member[2] [U:1:876565069]  team = TF_GC_TEAM_DEFENDERS  type = MATCH_PLAYER', '  Member[3] [U:1:121814266]  team = TF_GC_TEAM_INVADERS  type = MATCH_PLAYER', '  Member[4] [U:1:420805814]  team = TF_GC_TEAM_INVADERS  type = MATCH_PLAYER', '  Member[5] [U:1:1243358313]  team = TF_GC_TEAM_DEFENDERS  type = MATCH_PLAYER', '  Member[6] [U:1:86582741]  team = TF_GC_TEAM_DEFENDERS  type = MATCH_PLAYER', '  Member[7] [U:1:102721937]  team = TF_GC_TEAM_INVADERS  type = MATCH_PLAYER', '  Member[8] [U:1:144251601]  team = TF_GC_TEAM_INVADERS  type = MATCH_PLAYER', '  Member[9] [U:1:1423701817]  team = TF_GC_TEAM_DEFENDERS  type = MATCH_PLAYER', '  Member[10] [U:1:1350594527]  team = TF_GC_TEAM_INVADERS  type = MATCH_PLAYER', '  Member[11] [U:1:1141016362]  team = TF_GC_TEAM_INVADERS  type = MATCH_PLAYER', '  Member[12] [U:1:1425555038]  team = TF_GC_TEAM_INVADERS  type = MATCH_PLAYER', '  Member[13] [U:1:72310870]  team = TF_GC_TEAM_INVADERS  type = MATCH_PLAYER', '  Member[14] [U:1:197996563]  team = TF_GC_TEAM_DEFENDERS  type = MATCH_PLAYER', '  Member[15] [U:1:1274985328]  team = TF_GC_TEAM_DEFENDERS  type = MATCH_PLAYER', '  Member[16] [U:1:111216987]  team = TF_GC_TEAM_INVADERS  type = MATCH_PLAYER', '  Member[17] [U:1:1056508400]  team = TF_GC_TEAM_DEFENDERS  type = MATCH_PLAYER', '  Member[18] [U:1:201213744]  team = TF_GC_TEAM_DEFENDERS  type = MATCH_PLAYER', '  Member[19] [U:1:344989649]  team = TF_GC_TEAM_INVADERS  type = MATCH_PLAYER', '  Member[20] [U:1:1400248603]  team = TF_GC_TEAM_DEFENDERS  type = MATCH_PLAYER', '  Member[21] [U:1:146212407]  team = TF_GC_TEAM_INVADERS  type = MATCH_PLAYER', '  Member[22] [U:1:1404075701]  team = TF_GC_TEAM_DEFENDERS  type = MATCH_PLAYER', '  Member[23] [U:1:123190320]  team = TF_GC_TEAM_DEFENDERS  type = MATCH_PLAYER', '']



def main(_steam: Steam):
    test(_steam)


if __name__ == "__main__":
    load_dotenv()
    steam = Steam(os.environ["STEAM_WEB_API_KEY"])
    main(steam)
