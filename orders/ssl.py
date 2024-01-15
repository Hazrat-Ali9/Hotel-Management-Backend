import string
import random
from django.conf import settings
from django.contrib.auth.decorators import login_required  # Import the login_required decorator
from django.http import HttpResponse, JsonResponse
from sslcommerz_lib import SSLCOMMERZ
from .models import PaymentGatewaySettings

def unique_trangection_id_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

@login_required  # Apply the login_required decorator to ensure the user is logged in
def sslcommerz_payment_gateway(request, number, id, amount, email):
    gateway_auth_details = PaymentGatewaySettings.objects.all().first()
    settings = {'store_id': gateway_auth_details.store_id,
                'store_pass': gateway_auth_details.store_pass, 'issandbox': True}

    sslcommez = SSLCOMMERZ(settings)
    post_body = {}
    post_body['total_amount'] = amount
    post_body['currency'] = "BDT"
    post_body['tran_id'] = unique_trangection_id_generator()
    post_body['success_url'] = 'http://127.0.0.1:8000/orders/payment/success/'
    post_body['fail_url'] = 'http://127.0.0.1:8000/orders/payment/faild/'
    post_body['cancel_url'] = 'http://127.0.0.1:8000/'
    post_body['emi_option'] = 0
    post_body['cus_email'] = 'request.user.email'  # Retrieve email from the current user session
    post_body['cus_phone'] = 'request.user.phone'  # Retrieve phone from the current user session
    post_body['cus_add1'] = 'request.user.address'  # Retrieve address from the current user session
    post_body['cus_city'] = 'request.user.city'  # Retrieve city from the current user session
    post_body['cus_country'] = 'Bangladesh'
    post_body['shipping_method'] = "NO"
    post_body['multi_card_name'] = ""
    post_body['num_of_item'] = 1
    post_body['product_name'] = "Test"
    post_body['product_category'] = "Test Category"
    post_body['product_profile'] = "general"

    # OPTIONAL PARAMETERS
    post_body['value_a'] = id
    post_body['value_b'] = number
    post_body['value_c'] = email

    response = sslcommez.createSession(post_body)
    # print(response)
    # return JsonResponse(response)
    return 'https://sandbox.sslcommerz.com/gwprocess/v4/gw.php?Q=pay&SESSIONKEY=' + response["sessionkey"]
