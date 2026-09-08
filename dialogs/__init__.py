from dialogs.user_dialog.dialog import user_dialog
from dialogs.gifts_dialog.dialog import gift_dialog
from dialogs.admin_dialog.dialog import admin_dialog
from dialogs.sub_dialog.dialog import sub_dialog
from dialogs.payment_dialog.dialog import payment_dialog


def get_dialogs():
    return [user_dialog, gift_dialog, payment_dialog, sub_dialog, admin_dialog]