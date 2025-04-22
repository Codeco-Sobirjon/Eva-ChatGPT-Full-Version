# import hashlib
# import urllib.parse
#
# merchant_login = "sobirbobojonov2000@gmail.com"
# password1 = "E802VhP4wJVuT6XrHIBd"
# out_sum = "500.00"
# invoice_id = "1"
# description = "askEVA plan"
#
# # Генерация подписи
# sign_str = f"{merchant_login}:{out_sum}:{invoice_id}:{password1}"
# signature = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
#
# # Кодируем описание
# encoded_description = urllib.parse.quote(description)
#
# # Собираем итоговую ссылку
# payment_url = (
#     f"https://auth.robokassa.ru/Merchant/Index.aspx?"
#     f"MerchantLogin={merchant_login}"
#     f"&OutSum={out_sum}"
#     f"&InvoiceID={invoice_id}"
#     f"&Description={encoded_description}"
#     f"&SignatureValue={signature}"
#     f"&Culture=ru"
#     f"&Encoding=utf-8"
# )
#
# print(payment_url)
