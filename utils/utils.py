import random
import requests

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

from celery import shared_task

from customer_auth.models import EditPhoneOtp
from users.models import Owner, Manager, OutletManager, Otp, TemporaryEmail
from customer.models import Customer

User = get_user_model()


def get_otp():
    return random.randint(1000, 9999)


@shared_task
def send_otp_via_mail(to_email, change_email=False):
    otp = get_otp()
    message = f"Your otp is {otp}"
    subject = "Confirm your email - onnow.io"
    email_from = settings.EMAIL_HOST_USER
    send_mail(subject, message, email_from, [to_email])

    if change_email == False:
        user = User.objects.filter(email=to_email).first()
    else:
        tempEmailObj = TemporaryEmail.objects.filter(email=to_email).first()
        user = tempEmailObj.user

    otp_obj = Otp.objects.create(user=user, otp=otp)
    otp_obj.save()


def send_otp_sms(to_phone):
    otp = get_otp()
    message = f"Your otp for onnow.io is {otp}"
    user = User.objects.filter(phone_number=to_phone).first()
    otp_obj = Otp.objects.create(user=user, otp=otp)
    otp_obj.save()
    url = "https://api.sms.net.bd/sendsms"

    payload = {'api_key': '43UMeTGY4kSoap2a9mBpJAtgH2poWg9lR3xAItrJ',
               'msg': message,
               'to': to_phone
               }

    response = requests.request("POST", url, data=payload)
    return response


def send_phone_edit_otp_sms(to_phone):
    otp = get_otp()
    message = f"Your otp for onnow.io is {otp}"
    otp_obj = EditPhoneOtp.objects.create(phone=to_phone, otp=otp)
    otp_obj.save()
    url = "https://api.sms.net.bd/sendsms"

    payload = {'api_key': '43UMeTGY4kSoap2a9mBpJAtgH2poWg9lR3xAItrJ',
               'msg': message,
               'to': to_phone
               }

    response = requests.request("POST", url, data=payload)
    return response


def create_user_profile(user):
    if user.user_type == 'ACO':
        Owner.objects.create(user=user)
    elif user.user_type == 'MGR':
        Manager.objects.create(user=user)
    elif user.user_type == 'STF':
        OutletManager.objects.create(user=user)
    else:
        Customer.objects.create(user=user)


@shared_task
def send_invitation_link(data):
    template = render_to_string('activate_profile.html', {
        'absurl': data.get('absurl'),

        'name': data.get('name'),
        'url': data.get('url'),
        'to_email': data.get('to_email'),
        'user_type': data.get('user_type')
    })
    user_type = data.get('user_type')
    if user_type == 'MGR':
        user_type = 'Brand Manager'
    else:
        user_type = 'Outlet Manager'

    email_body = template
    email_subject = 'Activate your manager account - onnow.io'
    email_from = settings.EMAIL_HOST_USER
    send_mail(
        subject=email_subject,
        message=None,
        from_email=email_from,
        recipient_list=[data.get('to_email')],
        html_message=template
    )


@shared_task
def send_profile_creation_notification_email(data):
    user_type = data.get('user_type')
    if user_type == 'MGR':
        user_type = 'Brand Manager'
    else:
        user_type = 'Outlet Manager'

    template = render_to_string('staff_joined_notification.html', {
        'owner_name': data.get('owner_name'),
        'staff_name': data.get('user_name'),
        'user_type': user_type,
        # 'absurl': data.get('absurl'),
        'absurl': 'https://app.onnow.io/invitation',
        'email': data.get('to_email')
    })

    email_subject = f'A new {user_type} has joined your team - onnow.io'
    email_from = settings.EMAIL_HOST_USER
    send_mail(
        subject=email_subject,
        message=None,
        from_email=email_from,
        recipient_list=[data.get('to_email')],
        html_message=template
    )
