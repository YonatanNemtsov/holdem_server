from django.shortcuts import render
from django.http import HttpResponse
from .models import GameTable
# Create your views here.
def game(request,table_name):
    
    #print(request.user.username)
    try:
        table = GameTable.objects.get(table_name=table_name)
    except:
        return HttpResponse('not found',status=404)
    

    if request.user.is_authenticated:
        if request.user in [table.player2, table.player1]:
            context={
                'table_name':table_name,
                'player':request.user,
                'p1':table.player1,
                'p2':table.player2
            }
            return render(request,'game.html',context)
    else:
        return HttpResponse('Unauthorized', status=401)
 

def sit(request,table_name,sit_number):
    try:
        table = GameTable.objects.get(table_name=table_name)
    except:
        return HttpResponse('not found',status=404)


    context={'table_name':table_name,'sit_number':sit_number}
    return render(request,'sit.html',context=context)


def login(request):
    return render(request, 'login.html')

