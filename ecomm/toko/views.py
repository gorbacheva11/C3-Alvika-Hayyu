from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils import timezone
from django.views import generic
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from paypal.standard.forms import PayPalPaymentsForm
from .forms import CheckoutForm
from .models import ProdukItem, OrderProdukItem, Order, AlamatPengiriman, Payment
from django.views.decorators.csrf import csrf_protect, csrf_exempt


class HomeListView(generic.ListView):
    template_name = 'home.html'
    queryset = ProdukItem.objects.all()
    paginate_by = 8


class ProductDetailView(generic.DetailView):
    template_name = 'product_detail.html'
    queryset = ProdukItem.objects.all()


def __init__(self, request):
    self.session = request.session
    basket = self.session.get('skey')
    if 'skey' not in request.session:
        basket = self.session['skey'] = {}
    self.basket = basket


@require_POST
def add_quantity(request, slug):
    # adding and updating the users quantity to basket#
    cart = OrderProdukItem(request)
    produk_item = get_object_or_404(ProdukItem, slug=slug)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.Order.objects.filter(user=request.user, produk_item=produk_item, quantity=cd['quantity'],
                                  override_quantity=cd['override'])
    return redirect('toko:produk-detail', slug=slug)


class CheckoutView(LoginRequiredMixin, generic.FormView):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if order.produk_items.count() == 0:
                messages.warning(
                    self.request, 'Belum ada belajaan yang Anda pesan, lanjutkan belanja')
                return redirect('toko:home-produk-list')
        except ObjectDoesNotExist:
            order = {}
            messages.warning(
                self.request, 'Belum ada belajaan yang Anda pesan, lanjutkan belanja')
            return redirect('toko:home-produk-list')

        context = {
            'form': form,
            'keranjang': order,
        }
        template_name = 'checkout.html'
        return render(self.request, template_name, context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                alamat_1 = form.cleaned_data.get('alamat_1')
                alamat_2 = form.cleaned_data.get('alamat_2')
                negara = form.cleaned_data.get('negara')
                kode_pos = form.cleaned_data.get('kode_pos')
                opsi_pembayaran = form.cleaned_data.get('opsi_pembayaran')
                alamat_pengiriman = AlamatPengiriman(
                    user=self.request.user,
                    alamat_1=alamat_1,
                    alamat_2=alamat_2,
                    negara=negara,
                    kode_pos=kode_pos,
                )

                alamat_pengiriman.save()
                order.alamat_pengiriman = alamat_pengiriman
                order.save()
                if opsi_pembayaran == 'P':
                    return redirect('toko:payment', payment_method='paypal')
                else:
                    return redirect('toko:payment', payment_method='stripe')

            messages.warning(self.request, 'Gagal checkout')
            return redirect('toko:checkout')
        except ObjectDoesNotExist:
            messages.error(self.request, 'Tidak ada pesanan yang aktif')
            return redirect('toko:order-summary')


class PaymentView(LoginRequiredMixin, generic.FormView):
    def get(self, *args, **kwargs):
        template_name = 'payment.html'
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)

            paypal_data = {
                'business': settings.PAYPAL_RECEIVER_EMAIL,
                'amount': order.get_total_harga_order,
                'item_name': f'Pembayaran belajanan order: {order.id}',
                'invoice': f'{order.id}-{timezone.now().timestamp()}',
                'currency_code': 'USD',
                'notify_url': self.request.build_absolute_uri(reverse('paypal-ipn')),
                'return_url': self.request.build_absolute_uri(reverse('toko:paypal-return')),
                'cancel_return': self.request.build_absolute_uri(reverse('toko:paypal-cancel')),
            }

            qPath = self.request.get_full_path()
            isPaypal = 'paypal' in qPath

            form = PayPalPaymentsForm(initial=paypal_data)
            context = {
                'paypalform': form,
                'order': order,
                'is_paypal': isPaypal,
            }
            return render(self.request, template_name, context)

        except ObjectDoesNotExist:
            return redirect('toko:checkout')


class OrderSummaryView(LoginRequiredMixin, generic.TemplateView):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'keranjang': order
            }
            template_name = 'order_summary.html'
            return render(self.request, template_name, context)
        except ObjectDoesNotExist:
            messages.error(self.request, 'Tidak ada pesanan yang aktif')
            return redirect('/')


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


@login_required
def add_to_cart(request, slug):
    if request.user.is_authenticated:
        produk_item = get_object_or_404(ProdukItem, slug=slug)
        order_produk_item, _ = OrderProdukItem.objects.get_or_create(
            produk_item=produk_item,
            user=request.user,
            ordered=False
        )
        order_query = Order.objects.filter(user=request.user, ordered=False)
        if order_query.exists():
            order = order_query[0]
            #stock = request.GET.get('stock')
            if order.produk_items.filter(produk_item__slug=produk_item.slug).exists():
                if produk_item.stock <= order_produk_item.quantity:
                    order_produk_item.save()
                    messages.error(request, 'Produk hanya tersisa 1')
                    return redirect('toko:produk-detail', slug=slug)
                else:
                    order_produk_item.quantity += 1
                    order_produk_item.save()
                    pesan = f"ProdukItem sudah diupdate menjadi: {order_produk_item.quantity}"
                    messages.info(request, pesan)
                    return redirect('toko:order-summary')
            else:
                order.produk_items.add(order_produk_item)
                messages.info(request, 'ProdukItem pilihanmu sudah ditambahkan')
                return redirect('toko:produk-detail', slug=slug)
        else:
            tanggal_order = timezone.now()
            order = Order.objects.create(
                user=request.user, tanggal_order=tanggal_order)
            order.produk_items.add(order_produk_item)
            messages.info(request, 'ProdukItem pilihanmu sudah ditambahkan')
            return redirect('toko:produk-detail', slug=slug)
    else:
        return redirect('/accounts/login')


