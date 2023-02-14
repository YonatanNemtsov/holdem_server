from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from game.models import UserAccount

# Create your forms here.

class NewUserForm(UserCreationForm):
	email = forms.EmailField(required=True)
	
	class Meta:
		model = User
		fields = ("username", "email")
	
	def save(self, commit=True):
		print(10)
		user = super(NewUserForm, self).save(commit=False)
		user.email = self.cleaned_data['email']
		
		if commit:
			user.save()
			account = UserAccount.objects.create(user=user)
			account.save()
		#account.save()
		return user