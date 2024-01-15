from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from cart.models import CartItem
from .forms import OrderForm
import datetime
from .models import Order, Payment, OrderProduct
import json
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from decimal import Decimal
from django.conf import settings
from django.urls import reverse

from django.shortcuts import render, redirect
from django.http import HttpResponse 
from django.views.generic import View, TemplateView, DetailView
from django.contrib import messages, auth
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from accounts.models import Account
from .models import Payment
from .ssl import sslcommerz_payment_gateway

@method_decorator(csrf_exempt, name='dispatch')
class CheckoutSuccessView(View):
    model = Payment
    template_name = 'orders/success.html'
    
    def post(self, request, *args, **kwargs):

        data = self.request.POST
        try: 
            user_id = int(data['value_a'])  # Retrieve the stored user ID as an integer
            user = Account.objects.get(pk=user_id)
            order = Order.objects.get(user=user, is_ordered=False, order_number=data['value_b'])
            payment = Payment(
                user = user,
                payment_id = data['tran_id'],
                payment_method = data['card_type'],
                amount_paid = order.order_total,
                status = data['status'],
            )
            payment.save()

            order.payment = payment
            order.is_ordered = True
            order.save()
            # Move the cart items to Order Product table
            cart_items = CartItem.objects.filter(user=user)

            for item in cart_items:
                orderproduct = OrderProduct()
                orderproduct.order_id = order.id
                orderproduct.payment = payment
                orderproduct.user_id = user_id
                orderproduct.product_id = item.product_id
                orderproduct.quantity = item.quantity
                orderproduct.product_price = item.product.price
                orderproduct.ordered = True
                orderproduct.save()

                cart_item = CartItem.objects.get(id=item.id)
                orderproduct = OrderProduct.objects.get(id=orderproduct.id)
                orderproduct.save()

                # Reduce the quantity of the sold products
                product = Product.objects.get(id=item.product_id)
                product.stock -= item.quantity
                product.save()

            # Clear cart
            CartItem.objects.filter(user=user).delete()
            auth.login(request, user)
            mail_subject = 'Thank you for your order!'
            message = render_to_string('orders/order_recieved_email.html', {
                'user': user,
                'order': order,
            })
            to_email = data['value_c']
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            url = reverse('order_complete') + f'?order_id={order.order_number}&transaction_id={payment.payment_id}'

            return redirect(url)

        except:
            messages.success(request,'Something Went Wrong')
        
        return render(request, 'orders/success.html')


@method_decorator(csrf_exempt, name='dispatch')
class CheckoutFaildView(View):
    template_name = 'failed.html'
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        return render(request, self.template_name)

def place_order(request, total=0, quantity=0,):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total)/100
    grand_total = total + tax
    print(current_user)
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            form.instance.user = current_user
            form.instance.order_total = grand_total
            form.instance.tax = tax
            form.instance.ip = request.META.get('REMOTE_ADDR')
            saved_instance = form.save()  # Save the form data to the database
            saved_instance_id = saved_instance.id 
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(saved_instance_id)
            form.instance.order_number = order_number
            form.save()
            print("order number indeis ", order_number)
            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            return redirect(sslcommerz_payment_gateway(request,order_number, str(current_user.id), grand_total, form.instance.email))
         
    else:
        return render(request, 'orders/payments.html')


def order_complete(request):
    order_number = request.GET.get('order_id')
    transID = request.GET.get('transaction_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
