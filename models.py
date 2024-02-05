from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class Category(models.Model):
    title = models.CharField(max_length=150, verbose_name='Designation of category')
    image = models.ImageField(upload_to='categories/', null=True, blank=True, verbose_name='Photos')
    slug = models.SlugField(unique=True, null=True)
    parent = models.ForeignKey('self',
                               on_delete=models.CASCADE,
                               null=True, blank=True,
                               verbose_name='Category',
                               related_name='subcategories')

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})

    def get_image(self):
        if self.image:
            return self.image.url
        else:
            return 'https://cdn5.vectorstock.com/i/1000x1000/74/09/no-watch-not-allow-smart-red-circle-vector-31667409.jpg'

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'Category: pk={self.pk}, title={self.title}'

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class Product(models.Model):
    title = models.CharField(max_length=150, verbose_name='Designation of product')
    price = models.FloatField(verbose_name='Price')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date of creation')
    quantity = models.IntegerField(default=0, verbose_name='Quantity in composition')
    description = models.TextField(default='Soon...!', verbose_name='Description of product')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Category', related_name='products')
    slug = models.SlugField(unique=True, null=True)
    size = models.IntegerField(default=30, verbose_name='Size in mm')
    color = models.CharField(max_length=40, default='silver', verbose_name='Color/Material')

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})

    def get_first_photo(self):
        if self.images:
            try:
                return self.images.first().image.url
            except:
                return 'https://cdn5.vectorstock.com/i/1000x1000/74/09/no-watch-not-allow-smart-red-circle-vector-31667409.jpg'
        else:
            return ''

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'Product: pk={self.pk}, title={self.title}, price={self.price}'

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'


class Gallery(models.Model):
    image = models.ImageField(upload_to='products/', verbose_name='Pictures')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')

    class Meta:
        verbose_name = 'Pictures'
        verbose_name_plural = 'Pictures of products'


class Review(models.Model):
    text = models.TextField(verbose_name='Текст отзыв')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.author.username

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'


class FavouriteProducts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Продукт')

    def __str__(self):
        return self.product.title

    class Meta:
        verbose_name = 'Избранный товар'
        verbose_name_plural = 'Избранные товары'


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Покупатель')
    first_name = models.CharField(max_length=255, verbose_name='Имя покупателя', default='')
    last_name = models.CharField(max_length=255, verbose_name='Фамилия покупателя', default='')

    def __str__(self):
        return self.first_name

    class Meta:
        verbose_name = 'Покупатель'
        verbose_name_plural = 'Покупатели'


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Покупатель')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата заказа')
    shipping = models.BooleanField(default=True, verbose_name='Доставка')

    def __str__(self):
        return str(self.pk) + '  '

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    @property
    def get_cart_total_price(self):
        order_products = self.orderproduct_set.all()
        total_price = sum([product.get_total_price for product in order_products])
        return total_price

    @property
    def get_cart_total_quantity(self):
        order_products = self.orderproduct_set.all()
        total_quantity = sum([product.quantity for product in order_products])
        return total_quantity


class OrderProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name='Продукт')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, verbose_name='Заказ')
    quantity = models.IntegerField(default=0, null=True, blank=True, verbose_name='Количество')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказе'

    @property
    def get_total_price(self):
        total_price = self.product.price * self.quantity
        return total_price


class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address

    class Meta:
        verbose_name = 'Адресс доставки'
        verbose_name_plural = 'Адресса доставок'
