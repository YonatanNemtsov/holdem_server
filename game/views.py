from django.shortcuts import render
from django.http import HttpResponse
from .models import GameTable,UserAccount
# Create your views here.
def game(request,table_id):
    NUM_OF_SITS = 9
    #print(request.user.username)
    try:
        table = GameTable.objects.get(id=table_id)
    except:
        return HttpResponse('not found',status=404)
    

    if request.user.is_authenticated:
        context={
            'table_id':table_id,
            'player':request.user,
            'sits':list(range(1,NUM_OF_SITS+1)),
            'balance':UserAccount.objects.get(user=request.user).balance
        }
        return render(request,'game.html',context)
    else:
        return HttpResponse('Unauthorized', status=401)



def login(request):
    return render(request, 'login.html')

