from game.models import GameLog


def play_round():
    game_log = GameLog.objects.create()
    p1_choice = int(input())
    game_log.log.append(p1_choice)
    game_log.save()
    p2_choice = int(input())
    game_log.log.append(p2_choice)
    game_log.save()
    if (p1_choice+p2_choice) % 2 == 0:
        game_log.log.append('p1 wins')
        game_log.save()
        print(game_log.log[-1])
    else:
        game_log.log.append('p2 wins')
        game_log.save()
        print(game_log.log[-1])
