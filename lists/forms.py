from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
User = get_user_model()

from lists.models import Item, List

EMPTY_ITEM_ERROR = "You can't have an empty list item"
DUPLICATE_ITEM_ERROR = "You've already got this in your list"
EMPTY_SHAREE_ERROR = "Please enter an email address"
NO_USER_ERROR = "Please enter email of an existing Superlists user"
DUPLICATE_USER_ERROR = "Already shared this list with this user!"

class ItemForm(forms.models.ModelForm):

    class Meta:
        model = Item
        fields = ('text',)
        widgets = {
            'text': forms.fields.TextInput(attrs={
                'placeholder': 'Enter a to-do item',
                'class': 'form-control input-lg',
            }),
        }
        error_messages = {
            'text': {'required': EMPTY_ITEM_ERROR}
        }


class NewListForm(ItemForm):

    def save(self, owner):
        if owner.is_authenticated:
            return List.create_new(first_item_text=self.cleaned_data['text'], owner=owner)
        else:
            return List.create_new(first_item_text=self.cleaned_data['text'])


class ExistingListItemForm(ItemForm):
    def __init__(self, for_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.list = for_list

    def validate_unique(self):
        try:
            self.instance.validate_unique()
        except ValidationError as e:
            e.error_dict = {'text': [DUPLICATE_ITEM_ERROR]}
            self._update_errors(e)

class ShareWithForm(forms.models.ModelForm):
    sharee = forms.fields.CharField(
        widget=forms.fields.TextInput(attrs={
            'class': 'form-control input-md',
            'placeholder': 'your-friend@example.com',
        }),
        error_messages={"required": EMPTY_SHAREE_ERROR}
    )

    def __init__(self, for_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = for_list

    def clean_sharee(self):
        try:
            user = User.objects.get(email=self.cleaned_data['sharee'])
            if user in self.instance.shared_with.all():
                raise forms.ValidationError(DUPLICATE_USER_ERROR)
        except User.DoesNotExist:
            raise forms.ValidationError(NO_USER_ERROR)
        return user

    def save(self):
        self.instance.shared_with.add(self.cleaned_data['sharee'])
        self.instance.save()
        return self.instance

    class Meta:
        model = List
        fields = ('sharee',)
