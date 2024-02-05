from random import randint
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from .forms import *
from django.contrib.auth import login, logout
from django.contrib import messages
from django.db.models import Q
from .models import *
from django.views.generic import ListView, DetailView
from .utils import CartAuthenticatedUser, get_cart_data
import stripe
from shop import settings


class ProductList(ListView):
    model = Product
    context_object_name = 'categories'
    extra_context = {
        'title': 'TOTEMBO: Главная страница'
    }
    template_name = 'store/product_list.html'

    def get_queryset(self):
        categories = Category.objects.filter(parent=None)
        return categories


class CategoryView(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'store/category_page.html'

    paginate_by = 3

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        main_category = Category.objects.get(slug=self.kwargs['slug'])
        context['category'] = main_category
        context['title'] = f'Категория: {main_category.title}'
        return context

    def get_queryset(self):
        sort_field = self.request.GET.get('sort')
        type_field = self.request.GET.get('type')

        if type_field:
            products = Product.objects.filter(category__slug=type_field)
            return products
        main_category = Category.objects.get(slug=self.kwargs['slug'])
        subcategories = main_category.subcategories.all()
        products = Product.objects.filter(category__in=subcategories)

        if sort_field:
            products = products.order_by(sort_field)
        return products


class ProductDetail(DetailView):
    model = Product
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        product = Product.objects.get(slug=self.kwargs['slug'])
        context['title'] = f'{product.title}'

        products = Product.objects.all()
        data = []
        for i in range(5):
            random_index = randint(0, len(products) - 1)
            p = products[random_index]
            if p not in data:
                data.append(p)
        context['products'] = data

        context['reviews'] = Review.objects.filter(product=product)

        if self.request.user.is_authenticated:
            context['review_form'] = ReviewForms()

        return context


def save_review(request, product_id):
    form = ReviewForms(data=request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.author = request.user
        product = Product.objects.get(pk=product_id)
        review.product = product
        review.save()
    else:
        pass
    return redirect('product_detail', product.slug)


def login_registration(request):
    context = {
        'title': 'Войти или зарегистрироваться',
        'login_form': LoginForm(),
        'register_form': RegistrationForm
    }

    return render(request, 'store/login_register.html', context)


def user_login(request):
    form = LoginForm(data=request.POST)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, 'Вы вошли в аккаунт!')
        return redirect('product_list')
    else:
        messages.error(request, 'Что-то пошло не так!')
        return redirect('login_registration')


def user_logout(request):
    logout(request)
    messages.warning(request, 'Уже уходите ??')
    return redirect('login')


def register(request):
    form = RegistrationForm(data=request.POST)
    if form.is_valid():
        user = form.save()
        messages.success(request, 'Регистрация прошла успешно!')
        return redirect('product_list')
    else:
        for field in form.errors:
            messages.error(request, form.errors[field].as_text())

    return redirect('login_registration')


def save_favourite_product(request, product_slug):
    user = request.user if request.user.is_authenticated else None
    product = Product.objects.get(slug=product_slug)
    favourite_products = FavouriteProducts.objects.filter(user=user)
    if user:
        if product in [i.product for i in favourite_products]:
            fav_product = FavouriteProducts.objects.get(user=user, product=product)
            fav_product.delete()
        else:
            FavouriteProducts.objects.create(user=user, product=product)
    next_page = request.META.get('HTTPS_REFERER', 'product_list')
    return redirect(next_page)


class FavouriteProductsView(LoginRequiredMixin, ListView):
    model = FavouriteProducts
    context_object_name = 'products'
    template_name = 'store/favourite_products.html'
    login_url = 'login_registration'

    def get_queryset(self):
        user = self.request.user
        favs = FavouriteProducts.objects.filter(user=user)
        products = [i.product for i in favs]
        return products


def cart(request):
    cart_info = get_cart_data(request)

    context = {
        'cart_total_quantity': cart_info['cart_total_quantity'],
        'order': cart_info['order'],
        'products': cart_info['products']
    }

    return render(request, 'store/cart.html', context)


def to_cart(request, product_id, action):
    if request.user.is_authenticated:
        user_cart = CartAuthenticatedUser(request, product_id, action)
        return redirect('cart')
    else:
        messages.error(request, 'Авторизуйтесь что бы совершить покупку!')
        return redirect('login_registration')


def checkout(request):
    cart_info = get_cart_data(request)

    context = {
        'cart_total_quantity': cart_info['cart_total_quantity'],
        'order': cart_info['order'],
        'products': cart_info['products'],
        'title': 'Оформление заказа',
        'customer_form': CustomerForm(),
        'shipping_form': ShippingForm()
    }

    return render(request, 'store/checkout.html', context)


def create_checkout_session(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    if request.method == 'POST':
        user_cart = CartAuthenticatedUser(request)
        cart_info = user_cart.get_cart_info()

        total_price = cart_info['cart_total_price']
        session = stripe.checkout.Session.create(
            line_items=[{
                'price_data': {
                    'currency': "usd",
                    'product_data': {
                        'name': 'Товар магазина: TOTEMBO'
                    },
                    'unit_amount': int(total_price * 100)
                },
                'quantity': 1
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('product_list')),
            cancel_url=request.build_absolute_uri(reverse('checkout'))
        )
        return redirect(session.url, 303)


def successPayment(request):
    user_cart = CartAuthenticatedUser(request)
    user_cart.clear()
    messages.success(request, 'Оплата прошла успешно')
    return redirect('product_list')


def clear_cart(request):
    user_cart = CartAuthenticatedUser(request)
    order = user_cart.get_cart_info()['order']
    order_products = order.orderproduct_set.all()
    for order_product in order_products:
        quantity = order_product.quantity
        product = order_product.product
        order_product.delete()
        product.quantity += quantity
        product.save()
    return redirect('cart')


def search(request):
    word = request.GET.get('q')
    products = Product.objects.filter(
        Q(title__icontains=word) | Q(description__icontains=word)
    )

    context = {
        'products': products
    }

    return render(request, 'store/product_list.html', context)


def profile(request):
    return render(request, 'store/profile.html')
