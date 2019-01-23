import unittest
from unittest.mock import patch, Mock
from django.test import TestCase

from lists.forms import (
    DUPLICATE_ITEM_ERROR, EMPTY_ITEM_ERROR, EMPTY_SHAREE_ERROR, NO_USER_ERROR,
    DUPLICATE_USER_ERROR,
    ExistingListItemForm, ItemForm, NewListForm, ShareWithForm
)
from lists.models import Item, List
from django.contrib.auth import get_user_model
User = get_user_model()

class ItemFormTest(TestCase):

    def test_form_item_input_has_placeholder_and_css_classes(self):
        form = ItemForm()
        self.assertIn('placeholder="Enter a to-do item"', form.as_p())
        self.assertIn('class="form-control input-lg"', form.as_p())

    def test_form_validation_for_blank_items(self):
        form = ItemForm(data={'text': ''})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['text'],
            [EMPTY_ITEM_ERROR],
        )


class ExistingListItemFormTest(TestCase):

    def test_form_renders_item_text_input(self):
        list_ = List.objects.create()
        form = ExistingListItemForm(for_list=list_)
        self.assertIn('placeholder="Enter a to-do item"', form.as_p())

    def test_form_validation_for_blank_items(self):
        list_ = List.objects.create()
        form = ExistingListItemForm(for_list=list_, data={'text': ''})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['text'],
            [EMPTY_ITEM_ERROR],
        )

    def test_form_validation_for_duplicate_items(self):
        list_ = List.objects.create()
        Item.objects.create(list=list_, text='no twins!')
        form = ExistingListItemForm(for_list=list_, data={'text': 'no twins!'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['text'], [DUPLICATE_ITEM_ERROR])

    def test_form_save(self):
        list_ = List.objects.create()
        form = ExistingListItemForm(for_list=list_, data={'text': 'hi'})
        new_item = form.save()
        self.assertEqual(new_item, Item.objects.all()[0])


class NewListFormTest(unittest.TestCase):

    @patch('lists.forms.List.create_new')
    def test_save_creates_new_list_from_post_data_if_user_not_authenticated(
        self, mock_List_create_new
    ):
        user = Mock(is_authenticated=False)
        form = NewListForm(data={'text': 'new item text'})
        form.is_valid()
        form.save(owner=user)
        mock_List_create_new.assert_called_once_with(
            first_item_text='new item text'
        )

    @patch('lists.forms.List.create_new')
    def test_save_creates_new_list_from_post_data_if_user_authenticated(
        self, mock_List_create_new
    ):
        user = Mock(is_authenticated=True)
        form = NewListForm(data={'text': 'new item text'})
        form.is_valid()
        form.save(owner=user)
        mock_List_create_new.assert_called_once_with(
            first_item_text='new item text', owner=user
        )

    @patch('lists.forms.List.create_new')
    def test_save_returns_new_list_object(self, mock_List_create_new):
        user = Mock(is_authenticated=True)
        form = NewListForm(data={'text': 'new item text'})
        form.is_valid()
        response = form.save(owner=user)
        self.assertEqual(response, mock_List_create_new.return_value)


class ShareWithFormTest(TestCase):

    def test_form_renders_sharebox(self):
        list_ = List.objects.create()
        form = ShareWithForm(for_list=list_)
        self.assertIn('name="sharee"', form.as_p())

    def test_share_with_form_validation_for_blank_items(self):
        list_ = List.objects.create()
        form = ShareWithForm(for_list=list_, data={'sharee': ''})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['sharee'],
            [EMPTY_SHAREE_ERROR],
        )

    def test_share_with_form_validation_user_does_not_exist(self):
        list_ = List.objects.create()
        form = ShareWithForm(for_list=list_, data={'sharee': 'man@b.net'})

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['sharee'],
            [NO_USER_ERROR],
        )

    def test_share_with_form_validation_duplicate_user(self):
        list_ = List.objects.create()
        user = User.objects.create(email="man@b.net")
        list_.shared_with.add(user)
        form = ShareWithForm(for_list=list_, data={'sharee': 'man@b.net'})

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['sharee'],
            [DUPLICATE_USER_ERROR],
        )

    def test_share_with_existing_user_form_save(self):
        list_ = List.objects.create()
        user = User.objects.create(email="man@b.net")

        form = ShareWithForm(for_list=list_, data={'sharee': 'man@b.net'})
        form.is_valid()
        saved_list = form.save()
        self.assertEqual(saved_list, list_)
        self.assertEqual(saved_list.shared_with.first(), user)
