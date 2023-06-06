from captcha.fields import CaptchaField
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

PILIHAN_PEMBAYARAN = (
    ('P', 'Paypal'),
    ('S', 'Stripe'),
)


class CheckoutForm(forms.Form):
    alamat_1 = forms.CharField(widget=forms.TextInput(
        attrs={'placeholder': 'Alamat Anda', 'class': 'textinput form-control'}))
    alamat_2 = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'placeholder': 'Apartement, Rumah, atau yang lain (opsional)', 'class': 'textinput form-control'}))
    negara = CountryField(blank_label='(Pilih Negara)').formfield(
        widget=CountrySelectWidget(attrs={'class': 'countryselectwidget form-select'}))
    kode_pos = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'textinput form-outline', 'placeholder': 'Kode Pos'}))
    simpan_info_alamat = forms.BooleanField(
        widget=forms.CheckboxInput(), required=False)
    opsi_pembayaran = forms.ChoiceField(
        widget=forms.RadioSelect(), choices=PILIHAN_PEMBAYARAN)
    captcha = CaptchaField()



class ContactForm(forms.Form):
    nama = forms.CharField(widget=forms.TextInput(
        attrs={'placeholder': 'Nama Anda', 'class': 'textinput form-control'}))
    email = forms.EmailField(widget=forms.TextInput(
        attrs={'placeholder': 'Email Anda', 'class': 'textinput form-control'}))
    pesan = forms.CharField(widget=forms.Textarea(
        attrs={'placeholder': 'Pesan Anda', 'class': 'textinput form-control'}))
    captcha = CaptchaField()


class CaptchaForm(UserCreationForm):
    email = forms.EmailField(required=True)
    captcha = CaptchaField()
