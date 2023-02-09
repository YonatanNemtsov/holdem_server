from django.shortcuts import render
from django.http import HttpResponse
from .models import GameTable
# Create your views here.
def game(request,table_name):
    NUM_OF_SITS = 9
    #print(request.user.username)
    try:
        table = GameTable.objects.get(table_name=table_name)
    except:
        return HttpResponse('not found',status=404)
    

    if request.user.is_authenticated:
        context={
            'table_name':table_name,
            'player':request.user,
            'sits':list(range(1,NUM_OF_SITS+1))
        }
        return render(request,'game.html',context)
    else:
        return HttpResponse('Unauthorized', status=401)



def login(request):
    return render(request, 'login.html')