def remove_single_item_from_cart(request, slug):
    if request.user.is_authenticated:
        produk_item = get_object_or_404(ProdukItem, slug=slug)
        order_query = Order.objects.filter(
            user=request.user,
            ordered=False
        )
        if order_query.exists():
            order = order_query[0]
            # check if the order item is in the order
            if order.produk_items.filter(produk_item__slug=produk_item.slug).exists():
                order_produk_item = OrderProdukItem.objects.filter(
                    produk_item=produk_item,
                    user=request.user,
                    ordered=False
                )[0]
                if order_produk_item.quantity > 1:
                    order_produk_item.quantity -= 1
                    order_produk_item.save()
                else:
                    order.produk_items.remove(order_produk_item)
                messages.info(
                    request, "Jumlah item pilihanmu sudah diperbarui")
                return redirect('toko:order-summary')
            else:
                messages.info(request, "Ups, item tidak ada di daftar belanja")
                return redirect('toko:produk-detail', slug=slug)
        else:
            messages.info(request, "Kamu tidak punya order")
            return redirect('toko:produk-detail', slug=slug)


@login_required()
def remove_from_cart(request, slug):
    if request.user.is_authenticated:
        produk_item = get_object_or_404(ProdukItem, slug=slug)
        order_query = Order.objects.filter(
            user=request.user, ordered=False
        )
        if order_query.exists():
            order = order_query[0]
            if order.produk_items.filter(produk_item__slug=produk_item.slug).exists():
                try:
                    order_produk_item = OrderProdukItem.objects.filter(
                        produk_item=produk_item,
                        user=request.user,
                        ordered=False
                    )[0]

                    order.produk_items.remove(order_produk_item)
                    order_produk_item.delete()

                    pesan = f"ProdukItem sudah dihapus"
                    messages.info(request, pesan)
                    return redirect('toko:produk-detail', slug=slug)
                except ObjectDoesNotExist:
                    print('Error: order ProdukItem sudah tidak ada')
            else:
                messages.info(request, 'ProdukItem tidak ada')
                return redirect('toko:produk-detail', slug=slug)
        else:
            messages.info(request, 'ProdukItem tidak ada order yang aktif')
            return redirect('toko:produk-detail', slug=slug)
    else:
        return redirect('/accounts/login')

# @csrf_exempt


def paypal_return(request):
    if request.user.is_authenticated:
        try:
            print('paypal return', request)
            order = Order.objects.get(user=request.user, ordered=False)
            payment = Payment()
            payment.user = request.user
            payment.amount = order.get_total_harga_order()
            payment.payment_option = 'P'  # paypal kalai 'S' stripe
            payment.charge_id = f'{order.id}-{timezone.now()}'
            payment.timestamp = timezone.now()
            payment.save()

            order_produk_item = OrderProdukItem.objects.filter(
                user=request.user, ordered=False)
            order_produk_item.update(ordered=True)

            order.payment = payment
            order.ordered = True
            order.save()

            messages.info(request, 'Pembayaran sudah diterima, terima kasih')
            return redirect('toko:home-produk-list')
        except ObjectDoesNotExist:
            messages.error(request, 'Periksa kembali pesananmu')
            return redirect('toko:order-summary')
    else:
        return redirect('/accounts/login')

# @csrf_exempt


def paypal_cancel(request):
    messages.error(request, 'Pembayaran dibatalkan')
    return redirect('toko:order-summary')


def sortir_produk(request):
    kategori = request.GET.get('kategori')
    if kategori == 'all':
        produk = ProdukItem.objects.all()
    else:
        produk = ProdukItem.objects.filter(kategori=kategori)
    context = {
        'produk': produk,
        'kategori': kategori
    }
    return render(request, 'sortir_produk.html', context)


def search_produk(request):
    query = request.GET.get('query')
    produk = ProdukItem.objects.all()
    if query:
        produk = produk.filter(nama_produk__icontains=query)
    context = {
        'produk': produk,
        'query': query
    }
    return render(request, 'search.html', context)


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            nama = form.cleaned_data['nama']
            email = form.cleaned_data['email']
            pesan = form.cleaned_data['pesan']

            # Mengirim email ke perusahaan
            send_mail(
                'Pesan dari Customer E-commerce Django',
                f'Nama: {nama}\nEmail: {email}\nPesan: {pesan}',
                email,
                ['witc3sore@gmail.com'],
                fail_silently=False,
            )

            # Ganti dengan URL halaman sukses pengiriman pesan
            messages.info(
                request, "Pesan kamu sudah kami terima, thank you for contacting us!")
            return redirect('toko:contact')
    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})

